import os

# -------------------------
# Base directory
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# -------------------------
# Folder paths
# -------------------------
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "static", "output")

# -------------------------
# Allowed file extensions
# -------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

# -------------------------
# Max upload size (5 MB)
# -------------------------
MAX_CONTENT_LENGTH = 5 * 1024 * 1024