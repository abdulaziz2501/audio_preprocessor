/**
 * AudioAI - Verification Page JavaScript
 * Audio-Text verification batch processing
 */

// ============== Configuration ==============
const CONFIG = {
    API_BASE: 'http://localhost:8000/api',
    MAX_FILE_SIZE: 100 * 1024 * 1024, // 100 MB
    ALLOWED_EXTENSIONS: ['.wav', '.mp3', '.ogg', '.flac', '.m4a'],
    POLL_INTERVAL: 1000, // 1 second
};

// ============== State ==============
let uploadedFiles = [];
let currentJobId = null;
let pollInterval = null;
let results = [];

// ============== DOM Elements ==============
const referenceText = document.getElementById('referenceText');
const charCount = document.getElementById('charCount');
const uploadZone = document.getElementById('uploadZone');
const audioInput = document.getElementById('audioInput');
const fileList = document.getElementById('fileList');
const startBtn = document.getElementById('startBtn');

// Options
const whisperModel = document.getElementById('whisperModel');
const language = document.getElementById('language');
const optPreprocess = document.getElementById('optPreprocess');
const optTrimSilence = document.getElementById('optTrimSilence');

// Sections
const inputSection = document.getElementById('inputSection');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');

// Progress elements
const progressBar = document.getElementById('progressBar');
const progressPercent = document.getElementById('progressPercent');
const progressStatus = document.getElementById('progressStatus');
const completedCount = document.getElementById('completedCount');
const totalCount = document.getElementById('totalCount');
const taskList = document.getElementById('taskList');

// Results elements
const summaryTotal = document.getElementById('summaryTotal');
const summaryValid = document.getElementById('summaryValid');
const summaryWarning = document.getElementById('summaryWarning');
const summaryReject = document.getElementById('summaryReject');
const summaryAvg = document.getElementById('summaryAvg');
const resultsBody = document.getElementById('resultsBody');

// Modal
const detailModal = document.getElementById('detailModal');
const closeModal = document.getElementById('closeModal');

// ============== Initialize ==============
document.addEventListener('DOMContentLoaded', function() {
    initTextInput();
    initUpload();
    initButtons();
    initModal();
    initFilters();
});

function initTextInput() {
    referenceText.addEventListener('input', () => {
        charCount.textContent = referenceText.value.length;
        validateForm();
    });
}

function initUpload() {
    // Click to upload
    uploadZone.addEventListener('click', () => audioInput.click());

    // Drag & drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        handleFiles(Array.from(e.dataTransfer.files));
    });

    // File input change
    audioInput.addEventListener('change', (e) => {
        handleFiles(Array.from(e.target.files));
        audioInput.value = '';
    });
}

function initButtons() {
    startBtn.addEventListener('click', startVerification);

    document.getElementById('newJobBtn').addEventListener('click', resetAll);
    document.getElementById('downloadResultsBtn').addEventListener('click', downloadResults);
}

function initModal() {
    closeModal.addEventListener('click', () => {
        detailModal.classList.remove('visible');
    });

    detailModal.addEventListener('click', (e) => {
        if (e.target === detailModal) {
            detailModal.classList.remove('visible');
        }
    });
}

function initFilters() {
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const filter = tab.dataset.filter;
            renderResults(filter);
        });
    });
}

// ============== File Handling ==============
function handleFiles(files) {
    for (const file of files) {
        // Validate
        const ext = '.' + file.name.split('.').pop().toLowerCase();

        if (!CONFIG.ALLOWED_EXTENSIONS.includes(ext)) {
            showToast(`${file.name}: Noto'g'ri format`, 'error');
            continue;
        }

        if (file.size > CONFIG.MAX_FILE_SIZE) {
            showToast(`${file.name}: Fayl juda katta (max 100MB)`, 'error');
            continue;
        }

        // Check duplicate
        if (uploadedFiles.some(f => f.name === file.name)) {
            continue;
        }

        uploadedFiles.push(file);
    }

    renderFileList();
    validateForm();
}

function renderFileList() {
    if (uploadedFiles.length === 0) {
        fileList.innerHTML = '';
        uploadZone.classList.remove('has-files');
        return;
    }

    uploadZone.classList.add('has-files');

    fileList.innerHTML = uploadedFiles.map((file, index) => `
        <div class="file-item">
            <i class="fas fa-file-audio"></i>
            <span class="file-name" title="${file.name}">${file.name}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
            <button class="remove-btn" onclick="removeFile(${index})">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

function removeFile(index) {
    uploadedFiles.splice(index, 1);
    renderFileList();
    validateForm();
}

window.removeFile = removeFile;

// ============== Form Validation ==============
function validateForm() {
    const hasText = referenceText.value.trim().length > 0;
    const hasFiles = uploadedFiles.length > 0;

    startBtn.disabled = !(hasText && hasFiles);
}

// ============== Start Verification ==============
async function startVerification() {
    if (!referenceText.value.trim() || uploadedFiles.length === 0) {
        showToast('Reference matn va audio fayllar kerak', 'error');
        return;
    }

    // Show progress section
    inputSection.style.display = 'none';
    progressSection.classList.add('visible');
    resultsSection.classList.remove('visible');

    // Reset progress
    totalCount.textContent = uploadedFiles.length;
    completedCount.textContent = '0';
    progressBar.style.width = '0%';
    progressPercent.textContent = '0%';

    try {
        // Create FormData
        const formData = new FormData();
        formData.append('reference_text', referenceText.value.trim());
        formData.append('language', language.value);
        formData.append('whisper_model', whisperModel.value);
        formData.append('preprocess', optPreprocess.checked);
        formData.append('trim_silence', optTrimSilence.checked);
        formData.append('denoise', optPreprocess.checked);

        // Add all files
        for (const file of uploadedFiles) {
            formData.append('audio_files', file);
        }

        progressStatus.textContent = 'Fayllar yuklanmoqda...';

        // Upload and start job
        const response = await fetch(`${CONFIG.API_BASE}/verify-audios`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload xatosi');
        }

        const data = await response.json();
        currentJobId = data.job_id;

        progressStatus.textContent = 'Processing boshlanmoqda...';

        // Start polling
        startPolling();

    } catch (error) {
        console.error('Verification error:', error);
        showToast('Xato: ' + error.message, 'error');
        resetToInput();
    }
}

// ============== Status Polling ==============
function startPolling() {
    pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${CONFIG.API_BASE}/verify-status/${currentJobId}`);
            const status = await response.json();

            updateProgress(status);

            if (status.status === 'completed' || status.status === 'partial' || status.status === 'failed') {
                clearInterval(pollInterval);
                pollInterval = null;

                // Get results
                await fetchResults();
            }

        } catch (error) {
            console.error('Polling error:', error);
        }
    }, CONFIG.POLL_INTERVAL);
}

function updateProgress(status) {
    const progress = status.progress || 0;

    progressBar.style.width = `${progress}%`;
    progressPercent.textContent = `${Math.round(progress)}%`;
    completedCount.textContent = status.completed_tasks || 0;

    // Status message
    if (status.status === 'running') {
        progressStatus.textContent = `Processing... (${status.completed_tasks}/${status.total_tasks})`;
    } else if (status.status === 'completed') {
        progressStatus.textContent = 'Tugadi! ✅';
    }

    // Render task list
    renderTaskList(status.tasks || []);
}

function renderTaskList(tasks) {
    taskList.innerHTML = tasks.map(task => {
        const iconClass = {
            pending: 'fa-clock',
            processing: 'fa-spinner fa-spin',
            completed: 'fa-check',
            failed: 'fa-exclamation-triangle'
        }[task.status] || 'fa-clock';

        return `
            <div class="task-item ${task.status}">
                <div class="task-icon">
                    <i class="fas ${iconClass}"></i>
                </div>
                <span class="task-name">${task.audio_name}</span>
                <span class="task-status">${task.status}</span>
            </div>
        `;
    }).join('');
}

// ============== Fetch Results ==============
async function fetchResults() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/verify-result/${currentJobId}`);

        if (response.status === 202) {
            // Still processing
            setTimeout(fetchResults, 1000);
            return;
        }

        const data = await response.json();
        results = data.results || [];

        showResults(data);

    } catch (error) {
        console.error('Fetch results error:', error);
        showToast('Natijalarni olishda xato', 'error');
    }
}

// ============== Show Results ==============
function showResults(data) {
    progressSection.classList.remove('visible');
    resultsSection.classList.add('visible');

    // Update summary
    const summary = data.summary || {};
    summaryTotal.textContent = summary.total_processed || 0;
    summaryValid.textContent = summary.valid_count || 0;
    summaryWarning.textContent = summary.warning_count || 0;
    summaryReject.textContent = summary.reject_count || 0;
    summaryAvg.textContent = `${Math.round((summary.average_similarity || 0) * 100)}%`;

    // Render results table
    renderResults('all');

    showToast('Verification tugadi! 🎉', 'success');
}

function renderResults(filter = 'all') {
    let filteredResults = results;

    if (filter !== 'all') {
        filteredResults = results.filter(r => r.status === filter);
    }

    resultsBody.innerHTML = filteredResults.map((result, index) => {
        const similarity = Math.round((result.similarity || 0) * 100);
        const statusClass = result.status || 'reject';

        const statusIcon = {
            valid: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            reject: 'fa-times-circle'
        }[statusClass] || 'fa-question-circle';

        const transcription = result.transcription || '-';
        const shortTranscription = transcription.length > 50
            ? transcription.substring(0, 50) + '...'
            : transcription;

        return `
            <tr data-index="${index}">
                <td class="audio-name" title="${result.audio_name}">${result.audio_name}</td>
                <td>
                    <span class="similarity-badge ${statusClass}">${similarity}%</span>
                </td>
                <td>
                    <i class="fas ${statusIcon} status-icon ${statusClass}"></i>
                </td>
                <td title="${transcription}">${shortTranscription}</td>
                <td>
                    <button class="expand-btn" onclick="showDetail(${index})">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// ============== Detail Modal ==============
function showDetail(index) {
    const result = results[index];
    if (!result) return;

    document.getElementById('modalFileName').textContent = result.audio_name;
    document.getElementById('modalSimilarity').innerHTML = `
        <span class="similarity-badge ${result.status}">${Math.round(result.similarity * 100)}%</span>
        <span style="margin-left: 8px;">${result.status}</span>
    `;
    document.getElementById('modalTranscription').textContent = result.transcription || '-';
    document.getElementById('modalReference').textContent = result.reference_text || referenceText.value;

    // Missing words
    const missing = result.missing_words || [];
    document.getElementById('modalMissing').innerHTML = missing.length > 0
        ? missing.map(w => `<span class="word-tag missing">${w}</span>`).join(' ')
        : '<span style="color: var(--gray-500);">Yo\'q</span>';

    // Extra words
    const extra = result.extra_words || [];
    document.getElementById('modalExtra').innerHTML = extra.length > 0
        ? extra.map(w => `<span class="word-tag extra">${w}</span>`).join(' ')
        : '<span style="color: var(--gray-500);">Yo\'q</span>';

    detailModal.classList.add('visible');
}

window.showDetail = showDetail;

// ============== Download Results ==============
function downloadResults() {
    if (results.length === 0) {
        showToast('Yuklab olinadigan natija yo\'q', 'error');
        return;
    }

    // Create CSV
    const headers = ['Fayl nomi', 'Moslik', 'Status', 'Transcription', 'Missing Words', 'Extra Words'];
    const rows = results.map(r => [
        r.audio_name,
        `${Math.round(r.similarity * 100)}%`,
        r.status,
        `"${(r.transcription || '').replace(/"/g, '""')}"`,
        (r.missing_words || []).join('; '),
        (r.extra_words || []).join('; ')
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');

    // Download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `verification_results_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    showToast('CSV yuklab olindi', 'success');
}

// ============== Reset ==============
function resetAll() {
    // Clear state
    uploadedFiles = [];
    currentJobId = null;
    results = [];

    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }

    // Reset form
    referenceText.value = '';
    charCount.textContent = '0';
    renderFileList();
    validateForm();

    // Show input section
    inputSection.style.display = 'block';
    progressSection.classList.remove('visible');
    resultsSection.classList.remove('visible');
}

function resetToInput() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }

    inputSection.style.display = 'block';
    progressSection.classList.remove('visible');
}

// ============== Utilities ==============
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
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
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

console.log('🔍 Verification page initialized');