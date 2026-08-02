import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ============================
# DATABASE
# ============================

DATABASE_FOLDER = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_FOLDER, "phones.db")

DATABASE_URI = f"sqlite:///{DATABASE_PATH}"

# ============================
# UPLOAD
# ============================

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# ============================
# DATASET
# ============================

DATASET_FOLDER = os.path.join(BASE_DIR, "dataset")

IMAGES_FOLDER = os.path.join(DATASET_FOLDER, "images")

LABELS_FOLDER = os.path.join(DATASET_FOLDER, "labels")

# ============================
# MODEL
# ============================

WEIGHTS_FOLDER = os.path.join(BASE_DIR, "weights")

MODEL_PATH = os.path.join(WEIGHTS_FOLDER, "best.pt")

# ============================
# CAMERA
# ============================

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

CONFIDENCE = 0.5
