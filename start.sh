#!/bin/bash

# AudioAI - Quick Start Script
# Bu script loyihani avtomatik ravishda ishga tushiradi

echo "🎵 AudioAI - Starting..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 topilmadi. Iltimos, Python 3.8+ o'rnating.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python topildi: $(python3 --version)${NC}"

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}⚠️  FFmpeg topilmadi. Audio processing uchun FFmpeg kerak.${NC}"
    echo -e "${YELLOW}   Ubuntu/Debian: sudo apt install ffmpeg${NC}"
    echo -e "${YELLOW}   Mac: brew install ffmpeg${NC}"
    read -p "Davom ettirishni xohlaysizmi? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ FFmpeg topildi${NC}"
fi

# Backend setup
echo ""
echo -e "${BLUE}📦 Backend'ni tayyorlash...${NC}"

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}   Virtual environment yaratilmoqda...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}   Dependencies o'rnatilmoqda...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend dependencies o'rnatildi${NC}"
else
    echo -e "${RED}❌ Dependencies o'rnatishda xatolik${NC}"
    exit 1
fi

# Create necessary directories
mkdir -p uploads outputs outputs/segments temp

# Start backend
echo ""
echo -e "${BLUE}🚀 Backend ishga tushirilmoqda...${NC}"
echo -e "${YELLOW}   Backend URL: http://localhost:8000${NC}"
echo -e "${YELLOW}   API Docs: http://localhost:8000/api/docs${NC}"
echo ""

python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend ishga tushdi!${NC}"
else
    echo -e "${RED}❌ Backend ishga tushmadi${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Frontend setup
echo ""
echo -e "${BLUE}🌐 Frontend'ni ishga tushirish...${NC}"

cd ../frontend

# Check if Python http.server can be used
if command -v python3 &> /dev/null; then
    echo -e "${YELLOW}   Frontend URL: http://localhost:3000${NC}"
    echo ""
    python3 -m http.server 3000 &
    FRONTEND_PID=$!
    
    sleep 2
    
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Frontend ishga tushdi!${NC}"
    else
        echo -e "${RED}❌ Frontend ishga tushmadi${NC}"
    fi
fi

# Final message
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                       ║${NC}"
echo -e "${GREEN}║      🎵 AudioAI Ishga Tushdi! 🎵     ║${NC}"
echo -e "${GREEN}║                                       ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Backend:${NC}  http://localhost:8000"
echo -e "${BLUE}Frontend:${NC} http://localhost:3000"
echo -e "${BLUE}API Docs:${NC} http://localhost:8000/api/docs"
echo ""
echo -e "${YELLOW}To'xtatish uchun: Ctrl+C${NC}"
echo ""

# Wait for user interrupt
trap "echo ''; echo 'To\'xtatilmoqda...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

# Keep script running
wait
