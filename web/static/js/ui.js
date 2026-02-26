// UI utilities for modals, toasts, and notifications - Optimized

const Modal = {
    create(options) {
        const {
            title = '',
            body = '',
            buttons = [],
            onClose = null
        } = options;
        
        // Create modal HTML
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${title}</h2>
                </div>
                <div class="modal-body">
                    ${body}
                </div>
                <div class="modal-footer">
                    ${buttons.map((btn, index) => `
                        <button class="modal-btn modal-btn-${btn.type || 'secondary'}" data-button-index="${index}">
                            ${btn.icon ? `<i class="fas fa-${btn.icon}"></i>` : ''}
                            ${btn.text}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Force reflow before adding show class for smooth animation
        modal.offsetHeight;
        
        // Show modal with animation
        requestAnimationFrame(() => {
            modal.classList.add('show');
        });
        
        // Handle button clicks
        modal.querySelectorAll('[data-button-index]').forEach((btn, index) => {
            btn.addEventListener('click', () => {
                const buttonData = buttons[index];
                if (buttonData.onClick) {
                    buttonData.onClick();
                }
                this.close(modal);
            });
        });
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.close(modal);
                if (onClose) onClose();
            }
        });
        
        // Close on Escape key
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                this.close(modal);
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
        
        return modal;
    },
    
    close(modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 200);
    },
    
    confirm(options) {
        const {
            title = 'Confirm',
            message = 'Are you sure?',
            confirmText = 'Confirm',
            cancelText = 'Cancel',
            confirmType = 'primary',
            onConfirm = null,
            onCancel = null
        } = options;
        
        return this.create({
            title,
            body: `<p>${message}</p>`,
            buttons: [
                {
                    text: cancelText,
                    type: 'secondary',
                    onClick: onCancel
                },
                {
                    text: confirmText,
                    type: confirmType,
                    icon: confirmType === 'danger' ? 'exclamation-triangle' : 'check',
                    onClick: onConfirm
                }
            ]
        });
    },
    
    alert(options) {
        const {
            title = 'Notice',
            message = '',
            type = 'info',
            buttonText = 'OK',
            onClose = null
        } = options;
        
        return this.create({
            title,
            body: `<p>${message}</p>`,
            buttons: [
                {
                    text: buttonText,
                    type: type === 'error' ? 'danger' : 'primary',
                    onClick: onClose
                }
            ],
            onClose
        });
    },
    
    // Progress modal that shows while processing
    progress(options) {
        const {
            title = 'Processing...',
            message = 'Please wait'
        } = options;
        
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content" style="text-align: center; padding: 2.5rem;">
                <div class="progress-spinner"></div>
                <h2 style="margin: 1.5rem 0 0.75rem; font-size: 1.25rem;">${title}</h2>
                <p style="color: var(--text-muted); margin: 0;">${message}</p>
            </div>
        `;
        
        document.body.appendChild(modal);
        modal.offsetHeight;
        requestAnimationFrame(() => modal.classList.add('show'));
        
        return modal;
    },
    
    broadcastReport(data) {
        const successRate = data.success_rate || 0;
        const successColor = successRate >= 80 ? 'var(--success)' : successRate >= 50 ? '#f59e0b' : 'var(--danger)';
        
        const body = `
            <div class="broadcast-report">
                <div class="report-stats">
                    <div class="report-stat">
                        <div class="report-stat-value">${data.total}</div>
                        <div class="report-stat-label">Total</div>
                    </div>
                    <div class="report-stat">
                        <div class="report-stat-value" style="color: var(--success);">${data.sent}</div>
                        <div class="report-stat-label">Sent</div>
                    </div>
                    <div class="report-stat">
                        <div class="report-stat-value" style="color: var(--danger);">${data.failed}</div>
                        <div class="report-stat-label">Failed</div>
                    </div>
                </div>
                <div style="text-align: center; margin-bottom: 1.5rem;">
                    <div style="font-size: 2.5rem; font-weight: 700; color: ${successColor};">
                        ${successRate}%
                    </div>
                    <div style="color: var(--text-muted);">Success Rate</div>
                </div>
                ${data.details && data.details.length > 0 ? `
                    <h3 style="margin-bottom: 1rem; font-size: 1rem;">Delivery Details</h3>
                    <div class="report-list">
                        ${data.details.slice(0, 50).map(detail => `
                            <div class="report-item report-item-${detail.status}">
                                <div class="report-item-icon">
                                    <i class="fas fa-${detail.status === 'success' ? 'check' : 'times'}"></i>
                                </div>
                                <div class="report-item-info">
                                    <div class="report-item-name">${detail.username}</div>
                                    <div class="report-item-detail">
                                        ID: ${detail.user_id}
                                        ${detail.error ? ` - ${detail.error}` : ''}
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                        ${data.details.length > 50 ? `<div class="report-item"><div class="report-item-info" style="text-align: center; color: var(--text-muted);">... and ${data.details.length - 50} more</div></div>` : ''}
                    </div>
                ` : ''}
            </div>
        `;
        
        return this.create({
            title: '📊 Broadcast Report',
            body,
            buttons: [
                {
                    text: 'Close',
                    type: 'primary',
                    icon: 'check'
                }
            ]
        });
    }
};

const Toast = {
    container: null,
    
    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },
    
    show(options) {
        this.init();
        
        const {
            title = '',
            message = '',
            type = 'info',
            duration = 3500
        } = options;
        
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            info: 'info-circle',
            warning: 'exclamation-triangle'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas fa-${icons[type]}"></i>
            </div>
            <div class="toast-body">
                ${title ? `<div class="toast-title">${title}</div>` : ''}
                <div class="toast-message">${message}</div>
            </div>
        `;
        
        this.container.appendChild(toast);
        
        // Force reflow and show
        toast.offsetHeight;
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Auto remove
        const hideToast = () => {
            toast.classList.add('hiding');
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 250);
        };
        
        const timeoutId = setTimeout(hideToast, duration);
        
        // Click to close
        toast.addEventListener('click', () => {
            clearTimeout(timeoutId);
            hideToast();
        });
    },
    
    success(message, title = 'Success') {
        this.show({ title, message, type: 'success' });
    },
    
    error(message, title = 'Error') {
        this.show({ title, message, type: 'error', duration: 5000 });
    },
    
    info(message, title = 'Info') {
        this.show({ title, message, type: 'info' });
    },
    
    warning(message, title = 'Warning') {
        this.show({ title, message, type: 'warning' });
    }
};

// Export to global
window.Modal = Modal;
window.Toast = Toast;
