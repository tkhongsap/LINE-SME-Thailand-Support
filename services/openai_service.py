import logging
import base64
import asyncio
import time
from typing import Dict, List, Optional, Iterator
from openai import AzureOpenAI
from config import Config
from utils.logger import setup_logger
from prompts.mega_prompt import MegaPrompt
from services.ai_optimizer import (
    ai_optimizer, TokenUsage, ModelType,
    ContextOptimizer, ResponseCache, RequestOptimizer
)
from services.metrics_collector import metrics_collector

logger = setup_logger(__name__)

class OpenAIService:
    def __init__(self):
        self.config_valid = Config.validate_config()
        if self.config_valid:
            logger.info(f"Azure OpenAI Configuration:")
            logger.info(f"  Endpoint: {Config.AZURE_OPENAI_ENDPOINT}")
            logger.info(f"  API Version: {Config.AZURE_OPENAI_API_VERSION}")
            logger.info(f"  Deployment: {Config.AZURE_OPENAI_DEPLOYMENT_NAME}")
            logger.info(f"  API Key: {'***' + Config.AZURE_OPENAI_API_KEY[-4:] if Config.AZURE_OPENAI_API_KEY else 'None'}")
            
            try:
                self.client = AzureOpenAI(
                    api_key=Config.AZURE_OPENAI_API_KEY,
                    api_version=Config.AZURE_OPENAI_API_VERSION,
                    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
                )
                self.deployment_name = Config.AZURE_OPENAI_DEPLOYMENT_NAME
                logger.info("Azure OpenAI client initialized successfully")
                
                # Test connectivity
                self._test_azure_openai_connectivity()
                
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {e}", exc_info=True)
                logger.warning("Falling back to development mode due to initialization failure")
                self.config_valid = False
                self.client = None
                self.deployment_name = None
        else:
            logger.warning("Azure OpenAI credentials not configured. Running in development mode.")
            self.client = None
            self.deployment_name = None
        
        # Initialize optimization components
        self.ai_optimizer = ai_optimizer
        self.retry_config = {
            'max_retries': 3,
            'initial_delay': 1,
            'exponential_base': 2,
            'jitter': True
        }
        self._request_times = []  # For rate limiting
    
    def generate_text_response(self, user_message, conversation_history=None, user_context=None):
        """Generate text response using Azure OpenAI with enhanced Thai SME intelligence"""
        start_time = time.time()
        logger.info(f"Generating text response for message: {user_message[:50]}...")
        
        if not self.config_valid or not self.client:
            logger.warning("Using development response - Azure OpenAI not configured")
            return self._get_dev_response(user_message, 'text')
        
        try:
            # Use simplified context - let the AI handle cultural intelligence naturally
            enhanced_context = user_context or {}
            enhanced_system_prompt = None
            
            # Prepare optimization context
            task_type = self._detect_task_type(user_message)
            messages = self._build_messages(user_message, conversation_history, enhanced_context, enhanced_system_prompt)
            
            # Optimize request
            optimization = self.ai_optimizer.optimize_request(
                messages, user_context or {}, task_type
            )
            
            # Check for cached response
            if optimization['cached_response']:
                logger.info("Returning cached response")
                return optimization['cached_response']
            
            # Apply rate limiting
            self._apply_rate_limit()
            
            # Make API call with retry logic
            response = self._call_with_retry(
                optimization['messages'],
                optimization['model'] or self.deployment_name,
                optimization['max_tokens'],
                optimization['temperature']
            )
            
            response_text = response.choices[0].message.content
            
            # Post-process and cache
            token_usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                estimated_cost=self._calculate_cost(response.usage, optimization['model']),
                model=optimization['model'] or self.deployment_name,
                timestamp=time.time()
            )
            
            self.ai_optimizer.post_process_response(
                user_message, response_text, user_context or {}, token_usage
            )
            
            # Record performance metrics
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            user_id = user_context.get('user_id', 'anonymous') if user_context else 'anonymous'
            
            # Record user interaction metrics
            cultural_score = 0.85  # Would be calculated from SME analysis
            business_relevance = 0.80  # Would be calculated from SME analysis
            if Config.SME_INTELLIGENCE_ENABLED and user_context and 'sme_analysis' in enhanced_context:
                cultural_score = enhanced_context['sme_analysis'].get('cultural_appropriateness_score', 0.85)
                business_relevance = enhanced_context['sme_analysis'].get('business_relevance_score', 0.80)
            
            metrics_collector.record_user_interaction(
                user_id=user_id,
                interaction_type='text_generation',
                response_time=response_time / 1000,  # Convert back to seconds
                success=True,
                cultural_score=cultural_score,
                business_relevance=business_relevance,
                satisfaction_indicator='positive'
            )
            
            # Record AI usage metrics
            metrics_collector.record_ai_usage(
                model_used=token_usage.model,
                prompt_tokens=token_usage.prompt_tokens,
                completion_tokens=token_usage.completion_tokens,
                estimated_cost=token_usage.estimated_cost,
                task_type=task_type,
                user_context=enhanced_context or {},
                cache_hit=optimization.get('cached_response') is not None
            )
            
            # Record performance metric
            metrics_collector.record_performance_metric(
                metric_name='response_time',
                value=response_time,
                tags={'model': token_usage.model, 'task_type': task_type},
                category='performance'
            )
            
            logger.info(f"Generated text response - Tokens: {token_usage.total_tokens}, Cost: ${token_usage.estimated_cost:.4f}")
            return response_text
            
        except Exception as e:
            # Record error metrics
            response_time = (time.time() - start_time) * 1000
            user_id = user_context.get('user_id', 'anonymous') if user_context else 'anonymous'
            
            metrics_collector.record_user_interaction(
                user_id=user_id,
                interaction_type='text_generation',
                response_time=response_time / 1000,
                success=False,
                cultural_score=0.0,
                business_relevance=0.0,
                satisfaction_indicator='error'
            )
            
            metrics_collector.record_performance_metric(
                metric_name='error_count',
                value=1,
                tags={'error_type': 'openai_error', 'function': 'generate_text_response'},
                category='errors'
            )
            
            logger.error(f"Azure OpenAI API call failed: {e}", exc_info=True)
            logger.error(f"Failing over to development response instead of error message")
            
            # Instead of returning an error message, provide a helpful development response
            return self._get_dev_response(user_message, 'text')
    
    def analyze_image(self, image_content, user_message=None, user_context=None):
        """Analyze image using GPT-4 Vision with optimization"""
        if not self.config_valid or not self.client:
            return self._get_dev_response("Image uploaded", "image")
        
        try:
            # Optimize image size if needed
            optimized_image = self._optimize_image_for_analysis(image_content)
            
            # Encode image to base64
            image_base64 = base64.b64encode(optimized_image).decode('utf-8')
            
            # Use the single comprehensive mega prompt
            system_prompt = MegaPrompt.get_system_prompt()
            
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message or "Please analyze this image and provide business insights relevant to Thai SME operations."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            # Apply rate limiting
            self._apply_rate_limit()
            
            # Make API call with retry logic
            response = self._call_with_retry(
                messages,
                self.deployment_name,  # Always use GPT-4 for vision
                600,  # Optimized for image analysis
                0.4   # Lower temperature for accuracy
            )
            
            response_text = response.choices[0].message.content
            
            # Track usage
            token_usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                estimated_cost=self._calculate_cost(response.usage, self.deployment_name),
                model=self.deployment_name,
                timestamp=time.time()
            )
            
            self.ai_optimizer.post_process_response(
                user_message or "image_analysis", response_text, 
                user_context or {}, token_usage
            )
            
            logger.info(f"Generated image analysis - Tokens: {token_usage.total_tokens}")
            return response_text
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return self._get_error_message('invalid_image')
    
    def process_file_content(self, file_content, filename, user_message=None, user_context=None):
        """Process file content and generate response with optimization"""
        if not self.config_valid or not self.client:
            return self._get_dev_response(f"File uploaded: {filename}", "file")
        
        try:
            # Use optimized content if already processed, otherwise optimize
            if isinstance(file_content, str):
                # Already processed text content
                optimized_content = self._optimize_file_content(file_content, filename)
            else:
                # Raw file content, needs processing
                from services.streaming_file_processor import streaming_processor
                import asyncio
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    success, error_code, extracted_text, metadata = loop.run_until_complete(
                        streaming_processor.process_file_streaming(
                            file_content, filename, None, user_context or {}
                        )
                    )
                    
                    if not success:
                        return self._get_error_message(error_code)
                    
                    optimized_content = extracted_text
                finally:
                    loop.close()
            
            # Prepare context with file type
            enhanced_context = (user_context or {}).copy()
            enhanced_context['file_type'] = filename.split('.')[-1].lower()
            
            # Use the single comprehensive mega prompt
            system_prompt = MegaPrompt.get_system_prompt()
            
            # Build simple file prompt
            file_prompt = f"""File: {filename}
Content preview:
{optimized_content}

Request: {user_message or 'Analyze this file and provide actionable business insights for Thai SME operations.'}"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": file_prompt}
            ]
            
            # Check cache for similar file analysis
            cache_key = f"file_{filename}_{user_message}"
            cached_response = self.ai_optimizer.response_cache.get(cache_key, enhanced_context)
            if cached_response:
                logger.info(f"Returning cached file analysis for: {filename}")
                return cached_response
            
            # Determine task complexity
            task_type = 'document_analysis'
            complexity = self.ai_optimizer.model_selector.estimate_task_complexity(
                file_prompt, has_context=True
            )
            
            # Select model based on file size and complexity
            selected_model = self.ai_optimizer.model_selector.select_model(
                task_type, complexity, enhanced_context.get('tier', 'free')
            )
            
            # Apply rate limiting
            self._apply_rate_limit()
            
            # Make API call with retry logic
            response = self._call_with_retry(
                messages,
                selected_model.value,
                1000,  # Max tokens for file analysis
                0.5    # Balanced temperature
            )
            
            response_text = response.choices[0].message.content
            
            # Track usage
            token_usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                estimated_cost=self._calculate_cost(response.usage, selected_model.value),
                model=selected_model.value,
                timestamp=time.time()
            )
            
            # Update costs and cache
            self.ai_optimizer.model_selector.update_cost(selected_model, token_usage)
            self.ai_optimizer.response_cache.set(cache_key, response_text, enhanced_context)
            
            logger.info(f"Generated file analysis for {filename} - Model: {selected_model.value}, "
                       f"Tokens: {token_usage.total_tokens}, Cost: ${token_usage.estimated_cost:.4f}")
            return response_text
            
        except Exception as e:
            logger.error(f"Error processing file content: {e}")
            return self._get_error_message('processing_error')
    
    def _build_messages(self, user_message, conversation_history=None, user_context=None, enhanced_system_prompt=None):
        """Build optimized message history for conversation context using simplified mega prompt"""
        # Use the single comprehensive mega prompt
        system_prompt = MegaPrompt.get_system_prompt()
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history with compression if needed
        if conversation_history:
            # Limit history based on context window
            history_limit = min(Config.MAX_CONVERSATION_HISTORY, 8)
            recent_history = conversation_history[-history_limit:]
            
            # Check if we need to compress older context
            if len(conversation_history) > history_limit:
                summary = self.ai_optimizer.context_optimizer.summarize_old_context(
                    conversation_history, keep_recent=history_limit
                )
                if summary:
                    messages.append({
                        "role": "system", 
                        "content": f"Previous conversation summary: {summary}"
                    })
            
            # Add recent conversation history
            for conv in recent_history:
                if conv.user_message:
                    messages.append({"role": "user", "content": conv.user_message})
                if conv.bot_response:
                    messages.append({"role": "assistant", "content": conv.bot_response})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Compress if total context is too large
        if len(str(messages)) > 12000:  # Rough token estimate
            messages = self.ai_optimizer.context_optimizer.compress_context(
                messages, target_tokens=3000
            )
        
        return messages
    
    def _optimize_image_for_analysis(self, image_content: bytes) -> bytes:
        """Optimize image size and quality for analysis"""
        try:
            from PIL import Image
            import io
            
            # Load image
            image = Image.open(io.BytesIO(image_content))
            
            # Resize if too large (to save on token costs)
            max_size = (1024, 1024)  # Optimal for GPT-4 Vision
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image to {image.size} for optimization")
            
            # Convert to RGB if needed
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Save optimized image
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
            
        except ImportError:
            logger.warning("PIL not available, using original image")
            return image_content
        except Exception as e:
            logger.error(f"Error optimizing image: {e}")
            return image_content
    
    def _optimize_file_content(self, file_content: str, filename: str) -> str:
        """Optimize file content for efficient processing"""
        # Truncate very long content to manage token costs
        max_length = 8000  # Conservative limit
        
        if len(file_content) <= max_length:
            return file_content
        
        # For structured files, try to keep important sections
        file_ext = filename.lower().split('.')[-1]
        
        if file_ext in ['csv', 'xlsx']:
            # For spreadsheets, keep headers and first/last rows
            lines = file_content.split('\n')
            if len(lines) > 50:
                header_section = '\n'.join(lines[:10])
                sample_section = '\n'.join(lines[10:30])
                footer_section = '\n'.join(lines[-10:])
                
                return f"{header_section}\n\n[... {len(lines)-40} more rows ...]\n\n{sample_section}\n\n[... sample data ...]\n\n{footer_section}"
        
        elif file_ext in ['pdf', 'docx', 'txt']:
            # For documents, keep beginning and end
            truncated = file_content[:max_length//2] + '\n\n[... content truncated ...]\n\n' + file_content[-max_length//2:]
            return truncated
        
        # Default truncation
        return file_content[:max_length] + '\n\n[... content truncated for processing efficiency ...]'
    
    def get_optimization_metrics(self) -> Dict:
        """Get current optimization metrics"""
        return self.ai_optimizer.get_metrics_summary()
    

    
    def _get_error_message(self, error_type):
        """Get error message"""
        error_messages = MegaPrompt.get_error_messages()
        return error_messages.get(error_type, 'An error occurred.')
    
    def _get_dev_response(self, user_message, message_type='text'):
        """Generate development mode response when OpenAI is not configured"""
        dev_responses = MegaPrompt.get_dev_responses()
        
        if message_type == 'text':
            return dev_responses['text'].format(user_message=user_message)
        else:
            return dev_responses.get(message_type, dev_responses['text'].format(user_message=user_message))
    
    def _test_azure_openai_connectivity(self):
        """Test Azure OpenAI connectivity with minimal API call"""
        try:
            logger.info("Testing Azure OpenAI connectivity...")
            
            # Make a minimal test call
            test_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hi"}
            ]
            
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=test_messages,
                max_tokens=10,
                temperature=0.1
            )
            
            test_duration = time.time() - start_time
            logger.info(f"✅ Azure OpenAI connectivity test successful in {test_duration:.2f}s")
            logger.info(f"Test response: {response.choices[0].message.content[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Azure OpenAI connectivity test failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.warning("Azure OpenAI may not be properly configured or accessible")
            # Don't disable config here - let actual calls handle the fallback
    
    def _detect_task_type(self, user_message: str) -> str:
        """Detect task type from user message"""
        message_lower = user_message.lower()
        
        # Simple greeting detection
        greetings = ['สวัสดี', 'hello', 'hi', 'hey', 'ขอบคุณ', 'thank']
        if any(greeting in message_lower for greeting in greetings):
            return 'simple_greeting'
        
        # Business advice detection
        business_keywords = ['ธุรกิจ', 'business', 'การตลาด', 'marketing', 
                           'การเงิน', 'finance', 'ภาษี', 'tax']
        if any(keyword in message_lower for keyword in business_keywords):
            return 'business_advice'
        
        # Document analysis
        if 'วิเคราะห์' in message_lower or 'analyze' in message_lower:
            return 'document_analysis'
        
        return 'conversation'
    
    def _apply_rate_limit(self):
        """Apply rate limiting to prevent API overload"""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self._request_times = [t for t in self._request_times if current_time - t < 60]
        
        # Check rate limit (e.g., 60 requests per minute)
        if len(self._request_times) >= Config.RATE_LIMIT_PER_MINUTE:
            sleep_time = 60 - (current_time - self._request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self._request_times.append(current_time)
    
    def _call_with_retry(self, messages: List[Dict], model: str, 
                        max_tokens: int, temperature: float):
        """Call API with exponential backoff retry and comprehensive logging"""
        last_exception = None
        
        logger.info(f"Making Azure OpenAI API call:")
        logger.info(f"  Model: {model}")
        logger.info(f"  Messages: {len(messages)} messages")
        logger.info(f"  Max tokens: {max_tokens}")
        logger.info(f"  Temperature: {temperature}")
        
        for attempt in range(self.retry_config['max_retries']):
            try:
                logger.info(f"API call attempt {attempt + 1}/{self.retry_config['max_retries']}")
                start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.8,
                    frequency_penalty=0.1,
                    presence_penalty=0.1,
                    stream=False
                )
                
                call_duration = time.time() - start_time
                logger.info(f"Azure OpenAI API call successful in {call_duration:.2f}s")
                logger.info(f"Response usage: {response.usage.total_tokens} tokens")
                return response
                
            except Exception as e:
                call_duration = time.time() - start_time if 'start_time' in locals() else 0
                logger.error(f"API call failed after {call_duration:.2f}s")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Error message: {str(e)}")
                
                last_exception = e
                if attempt < self.retry_config['max_retries'] - 1:
                    # Calculate delay with exponential backoff
                    delay = self.retry_config['initial_delay'] * (
                        self.retry_config['exponential_base'] ** attempt
                    )
                    
                    # Add jitter if enabled
                    if self.retry_config['jitter']:
                        import random
                        delay *= (0.5 + random.random())
                    
                    logger.warning(f"Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.retry_config['max_retries']} API call attempts failed")
        
        raise last_exception
    
    def _calculate_cost(self, usage, model: str) -> float:
        """Calculate estimated cost based on token usage"""
        try:
            model_type = ModelType(model) if model else ModelType.GPT4
            costs = model_type.cost_per_1k_tokens
            
            input_cost = (usage.prompt_tokens / 1000) * costs['input']
            output_cost = (usage.completion_tokens / 1000) * costs['output']
            
            return input_cost + output_cost
        except:
            # Fallback to default GPT-4 pricing
            return (usage.prompt_tokens / 1000) * 0.03 + (usage.completion_tokens / 1000) * 0.06
    
    def generate_text_response_stream(self, user_message, conversation_history=None, 
                                    user_context=None) -> Iterator[str]:
        """Generate text response with streaming for real-time delivery"""
        if not self.config_valid or not self.client:
            yield self._get_dev_response(user_message, 'text')
            return
        
        try:
            # Prepare optimization context
            task_type = self._detect_task_type(user_message)
            messages = self._build_messages(user_message, conversation_history, user_context)
            
            # Optimize request
            optimization = self.ai_optimizer.optimize_request(
                messages, user_context or {}, task_type
            )
            
            # Check for cached response
            if optimization['cached_response']:
                logger.info("Returning cached response (streamed)")
                # Simulate streaming for cached response
                words = optimization['cached_response'].split()
                for i in range(0, len(words), 3):
                    yield ' '.join(words[i:i+3]) + ' '
                return
            
            # Apply rate limiting
            self._apply_rate_limit()
            
            # Make streaming API call
            stream = self.client.chat.completions.create(
                model=optimization['model'] or self.deployment_name,
                messages=optimization['messages'],
                max_tokens=optimization['max_tokens'],
                temperature=optimization['temperature'],
                top_p=0.8,
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # Cache the complete response
            if full_response:
                # Estimate token usage for caching
                estimated_tokens = len(full_response) // 4  # Rough estimate
                token_usage = TokenUsage(
                    prompt_tokens=len(str(optimization['messages'])) // 4,
                    completion_tokens=estimated_tokens,
                    total_tokens=estimated_tokens * 2,
                    estimated_cost=0.0,  # Will be calculated properly
                    model=optimization['model'] or self.deployment_name,
                    timestamp=time.time()
                )
                
                self.ai_optimizer.post_process_response(
                    user_message, full_response, user_context or {}, token_usage
                )
            
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield self._get_error_message('openai_error')
