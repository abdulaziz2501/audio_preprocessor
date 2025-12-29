/**
 * UI Controller - Foydalanuvchi interfeysi boshqaruvi
 * Barcha UI elementlarni boshqarish va animatsiyalar
 */

const UIController = {
    // UI elementlari
    elements: {
        uploadArea: document.getElementById('uploadArea'),
        fileInput: document.getElementById('audioFile'),
        uploadProgress: document.getElementById('uploadProgress'),
        progressFill: document.getElementById('progressFill'),
        progressText: document.getElementById('progressText'),
        fileInfo: document.getElementById('fileInfo'),
        fileName: document.getElementById('fileName'),
        fileSize: document.getElementById('fileSize'),
        processingSection: document.getElementById('processingSection'),
        statusSection: document.getElementById('statusSection'),
        resultsSection: document.getElementById('resultsSection'),
        resultsGrid: document.getElementById('resultsGrid'),
        
        // Toggles
        noiseToggle: document.getElementById('noiseToggle'),
        silenceToggle: document.getElementById('silenceToggle'),
        segmentToggle: document.getElementById('segmentToggle'),
        
        // Settings
        noiseSettings: document.getElementById('noiseSettings'),
        silenceSettings: document.getElementById('silenceSettings'),
        segmentSettings: document.getElementById('segmentSettings'),
        
        // Values
        noiseStrength: document.getElementById('noiseStrength'),
        noiseStrengthValue: document.getElementById('noiseStrengthValue'),
        silenceThreshold: document.getElementById('silenceThreshold'),
        silenceThresholdValue: document.getElementById('silenceThresholdValue'),
        silenceDuration: document.getElementById('silenceDuration'),
        silenceDurationValue: document.getElementById('silenceDurationValue'),
        segmentDuration: document.getElementById('segmentDuration'),
        segmentDurationValue: document.getElementById('segmentDurationValue'),
        segmentOverlap: document.getElementById('segmentOverlap'),
        segmentOverlapValue: document.getElementById('segmentOverlapValue'),
    },
    
    /**
     * UI Controller'ni ishga tushirish
     */
    init() {
        this.setupEventListeners();
        this.setupRangeInputs();
        this.setupToggleSwitches();
        console.log('✅ UI Controller initialized');
    },
    
    /**
     * Event listener'larni sozlash
     */
    setupEventListeners() {
        const { uploadArea, fileInput } = this.elements;
        
        // Upload area click
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                AudioHandler.handleFileSelect(e.target.files[0]);
            }
        });
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                AudioHandler.handleFileSelect(files[0]);
            }
        });
    },
    
    /**
     * Range input'larni sozlash (real-time qiymat ko'rsatish)
     */
    setupRangeInputs() {
        const ranges = [
            { input: 'noiseStrength', value: 'noiseStrengthValue' },
            { input: 'silenceThreshold', value: 'silenceThresholdValue' },
            { input: 'silenceDuration', value: 'silenceDurationValue' },
            { input: 'segmentDuration', value: 'segmentDurationValue' },
            { input: 'segmentOverlap', value: 'segmentOverlapValue' }
        ];
        
        ranges.forEach(({ input, value }) => {
            const inputEl = this.elements[input];
            const valueEl = this.elements[value];
            
            if (inputEl && valueEl) {
                inputEl.addEventListener('input', (e) => {
                    valueEl.textContent = e.target.value;
                });
            }
        });
    },
    
    /**
     * Toggle switch'larni sozlash
     */
    setupToggleSwitches() {
        const toggles = [
            { toggle: 'noiseToggle', settings: 'noiseSettings', card: 'noise' },
            { toggle: 'silenceToggle', settings: 'silenceSettings', card: 'silence' },
            { toggle: 'segmentToggle', settings: 'segmentSettings', card: 'segment' }
        ];
        
        toggles.forEach(({ toggle, settings, card }) => {
            const toggleEl = this.elements[toggle];
            const settingsEl = this.elements[settings];
            const cardEl = document.querySelector(`[data-option="${card}"]`);
            
            if (toggleEl && settingsEl) {
                toggleEl.addEventListener('change', (e) => {
                    if (e.target.checked) {
                        settingsEl.style.display = 'block';
                        cardEl.classList.add('active');
                        settingsEl.classList.add('fade-in');
                    } else {
                        settingsEl.style.display = 'none';
                        cardEl.classList.remove('active');
                    }
                });
            }
        });
    },
    
    /**
     * Upload progress'ni ko'rsatish
     */
    showUploadProgress() {
        const { uploadProgress } = this.elements;
        uploadProgress.style.display = 'block';
        uploadProgress.classList.add('fade-in');
    },
    
    /**
     * Upload progress'ni yashirish
     */
    hideUploadProgress() {
        const { uploadProgress } = this.elements;
        uploadProgress.style.display = 'none';
    },
    
    /**
     * Progress bar'ni yangilash
     */
    updateProgress(percent, text = '') {
        const { progressFill, progressText } = this.elements;
        progressFill.style.width = `${percent}%`;
        if (text) {
            progressText.textContent = text;
        }
    },
    
    /**
     * Fayl ma'lumotlarini ko'rsatish
     */
    showFileInfo(filename, filesize) {
        const { fileInfo, fileName, fileSize } = this.elements;
        
        fileName.textContent = filename;
        fileSize.textContent = `${filesize} MB`;
        
        fileInfo.style.display = 'block';
        fileInfo.classList.add('slide-up');
        
        this.hideUploadProgress();
    },
    
    /**
     * Processing section'ni ko'rsatish
     */
    showProcessingOptions() {
        const { processingSection } = this.elements;
        processingSection.style.display = 'block';
        processingSection.classList.add('fade-in');
        
        // Smooth scroll
        setTimeout(() => {
            processingSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    },
    
    /**
     * Processing status'ni ko'rsatish
     */
    showProcessingStatus(title = 'Processing Your Audio...', message = 'Please wait') {
        const { statusSection, processingSection } = this.elements;
        
        document.getElementById('statusTitle').textContent = title;
        document.getElementById('statusMessage').textContent = message;
        document.getElementById('statusProgressFill').style.width = '0%';
        
        processingSection.style.display = 'none';
        statusSection.style.display = 'block';
        statusSection.classList.add('fade-in');
        
        // Smooth scroll
        setTimeout(() => {
            statusSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
        
        // Animate progress
        this.animateStatusProgress();
    },
    
    /**
     * Status progress animatsiyasi
     */
    animateStatusProgress() {
        const progressFill = document.getElementById('statusProgressFill');
        let progress = 0;
        
        const interval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 90) {
                progress = 90;
                clearInterval(interval);
            }
            progressFill.style.width = `${progress}%`;
        }, 500);
        
        // Interval'ni saqlash (to'xtatish uchun)
        this.statusInterval = interval;
    },
    
    /**
     * Status progress'ni to'xtatish
     */
    completeStatusProgress() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }
        document.getElementById('statusProgressFill').style.width = '100%';
    },
    
    /**
     * Natijalarni ko'rsatish
     */
    showResults(results) {
        const { statusSection, resultsSection, resultsGrid } = this.elements;
        
        this.completeStatusProgress();
        
        // Status yashirish
        setTimeout(() => {
            statusSection.style.display = 'none';
            
            // Natijalarni qo'shish
            resultsGrid.innerHTML = '';
            
            if (Array.isArray(results)) {
                // Segmentlar uchun
                results.forEach((segment, index) => {
                    resultsGrid.appendChild(this.createResultCard(
                        `Segment ${segment.segment_number + 1}`,
                        `Duration: ${segment.duration}s`,
                        segment.file_path
                    ));
                });
            } else {
                // Bitta fayl uchun
                resultsGrid.appendChild(this.createResultCard(
                    'Processed Audio',
                    'Ready to download',
                    results.file_path || results
                ));
            }
            
            // Results section'ni ko'rsatish
            resultsSection.style.display = 'block';
            resultsSection.classList.add('fade-in');
            
            // Smooth scroll
            setTimeout(() => {
                resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }, 1000);
    },
    
    /**
     * Result card yaratish
     */
    createResultCard(title, description, filePath) {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        card.innerHTML = `
            <div class="result-info">
                <div class="result-icon">
                    <i class="fas fa-check"></i>
                </div>
                <div class="result-details">
                    <h4>${title}</h4>
                    <p>${description}</p>
                </div>
            </div>
            <button class="btn btn-primary" onclick="AudioHandler.downloadFile('${filePath}')">
                <i class="fas fa-download"></i> Download
            </button>
        `;
        
        return card;
    },
    
    /**
     * Error xabar ko'rsatish
     */
    showError(message) {
        const { statusSection } = this.elements;
        
        document.getElementById('statusTitle').textContent = 'Error Occurred';
        document.getElementById('statusMessage').textContent = message;
        document.querySelector('.status-icon i').className = 'fas fa-exclamation-triangle';
        document.querySelector('.status-icon').style.color = 'var(--error)';
        
        this.completeStatusProgress();
        
        statusSection.style.display = 'block';
        statusSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    },
    
    /**
     * Barcha narsani reset qilish
     */
    reset() {
        const { 
            fileInfo, 
            processingSection, 
            statusSection, 
            resultsSection,
            fileInput
        } = this.elements;
        
        // File input'ni tozalash
        fileInput.value = '';
        
        // Barcha section'larni yashirish
        fileInfo.style.display = 'none';
        processingSection.style.display = 'none';
        statusSection.style.display = 'none';
        resultsSection.style.display = 'none';
        
        // Toggle'larni o'chirish
        this.elements.noiseToggle.checked = false;
        this.elements.silenceToggle.checked = false;
        this.elements.segmentToggle.checked = false;
        
        // Settings'ni yashirish
        this.elements.noiseSettings.style.display = 'none';
        this.elements.silenceSettings.style.display = 'none';
        this.elements.segmentSettings.style.display = 'none';
        
        // Active klasslarni o'chirish
        document.querySelectorAll('.option-card').forEach(card => {
            card.classList.remove('active');
        });
        
        // Upload section'ga scroll qilish
        document.getElementById('upload').scrollIntoView({ behavior: 'smooth' });
        
        console.log('🔄 UI reset qilindi');
    }
};

// Helper functions
function scrollToUpload() {
    document.getElementById('upload').scrollIntoView({ behavior: 'smooth' });
}

function removeFile() {
    UIController.reset();
}

function resetApp() {
    UIController.reset();
}

// Sahifa yuklanganda ishga tushirish
document.addEventListener('DOMContentLoaded', () => {
    UIController.init();
});
