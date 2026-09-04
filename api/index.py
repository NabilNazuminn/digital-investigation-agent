import sys
import os

# Biar bisa import "app.main" (folder app/ ada di root project, bukan di
# dalam folder api/), python perlu tau root project ada di parent folder ini.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Vercel otomatis detect variable "app" di file ini sebagai ASGI app yang
# harus dijalanin -- jangan bikin FastAPI() baru di sini, dan jangan
# daftarin ulang route yang udah ada di app.main (misal /health), karena
# bakal duplikat sama yang di app/main.py.
from app.main import app  # noqa: E402,F401