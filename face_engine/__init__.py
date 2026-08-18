"""
Package Face Recognition & Cross-Device eKYC Engine for RinRec / VPBank SmartAdvisor 360.
"""

from .face_recognizer import FaceRecognizerEngine, get_face_engine
from .session_manager import CrossDeviceSessionManager, get_session_manager

__all__ = [
    "FaceRecognizerEngine",
    "get_face_engine",
    "CrossDeviceSessionManager",
    "get_session_manager"
]
