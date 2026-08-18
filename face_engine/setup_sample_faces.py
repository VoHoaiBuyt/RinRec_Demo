"""
Utility script to create sample customer face portraits for local testing.
Generates realistic face portrait files in face_engine/customer_faces/
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2

def create_synthetic_portrait(cif: str, name: str, segment: str, bg_color: tuple, skin_tone: tuple, hair_color: tuple, gender: str = "M") -> np.ndarray:
    """Tạo ảnh chân dung sinh trắc học chuẩn cho demo"""
    w, h = 400, 480
    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Gradient Background
    for y in range(h):
        r = int(bg_color[0] * (1 - y / (h * 1.5)))
        g = int(bg_color[1] * (1 - y / (h * 1.5)))
        b = int(bg_color[2] * (1 - y / (h * 1.5)))
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # 2. Body / Shoulders
    suit_color = (25, 35, 55) if segment == "DIAMOND" else ((35, 60, 45) if segment == "PRIME" else (40, 50, 70))
    draw.ellipse([-50, 360, 450, 650], fill=suit_color)
    # Shirt collar
    draw.polygon([(160, 370), (200, 420), (240, 370), (220, 360), (180, 360)], fill=(240, 245, 250))
    if segment in ("DIAMOND", "PRIME"):
        # Tie
        tie_color = (0, 177, 79) if segment == "PRIME" else (212, 175, 55)
        draw.polygon([(192, 385), (208, 385), (215, 480), (200, 490), (185, 480)], fill=tie_color)

    # 3. Neck
    neck_color = (skin_tone[0] - 15, skin_tone[1] - 15, skin_tone[2] - 15)
    draw.rectangle([165, 300, 235, 380], fill=neck_color)

    # 4. Face Oval
    face_box = [110, 120, 290, 330]
    draw.ellipse(face_box, fill=skin_tone, outline=(skin_tone[0] - 25, skin_tone[1] - 25, skin_tone[2] - 25), width=2)

    # 5. Ears
    draw.ellipse([95, 195, 118, 255], fill=skin_tone)
    draw.ellipse([282, 195, 305, 255], fill=skin_tone)

    # 6. Hair
    if gender == "F":
        # Long hair
        draw.ellipse([90, 80, 310, 280], fill=hair_color)
        draw.ellipse([70, 140, 120, 380], fill=hair_color)
        draw.ellipse([280, 140, 330, 380], fill=hair_color)
        draw.ellipse(face_box, fill=skin_tone) # redraw face
    else:
        # Short hair
        draw.ellipse([100, 75, 300, 190], fill=hair_color)
        draw.polygon([(100, 130), (105, 200), (120, 140)], fill=hair_color)
        draw.polygon([(300, 130), (295, 200), (280, 140)], fill=hair_color)

    # 7. Eyebrows & Eyes
    # Eyebrows
    draw.arc([130, 170, 175, 185], start=180, end=360, fill=hair_color, width=4)
    draw.arc([225, 170, 270, 185], start=180, end=360, fill=hair_color, width=4)
    
    # Eye whites
    draw.ellipse([135, 190, 175, 212], fill=(255, 255, 255), outline=(100, 100, 100))
    draw.ellipse([225, 190, 265, 212], fill=(255, 255, 255), outline=(100, 100, 100))
    
    # Irises
    draw.ellipse([148, 192, 166, 210], fill=(45, 30, 20))
    draw.ellipse([238, 192, 256, 210], fill=(45, 30, 20))
    # Pupils
    draw.ellipse([153, 197, 161, 205], fill=(10, 10, 10))
    draw.ellipse([243, 197, 251, 205], fill=(10, 10, 10))

    # 8. Nose
    draw.line([(200, 195), (200, 245)], fill=(skin_tone[0] - 30, skin_tone[1] - 30, skin_tone[2] - 30), width=2)
    draw.arc([190, 235, 210, 250], start=0, end=180, fill=(skin_tone[0] - 40, skin_tone[1] - 40, skin_tone[2] - 40), width=2)

    # 9. Mouth / Smile
    lips_color = (205, 115, 110) if gender == "F" else (190, 120, 115)
    draw.arc([165, 265, 235, 295], start=0, end=180, fill=lips_color, width=4)
    draw.line([(170, 275), (230, 275)], fill=(180, 100, 95), width=2)

    # 10. Watermark Badge
    badge_bg = (10, 37, 64)
    draw.rectangle([10, 10, 160, 48], fill=badge_bg, outline=(0, 177, 79), width=1)
    draw.text((18, 14), f"VPBank eKYC", fill=(0, 220, 100))
    draw.text((18, 28), f"{cif} - {segment}", fill=(255, 255, 255))

    return np.array(img)

def setup_faces():
    faces_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "customer_faces")
    os.makedirs(faces_dir, exist_ok=True)
    
    customers = [
        {"cif": "CUST_0093", "name": "Vũ Quang Tuấn", "segment": "MASS", "bg": (220, 230, 242), "skin": (245, 208, 180), "hair": (40, 35, 30), "gender": "M"},
        {"cif": "CUST_0068", "name": "Đỗ Tuấn Long", "segment": "MASS", "bg": (235, 235, 245), "skin": (240, 200, 175), "hair": (30, 25, 20), "gender": "M"},
        {"cif": "CUST_0025", "name": "Huỳnh Thị Thảo", "segment": "PRIME", "bg": (240, 248, 240), "skin": (250, 218, 195), "hair": (55, 35, 25), "gender": "F"},
        {"cif": "CUST_0022", "name": "Võ Đức Dũng", "segment": "MASS", "bg": (230, 240, 250), "skin": (238, 198, 170), "hair": (35, 30, 25), "gender": "M"},
        {"cif": "CUST_0009", "name": "Nguyễn Văn An", "segment": "DIAMOND", "bg": (248, 244, 230), "skin": (242, 205, 178), "hair": (45, 40, 35), "gender": "M"},
        {"cif": "CUST_0015", "name": "Trần Thị Mai", "segment": "PRIME", "bg": (245, 240, 248), "skin": (252, 222, 200), "hair": (50, 30, 20), "gender": "F"},
    ]

    for cust in customers:
        img_rgb = create_synthetic_portrait(
            cif=cust["cif"],
            name=cust["name"],
            segment=cust["segment"],
            bg_color=cust["bg"],
            skin_tone=cust["skin"],
            hair_color=cust["hair"],
            gender=cust["gender"]
        )
        file_path = os.path.join(faces_dir, f"{cust['cif']}.jpg")
        cv2.imwrite(file_path, cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR))
        print(f"[OK] Created face portrait: {file_path}")

if __name__ == "__main__":
    setup_faces()
