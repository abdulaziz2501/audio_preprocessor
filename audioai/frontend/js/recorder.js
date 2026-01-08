/**
 * AudioAI - Recorder JavaScript
 * Web audio yozish, live visualization va processing
 */

// ============== Configuration ==============
const CONFIG = {
    // Transcription majburiy yoki yo'qligini belgilash
    // true = majburiy, false = ixtiyoriy
    TRANSCRIPTION_REQUIRED: false,
    
    // Minimal transcription uzunligi (agar required bo'lsa)
    MIN_TRANSCRIPTION_LENGTH: 1,
    
    // Maksimal yozish vaqti (sekundda)
    MAX_RECORDING_TIME: 300, // 5 daqiqa
};

// ============== State ==============
let mediaRecorder = null;
let audioChunks = [];
let audioBlob = null;
let audioUrl = null;
let isRecording = false;
let timerInterval = null;
let recordingTime = 0;
let audioContext = null;
let analyser = null;
let animationId = null;

// ============== DOM Elements ==============
const recordBtn = document.getElementById('recordBtn');
const recordIcon = document.getElementById('recordIcon');
const recordingStatus = document.getElementById('recordingStatus');
const statusText = document.getElementById('statusText');
const timerDisplay = document.getElementById('timerDisplay');
const waveform = document.getElementById('waveform');
const resetBtn = document.getElementById('resetBtn');
const processBtn = document.getElementById('processBtn');
const previewSection = document.getElementById('previewSection');
const audioPreview = document.getElementById('audioPreview');
const permissionModal = document.getElementById('permissionModal');
const transcriptionInput = document.getElementById('transcriptionInput');
const optionalBadge = document.getElementById('optionalBadge');

// ============== Initialize ==============
document.addEventListener('DOMContentLoaded', function() {
    initRecorder();
    initWaveformBars();
    initTranscriptionConfig();
});

function initTranscriptionConfig() {
    // Transcription required/optional badge yangilash
    if (CONFIG.TRANSCRIPTION_REQUIRED) {
        optionalBadge.textContent = 'majburiy';
        optionalBadge.classList.add('required');
        transcriptionInput.setAttribute('required', 'true');
    } else {
        optionalBadge.textContent = 'ixtiyoriy';
        optionalBadge.classList.remove('required');
        transcriptionInput.removeAttribute('required');
    }
}

function initRecorder() {
    // Record button
    recordBtn.addEventListener('click', toggleRecording);
    
    // Reset button
    resetBtn.addEventListener('click', resetRecording);
    
    // Process button
    processBtn.addEventListener('click', sendToProcessing);
    
    // Check mikrofon permission
    checkMicrophonePermission();
}

// ============== Waveform Visualization ==============
function initWaveformBars() {
    // 40 ta bar yaratish
    const barCount = 40;
    waveform.innerHTML = '';
    
    for (let i = 0; i < barCount; i++) {
        const bar = document.createElement('div');
        bar.className = 'bar';
        bar.style.setProperty('--wave-height', '20px');
        bar.style.animationDelay = `${Math.random() * 0.5}s`;
        waveform.appendChild(bar);
    }
}

function updateWaveform(dataArray) {
    const bars = waveform.querySelectorAll('.bar');
    const bufferLength = dataArray.length;
    const step = Math.floor(bufferLength / bars.length);
    
    bars.forEach((bar, index) => {
        const value = dataArray[index * step] || 0;
        const height = Math.max(10, (value / 255) * 80);
        bar.style.height = `${height}px`;
    });
}

function startWaveformAnimation() {
    waveform.classList.add('active');
    
    function animate() {
        if (!isRecording || !analyser) return;
        
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyser.getByteFrequencyData(dataArray);
        
        updateWaveform(dataArray);
        
        animationId = requestAnimationFrame(animate);
    }
    
    animate();
}

function stopWaveformAnimation() {
    waveform.classList.remove('active');
    if (animationId) {
        cancelAnimationFrame(animationId);
    }
    
    // Barlarni default holatga qaytarish
    const bars = waveform.querySelectorAll('.bar');
    bars.forEach(bar => {
        bar.style.height = '20px';
    });
}

// ============== Microphone Permission ==============
async function checkMicrophonePermission() {
    try {
        const permissionStatus = await navigator.permissions.query({ name: 'microphone' });
        
        if (permissionStatus.state === 'denied') {
            showPermissionModal();
        }
        
        permissionStatus.onchange = () => {
            if (permissionStatus.state === 'denied') {
                showPermissionModal();
            } else {
                hidePermissionModal();
            }
        };
    } catch (error) {
        // Firefox da permissions API boshqacha ishlaydi
        console.log('Permission API not fully supported');
    }
}

function showPermissionModal() {
    permissionModal.classList.add('visible');
}

function hidePermissionModal() {
    permissionModal.classList.remove('visible');
}

async function requestPermission() {
    try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        hidePermissionModal();
        showToast('Mikrofon ruxsati berildi!', 'success');
    } catch (error) {
        showToast('Mikrofon ruxsati berilmadi', 'error');
    }
}

// ============== Recording ==============
async function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

async function startRecording() {
    try {
        // Mikrofonga ulanish
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                sampleRate: 16000
            } 
        });
        
        // Audio context yaratish (visualization uchun)
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);
        
        // MediaRecorder yaratish
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: getSupportedMimeType()
        });
        
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = handleRecordingStop;
        
        // Yozishni boshlash
        mediaRecorder.start(100); // 100ms intervalda data olish
        isRecording = true;
        
        // UI yangilash
        updateRecordingUI(true);
        
        // Timer boshlash
        startTimer();
        
        // Waveform animatsiya
        startWaveformAnimation();
        
    } catch (error) {
        console.error('Recording error:', error);
        
        if (error.name === 'NotAllowedError') {
            showPermissionModal();
        } else {
            showToast('Yozib olishda xato: ' + error.message, 'error');
        }
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        
        // Stream to'xtatish
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
    
    isRecording = false;
    
    // Timer to'xtatish
    stopTimer();
    
    // UI yangilash
    updateRecordingUI(false);
    
    // Waveform to'xtatish
    stopWaveformAnimation();
    
    // Audio context yopish
    if (audioContext) {
        audioContext.close();
    }
}

function handleRecordingStop() {
    // Audio blob yaratish
    const mimeType = getSupportedMimeType();
    audioBlob = new Blob(audioChunks, { type: mimeType });
    audioUrl = URL.createObjectURL(audioBlob);
    
    // Preview ko'rsatish
    showPreview();
    
    // Buttons enable
    resetBtn.disabled = false;
    processBtn.disabled = false;
    
    showToast('Yozib olindi! (' + formatTime(recordingTime) + ')', 'success');
}

// ============== Timer ==============
function startTimer() {
    recordingTime = 0;
    updateTimerDisplay();
    
    timerInterval = setInterval(() => {
        recordingTime++;
        updateTimerDisplay();
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function updateTimerDisplay() {
    const mins = Math.floor(recordingTime / 60);
    const secs = recordingTime % 60;
    timerDisplay.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// ============== UI Updates ==============
function updateRecordingUI(recording) {
    if (recording) {
        recordBtn.classList.add('recording');
        recordIcon.className = 'fas fa-stop';
        recordingStatus.classList.add('active');
        statusText.textContent = 'Yozilmoqda...';
        timerDisplay.classList.add('recording');
        
        // Disable buttons
        resetBtn.disabled = true;
        processBtn.disabled = true;
        
        // Hide preview
        previewSection.classList.remove('visible');
    } else {
        recordBtn.classList.remove('recording');
        recordIcon.className = 'fas fa-microphone';
        recordingStatus.classList.remove('active');
        statusText.textContent = 'To\'xtatildi';
        timerDisplay.classList.remove('recording');
    }
}

function showPreview() {
    audioPreview.src = audioUrl;
    previewSection.classList.add('visible');
}

// ============== Reset ==============
function resetRecording() {
    // Tozalash
    audioChunks = [];
    audioBlob = null;
    
    if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
        audioUrl = null;
    }
    
    // Timer reset
    recordingTime = 0;
    updateTimerDisplay();
    
    // UI reset
    statusText.textContent = 'Tayyor';
    previewSection.classList.remove('visible');
    audioPreview.src = '';
    
    // Transcription reset
    transcriptionInput.value = '';
    transcriptionInput.classList.remove('error');
    
    // Buttons
    resetBtn.disabled = true;
    processBtn.disabled = true;
    
    showToast('Tozalandi', 'info');
}

// ============== Send to Processing ==============
async function sendToProcessing() {
    if (!audioBlob) {
        showToast('Avval audio yozib oling', 'error');
        return;
    }
    
    // Transcription validation
    const transcription = transcriptionInput.value.trim();
    
    if (CONFIG.TRANSCRIPTION_REQUIRED) {
        if (transcription.length < CONFIG.MIN_TRANSCRIPTION_LENGTH) {
            showToast('Iltimos, audio matnini kiriting', 'error');
            transcriptionInput.classList.add('error');
            transcriptionInput.focus();
            return;
        }
    }
    
    // Error class olib tashlash
    transcriptionInput.classList.remove('error');
    
    // Audio faylni localStorage ga saqlash va editor sahifasiga yo'naltirish
    try {
        processBtn.disabled = true;
        processBtn.innerHTML = '<div class="spinner" style="display:inline-block"></div> Yuklanmoqda...';
        
        // Blob ni base64 ga aylantirish
        const reader = new FileReader();
        reader.onloadend = function() {
            // Session storage ga saqlash
            sessionStorage.setItem('recordedAudio', reader.result);
            sessionStorage.setItem('recordedAudioName', `recording_${Date.now()}.wav`);
            sessionStorage.setItem('recordedAudioDuration', recordingTime.toString());
            
            // Transcription saqlash (bo'sh bo'lsa ham)
            sessionStorage.setItem('recordedAudioTranscription', transcription);
            
            // Editor sahifasiga o'tish
            window.location.href = 'editor.html?fromRecorder=true';
        };
        reader.readAsDataURL(audioBlob);
        
    } catch (error) {
        console.error('Send error:', error);
        showToast('Xato: ' + error.message, 'error');
        processBtn.disabled = false;
        processBtn.innerHTML = '<i class="fas fa-wand-magic-sparkles"></i> Processing';
    }
}

// ============== Utility Functions ==============
function getSupportedMimeType() {
    const types = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/wav',
        'audio/mp4'
    ];
    
    for (const type of types) {
        if (MediaRecorder.isTypeSupported(type)) {
            return type;
        }
    }
    
    return 'audio/webm';
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function showToast(message, type = 'info') {
    // main.js dagi funksiyani ishlatish
    if (window.AudioAI && window.AudioAI.showToast) {
        window.AudioAI.showToast(message, type);
    } else {
        alert(message);
    }
}

// ============== Window Events ==============
window.addEventListener('beforeunload', (event) => {
    if (isRecording) {
        event.preventDefault();
        event.returnValue = 'Yozish davom etmoqda. Sahifani yopmoqchimisiz?';
    }
});

// Global function for permission modal
window.requestPermission = requestPermission;

console.log('🎙️ Recorder initialized');
