"""
Bước 1: Lọc dataset - Chỉ giữ lại 5 loại iPhone
Classes được chọn:
  0: iPhone-11
  1: iPhone-12
  2: iPhone-13
  3: iPhone-14
  4: iPhone-15
"""
import os
import shutil
from pathlib import Path

# ===== CẤU HÌNH =====
SOURCE_DIR = r"C:\Users\ACER\Downloads\iPhones.v1i.yolov8 (1)"
OUTPUT_DIR = r"C:\Users\ACER\.gemini\antigravity\scratch\quan_ly_kho\ai_model\dataset"

# Các class muốn giữ (index trong file gốc)
# ['iPhone 15 Pro'=0, 'iPhone-11'=1, 'iPhone-11-Pro'=2, 'iPhone-12'=3,
#  'iPhone-12-Pro'=4, 'iPhone-13'=5, 'iPhone-13-Pro'=6, 'iPhone-14'=7,
#  'iPhone-14-Pro'=8, 'iPhone-15'=9, ...]
SELECTED_CLASSES = {
    1: 0,   # iPhone-11  → class 0
    3: 1,   # iPhone-12  → class 1
    5: 2,   # iPhone-13  → class 2
    7: 3,   # iPhone-14  → class 3
    9: 4,   # iPhone-15  → class 4
}

CLASS_NAMES = ['iPhone-11', 'iPhone-12', 'iPhone-13', 'iPhone-14', 'iPhone-15']

def filter_label_file(src_label, dst_label):
    """Lọc file label, chỉ giữ các class được chọn và remap ID."""
    filtered_lines = []
    try:
        with open(src_label, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                class_id = int(parts[0])
                if class_id in SELECTED_CLASSES:
                    new_id = SELECTED_CLASSES[class_id]
                    filtered_lines.append(f"{new_id} {' '.join(parts[1:])}")
    except Exception as e:
        print(f"Lỗi đọc label {src_label}: {e}")
    
    if filtered_lines:
        os.makedirs(os.path.dirname(dst_label), exist_ok=True)
        with open(dst_label, 'w') as f:
            f.write('\n'.join(filtered_lines) + '\n')
        return True
    return False

def process_split(split_name):
    src_img_dir = Path(SOURCE_DIR) / split_name / "images"
    src_lbl_dir = Path(SOURCE_DIR) / split_name / "labels"
    dst_img_dir = Path(OUTPUT_DIR) / split_name / "images"
    dst_lbl_dir = Path(OUTPUT_DIR) / split_name / "labels"

    dst_img_dir.mkdir(parents=True, exist_ok=True)
    dst_lbl_dir.mkdir(parents=True, exist_ok=True)

    if not src_img_dir.exists():
        print(f"  Không tìm thấy: {src_img_dir}")
        return 0

    images = list(src_img_dir.glob("*.jpg")) + list(src_img_dir.glob("*.png"))
    kept = 0
    skipped = 0

    for img_path in images:
        label_path = src_lbl_dir / (img_path.stem + ".txt")
        dst_label  = dst_lbl_dir / (img_path.stem + ".txt")
        dst_image  = dst_img_dir / img_path.name

        if label_path.exists():
            if filter_label_file(str(label_path), str(dst_label)):
                shutil.copy2(str(img_path), str(dst_image))
                kept += 1
            else:
                skipped += 1
        else:
            skipped += 1

    print(f"  [{split_name}] Giữ lại: {kept} ảnh | Bỏ qua: {skipped} ảnh")
    return kept

def create_data_yaml():
    yaml_content = f"""train: {OUTPUT_DIR}/train/images
val: {OUTPUT_DIR}/test/images
test: {OUTPUT_DIR}/test/images

nc: {len(CLASS_NAMES)}
names: {CLASS_NAMES}
"""
    yaml_path = Path(OUTPUT_DIR) / "data.yaml"
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    print(f"\n[OK] Da tao: {yaml_path}")
    return str(yaml_path)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 50)
    print("[*] LOC DATASET - 5 IPHONE CLASSES")
    print("=" * 50)
    print(f"Classes: {CLASS_NAMES}\n")

    total = 0
    for split in ["train", "test"]:
        total += process_split(split)

    yaml_path = create_data_yaml()
    print(f"\n[OK] Hoan tat! Tong: {total} anh da loc")
    print(f"[>] Dataset tai: {OUTPUT_DIR}")
