# 🎵 AudioAI - Professional Audio Preprocessing Platform

Audio fayllarni professional darajada qayta ishlash uchun to'liq yechim. Shovqin tozalash, jimlikni olib tashlash va audio segmentatsiya imkoniyatlari.

## 📋 Xususiyatlar

### ✨ Asosiy Imkoniyatlar

1. **Noise Reduction (Shovqin Tozalash)**
   - Professional darajadagi shovqin tozalash
   - Sozlanuvchi tozalash kuchi (0.0 - 1.0)
   - Adaptiv va multi-pass tozalash

2. **Silence Removal (Jimlikni Olib Tashlash)**
   - Avtomatik jimlik aniqlash
   - Sozlanuvchi threshold va davomiylik
   - Bosh va oxir kesish imkoniyati

3. **Audio Segmentation (Bo'laklarga Bo'lish)**
   - Vaqt bo'yicha segmentatsiya
   - Jimlik joylarida bo'lish
   - Aqlli segmentatsiya (onset detection)
   - Overlap imkoniyati

### 🎨 Frontend Xususiyatlari

- Modern va responsive dizayn
- Drag & drop fayl yuklash
- Real-time progress tracking
- Sozlanuvchi parametrlar
- Mobile-friendly interface

### ⚡ Backend Xususiyatlari

- FastAPI + Uvicorn (yuqori tezlik)
- Asinxron qayta ishlash
- Professional audio kutubxonalar
- RESTful API
- Avtomatik dokumentatsiya

## 🚀 Ishga Tushirish

### 1️⃣ Talablar

- Python 3.8 yoki yuqori
- FFmpeg (audio processing uchun)
- 2GB+ RAM (tavsiya)

### 2️⃣ Tizimni Tayyorlash

#### Ubuntu/Linux:
```bash
# Python va pip yangilash
sudo apt update
sudo apt install python3 python3-pip ffmpeg

# Virtual environment o'rnatish
sudo apt install python3-venv
```

#### Windows:
```bash
# Python 3.8+ yuklab oling: python.org
# FFmpeg yuklab oling: ffmpeg.org
```

### 3️⃣ Backend'ni O'rnatish

```bash
# Loyiha papkasiga o'tish
cd backend

# Virtual environment yaratish
python3 -m venv venv

# Virtual environment'ni aktivlashtirish
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Dependency'larni o'rnatish
pip install -r requirements.txt
```

### 4️⃣ Backend'ni Ishga Tushirish

```bash
# Backend papkasida
python main.py
```

Yoki:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server ishga tushgandan keyin:
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

### 5️⃣ Frontend'ni Ishga Tushirish

Frontend uchun oddiy HTTP server kerak:

#### Python bilan:
```bash
cd frontend
python -m http.server 3000
```

#### Node.js bilan:
```bash
cd frontend
npx http-server -p 3000
```

#### VS Code Live Server:
- VS Code'da `frontend` papkasini oching
- `index.html`ni o'ng tugma bilan bosing
- "Open with Live Server" tanlang

Frontend ishga tushgandan keyin:
- Web Interface: http://localhost:3000

## 📁 Loyiha Strukturasi

```
AudioAI/
├── backend/
│   ├── main.py                 # FastAPI asosiy fayl
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API endpoint'lar
│   ├── services/
│   │   ├── noise_reducer.py   # Shovqin tozalash
│   │   ├── segmentation.py    # Segmentatsiya
│   │   └── silence_remover.py # Jimlik olib tashlash
│   ├── utils/
│   │   └── audio_utils.py     # Yordamchi funksiyalar
│   ├── uploads/               # Yuklangan fayllar
│   ├── outputs/               # Qayta ishlangan fayllar
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── index.html             # Asosiy HTML
│   ├── css/
│   │   ├── style.css          # Asosiy CSS
│   │   └── responsive.css     # Mobile CSS
│   └── js/
│       ├── app.js             # Main application
│       ├── audio-handler.js   # API bilan ishlash
│       └── ui-controller.js   # UI boshqaruvi
└── README.md                  # Bu fayl
```

## 🔧 API Endpoint'lar

### 1. Fayl Yuklash
```http
POST /api/v1/upload
Content-Type: multipart/form-data

file: audio_file.mp3
```

### 2. Shovqin Tozalash
```http
POST /api/v1/process/noise-reduction
Content-Type: multipart/form-data

file_id: 12345abcde
noise_reduction_strength: 0.8
```

### 3. Jimlikni Olib Tashlash
```http
POST /api/v1/process/remove-silence
Content-Type: multipart/form-data

file_id: 12345abcde
silence_threshold: -40
min_silence_duration: 500
```

### 4. Segmentatsiya
```http
POST /api/v1/process/segmentation
Content-Type: multipart/form-data

file_id: 12345abcde
segment_duration: 30
overlap: 0
```

### 5. To'liq Processing
```http
POST /api/v1/process/complete
Content-Type: multipart/form-data

file_id: 12345abcde
operations: {
  "noise_reduction": {"strength": 0.8},
  "remove_silence": {"threshold": -40},
  "segmentation": {"duration": 30}
}
```

## 💡 Foydalanish

### 1. Web Interface Orqali

1. Brauzerda http://localhost:3000 oching
2. Audio fayl yuklang (drag & drop yoki click)
3. Kerakli operatsiyalarni tanlang va sozlang:
   - Noise Reduction (shovqin tozalash)
   - Remove Silence (jimlikni olib tashlash)
   - Segmentation (bo'laklarga bo'lish)
4. "Start Processing" tugmasini bosing
5. Natijalarni yuklab oling

### 2. API Orqali (cURL)

```bash
# Fayl yuklash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@audio.mp3"

# Shovqin tozalash
curl -X POST http://localhost:8000/api/v1/process/noise-reduction \
  -F "file_id=12345" \
  -F "noise_reduction_strength=0.8" \
  --output cleaned_audio.wav
```

### 3. Python orqali

```python
import requests

# Fayl yuklash
with open('audio.mp3', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/upload',
        files={'file': f}
    )
    file_id = response.json()['file_id']

# Shovqin tozalash
response = requests.post(
    'http://localhost:8000/api/v1/process/noise-reduction',
    data={
        'file_id': file_id,
        'noise_reduction_strength': 0.8
    }
)

# Natijani saqlash
with open('cleaned_audio.wav', 'wb') as f:
    f.write(response.content)
```

## ⚙️ Konfiguratsiya

### Backend Sozlamalari

`backend/main.py` faylida:
```python
# Server host va port
host = "0.0.0.0"
port = 8000

# CORS sozlamalari
allow_origins = ["*"]  # Production'da aniq domenlarni yozing
```

### Frontend Sozlamalari

`frontend/js/audio-handler.js` faylida:
```javascript
// API URL
API_URL: 'http://localhost:8000/api/v1'
```

## 🐛 Muammolarni Hal Qilish

### Backend ishlamayapti
```bash
# Virtual environment aktivligini tekshiring
which python  # Linux/Mac
where python  # Windows

# Port bandligini tekshiring
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Loglarni ko'ring
python main.py
```

### Frontend backend'ga ulanmayapti
```bash
# CORS sozlamalarini tekshiring
# Browser console'da xatolarni ko'ring (F12)
# Backend ishga tushganini tekshiring: http://localhost:8000/health
```

### FFmpeg topilmadi
```bash
# Ubuntu/Linux
sudo apt install ffmpeg

# Mac
brew install ffmpeg

# Windows
# ffmpeg.org dan yuklab oling va PATH'ga qo'shing
```

## 📊 Performance

- **Small files** (<10MB): ~2-5 sekund
- **Medium files** (10-50MB): ~5-15 sekund
- **Large files** (50-100MB): ~15-30 sekund

Tezlik kompyuter imkoniyatlariga va tanlangan operatsiyalarga bog'liq.

## 🔒 Xavfsizlik

- Fayllar 24 soatdan keyin avtomatik o'chiriladi
- Maksimal fayl hajmi: 100MB
- Faqat audio formatlar qabul qilinadi
- CORS himoyasi

## 🚧 Kelajakdagi Rejalar

- [ ] Batch processing (ko'p fayllarni bir vaqtda)
- [ ] Audio effects (reverb, echo, etc.)
- [ ] Format conversion
- [ ] Cloud storage integration
- [ ] User authentication
- [ ] Processing history
- [ ] Audio visualization

## 🤝 Hissa Qo'shish

Bu loyihani yaxshilash uchun Pull Request yuboring yoki Issue yarating.

## 📄 Litsenziya

MIT License - bepul foydalanish mumkin.

## 👨‍💻 Muallif

**Your Name**
- Email: your.email@example.com
- GitHub: github.com/yourusername

## 🙏 Minnatdorchilik

- [FastAPI](https://fastapi.tiangolo.com/)
- [Librosa](https://librosa.org/)
- [Pydub](http://pydub.com/)
- [Noisereduce](https://github.com/timsainb/noisereduce)

---

**AudioAI** - Professional Audio Preprocessing Made Simple! 🎵
