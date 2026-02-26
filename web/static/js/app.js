// Основной JS файл для админпанели

// Утилиты для работы с API
const API = {
    async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    get(url) {
        return this.request(url);
    },
    
    post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    patch(url, data) {
        return this.request(url, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },
    
    delete(url) {
        return this.request(url, {
            method: 'DELETE'
        });
    }
};

// Утилиты для UI
const UI = {
    showLoading(element) {
        element.innerHTML = '<div class="loading"></div>';
    },
    
    showError(message) {
        alert(message); // TODO: better notifications
    },
    
    confirm(message) {
        return window.confirm(message);
    },
    
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en');
    },
    
    formatDateTime(dateString) {
        return new Date(dateString).toLocaleString('en');
    }
};

// Message Builder helpers
const MessageBuilder = {
    buttons: [],
    mediaType: null,
    mediaFileId: null,
    
    addButton(text, url) {
        this.buttons.push({text, url});
        this.renderButtons();
    },
    
    removeButton(index) {
        this.buttons.splice(index, 1);
        this.renderButtons();
        // Trigger preview update if function exists
        if (typeof updatePreview === 'function') {
            updatePreview();
        }
    },
    
    renderButtons() {
        const container = document.getElementById('buttonsList');
        if (!container) return;
        
        if (this.buttons.length === 0) {
            container.innerHTML = '<p class="text-muted">No buttons</p>';
            return;
        }
        
        container.innerHTML = this.buttons.map((btn, i) => `
            <div class="button-item">
                <div>
                    <strong>${btn.text}</strong><br>
                    <small class="text-muted">${btn.url}</small>
                </div>
                <button onclick="MessageBuilder.removeButton(${i})" class="btn btn-danger btn-sm">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
    },
    
    getButtonsJSON() {
        return this.buttons.length > 0 ? JSON.stringify(this.buttons) : null;
    },
    
    loadButtons(buttonsJSON) {
        if (buttonsJSON) {
            this.buttons = JSON.parse(buttonsJSON);
            this.renderButtons();
        }
    },
    
    reset() {
        this.buttons = [];
        this.mediaType = null;
        this.mediaFileId = null;
    }
};

// Глобальные функции
window.API = API;
window.UI = UI;
window.MessageBuilder = MessageBuilder;

// Навигация
document.addEventListener('DOMContentLoaded', () => {
    // Подсветка активного пункта меню
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-menu a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

