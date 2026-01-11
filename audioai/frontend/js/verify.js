/**
 * AudioAI - Verification Page JavaScript
 * Audio-Text verification batch processing (Updated for dual upload)
 */

// ============== Configuration ==============
const CONFIG = {
    API_BASE: 'http://localhost:8000/api',
    MAX_FILE_SIZE: 100 * 1024 * 1024, // 100 MB
    POLL_INTERVAL: 1000, // 1 second
    MIN_SIMILARITY_VALID: 0.9, // 90% va undan yuqori
    MIN_SIMILARITY_WARNING: 0.7, // 70-90%
};

// ============== State ==============
let uploadedTextFiles = [];
let uploadedAudioFiles = [];
let matchedPairs = [];
let currentJobId = null;
let pollInterval = null;
let results = [];

// ============== DOM Elements ==============
// Text Upload Elements
const textUploadZone = document.getElementById('textUploadZone');
const textInput = document.getElementById('textInput');
const textFileList = document.getElementById('textFileList');
const textCount = document.getElementById('textCount');

// Audio Upload Elements
const audioUploadZone = document.getElementById('audioUploadZone');
const audioInput = document.getElementById('audioInput');
const audioFileList = document.getElementById('audioFileList');
const audioCount = document.getElementById('audioCount');

// Match Preview Elements
const matchSection = document.getElementById('matchSection');
const matchList = document.getElementById('matchList');
const matchedCount = document.getElementById('matchedCount');
const unmatchedCount = document.getElementById('unmatchedCount');

// Options
const whisperModel = document.getElementById('whisperModel');
const language = document.getElementById('language');
const optPreprocess = document.getElementById('optPreprocess');
const optTrimSilence = document.getElementById('optTrimSilence');

// Buttons
const clearBtn = document.getElementById('clearBtn');
const startBtn = document.getElementById('startBtn');
const newJobBtn = document.getElementById('newJobBtn');
const downloadResultsBtn = document.getElementById('downloadResultsBtn');

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
const modalFileName = document.getElementById('modalFileName');
const modalSimilarity = document.getElementById('modalSimilarity');
const modalTranscription = document.getElementById('modalTranscription');
const modalReference = document.getElementById('modalReference');
const modalMissing = document.getElementById('modalMissing');
const modalExtra = document.getElementById('modalExtra');

// ============== Initialize ==============
document.addEventListener('DOMContentLoaded', function() {
    initUploadZones();
    initButtons();
    initModal();
    initFilters();
    updateStartButton();
});

function initUploadZones() {
    // Text Upload Zone
    textUploadZone.addEventListener('click', () => textInput.click());
    initDragAndDrop(textUploadZone, handleTextFiles);
    textInput.addEventListener('change', (e) => {
        handleTextFiles(Array.from(e.target.files));
        textInput.value = '';
    });

    // Audio Upload Zone
    audioUploadZone.addEventListener('click', () => audioInput.click());
    initDragAndDrop(audioUploadZone, handleAudioFiles);
    audioInput.addEventListener('change', (e) => {
        handleAudioFiles(Array.from(e.target.files));
        audioInput.value = '';
    });
}

function initDragAndDrop(zone, handleFilesCallback) {
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        handleFilesCallback(Array.from(e.dataTransfer.files));
    });
}

function initButtons() {
    clearBtn.addEventListener('click', clearAllFiles);
    startBtn.addEventListener('click', startVerification);
    newJobBtn.addEventListener('click', resetAll);
    downloadResultsBtn.addEventListener('click', downloadResults);
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
function handleTextFiles(files) {
    for (const file of files) {
        // Validate file extension
        if (!file.name.toLowerCase().endsWith('.txt')) {
            showToast(`${file.name}: Faqat .txt fayllar qabul qilinadi`, 'error');
            continue;
        }

        // Validate file size
        if (file.size > CONFIG.MAX_FILE_SIZE) {
            showToast(`${file.name}: Fayl juda katta (max 100MB)`, 'error');
            continue;
        }

        // Check for duplicates
        if (uploadedTextFiles.some(f => f.name === file.name)) {
            showToast(`${file.name}: Bu fayl allaqachon yuklangan`, 'info');
            continue;
        }

        uploadedTextFiles.push(file);
    }

    renderTextFileList();
    matchFiles();
    updateStartButton();
}

function handleAudioFiles(files) {
    for (const file of files) {
        // Validate file extension
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        const allowedAudioExt = ['.wav', '.mp3', '.ogg', '.flac', '.m4a'];

        if (!allowedAudioExt.includes(ext)) {
            showToast(`${file.name}: Noto'g'ri audio format`, 'error');
            continue;
        }

        // Validate file size
        if (file.size > CONFIG.MAX_FILE_SIZE) {
            showToast(`${file.name}: Fayl juda katta (max 100MB)`, 'error');
            continue;
        }

        // Check for duplicates
        if (uploadedAudioFiles.some(f => f.name === file.name)) {
            showToast(`${file.name}: Bu fayl allaqachon yuklangan`, 'info');
            continue;
        }

        uploadedAudioFiles.push(file);
    }

    renderAudioFileList();
    matchFiles();
    updateStartButton();
}

function removeTextFile(index) {
    uploadedTextFiles.splice(index, 1);
    renderTextFileList();
    matchFiles();
    updateStartButton();
}

function removeAudioFile(index) {
    uploadedAudioFiles.splice(index, 1);
    renderAudioFileList();
    matchFiles();
    updateStartButton();
}

window.removeTextFile = removeTextFile;
window.removeAudioFile = removeAudioFile;

function renderTextFileList() {
    textCount.textContent = uploadedTextFiles.length;
    textCount.classList.toggle('has-files', uploadedTextFiles.length > 0);
    textUploadZone.classList.toggle('has-files', uploadedTextFiles.length > 0);

    if (uploadedTextFiles.length === 0) {
        textFileList.innerHTML = '';
        return;
    }

    textFileList.innerHTML = uploadedTextFiles.map((file, index) => `
        <div class="file-item text-file">
            <i class="fas fa-file-lines"></i>
            <span class="file-name" title="${file.name}">${file.name}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
            <button class="remove-btn" onclick="removeTextFile(${index})">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

function renderAudioFileList() {
    audioCount.textContent = uploadedAudioFiles.length;
    audioCount.classList.toggle('has-files', uploadedAudioFiles.length > 0);
    audioUploadZone.classList.toggle('has-files', uploadedAudioFiles.length > 0);

    if (uploadedAudioFiles.length === 0) {
        audioFileList.innerHTML = '';
        return;
    }

    audioFileList.innerHTML = uploadedAudioFiles.map((file, index) => `
        <div class="file-item audio-file">
            <i class="fas fa-file-audio"></i>
            <span class="file-name" title="${file.name}">${file.name}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
            <button class="remove-btn" onclick="removeAudioFile(${index})">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

// ============== File Matching ==============
function matchFiles() {
    matchedPairs = [];

    // Create maps for easy lookup
    const textFilesMap = new Map();
    const audioFilesMap = new Map();

    uploadedTextFiles.forEach(file => {
        const baseName = getBaseName(file.name);
        textFilesMap.set(baseName, file);
    });

    uploadedAudioFiles.forEach(file => {
        const baseName = getBaseName(file.name);
        audioFilesMap.set(baseName, file);
    });

    // Find matches
    const allBaseNames = new Set([...textFilesMap.keys(), ...audioFilesMap.keys()]);

    allBaseNames.forEach(baseName => {
        const textFile = textFilesMap.get(baseName);
        const audioFile = audioFilesMap.get(baseName);

        if (textFile && audioFile) {
            matchedPairs.push({
                baseName: baseName,
                textFile: textFile,
                audioFile: audioFile,
                matched: true
            });
        } else if (textFile) {
            matchedPairs.push({
                baseName: baseName,
                textFile: textFile,
                audioFile: null,
                matched: false
            });
        } else if (audioFile) {
            matchedPairs.push({
                baseName: baseName,
                textFile: null,
                audioFile: audioFile,
                matched: false
            });
        }
    });

    // Sort by base name
    matchedPairs.sort((a, b) => a.baseName.localeCompare(b.baseName));

    renderMatchPreview();
}

function getBaseName(filename) {
    // Remove extension and any path
    const name = filename.split('/').pop().split('\\').pop();
    return name.replace(/\.[^/.]+$/, '');
}

function renderMatchPreview() {
    const matched = matchedPairs.filter(pair => pair.matched).length;
    const unmatched = matchedPairs.filter(pair => !pair.matched).length;

    matchedCount.textContent = matched;
    unmatchedCount.textContent = unmatched;

    // Show/hide match section
    if (matchedPairs.length > 0) {
        matchSection.style.display = 'block';
    } else {
        matchSection.style.display = 'none';
    }

    // Render match list
    matchList.innerHTML = matchedPairs.map(pair => `
        <div class="match-item ${pair.matched ? 'matched' : 'unmatched'}">
            <div class="text-name" title="${pair.textFile ? pair.textFile.name : ''}">
                ${pair.textFile ? pair.textFile.name : '<span class="no-match">No text</span>'}
            </div>
            <div class="match-icon">
                <i class="fas ${pair.matched ? 'fa-link' : 'fa-unlink'}"></i>
            </div>
            <div class="audio-name" title="${pair.audioFile ? pair.audioFile.name : ''}">
                ${pair.audioFile ? pair.audioFile.name : '<span class="no-match">No audio</span>'}
            </div>
        </div>
    `).join('');
}

// ============== Form Validation ==============
function updateStartButton() {
    const hasTextFiles = uploadedTextFiles.length > 0;
    const hasAudioFiles = uploadedAudioFiles.length > 0;
    const hasMatchedPairs = matchedPairs.some(pair => pair.matched);

    startBtn.disabled = !(hasTextFiles && hasAudioFiles && hasMatchedPairs);
}

// ============== Start Verification ==============
async function startVerification() {
    // Filter only matched pairs
    const validPairs = matchedPairs.filter(pair => pair.matched);

    if (validPairs.length === 0) {
        showToast('Moslashtirilgan fayllar yo\'q', 'error');
        return;
    }

    // Show progress section
    inputSection.style.display = 'none';
    progressSection.classList.add('visible');
    resultsSection.classList.remove('visible');

    // Reset progress
    totalCount.textContent = validPairs.length;
    completedCount.textContent = '0';
    progressBar.style.width = '0%';
    progressPercent.textContent = '0%';
    taskList.innerHTML = '';

    try {
        // Create FormData
        const formData = new FormData();
        formData.append('language', language.value);
        formData.append('whisper_model', whisperModel.value);
        formData.append('preprocess', optPreprocess.checked);
        formData.append('trim_silence', optTrimSilence.checked);
        formData.append('denoise', optPreprocess.checked);

        // Add text files
        validPairs.forEach(pair => {
            formData.append('text_files', pair.textFile);
        });

        // Add audio files
        validPairs.forEach(pair => {
            formData.append('audio_files', pair.audioFile);
        });

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

        const statusText = {
            pending: 'Kutilmoqda',
            processing: 'Processing',
            completed: 'Tayyor',
            failed: 'Xatolik'
        }[task.status] || task.status;

        return `
            <div class="task-item ${task.status}">
                <div class="task-icon">
                    <i class="fas ${iconClass}"></i>
                </div>
                <span class="task-name">${task.audio_name || task.filename || 'Noma\'lum'}</span>
                <span class="task-status">${statusText}</span>
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

        // Add status based on similarity
        results.forEach(result => {
            const similarity = result.similarity || 0;
            if (similarity >= CONFIG.MIN_SIMILARITY_VALID) {
                result.status = 'valid';
            } else if (similarity >= CONFIG.MIN_SIMILARITY_WARNING) {
                result.status = 'warning';
            } else {
                result.status = 'reject';
            }
        });

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

    // Calculate summary
    const total = results.length;
    const valid = results.filter(r => r.status === 'valid').length;
    const warning = results.filter(r => r.status === 'warning').length;
    const reject = results.filter(r => r.status === 'reject').length;
    const avgSimilarity = results.reduce((sum, r) => sum + (r.similarity || 0), 0) / total;

    // Update summary
    summaryTotal.textContent = total;
    summaryValid.textContent = valid;
    summaryWarning.textContent = warning;
    summaryReject.textContent = reject;
    summaryAvg.textContent = `${Math.round(avgSimilarity * 100)}%`;

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

    modalFileName.textContent = result.audio_name || 'Noma\'lum';
    modalSimilarity.innerHTML = `
        <span class="similarity-badge ${result.status}">${Math.round((result.similarity || 0) * 100)}%</span>
        <span style="margin-left: 8px; font-size: 0.9em; color: var(--gray-600)">${result.status}</span>
    `;
    modalTranscription.textContent = result.transcription || '-';
    modalReference.textContent = result.reference_text || '-';

    // Missing words
    const missing = result.missing_words || [];
    modalMissing.innerHTML = missing.length > 0
        ? missing.map(w => `<span class="word-tag missing">${w}</span>`).join(' ')
        : '<span style="color: var(--gray-500);">Yo\'q</span>';

    // Extra words
    const extra = result.extra_words || [];
    modalExtra.innerHTML = extra.length > 0
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
    const headers = ['Fayl nomi', 'Moslik', 'Status', 'Transcription', 'Reference Text', 'Missing Words', 'Extra Words'];
    const rows = results.map(r => [
        r.audio_name,
        `${Math.round((r.similarity || 0) * 100)}%`,
        r.status,
        `"${(r.transcription || '').replace(/"/g, '""')}"`,
        `"${(r.reference_text || '').replace(/"/g, '""')}"`,
        (r.missing_words || []).join('; '),
        (r.extra_words || []).join('; ')
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');

    // Download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `verification_results_${new Date().toISOString().split('T')[0]}_${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    showToast('CSV yuklab olindi', 'success');
}

// ============== Reset Functions ==============
function clearAllFiles() {
    uploadedTextFiles = [];
    uploadedAudioFiles = [];
    matchedPairs = [];

    renderTextFileList();
    renderAudioFileList();
    renderMatchPreview();
    updateStartButton();

    showToast('Barcha fayllar tozalandi', 'info');
}

function resetAll() {
    // Clear state
    uploadedTextFiles = [];
    uploadedAudioFiles = [];
    matchedPairs = [];
    currentJobId = null;
    results = [];

    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }

    // Reset UI
    renderTextFileList();
    renderAudioFileList();
    renderMatchPreview();
    updateStartButton();

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

console.log('🔍 Verification page initialized (Updated for dual upload)');