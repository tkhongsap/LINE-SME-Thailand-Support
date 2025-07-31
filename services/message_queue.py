import json
import time
import logging
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
from queue import Queue, Empty
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future
import uuid

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class QueueTask:
    """Represents a task in the message queue"""
    id: str
    task_type: str
    payload: Dict[str, Any]
    user_id: str
    reply_token: Optional[str] = None
    priority: int = 0  # Lower numbers = higher priority
    max_retries: int = 3
    retry_count: int = 0
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class MessageQueue:
    """In-memory message queue for processing LINE webhook events asynchronously"""
    
    def __init__(self, max_workers: int = 5):
        self.task_queue = Queue()
        self.processing_tasks = {}
        self.completed_tasks = {}
        self.failed_tasks = {}
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.shutdown = False
        self.task_handlers = {}
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'pending_tasks': 0,
            'processing_tasks': 0
        }
        
        # Start worker threads
        self._start_workers()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_old_tasks, daemon=True)
        self.cleanup_thread.start()
    
    def register_handler(self, task_type: str, handler: Callable[[QueueTask], Any]):
        """Register a handler for a specific task type"""
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    def enqueue(self, task: QueueTask) -> str:
        """Add a task to the queue"""
        self.task_queue.put(task)
        self.stats['total_tasks'] += 1
        self.stats['pending_tasks'] += 1
        
        logger.info(f"Enqueued task {task.id} of type {task.task_type}")
        return task.id
    
    def enqueue_text_processing(self, user_id: str, user_message: str, 
                              reply_token: str, user_context: Dict = None) -> str:
        """Convenience method to enqueue text processing task"""
        task = QueueTask(
            id=str(uuid.uuid4()),
            task_type="text_processing",
            payload={
                'user_message': user_message,
                'user_context': user_context or {}
            },
            user_id=user_id,
            reply_token=reply_token,
            priority=1
        )
        return self.enqueue(task)
    
    def enqueue_file_processing(self, user_id: str, file_content: bytes, 
                              filename: str, reply_token: str,
                              user_context: Dict = None) -> str:
        """Convenience method to enqueue file processing task"""
        task = QueueTask(
            id=str(uuid.uuid4()),
            task_type="file_processing",
            payload={
                'file_content': file_content,
                'filename': filename,
                'user_context': user_context or {}
            },
            user_id=user_id,
            reply_token=reply_token,
            priority=2  # Lower priority than text
        )
        return self.enqueue(task)
    
    def enqueue_image_processing(self, user_id: str, image_content: bytes,
                               reply_token: str, user_context: Dict = None) -> str:
        """Convenience method to enqueue image processing task"""
        task = QueueTask(
            id=str(uuid.uuid4()),
            task_type="image_processing",
            payload={
                'image_content': image_content,
                'user_context': user_context or {}
            },
            user_id=user_id,
            reply_token=reply_token,
            priority=2
        )
        return self.enqueue(task)
    
    def enqueue_long_running_task(self, user_id: str, task_data: Dict,
                                reply_token: str = None, push_message: bool = True) -> str:
        """Enqueue a long-running task that may need push messages"""
        task = QueueTask(
            id=str(uuid.uuid4()),
            task_type="long_running_task",
            payload={
                'task_data': task_data,
                'push_message': push_message
            },
            user_id=user_id,
            reply_token=reply_token,
            priority=3
        )
        return self.enqueue(task)
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a specific task"""
        # Check processing tasks
        if task_id in self.processing_tasks:
            task = self.processing_tasks[task_id]
            return {
                'id': task.id,
                'status': task.status.value,
                'progress': self._calculate_progress(task),
                'created_at': task.created_at,
                'started_at': task.started_at
            }
        
        # Check completed tasks
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return {
                'id': task.id,
                'status': task.status.value,
                'progress': 100,
                'created_at': task.created_at,
                'started_at': task.started_at,
                'completed_at': task.completed_at
            }
        
        # Check failed tasks
        if task_id in self.failed_tasks:
            task = self.failed_tasks[task_id]
            return {
                'id': task.id,
                'status': task.status.value,
                'error': task.error_message,
                'created_at': task.created_at,
                'retry_count': task.retry_count
            }
        
        return None
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        return {
            **self.stats,
            'pending_tasks': self.task_queue.qsize(),
            'processing_tasks': len(self.processing_tasks),
            'queue_health': 'healthy' if not self.shutdown else 'shutdown',
            'worker_count': self.max_workers
        }
    
    def get_user_tasks(self, user_id: str) -> List[Dict]:
        """Get all tasks for a specific user"""
        user_tasks = []
        
        # Check processing tasks
        for task in self.processing_tasks.values():
            if task.user_id == user_id:
                user_tasks.append({
                    'id': task.id,
                    'type': task.task_type,
                    'status': task.status.value,
                    'created_at': task.created_at
                })
        
        # Check recent completed/failed tasks
        for task_dict in [self.completed_tasks, self.failed_tasks]:
            for task in task_dict.values():
                if task.user_id == user_id:
                    user_tasks.append({
                        'id': task.id,
                        'type': task.task_type,
                        'status': task.status.value,
                        'created_at': task.created_at
                    })
        
        return sorted(user_tasks, key=lambda x: x['created_at'], reverse=True)
    
    def _start_workers(self):
        """Start worker threads to process tasks"""
        for i in range(self.max_workers):
            worker_thread = threading.Thread(
                target=self._worker_loop,
                name=f"MessageQueueWorker-{i}",
                daemon=True
            )
            worker_thread.start()
            logger.info(f"Started worker thread {i}")
    
    def _worker_loop(self):
        """Main worker loop"""
        while not self.shutdown:
            try:
                # Get task with timeout
                task = self.task_queue.get(timeout=1)
                self.stats['pending_tasks'] -= 1
                
                self._process_task(task)
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def _process_task(self, task: QueueTask):
        """Process a single task with timeout handling"""
        task.status = TaskStatus.PROCESSING
        task.started_at = time.time()
        self.processing_tasks[task.id] = task
        self.stats['processing_tasks'] += 1
        
        logger.info(f"Processing task {task.id} of type {task.task_type} for user {task.user_id}")
        
        # Set maximum task execution time
        MAX_TASK_TIMEOUT = 30  # 30 seconds timeout
        
        try:
            # Get handler for task type
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise Exception(f"No handler registered for task type: {task.task_type}")
            
            # Execute handler with timeout
            from concurrent.futures import TimeoutError
            future = self.executor.submit(handler, task)
            
            try:
                result = future.result(timeout=MAX_TASK_TIMEOUT)
            except TimeoutError:
                logger.error(f"Task {task.id} timed out after {MAX_TASK_TIMEOUT}s")
                future.cancel()
                raise Exception(f"Task timed out after {MAX_TASK_TIMEOUT} seconds")
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            
            # Move to completed tasks
            self.completed_tasks[task.id] = task
            del self.processing_tasks[task.id]
            
            self.stats['processing_tasks'] -= 1
            self.stats['completed_tasks'] += 1
            
            processing_time = task.completed_at - task.started_at
            logger.info(f"Completed task {task.id} in {processing_time:.2f}s")
            
        except Exception as e:
            processing_time = time.time() - task.started_at if task.started_at else 0
            logger.error(f"Task {task.id} failed after {processing_time:.2f}s: {e}")
            
            task.error_message = str(e)
            task.retry_count += 1
            
            # Check if we should retry (but not for timeout errors)
            if task.retry_count < task.max_retries and "timed out" not in str(e):
                task.status = TaskStatus.RETRYING
                # Re-queue with delay
                retry_delay = min(2 ** task.retry_count, 30)  # Exponential backoff with max 30s
                threading.Timer(retry_delay, lambda: self.enqueue(task)).start()
                logger.info(f"Retrying task {task.id} in {retry_delay}s (attempt {task.retry_count + 1}/{task.max_retries})")
            else:
                # Mark as failed
                task.status = TaskStatus.FAILED
                task.completed_at = time.time()
                self.failed_tasks[task.id] = task
                self.stats['failed_tasks'] += 1
                logger.error(f"Task {task.id} permanently failed after {task.retry_count} attempts")
            
            # Remove from processing
            if task.id in self.processing_tasks:
                del self.processing_tasks[task.id]
                self.stats['processing_tasks'] -= 1
    
    def _calculate_progress(self, task: QueueTask) -> int:
        """Calculate progress percentage for a task"""
        if task.status == TaskStatus.PENDING:
            return 0
        elif task.status == TaskStatus.PROCESSING:
            # Estimate based on time elapsed
            elapsed = time.time() - task.started_at
            # Assume average task takes 10 seconds
            progress = min(90, int((elapsed / 10) * 100))
            return progress
        elif task.status == TaskStatus.COMPLETED:
            return 100
        else:
            return 0
    
    def _cleanup_old_tasks(self):
        """Clean up old completed and failed tasks"""
        while not self.shutdown:
            try:
                current_time = time.time()
                cleanup_threshold = current_time - (24 * 60 * 60)  # 24 hours
                
                # Clean completed tasks
                to_remove = []
                for task_id, task in self.completed_tasks.items():
                    if task.completed_at and task.completed_at < cleanup_threshold:
                        to_remove.append(task_id)
                
                for task_id in to_remove:
                    del self.completed_tasks[task_id]
                
                # Clean failed tasks
                to_remove = []
                for task_id, task in self.failed_tasks.items():
                    if task.created_at < cleanup_threshold:
                        to_remove.append(task_id)
                
                for task_id in to_remove:
                    del self.failed_tasks[task_id]
                
                if to_remove:
                    logger.info(f"Cleaned up {len(to_remove)} old tasks")
                
                # Sleep for 1 hour before next cleanup
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                time.sleep(60)  # Retry in 1 minute
    
    def shutdown_gracefully(self, timeout: int = 30):
        """Shutdown the queue gracefully"""
        logger.info("Shutting down message queue...")
        self.shutdown = True
        
        # Wait for current tasks to complete
        start_time = time.time()
        while self.processing_tasks and time.time() - start_time < timeout:
            time.sleep(1)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Message queue shutdown complete")


# Global queue instance
message_queue = MessageQueue(max_workers=Config.CONNECTION_POOL_SIZE)


def send_processing_status(user_id: str, task_id: str, message: str):
    """Send processing status update to user"""
    from services.line_service_optimized import OptimizedLineService
    from linebot.models import TextSendMessage
    
    try:
        line_service = OptimizedLineService()
        status_message = TextSendMessage(text=f"🔄 {message}\n(Task ID: {task_id[:8]}...)")
        line_service.push_message(user_id, [status_message])
    except Exception as e:
        logger.error(f"Failed to send status update: {e}")