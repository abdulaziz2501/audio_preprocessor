import os
import shutil
from PIL import Image
import imagehash
from tqdm import tqdm

# ========== CONFIG ==========
DATASET_DIR = "dataset"
UNIQUE_DIR = "unique"
THRESHOLD = 7
PREFIX_BITS = 12
EXTS = (".jpg", ".jpeg", ".png", ".webp")
# ============================

os.makedirs(UNIQUE_DIR, exist_ok=True)

def phash_int(path):
    with Image.open(path) as img:
        img = img.convert("RGB")
        return int(str(imagehash.phash(img)), 16)

def prefix(h):
    return h >> (64 - PREFIX_BITS)

def hamming(a, b):
    return bin(a ^ b).count("1")

# ===== load existing unique hashes (IMPORTANT) =====
print("🔄 Loading existing UNIQUE hashes...")
global_buckets = {}

for class_name in os.listdir(UNIQUE_DIR):
    class_path = os.path.join(UNIQUE_DIR, class_name)
    if not os.path.isdir(class_path):
        continue

    for img in os.listdir(class_path):
        if not img.lower().endswith(EXTS):
            continue

        path = os.path.join(class_path, img)
        try:
            h = phash_int(path)
            p = prefix(h)
            global_buckets.setdefault(p, []).append(h)
        except:
            pass

print("✅ Existing UNIQUE loaded")

# ===== process dataset =====
for class_name in os.listdir(DATASET_DIR):
    src_class = os.path.join(DATASET_DIR, class_name)
    if not os.path.isdir(src_class):
        continue

    print(f"\n📂 Processing class: {class_name}")

    dst_class = os.path.join(UNIQUE_DIR, class_name)
    os.makedirs(dst_class, exist_ok=True)

    images = [f for f in os.listdir(src_class) if f.lower().endswith(EXTS)]

    for img_name in tqdm(images, desc=class_name):
        src_path = os.path.join(src_class, img_name)

        try:
            h = phash_int(src_path)
            p = prefix(h)

            is_duplicate = False

            # check neighbor buckets
            for nb in (p - 1, p, p + 1):
                if nb in global_buckets:
                    for eh in global_buckets[nb]:
                        if hamming(h, eh) <= THRESHOLD:
                            is_duplicate = True
                            break
                if is_duplicate:
                    break

            if not is_duplicate:
                dst_path = os.path.join(dst_class, img_name)

                # avoid overwrite
                base, ext = os.path.splitext(img_name)
                i = 1
                while os.path.exists(dst_path):
                    dst_path = os.path.join(dst_class, f"{base}_{i}{ext}")
                    i += 1

                shutil.copy2(src_path, dst_path)

                # add to global unique
                global_buckets.setdefault(p, []).append(h)

        except Exception as e:
            print(f"⚠️ Error: {img_name} → {e}")

print("\n✅ DONE — UNIQUE dataset safely built")
