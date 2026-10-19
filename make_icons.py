"""images/logo.png(투명 배경 로고)로 PWA 아이콘 3종을 만듭니다.
실행:  python make_icons.py        (Pillow 필요: pip install pillow)
결과:  icons/icon-192.png, icon-512.png, icon-maskable-512.png, apple-touch-icon.png
"""
import os
from PIL import Image

SRC = os.path.join("images", "logo.png")
OUT = "icons"
BG = (255, 255, 255, 255)  # 배경색: manifest의 background_color와 맞출 것

os.makedirs(OUT, exist_ok=True)
logo = Image.open(SRC).convert("RGBA")


def make(size, ratio, name):
    """ratio = 로고가 차지하는 비율. maskable은 가장자리가 잘리므로 작게(0.62)."""
    canvas = Image.new("RGBA", (size, size), BG)
    box = int(size * ratio)
    w, h = logo.size
    scale = box / max(w, h)
    lg = logo.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    canvas.paste(lg, ((size - lg.width) // 2, (size - lg.height) // 2), lg)
    canvas.convert("RGB").save(os.path.join(OUT, name), optimize=True)
    print("만듦:", os.path.join(OUT, name))


make(192, 0.80, "icon-192.png")
make(512, 0.80, "icon-512.png")
make(512, 0.62, "icon-maskable-512.png")  # 안드로이드 원형/둥근 마스크 안전영역
make(180, 0.80, "apple-touch-icon.png")   # 아이폰 홈 화면용
