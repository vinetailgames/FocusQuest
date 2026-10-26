# constants.py
import os

# Window
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Focus Quest"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BACKGROUND_PATH = os.path.join(ASSETS_DIR, "backgrounds", "desk.jpg")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
DATA_FILE = os.path.join(BASE_DIR, "data", "save.json")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (200, 200, 200)
GOLD = (255, 215, 0)
RED = (220, 50, 50)
GREEN = (50, 200, 50)

# UI
BUTTON_HEIGHT = 40
PADDING = 10