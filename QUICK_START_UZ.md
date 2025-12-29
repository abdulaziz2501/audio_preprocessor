# 🚀 AudioAI - Tez Ishga Tushirish (O'zbek)

## 📥 1. Loyihani Yuklab Olish

Barcha fayllar tayyor! Download tugmasini bosing va zip faylni kompyuteringizga saqlang.

## 🔧 2. Kerakli Dasturlar

### Ubuntu/Linux:
```bash
# Python va FFmpeg o'rnatish
sudo apt update
sudo apt install python3 python3-pip python3-venv ffmpeg
```

### Windows:
1. Python 3.8+ yuklab oling: https://python.org
2. FFmpeg yuklab oling: https://ffmpeg.org
3. FFmpeg'ni PATH'ga qo'shing

### Mac:
```bash
# Homebrew orqali
brew install python ffmpeg
```

## ⚡ 3. Ishga Tushirish (Super Oson!)

### Linux/Mac:
```bash
# Loyiha papkasiga kirish
cd AudioAI

# Avtomatik ishga tushirish
./start.sh
```

### Windows:
```bash
# Backend'ni ishga tushirish (1-terminal)
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Frontend'ni ishga tushirish (2-terminal)
cd frontend
python -m http.server 3000
```

## 🎯 4. Foydalanish

1. Brauzeringizda oching: **http://localhost:3000**
2. Audio fayl yuklang
3. Kerakli amaliyotlarni tanlang:
   - ✨ Shovqin tozalash
   - 🔇 Jimlikni olib tashlash
   - ✂️ Bo'laklarga bo'lish
4. Sozlamalarni o'zgartiring
5. "Start Processing" bosing
6. Natijalarni yuklab oling!

## 📊 API Hujjatlari

Backend ishga tushgandan keyin: **http://localhost:8000/api/docs**

## 🐛 Muammolar?

### Backend ishlamayapti?
```bash
# Port bandmi?
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Virtual environment aktivmi?
which python  # Natija venv papkasidan bo'lishi kerak
```

### FFmpeg topilmadi?
```bash
# Tekshirish
ffmpeg -version

# O'rnatish
# Ubuntu: sudo apt install ffmpeg
# Mac: brew install ffmpeg
# Windows: ffmpeg.org dan yuklab PATH'ga qo'shing
```

### Frontend backend'ga ulanmayapti?
- Backend ishga tushganini tekshiring: http://localhost:8000/health
- Browser console'ni tekshiring (F12)
- CORS xatosi bo'lsa, backend/main.py'da CORS sozlamalarini tekshiring

## 📁 Fayl Strukturasi

```
AudioAI/
├── 📂 backend/          # Python FastAPI backend
│   ├── main.py          # Server
│   ├── api/             # API endpoint'lar
│   ├── services/        # Audio processing
│   └── requirements.txt # Dependencies
├── 📂 frontend/         # Web interface
│   ├── index.html       # Asosiy sahifa
│   ├── css/             # Stillar
│   └── js/              # JavaScript
├── 📄 README.md         # To'liq dokumentatsiya
└── 🚀 start.sh          # Tez ishga tushirish
```

## 💡 Maslahatlar

1. **Kichik fayllar bilan sinab ko'ring** - birinchi marta 1-2 minutlik audio ishlatib ko'ring
2. **Parametrlarni sinab ko'ring** - har bir sozlama natijaga qanday ta'sir qilishini ko'ring
3. **Bir nechta operatsiyani birlashtiring** - shovqin tozalash + jimlik olib tashlash + segmentatsiya
4. **Natijalarni taqqoslang** - original va qayta ishlangan audio'ni solishtiring

## 🎓 Qo'shimcha Ma'lumot

- To'liq dokumentatsiya: README.md faylini o'qing
- API endpoint'lar: http://localhost:8000/api/docs
- Source code: Barcha fayllar ochiq va o'zgartirish mumkin

## ⚙️ Sozlamalar

### Backend Port O'zgartirish
`backend/main.py` faylida:
```python
port = 8000  # Bu qiymatni o'zgartiring
```

### Frontend API URL
`frontend/js/audio-handler.js` faylida:
```javascript
API_URL: 'http://localhost:8000/api/v1'  # O'zgartiring
```

## 🆘 Yordam Kerakmi?

- Backend loglarini ko'ring: Terminal'dagi xabarlar
- Browser console'ni tekshiring: F12 > Console
- README.md'da batafsil ma'lumotlar bor

---

**AudioAI** - Audio preprocessing oson va tez! 🎵

Omad! Savol bo'lsa so'rang! 😊
