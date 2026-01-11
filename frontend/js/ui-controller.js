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
        fileList: document.getElementById('fileList'),
        fileCount: document.getElementById('fileCount'),
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

        // File input change (multiple files)
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                AudioHandler.handleFileSelect(Array.from(e.target.files));
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
                AudioHandler.handleFileSelect(Array.from(files));
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
     * File list'ni tozalash
     */
    clearFileList() {
        const { fileList } = this.elements;
        if (fileList) {
            fileList.innerHTML = '';
        }
    },

    /**
     * File list'ga fayl qo'shish
     */
    addFileToList(fileData) {
        const { fileList } = this.elements;

        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';

        const statusIcon = fileData.status === 'success' ?
            '<i class="fas fa-check-circle" style="color: var(--success)"></i>' :
            '<i class="fas fa-exclamation-circle" style="color: var(--error)"></i>';

        fileItem.innerHTML = `
            <i class="fas fa-file-audio"></i>
            <div class="file-item-info">
                <h4>${fileData.filename}</h4>
                <p>${fileData.size} MB</p>
            </div>
            <div class="file-item-status ${fileData.status}">
                ${statusIcon}
                <span>${fileData.status === 'success' ? 'Ready' : 'Failed'}</span>
            </div>
        `;

        fileList.appendChild(fileItem);
    },

    /**
     * Fayl ma'lumotlarini ko'rsatish (batch)
     */
    showFileInfo(fileCount) {
        const { fileInfo } = this.elements;

        this.elements.fileCount.textContent = fileCount;

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
     * Batch processing natijalari
     */
    showBatchResults(results, summary) {
        const { statusSection, resultsSection, resultsGrid } = this.elements;

        this.completeStatusProgress();

        setTimeout(() => {
            statusSection.style.display = 'none';
            resultsGrid.innerHTML = '';

            // Summary header
            const summaryCard = document.createElement('div');
            summaryCard.className = 'result-card';
            summaryCard.style.background = 'linear-gradient(135deg, var(--primary-color), var(--secondary-color))';
            summaryCard.innerHTML = `
                <div class="result-info">
                    <div class="result-icon" style="background: white; color: var(--primary-color);">
                        <i class="fas fa-check"></i>
                    </div>
                    <div class="result-details" style="color: white;">
                        <h4>Batch Processing Complete!</h4>
                        <p>Processed: ${summary.processed}/${summary.total} files</p>
                    </div>
                </div>
            `;
            resultsGrid.appendChild(summaryCard);

            // Har bir natija
            results.forEach((result, index) => {
                if (result.type === 'segments') {
                    // Segmentlar
                    result.segments.forEach((segment, segIndex) => {
                        resultsGrid.appendChild(this.createResultCard(
                            `File ${index + 1} - Segment ${segIndex + 1}`,
                            `Duration: ${segment.duration}s`,
                            segment.file_path
                        ));
                    });
                } else if (result.type === 'file') {
                    // Oddiy fayl
                    resultsGrid.appendChild(this.createResultCard(
                        `Processed File ${index + 1}`,
                        result.file_id,
                        result.output_path
                    ));
                } else if (!result.success) {
                    // Xato
                    const errorCard = document.createElement('div');
                    errorCard.className = 'result-card';
                    errorCard.style.borderColor = 'var(--error)';
                    errorCard.innerHTML = `
                        <div class="result-info">
                            <div class="result-icon" style="background: var(--error);">
                                <i class="fas fa-times"></i>
                            </div>
                            <div class="result-details">
                                <h4>File ${index + 1} Failed</h4>
                                <p style="color: var(--error);">${result.error}</p>
                            </div>
                        </div>
                    `;
                    resultsGrid.appendChild(errorCard);
                }
            });
        });
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

        // File list'ni tozalash
        this.clearFileList();

        // Audio Handler'ni tozalash
        if (typeof AudioHandler !== 'undefined') {
            AudioHandler.uploadedFiles = [];
        }

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

function removeAllFiles() {
    UIController.reset();
}

function resetApp() {
    UIController.reset();
}

// Sahifa yuklanganda ishga tushirish
document.addEventListener('DOMContentLoaded', () => {
    UIController.init();
});
