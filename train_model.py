"""
Bước 2: Train YOLOv8n model nhận diện 5 loại iPhone
"""
from ultralytics import YOLO
import os
from pathlib import Path

DATASET_YAML = r"C:\Users\ACER\.gemini\antigravity\scratch\quan_ly_kho\ai_model\dataset\data.yaml"
MODEL_OUTPUT = r"C:\Users\ACER\.gemini\antigravity\scratch\quan_ly_kho\ai_model"

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 TRAIN YOLOv8n - iPhone Detector")
    print("=" * 50)

    # Load pretrained YOLOv8n (nano - nhanh nhất)
    model = YOLO('yolov8n.pt')

    # Train
    results = model.train(
        data=DATASET_YAML,
        epochs=20,           # 20 epochs - đủ để học tốt
        imgsz=416,           # Nhỏ hơn 640 để train nhanh hơn
        batch=16,
        name='iphone_detector',
        project=MODEL_OUTPUT,
        patience=5,          # Early stopping sau 5 epoch không cải thiện
        save=True,
        plots=True,
        verbose=True,
        device='cpu',        # Dùng CPU (đổi thành 0 nếu có GPU)
        workers=2,
        cache=False,
    )

    print("\n✅ Train xong!")
    
    # Lưu path model tốt nhất
    best_model = Path(MODEL_OUTPUT) / "iphone_detector" / "weights" / "best.pt"
    print(f"📁 Model tốt nhất: {best_model}")

    # Test nhanh
    print("\n🔍 Validate model...")
    metrics = model.val()
    print(f"mAP50: {metrics.box.map50:.3f}")
    print(f"mAP50-95: {metrics.box.map:.3f}")
