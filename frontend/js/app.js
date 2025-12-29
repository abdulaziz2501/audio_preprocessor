/**
 * AudioAI - Main Application
 * Asosiy dastur mantiq va koordinatsiya
 */

const App = {
    /**
     * Dasturni ishga tushirish
     */
    init() {
        console.log('%c🚀 AudioAI Started', 'color: #6366f1; font-size: 16px; font-weight: bold');
        console.log('%cProfessional Audio Preprocessing Platform', 'color: #8b5cf6; font-size: 12px');
        
        this.checkBackendStatus();
        this.setupGlobalErrorHandling();
        this.setupNavigationSmoothScroll();
        
        console.log('✅ App initialized successfully');
    },
    
    /**
     * Backend serverning holatini tekshirish
     */
    async checkBackendStatus() {
        try {
            const response = await fetch('http://localhost:8000/health');
            
            if (response.ok) {
                const data = await response.json();
                console.log('✅ Backend server:', data.status);
            } else {
                console.warn('⚠️ Backend server javob bermayapti');
                this.showBackendWarning();
            }
        } catch (error) {
            console.warn('⚠️ Backend serverga ulanib bo\'lmadi:', error.message);
            this.showBackendWarning();
        }
    },
    
    /**
     * Backend ogohlantirish
     */
    showBackendWarning() {
        const warning = document.createElement('div');
        warning.style.cssText = `
            position: fixed;
            top: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
            padding: 1rem 2rem;
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            animation: slideDown 0.3s ease-out;
        `;
        
        warning.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>Backend server ishlamayapti. Iltimos, serverni ishga tushiring.</span>
            <button onclick="this.parentElement.remove()" style="
                background: transparent;
                border: none;
                color: white;
                cursor: pointer;
                font-size: 1.25rem;
                padding: 0;
                margin-left: 0.5rem;
            ">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        document.body.appendChild(warning);
        
        // 10 sekunddan keyin avtomatik o'chirish
        setTimeout(() => {
            warning.remove();
        }, 10000);
    },
    
    /**
     * Global xatolarni ushlash
     */
    setupGlobalErrorHandling() {
        window.addEventListener('error', (event) => {
            console.error('❌ Global error:', event.error);
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            console.error('❌ Unhandled promise rejection:', event.reason);
        });
    },
    
    /**
     * Navigation smooth scroll
     */
    setupNavigationSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                
                if (target) {
                    // Active klassni yangilash
                    document.querySelectorAll('.nav-menu a').forEach(link => {
                        link.classList.remove('active');
                    });
                    this.classList.add('active');
                    
                    // Smooth scroll
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    },
    
    /**
     * Performance monitoring
     */
    logPerformance() {
        if (window.performance) {
            const perfData = window.performance.timing;
            const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
            console.log(`⚡ Sahifa yuklash vaqti: ${pageLoadTime}ms`);
        }
    }
};

/**
 * Keyboard shortcuts
 */
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + U - Upload fayl
    if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        document.getElementById('audioFile').click();
    }
    
    // Escape - Reset
    if (e.key === 'Escape') {
        const isProcessing = document.getElementById('statusSection').style.display !== 'none';
        if (!isProcessing) {
            resetApp();
        }
    }
});

/**
 * Console styling
 */
console.log(`
╔═══════════════════════════════════════╗
║                                       ║
║          🎵 AudioAI v1.0 🎵          ║
║   Professional Audio Preprocessing   ║
║                                       ║
╚═══════════════════════════════════════╝

Keyboard Shortcuts:
  • Ctrl/Cmd + U → Upload file
  • Escape → Reset app

Developer: Your Name
Built with: FastAPI, Vanilla JS, Modern CSS
`);

/**
 * Sahifa to'liq yuklanganda
 */
window.addEventListener('load', () => {
    App.init();
    App.logPerformance();
});

/**
 * Service Worker (agar kerak bo'lsa, offline support uchun)
 */
if ('serviceWorker' in navigator) {
    // Service worker registration
    // navigator.serviceWorker.register('/sw.js');
}

/**
 * Export (agar module sifatida ishlatilsa)
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = App;
}
