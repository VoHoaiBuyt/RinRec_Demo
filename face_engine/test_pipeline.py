"""
Unit Test Pipeline for FaceRecognizerEngine & CrossDeviceSessionManager.
"""

import os
import sys
import time
import base64
from PIL import Image
import cv2

# Thêm root vào sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from face_engine import get_face_engine, get_session_manager

def test_engine():
    print("=== 1. KIEM TRA FACE RECOGNIZER ENGINE ===")
    engine = get_face_engine()
    enrolled = engine.list_enrolled_customers()
    print(f"[OK] So luong khach hang da enroll: {len(enrolled)}")
    for cust in enrolled:
        print(f"  - {cust['cif_number']}: {cust['segment']}")

    # Test recognize on an existing face
    sample_path = engine.get_customer_face_path("CUST_0093")
    assert sample_path is not None, "Khong tim thay anh CUST_0093"
    
    result = engine.recognize_face(sample_path)
    print(f"\n[OK] Ket qua nhan dien anh mau CUST_0093:")
    print(f"  - Is Identified: {result['is_identified']}")
    print(f"  - CIF: {result['cif_number']}")
    print(f"  - Do khop: {result['confidence']}%")
    print(f"  - Engine: {result['engine']}")
    print(f"  - Thoi gian: {result['process_time_ms']} ms")
    assert result["is_identified"] == True
    assert result["cif_number"] == "CUST_0093"

    print("\n=== 2. KIEM TRA CROSS-DEVICE SESSION MANAGER ===")
    mgr = get_session_manager()
    session = mgr.create_session()
    sid = session["session_id"]
    print(f"[OK] Da tao session: {sid}")
    print(f"  - Mobile URL: {session['mobile_url']}")
    print(f"  - QR Base64 length: {len(session['qr_base64'])} chars")

    # Simulate mobile submit with base64 image
    with open(sample_path, "rb") as f:
        img_b64 = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")

    submit_res = mgr.submit_face(sid, img_b64)
    print(f"\n[OK] Ket qua Mobile Submit:")
    print(f"  - Success: {submit_res.get('success')}")
    print(f"  - Status: {submit_res.get('status')}")
    print(f"  - CIF: {submit_res.get('cif_number')}")

    # Check session status on desktop
    updated_session = mgr.get_session(sid)
    print(f"\n[OK] Trang thai session sau khi Mobile submit: {updated_session['status']}")
    assert updated_session["status"] == "VERIFIED"
    assert updated_session["result"]["cif_number"] == "CUST_0093"

    print("\n[SUCCESS] Tat ca cac test case deu PASSED 100%!")

if __name__ == "__main__":
    test_engine()
