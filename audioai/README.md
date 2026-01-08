# 🎙️ AudioAI - STT Dataset Audio Preprocessing

<div align="center">

![AudioAI Banner](https://img.shields.io/badge/AudioAI-STT_Preprocessing-6366f1?style=for-the-badge&logo=audio&logoColor=white)

**Professional audio preprocessing platform for Speech-to-Text datasets**

[Demo](#demo) • [Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [API](#-api-documentation)

</div>

---

## 🎯 Overview

AudioAI is a modern web application designed specifically for preparing audio files for Speech-to-Text (STT) model training. Inspired by cleanvoice.ai's clean design, it provides:

- **Noise Removal** - Remove background noise using spectral gating
- **Silence Trimming** - Trim silence at beginning and end
- **Speech Extraction** - Extract only spoken parts (VAD)
- **Original Filename Preservation** - Dataset structure remains intact

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔇 **Noise Removal** | Spectral gating algorithm removes background noise |
| ✂️ **Silence Trimming** | Automatically trim silent parts at start/end |
| 🗣️ **Speech Extraction** | VAD-based speech-only extraction (15s → 5s) |
| 📁 **Original Filename** | Keeps original filename for batch processing |
| 🎙️ **Web Recorder** | Record audio directly in browser |
| 🎨 **Modern UI** | Cleanvoice.ai-inspired minimal design |
| ⚡ **Fast Processing** | Optimized for quick turnaround |
| 📱 **Responsive** | Works on desktop and mobile |

## 🛠️ Tech Stack

### Backend
- **Python 3.9+**
- **FastAPI** - Async web framework
- **Librosa** - Audio processing
- **Soundfile** - Audio I/O
- **NumPy/SciPy** - Numerical computing

### Frontend
- **HTML5/CSS3/JavaScript**
- **Modern CSS** - Custom properties, Grid, Flexbox
- **Web Audio API** - Real-time visualization
- **MediaRecorder API** - Browser recording

## 📦 Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Backend Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/audioai.git
cd audioai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
cd backend
pip install -r requirements.txt

# 4. Run server
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Option 1: Python simple server
cd frontend
python -m http.server 3000

# Option 2: Node.js (if installed)
npx serve frontend -p 3000

# Option 3: VS Code Live Server extension
```

### Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🚀 Usage

### 1. Upload Audio

1. Go to **Editor** page
2. Drag & drop audio file or click to select
3. Supported formats: WAV, MP3, OGG, FLAC, M4A

### 2. Configure Processing

Toggle processing options:
- ✅ Noise Removal
- ✅ Silence Trimming  
- ✅ Speech Extraction
- ✅ Normalization

### 3. Process & Download

1. Click **"Processing boshlash"**
2. Wait for processing to complete
3. Preview before/after audio
4. Download processed file (original filename preserved!)

### Recording Audio

1. Go to **Recorder** page
2. Click record button 🔴
3. Speak into microphone
4. Click stop
5. Click **"Processing"** to send to editor

## 📡 API Documentation

### Endpoints

#### Upload Audio
```http
POST /api/upload
Content-Type: multipart/form-data

file: <audio_file>
```

Response:
```json
{
  "task_id": "uuid",
  "filename": "original_name.wav",
  "message": "Fayl qabul qilindi"
}
```

#### Start Processing
```http
POST /api/process/{task_id}
Content-Type: application/json

{
  "denoise": true,
  "trim_silence": true,
  "extract_speech": true,
  "normalize": true
}
```

#### Check Status
```http
GET /api/status/{task_id}
```

Response:
```json
{
  "task_id": "uuid",
  "status": "processing",
  "progress": 50,
  "message": "Noise olib tashlanmoqda...",
  "original_duration": 15.5,
  "processed_duration": null
}
```

#### Download Processed
```http
GET /api/download/{task_id}
```

Returns: Audio file with original filename

## 📁 Project Structure

```
audioai/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   ├── audio_processing/
│   │   ├── __init__.py
│   │   ├── denoise.py         # Noise reduction
│   │   ├── vad.py             # Voice activity detection
│   │   └── trim.py            # Silence trimming
│   └── uploads/
│       ├── original/          # Uploaded files
│       └── processed/         # Processed files
│
├── frontend/
│   ├── index.html             # Home page
│   ├── recorder.html          # Recording page
│   ├── editor.html            # Upload & processing page
│   ├── css/
│   │   └── styles.css         # Main stylesheet
│   └── js/
│       ├── main.js            # Shared utilities
│       ├── recorder.js        # Recording logic
│       └── editor.js          # Editor logic
│
└── README.md
```

## 🎨 Design System

### Colors
```css
--primary: #6366f1;           /* Indigo */
--primary-start: #7c3aed;     /* Purple */
--primary-end: #2563eb;       /* Blue */
--accent-coral: #f97316;      /* Orange */
--accent-teal: #14b8a6;       /* Teal */
```

### Typography
- **Display**: Satoshi (headers)
- **Body**: Inter (text)

## 🔧 Configuration

### Backend Settings (main.py)
```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.ogg', '.flac', '.m4a'}
```

### Audio Processing Settings
```python
# Denoise settings
sample_rate = 16000
noise_reduce_strength = 0.7
highpass_freq = 80

# VAD settings
frame_duration_ms = 30
energy_threshold = 0.02
min_speech_duration = 0.1
min_silence_duration = 0.3

# Trim settings
top_db = 25
```

## 🚧 Future Improvements

- [ ] Batch processing (multiple files)
- [ ] Dataset export (JSON metadata)
- [ ] Language detection
- [ ] Custom STT model integration
- [ ] Real-time processing preview
- [ ] Docker containerization
- [ ] Cloud deployment

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- [Cleanvoice.ai](https://cleanvoice.ai) - Design inspiration
- [Librosa](https://librosa.org) - Audio processing
- [FastAPI](https://fastapi.tiangolo.com) - Web framework
- [Font Awesome](https://fontawesome.com) - Icons

---

<div align="center">

**Made with ❤️ for STT Dataset Preparation**

</div>
