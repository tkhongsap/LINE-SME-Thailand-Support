class Dashboard {
    constructor() {
        this.charts = {};
        this.currentPeriod = 7;
        this.currentPage = {
            conversations: 1,
            webhooks: 1,
            logs: 1
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadDashboard();
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            this.loadDashboard();
        }, 30000);
    }
    
    setupEventListeners() {
        // Time period selector
        document.querySelectorAll('input[name="timePeriod"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentPeriod = parseInt(e.target.value);
                this.loadDashboard();
            });
        });
        
        // Tab switching
        document.querySelectorAll('#dataTabs button').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const target = e.target.getAttribute('data-bs-target');
                if (target === '#conversations') {
                    this.loadConversations();
                } else if (target === '#webhooks') {
                    this.loadWebhooks();
                } else if (target === '#logs') {
                    this.loadLogs();
                }
            });
        });
        
        // Log level filter
        document.getElementById('logLevelFilter').addEventListener('change', () => {
            this.currentPage.logs = 1;
            this.loadLogs();
        });
    }
    
    async loadDashboard() {
        try {
            const response = await fetch(`/api/stats?days=${this.currentPeriod}`);
            const data = await response.json();
            
            this.updateSummaryCards(data.summary);
            this.updateCharts(data);
            
            // Load active tab data
            const activeTab = document.querySelector('#dataTabs .nav-link.active');
            const target = activeTab.getAttribute('data-bs-target');
            
            if (target === '#conversations') {
                this.loadConversations();
            } else if (target === '#webhooks') {
                this.loadWebhooks();
            } else if (target === '#logs') {
                this.loadLogs();
            }
            
        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.showError('Failed to load dashboard data');
        }
    }
    
    updateSummaryCards(summary) {
        document.getElementById('totalConversations').textContent = 
            summary.total_conversations.toLocaleString();
        document.getElementById('totalUsers').textContent = 
            summary.total_users.toLocaleString();
        document.getElementById('totalWebhooks').textContent = 
            summary.total_webhooks.toLocaleString();
        document.getElementById('avgResponseTime').textContent = 
            `${summary.avg_response_time}ms`;
    }
    
    updateCharts(data) {
        this.updateDailyActivityChart(data.daily_activity);
        this.updateMessageTypesChart(data.message_types);
        this.updateLanguagesChart(data.languages);
        this.updateFileTypesChart(data.file_types);
    }
    
    updateDailyActivityChart(dailyActivity) {
        const ctx = document.getElementById('dailyActivityChart').getContext('2d');
        
        if (this.charts.dailyActivity) {
            this.charts.dailyActivity.destroy();
        }
        
        const labels = dailyActivity.map(item => 
            new Date(item.date).toLocaleDateString()
        );
        const counts = dailyActivity.map(item => item.count);
        
        this.charts.dailyActivity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Conversations',
                    data: counts,
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    updateMessageTypesChart(messageTypes) {
        const ctx = document.getElementById('messageTypesChart').getContext('2d');
        
        if (this.charts.messageTypes) {
            this.charts.messageTypes.destroy();
        }
        
        const labels = Object.keys(messageTypes);
        const counts = Object.values(messageTypes);
        const colors = [
            'rgb(255, 99, 132)',
            'rgb(54, 162, 235)',
            'rgb(255, 205, 86)',
            'rgb(75, 192, 192)',
            'rgb(153, 102, 255)'
        ];
        
        this.charts.messageTypes = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.map(label => 
                    label.charAt(0).toUpperCase() + label.slice(1)
                ),
                datasets: [{
                    data: counts,
                    backgroundColor: colors.slice(0, labels.length)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    updateLanguagesChart(languages) {
        const ctx = document.getElementById('languagesChart').getContext('2d');
        
        if (this.charts.languages) {
            this.charts.languages.destroy();
        }
        
        const labels = Object.keys(languages);
        const counts = Object.values(languages);
        
        this.charts.languages = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Messages',
                    data: counts,
                    backgroundColor: 'rgba(75, 192, 192, 0.8)',
                    borderColor: 'rgb(75, 192, 192)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    updateFileTypesChart(fileTypes) {
        const ctx = document.getElementById('fileTypesChart').getContext('2d');
        
        if (this.charts.fileTypes) {
            this.charts.fileTypes.destroy();
        }
        
        const labels = Object.keys(fileTypes);
        const counts = Object.values(fileTypes);
        
        this.charts.fileTypes = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Files',
                    data: counts,
                    backgroundColor: 'rgba(153, 102, 255, 0.8)',
                    borderColor: 'rgb(153, 102, 255)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    async loadConversations(page = 1) {
        try {
            const response = await fetch(`/api/conversations?page=${page}&per_page=10`);
            const data = await response.json();
            
            this.renderConversationsTable(data.conversations);
            this.renderPagination('conversations', data.pagination);
            
        } catch (error) {
            console.error('Error loading conversations:', error);
            this.showTableError('conversationsTable', 'Failed to load conversations');
        }
    }
    
    async loadWebhooks(page = 1) {
        try {
            const response = await fetch(`/api/webhooks?page=${page}&per_page=10`);
            const data = await response.json();
            
            this.renderWebhooksTable(data.webhooks);
            this.renderPagination('webhooks', data.pagination);
            
        } catch (error) {
            console.error('Error loading webhooks:', error);
            this.showTableError('webhooksTable', 'Failed to load webhook events');
        }
    }
    
    async loadLogs(page = 1) {
        try {
            const level = document.getElementById('logLevelFilter').value;
            const response = await fetch(`/api/logs?page=${page}&per_page=10&level=${level}`);
            const data = await response.json();
            
            this.renderLogsTable(data.logs);
            this.renderPagination('logs', data.pagination);
            
        } catch (error) {
            console.error('Error loading logs:', error);
            this.showTableError('logsTable', 'Failed to load logs');
        }
    }
    
    renderConversationsTable(conversations) {
        const tbody = document.getElementById('conversationsTable');
        
        if (conversations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No conversations found</td></tr>';
            return;
        }
        
        tbody.innerHTML = conversations.map(conv => `
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        <i class="fas fa-user me-2 text-muted"></i>
                        <div>
                            <div class="fw-bold">${this.escapeHtml(conv.user_name || 'Unknown')}</div>
                            <small class="text-muted">${this.escapeHtml(conv.user_id.substring(0, 8))}...</small>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="badge ${this.getMessageTypeBadge(conv.message_type)}">
                        ${conv.message_type}
                    </span>
                </td>
                <td>
                    <div class="text-truncate" style="max-width: 200px;">
                        ${this.escapeHtml(conv.user_message || '-')}
                    </div>
                </td>
                <td>
                    <div class="text-truncate" style="max-width: 200px;">
                        ${this.escapeHtml(conv.bot_response || '-')}
                    </div>
                </td>
                <td>
                    <span class="badge bg-secondary">${conv.language}</span>
                </td>
                <td>
                    <small class="text-muted">
                        ${this.formatDateTime(conv.created_at)}
                    </small>
                </td>
            </tr>
        `).join('');
    }
    
    renderWebhooksTable(webhooks) {
        const tbody = document.getElementById('webhooksTable');
        
        if (webhooks.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No webhook events found</td></tr>';
            return;
        }
        
        tbody.innerHTML = webhooks.map(webhook => `
            <tr>
                <td>
                    <span class="badge bg-info">${webhook.event_type}</span>
                </td>
                <td>
                    <small class="font-monospace">
                        ${webhook.user_id ? this.escapeHtml(webhook.user_id.substring(0, 12)) + '...' : '-'}
                    </small>
                </td>
                <td>
                    <span class="badge bg-secondary">${webhook.source_type || '-'}</span>
                </td>
                <td>
                    ${webhook.processed 
                        ? '<span class="badge bg-success">Success</span>'
                        : '<span class="badge bg-danger">Failed</span>'
                    }
                    ${webhook.error_message 
                        ? `<div class="text-danger small mt-1">${this.escapeHtml(webhook.error_message)}</div>`
                        : ''
                    }
                </td>
                <td>
                    ${webhook.processing_time ? `${webhook.processing_time}ms` : '-'}
                </td>
                <td>
                    <small class="text-muted">
                        ${this.formatDateTime(webhook.created_at)}
                    </small>
                </td>
            </tr>
        `).join('');
    }
    
    renderLogsTable(logs) {
        const tbody = document.getElementById('logsTable');
        
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No logs found</td></tr>';
            return;
        }
        
        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>
                    <span class="badge ${this.getLogLevelBadge(log.level)}">
                        ${log.level}
                    </span>
                </td>
                <td>
                    <div class="text-truncate" style="max-width: 400px;">
                        ${this.escapeHtml(log.message)}
                    </div>
                    ${log.error_details 
                        ? `<div class="text-danger small mt-1">${this.escapeHtml(log.error_details)}</div>`
                        : ''
                    }
                </td>
                <td>
                    <small class="font-monospace">
                        ${log.user_id ? this.escapeHtml(log.user_id.substring(0, 12)) + '...' : '-'}
                    </small>
                </td>
                <td>
                    <small class="text-muted">
                        ${this.formatDateTime(log.created_at)}
                    </small>
                </td>
            </tr>
        `).join('');
    }
    
    renderPagination(type, pagination) {
        const container = document.getElementById(`${type}Pagination`);
        
        if (pagination.pages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        const pages = [];
        const currentPage = pagination.page;
        const totalPages = pagination.pages;
        
        // Previous button
        pages.push(`
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage - 1}">Previous</a>
            </li>
        `);
        
        // Page numbers
        for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
            pages.push(`
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `);
        }
        
        // Next button
        pages.push(`
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage + 1}">Next</a>
            </li>
        `);
        
        container.innerHTML = `
            <ul class="pagination justify-content-center">
                ${pages.join('')}
            </ul>
        `;
        
        // Add click handlers
        container.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.getAttribute('data-page'));
                if (page && page !== currentPage) {
                    this.currentPage[type] = page;
                    if (type === 'conversations') {
                        this.loadConversations(page);
                    } else if (type === 'webhooks') {
                        this.loadWebhooks(page);
                    } else if (type === 'logs') {
                        this.loadLogs(page);
                    }
                }
            });
        });
    }
    
    getMessageTypeBadge(type) {
        const badges = {
            'text': 'bg-primary',
            'image': 'bg-success',
            'file': 'bg-warning',
            'system': 'bg-secondary'
        };
        return badges[type] || 'bg-secondary';
    }
    
    getLogLevelBadge(level) {
        const badges = {
            'ERROR': 'bg-danger',
            'WARNING': 'bg-warning',
            'INFO': 'bg-info',
            'DEBUG': 'bg-secondary'
        };
        return badges[level] || 'bg-secondary';
    }
    
    formatDateTime(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleString();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showTableError(tableId, message) {
        const tbody = document.getElementById(tableId);
        const colspan = tbody.closest('table').querySelectorAll('thead th').length;
        tbody.innerHTML = `
            <tr>
                <td colspan="${colspan}" class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                </td>
            </tr>
        `;
    }
    
    showError(message) {
        // Create a toast notification
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-danger border-0';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(toast);
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});
