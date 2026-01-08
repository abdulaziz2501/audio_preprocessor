/**
 * AudioAI - Main JavaScript
 * Navigation, animations va umumiy funksiyalar
 */

// ============== Constants ==============
const API_BASE = 'http://localhost:8000/api';

// ============== DOM Ready ==============
document.addEventListener('DOMContentLoaded', function() {
    initNavbar();
    initAnimations();
});

// ============== Navigation ==============
function initNavbar() {
    const navbar = document.getElementById('navbar');
    
    if (!navbar) return;
    
    // Scroll hodisasi
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        // Scrolled class qo'shish
        if (currentScroll > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        lastScroll = currentScroll;
    });
}

// ============== Animations ==============
function initAnimations() {
    // Intersection Observer - elementlar ko'ringanida animatsiya
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Animatsiya qilinadigan elementlar
    const animatedElements = document.querySelectorAll('.feature-card, .stat-card');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });
    
    // Animate-in class
    document.head.insertAdjacentHTML('beforeend', `
        <style>
            .animate-in {
                opacity: 1 !important;
                transform: translateY(0) !important;
            }
        </style>
    `);
}

// ============== Utility Functions ==============

/**
 * Faylni formatlash (hajmini ko'rsatish)
 * @param {number} bytes - Baytlarda hajm
 * @returns {string} - Formatlangan hajm
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Vaqtni formatlash (MM:SS)
 * @param {number} seconds - Sekundlar
 * @returns {string} - Formatlangan vaqt
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Vaqtni kengaytirilgan formatlash (davomiylik uchun)
 * @param {number} seconds - Sekundlar
 * @returns {string} - Formatlangan davomiylik
 */
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds.toFixed(1)}s`;
    }
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}m ${secs}s`;
}

/**
 * Toast notification ko'rsatish
 * @param {string} message - Xabar
 * @param {string} type - 'success', 'error', 'info'
 */
function showToast(message, type = 'info') {
    // Mavjud toast olib tashlash
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Toast yaratish
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span>${message}</span>
    `;
    
    // Stillar qo'shish
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#6366f1'};
        color: white;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 500;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    // Animatsiya CSS qo'shish
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // 3 sekunddan keyin olib tashlash
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Loading indicator yaratish
 * @param {HTMLElement} container - Container element
 * @param {string} message - Loading xabari
 */
function showLoading(container, message = 'Yuklanmoqda...') {
    const loader = document.createElement('div');
    loader.className = 'loading-overlay';
    loader.innerHTML = `
        <div class="loading-content">
            <div class="spinner"></div>
            <p>${message}</p>
        </div>
    `;
    
    loader.style.cssText = `
        position: absolute;
        inset: 0;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 100;
        border-radius: inherit;
    `;
    
    container.style.position = 'relative';
    container.appendChild(loader);
    
    return loader;
}

/**
 * Loading indicator olib tashlash
 * @param {HTMLElement} loader - Loader elementi
 */
function hideLoading(loader) {
    if (loader && loader.parentNode) {
        loader.remove();
    }
}

// ============== API Functions ==============

/**
 * Audio fayl yuklash
 * @param {File} file - Audio fayl
 * @returns {Promise} - Task ID va status
 */
async function uploadAudio(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload xatosi');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Upload error:', error);
        throw error;
    }
}

/**
 * Processing boshlash
 * @param {string} taskId - Task ID
 * @param {object} options - Processing parametrlari
 * @returns {Promise} - Status
 */
async function startProcessing(taskId, options = {}) {
    try {
        const response = await fetch(`${API_BASE}/process/${taskId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(options)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Processing xatosi');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Processing error:', error);
        throw error;
    }
}

/**
 * Processing statusini olish
 * @param {string} taskId - Task ID
 * @returns {Promise} - Status ma'lumotlari
 */
async function getProcessingStatus(taskId) {
    try {
        const response = await fetch(`${API_BASE}/status/${taskId}`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Status olishda xato');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Status error:', error);
        throw error;
    }
}

/**
 * Processed audio yuklab olish URL
 * @param {string} taskId - Task ID
 * @returns {string} - Download URL
 */
function getDownloadUrl(taskId) {
    return `${API_BASE}/download/${taskId}`;
}

// ============== Export ==============
window.AudioAI = {
    formatFileSize,
    formatTime,
    formatDuration,
    showToast,
    showLoading,
    hideLoading,
    uploadAudio,
    startProcessing,
    getProcessingStatus,
    getDownloadUrl,
    API_BASE
};

console.log('🎙️ AudioAI initialized');
