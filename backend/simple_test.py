#!/usr/bin/env python3
"""
Simple Import Test - Coverage'siz
"""

import sys
import os

# Backend papkani path'ga qo'shish
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

print("=" * 60)
print("🔍 AudioAI - Simple Import Test")
print("=" * 60)
print()

# Test 1: Strukturani tekshirish
print("📁 Checking Structure...")
dirs_ok = True
for dirname in ['api', 'services', 'utils']:
    path = os.path.join(backend_dir, dirname)
    if os.path.exists(path):
        print(f"   ✅ {dirname}/ exists")
    else:
        print(f"   ❌ {dirname}/ NOT FOUND")
        dirs_ok = False

print()

if not dirs_ok:
    print("❌ XATO: Ba'zi papkalar topilmadi!")
    print("   Loyiha strukturasini tekshiring")
    sys.exit(1)

# Test 2: Python fayllarni tekshirish
print("📄 Checking Files...")
files_ok = True
required_files = {
    'api/routes.py': 'API routes',
    'services/noise_reducer.py': 'Noise Reducer',
    'services/segmentation.py': 'Segmentation',
    'services/silence_remover.py': 'Silence Remover',
    'utils/audio_utils.py': 'Audio Utils'
}

for filepath, description in required_files.items():
    full_path = os.path.join(backend_dir, filepath)
    if os.path.exists(full_path):
        print(f"   ✅ {description}")
    else:
        print(f"   ❌ {description} NOT FOUND")
        files_ok = False

print()

if not files_ok:
    print("❌ XATO: Ba'zi fayllar topilmadi!")
    sys.exit(1)

# Test 3: Import'larni sinash
print("🧪 Testing Imports...")
print()

all_ok = True

# Utils
print("1️⃣ Utils...")
try:
    from utils import audio_utils
    print("   ✅ utils.audio_utils imported")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    all_ok = False

# Services
print()
print("2️⃣ Services...")
try:
    from services import noise_reducer
    print("   ✅ services.noise_reducer imported")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    all_ok = False

try:
    from services import segmentation
    print("   ✅ services.segmentation imported")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    all_ok = False

try:
    from services import silence_remover
    print("   ✅ services.silence_remover imported")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    all_ok = False

# API
print()
print("3️⃣ API...")
try:
    from api import routes
    print("   ✅ api.routes imported")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    all_ok = False

print()
print("=" * 60)

if all_ok:
    print("✅ SUCCESS! Barcha import'lar to'g'ri!")
    print()
    print("🚀 Backend ishga tushirishingiz mumkin:")
    print("   python main.py")
else:
    print("❌ FAILED! Ba'zi import'larda xato!")
    print()
    print("🔧 HAL QILISH:")
    print("   1. Virtual environment'ni faollashtiring:")
    print("      source venv/bin/activate")
    print()
    print("   2. Dependency'larni o'rnating:")
    print("      pip install -r requirements.txt")
    print()
    print("   3. __init__.py fayllar borligini tekshiring:")
    print("      ls api/__init__.py services/__init__.py utils/__init__.py")

print("=" * 60)