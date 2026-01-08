/**
 * AudioAI - Editor JavaScript
 * Batch audio upload, processing va download
 */

// ============== Configuration ==============
const CONFIG = {
    API_BASE: 'http://localhost:8000/api',
    MAX_FILE_SIZE: 50 * 1024 * 1024, // 50 MB
    ALLOWED_EXTENSIONS: ['.wav', '.mp3', '.ogg', '.flac', '.m4a'],
    MAX_BATCH_SIZE: 50, // Maksimal bir vaqtda yuklanadigan fayllar
};

// ============== State ==============
let fileQueue = []; // {id, file, status, taskId, transcription, originalUrl, processedUrl}
let isProcessing = false;
let currentProcessingIndex = 0;

// ============== DOM Elements ==============
const uploadSection = document.getElementById('uploadSection');
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileQueueEl = document.getElementById('fileQueue');
const queueList = document.getElementById('queueList');
const fileCount = document.getElementById('fileCount');
const clearAllBtn = document.getElementById('clearAllBtn');
const processAllBtn = document.getElementById('processAllBtn');

// Processing section elements (single file - backward compatibility)
const processingSection = document.getElementById('processingSection');
const resultsSection = document.getElementById('resultsSection');

// Options
const optDenoise = document.getElementById('optDenoise');
const optTrim = document.getElementById('optTrim');
const optExtract = document.getElementById('optExtract');
const optNormalize = document.getElementById('optNormalize');

// ============== Initialize ==============
document.addEventListener('DOMContentLoaded', function() {
    initUpload();
    initButtons();
    checkFromRecorder();
});

function initUpload() {
    // Drag & Drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // File input change (multiple)
    fileInput.addEventListener('change', handleFileSelect);
}

function initButtons() {
    // Clear all
    clearAllBtn.addEventListener('click', clearAllFiles);
    
    // Process all
    processAllBtn.addEventListener('click', processAllFiles);
}

// ============== Check if coming from Recorder ==============
function checkFromRecorder() {
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.get('fromRecorder') === 'true') {
        const audioData = sessionStorage.getItem('recordedAudio');
        const audioName = sessionStorage.getItem('recordedAudioName');
        const transcription = sessionStorage.getItem('recordedAudioTranscription') || '';
        
        if (audioData && audioName) {
            fetch(audioData)
                .then(res => res.blob())
                .then(blob => {
                    const file = new File([blob], audioName, { type: 'audio/wav' });
                    addFileToQueue(file, transcription);
                    
                    // Session storage tozalash
                    sessionStorage.removeItem('recordedAudio');
                    sessionStorage.removeItem('recordedAudioName');
                    sessionStorage.removeItem('recordedAudioDuration');
                    sessionStorage.removeItem('recordedAudioTranscription');
                    
                    showToast('Yozilgan audio yuklandi!', 'success');
                })
                .catch(err => {
                    console.error('Error loading recorded audio:', err);
                    showToast('Audio yuklashda xato', 'error');
                });
        }
    }
}

// ============== Drag & Drop Handlers ==============
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('drag-over');
    
    const files = Array.from(e.dataTransfer.files);
    handleMultipleFiles(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    handleMultipleFiles(files);
    // Input tozalash (qayta tanlash uchun)
    fileInput.value = '';
}

// ============== Multiple Files Handling ==============
function handleMultipleFiles(files) {
    let addedCount = 0;
    let skippedCount = 0;
    
    for (const file of files) {
        // Limit tekshirish
        if (fileQueue.length >= CONFIG.MAX_BATCH_SIZE) {
            showToast(`Maksimum ${CONFIG.MAX_BATCH_SIZE} ta fayl yuklash mumkin`, 'error');
            break;
        }
        
        // Validation
        const validation = validateFile(file);
        if (validation.valid) {
            addFileToQueue(file);
            addedCount++;
        } else {
            skippedCount++;
            console.warn(`Skipped ${file.name}: ${validation.reason}`);
        }
    }
    
    if (addedCount > 0) {
        showToast(`${addedCount} ta fayl qo'shildi`, 'success');
    }
    
    if (skippedCount > 0) {
        showToast(`${skippedCount} ta fayl o'tkazib yuborildi (noto'g'ri format yoki hajm)`, 'error');
    }
}

function validateFile(file) {
    // Extension tekshirish
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!CONFIG.ALLOWED_EXTENSIONS.includes(ext)) {
        return { valid: false, reason: 'Noto\'g\'ri format' };
    }
    
    // Hajm tekshirish
    if (file.size > CONFIG.MAX_FILE_SIZE) {
        return { valid: false, reason: 'Fayl juda katta' };
    }
    
    // Duplicate tekshirish
    const exists = fileQueue.some(item => item.file.name === file.name && item.file.size === file.size);
    if (exists) {
        return { valid: false, reason: 'Fayl allaqachon mavjud' };
    }
    
    return { valid: true };
}

function addFileToQueue(file, transcription = '') {
    const fileItem = {
        id: generateId(),
        file: file,
        status: 'pending', // pending, uploading, processing, completed, error
        taskId: null,
        transcription: transcription,
        originalUrl: URL.createObjectURL(file),
        processedUrl: null,
        stats: null,
        error: null
    };
    
    fileQueue.push(fileItem);
    renderQueue();
    showFileQueue();
}

function generateId() {
    return 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// ============== Queue UI ==============
function showFileQueue() {
    fileQueueEl.style.display = 'block';
    uploadArea.style.display = 'none';
}

function hideFileQueue() {
    fileQueueEl.style.display = 'none';
    uploadArea.style.display = 'block';
}

function renderQueue() {
    queueList.innerHTML = '';
    fileCount.textContent = fileQueue.length;
    
    if (fileQueue.length === 0) {
        hideFileQueue();
        return;
    }
    
    fileQueue.forEach(item => {
        const el = createQueueItemElement(item);
        queueList.appendChild(el);
    });
    
    // Process button state
    const hasCompletedAll = fileQueue.every(item => item.status === 'completed');
    const hasPending = fileQueue.some(item => item.status === 'pending');
    
    processAllBtn.disabled = isProcessing || (!hasPending && !hasCompletedAll);
    processAllBtn.innerHTML = isProcessing 
        ? '<div class="spinner" style="display:inline-block"></div> Processing...'
        : '<i class="fas fa-wand-magic-sparkles"></i> Hammasini processing qilish';
}

function createQueueItemElement(item) {
    const div = document.createElement('div');
    div.className = `queue-item ${item.status}`;
    div.id = `queue-item-${item.id}`;
    
    // Icon
    const iconClass = {
        pending: 'fa-file-audio',
        uploading: 'fa-spinner fa-spin',
        processing: 'fa-gear fa-spin',
        completed: 'fa-check',
        error: 'fa-exclamation-triangle'
    }[item.status] || 'fa-file-audio';
    
    // Status text
    const statusText = {
        pending: 'Kutmoqda',
        uploading: 'Yuklanmoqda',
        processing: 'Processing',
        completed: 'Tayyor',
        error: 'Xato'
    }[item.status] || 'Kutmoqda';
    
    // Stats info
    let statsInfo = formatFileSize(item.file.size);
    if (item.stats) {
        statsInfo = `${formatDuration(item.stats.original_duration)} → ${formatDuration(item.stats.processed_duration)}`;
    }
    
    div.innerHTML = `
        <div class="queue-item-icon">
            <i class="fas ${iconClass}"></i>
        </div>
        <div class="queue-item-info">
            <div class="queue-item-name" title="${item.file.name}">${item.file.name}</div>
            <div class="queue-item-meta">
                <span>${statsInfo}</span>
                ${item.transcription ? '<i class="fas fa-file-lines" title="Transcription mavjud"></i>' : ''}
            </div>
        </div>
        <span class="queue-item-status">${statusText}</span>
        <div class="queue-item-actions">
            ${item.status === 'completed' ? `
                <button class="queue-item-btn download" onclick="downloadFile('${item.id}')" title="Yuklab olish">
                    <i class="fas fa-download"></i>
                </button>
            ` : ''}
            ${item.status !== 'processing' && item.status !== 'uploading' ? `
                <button class="queue-item-btn" onclick="removeFile('${item.id}')" title="Olib tashlash">
                    <i class="fas fa-times"></i>
                </button>
            ` : ''}
        </div>
    `;
    
    return div;
}

function updateQueueItem(id, updates) {
    const index = fileQueue.findIndex(item => item.id === id);
    if (index !== -1) {
        fileQueue[index] = { ...fileQueue[index], ...updates };
        renderQueue();
    }
}

// ============== File Actions ==============
function removeFile(id) {
    const index = fileQueue.findIndex(item => item.id === id);
    if (index !== -1) {
        const item = fileQueue[index];
        
        // URL tozalash
        if (item.originalUrl) URL.revokeObjectURL(item.originalUrl);
        
        fileQueue.splice(index, 1);
        renderQueue();
        
        if (fileQueue.length === 0) {
            hideFileQueue();
        }
    }
}

function clearAllFiles() {
    if (isProcessing) {
        showToast('Processing tugashini kuting', 'error');
        return;
    }
    
    // URL larni tozalash
    fileQueue.forEach(item => {
        if (item.originalUrl) URL.revokeObjectURL(item.originalUrl);
    });
    
    fileQueue = [];
    renderQueue();
    hideFileQueue();
    showToast('Barcha fayllar tozalandi', 'info');
}

function downloadFile(id) {
    const item = fileQueue.find(item => item.id === id);
    if (!item || !item.taskId) {
        showToast('Fayl topilmadi', 'error');
        return;
    }
    
    const downloadUrl = `${CONFIG.API_BASE}/download/${item.taskId}`;
    
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = item.file.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast('Yuklab olish boshlandi', 'success');
}

// Make functions global
window.removeFile = removeFile;
window.downloadFile = downloadFile;

// ============== Batch Processing ==============
async function processAllFiles() {
    if (isProcessing) return;
    
    const pendingFiles = fileQueue.filter(item => item.status === 'pending');
    if (pendingFiles.length === 0) {
        showToast('Processing qilinadigan fayl yo\'q', 'info');
        return;
    }
    
    isProcessing = true;
    renderQueue();
    
    const options = {
        denoise: optDenoise?.checked ?? true,
        trim_silence: optTrim?.checked ?? true,
        extract_speech: optExtract?.checked ?? true,
        normalize: optNormalize?.checked ?? true
    };
    
    let successCount = 0;
    let errorCount = 0;
    
    for (const item of pendingFiles) {
        try {
            await processFile(item, options);
            successCount++;
        } catch (error) {
            console.error(`Error processing ${item.file.name}:`, error);
            updateQueueItem(item.id, { 
                status: 'error', 
                error: error.message 
            });
            errorCount++;
        }
    }
    
    isProcessing = false;
    renderQueue();
    
    // Natija xabari
    if (successCount > 0 && errorCount === 0) {
        showToast(`${successCount} ta fayl muvaffaqiyatli processing qilindi! 🎉`, 'success');
    } else if (successCount > 0 && errorCount > 0) {
        showToast(`${successCount} ta tayyor, ${errorCount} ta xato`, 'info');
    } else {
        showToast('Processing xatosi', 'error');
    }
}

async function processFile(item, options) {
    // 1. Upload
    updateQueueItem(item.id, { status: 'uploading' });
    
    const formData = new FormData();
    formData.append('file', item.file);
    
    const uploadResponse = await fetch(`${CONFIG.API_BASE}/upload`, {
        method: 'POST',
        body: formData
    });
    
    if (!uploadResponse.ok) {
        const error = await uploadResponse.json();
        throw new Error(error.detail || 'Upload xatosi');
    }
    
    const uploadResult = await uploadResponse.json();
    const taskId = uploadResult.task_id;
    
    updateQueueItem(item.id, { taskId: taskId });
    
    // 2. Start processing
    updateQueueItem(item.id, { status: 'processing' });
    
    const processResponse = await fetch(`${CONFIG.API_BASE}/process/${taskId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(options)
    });
    
    if (!processResponse.ok) {
        const error = await processResponse.json();
        throw new Error(error.detail || 'Processing xatosi');
    }
    
    // 3. Poll status
    await pollStatus(item.id, taskId);
}

async function pollStatus(itemId, taskId) {
    return new Promise((resolve, reject) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`${CONFIG.API_BASE}/status/${taskId}`);
                const status = await response.json();
                
                if (status.status === 'completed') {
                    clearInterval(interval);
                    
                    updateQueueItem(itemId, {
                        status: 'completed',
                        processedUrl: `${CONFIG.API_BASE}/download/${taskId}`,
                        stats: {
                            original_duration: status.original_duration,
                            processed_duration: status.processed_duration
                        }
                    });
                    
                    resolve();
                } else if (status.status === 'failed') {
                    clearInterval(interval);
                    reject(new Error(status.message || 'Processing failed'));
                }
            } catch (error) {
                clearInterval(interval);
                reject(error);
            }
        }, 500);
        
        // Timeout (5 daqiqa)
        setTimeout(() => {
            clearInterval(interval);
            reject(new Error('Processing timeout'));
        }, 5 * 60 * 1000);
    });
}

// ============== Download All ==============
function downloadAllCompleted() {
    const completedFiles = fileQueue.filter(item => item.status === 'completed');
    
    if (completedFiles.length === 0) {
        showToast('Yuklab olinadigan fayl yo\'q', 'info');
        return;
    }
    
    // Har bir faylni ketma-ket yuklab olish
    completedFiles.forEach((item, index) => {
        setTimeout(() => {
            downloadFile(item.id);
        }, index * 500);
    });
    
    showToast(`${completedFiles.length} ta fayl yuklab olinmoqda`, 'success');
}

// ============== Utility Functions ==============
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '0s';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}m ${secs}s`;
}

function showToast(message, type = 'info') {
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) existingToast.remove();
    
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        info: 'fa-info-circle'
    };
    
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        info: '#6366f1'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span>${message}</span>
    `;
    
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${colors[type]};
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
    
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============== Reset ==============
function resetEditor() {
    clearAllFiles();
}

window.resetEditor = resetEditor;

console.log('🎧 Editor with batch support initialized');
