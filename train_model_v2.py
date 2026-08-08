"""
Train lại với YOLOv8s (chính xác hơn nano) + augmentation mạnh hơn + 40 epochs
"""
from ultralytics import YOLO
import os
from pathlib import Path

DATASET_YAML = r"C:\Users\ACER\.gemini\antigravity\scratch\quan_ly_kho\ai_model\dataset\data.yaml"
MODEL_OUTPUT = r"C:\Users\ACER\.gemini\antigravity\scratch\quan_ly_kho\ai_model"

if __name__ == "__main__":
    print("=" * 55)
    print("[*] TRAIN YOLOv8s - iPhone Detector v2 (Better Accuracy)")
    print("=" * 55)

    # YOLOv8s = small model, chinh xac hon nano ~15%
    model = YOLO('yolov8s.pt')

    results = model.train(
        data=DATASET_YAML,
        epochs=40,
        imgsz=640,          # Tang len 640 de nhan dien ro hon
        batch=8,
        name='iphone_v2',
        project=MODEL_OUTPUT,
        patience=10,
        save=True,
        plots=True,
        verbose=True,
        device='cpu',
        workers=2,
        cache=False,
        # Augmentation manh hon de model khong bias
        flipud=0.1,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        degrees=15.0,
        translate=0.1,
        scale=0.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        # Class weights - giam bias ve class nhieu anh
        label_smoothing=0.1,
    )

    print("\n[OK] Train xong!")
    best = Path(MODEL_OUTPUT) / "iphone_v2" / "weights" / "best.pt"
    print(f"[>] Model: {best}")

    # Copy de thay the model cu
    import shutil
    old = Path(MODEL_OUTPUT) / "iphone_detector" / "weights" / "best.pt"
    old.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(best), str(old))
    print("[OK] Da cap nhat model chinh (iphone_detector/weights/best.pt)")

    print("\n[*] Validate...")
    metrics = model.val()
    print(f"mAP50:    {metrics.box.map50:.3f}")
    print(f"mAP50-95: {metrics.box.map:.3f}")
    for i, name in enumerate(['iPhone-11','iPhone-12','iPhone-13','iPhone-14','iPhone-15']):
        if i < len(metrics.box.ap_class_index):
            print(f"  {name}: mAP50={metrics.box.ap50[i]:.3f}")
