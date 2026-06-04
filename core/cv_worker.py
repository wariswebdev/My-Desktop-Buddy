import os
import time
import urllib.request
import cv2
import mediapipe as mp
from PyQt6.QtCore import QThread, pyqtSignal
from core.detectors import PostureDetector, FatigueDetector
from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions  # <-- Corrected modern import location

MODELS_DIR = "models"
POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"
FACE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
POSE_MODEL_PATH = os.path.join(MODELS_DIR, "pose_landmarker_full.task")
FACE_MODEL_PATH = os.path.join(MODELS_DIR, "face_landmarker.task")

def download_models():
    """Download MediaPipe models automatically if they are missing."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    if not os.path.exists(POSE_MODEL_PATH):
        print("Downloading Pose Landmarker model...")
        urllib.request.urlretrieve(POSE_MODEL_URL, POSE_MODEL_PATH)
    if not os.path.exists(FACE_MODEL_PATH):
        print("Downloading Face Landmarker model...")
        urllib.request.urlretrieve(FACE_MODEL_URL, FACE_MODEL_PATH)

class CVWorker(QThread):
    """
    Background worker thread for webcam analysis.
    Runs at 5 FPS and emits signals without blocking the GUI.
    Uses the modern MediaPipe Tasks API.
    """
    alert_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(dict)
    calibration_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True
        
        # Feature toggles
        self.posture_enabled = True
        self.fatigue_enabled = True
        
        # Detectors
        self.posture_detector = PostureDetector()
        self.fatigue_detector = FatigueDetector()
        
        # State
        self.needs_calibration = True
        self.calibration_frames_collected = 0
        self.CALIBRATION_TARGET_FRAMES = 15  # 3 seconds at 5 FPS
        
        # Alert tracking
        self.consecutive_slouch = 0
        self.consecutive_close = 0
        self.consecutive_yawn = 0
        self.ALERT_THRESHOLD = 25  # 5 seconds at 5 FPS
        
        # Cooldowns (timestamps)
        self.cooldowns = {
            'slouching': 0,
            'too_close': 0,
            'yawning': 0
        }
        self.COOLDOWN_SECONDS = 120

    def set_posture_enabled(self, enabled):
        self.posture_enabled = enabled
        self._check_recalibration()

    def set_fatigue_enabled(self, enabled):
        self.fatigue_enabled = enabled
        self._check_recalibration()

    def _check_recalibration(self):
        """If a feature is turned back on, we should recalibrate."""
        if self.posture_enabled or self.fatigue_enabled:
            self.needs_calibration = True
            self.calibration_frames_collected = 0

    def stop(self):
        self._is_running = False

    def run(self):
        download_models()

        # Initialize MediaPipe Landmarkers using the corrected BaseOptions layout
        pose_base_options = BaseOptions(model_asset_path=POSE_MODEL_PATH)
        pose_options = vision.PoseLandmarkerOptions(
            base_options=pose_base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1
        )
        pose_landmarker = vision.PoseLandmarker.create_from_options(pose_options)

        face_base_options = BaseOptions(model_asset_path=FACE_MODEL_PATH)
        face_options = vision.FaceLandmarkerOptions(
            base_options=face_base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1
        )
        face_landmarker = vision.FaceLandmarker.create_from_options(face_options)

        cap = None
        # Keep track of start time for timestamps required by VIDEO mode
        app_start_time = time.time()

        while self._is_running:
            loop_start_time = time.time()

            # If both features are off, release camera and sleep
            if not self.posture_enabled and not self.fatigue_enabled:
                if cap is not None and cap.isOpened():
                    cap.release()
                    cap = None
                time.sleep(0.5)
                continue
            
            # Ensure camera is open
            if cap is None or not cap.isOpened():
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    time.sleep(1)
                    continue

            ret, frame = cap.read()
            if not ret:
                time.sleep(0.2)
                continue

            # Convert frame to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Timestamp required for VIDEO mode
            timestamp_ms = int((time.time() - app_start_time) * 1000)

            pose_results = None
            face_results = None

            if self.posture_enabled:
                pose_results = pose_landmarker.detect_for_video(mp_image, timestamp_ms)
            if self.fatigue_enabled:
                face_results = face_landmarker.detect_for_video(mp_image, timestamp_ms)

            # --- Calibration Phase ---
            if self.needs_calibration:
                if self.calibration_frames_collected == 0:
                    self.calibration_signal.emit("started")
                
                if self.posture_enabled and pose_results and pose_results.pose_landmarks:
                    self.posture_detector.calibrate(pose_results.pose_landmarks[0])
                
                if self.fatigue_enabled and face_results and face_results.face_landmarks:
                    self.fatigue_detector.calibrate(face_results.face_landmarks[0])

                self.calibration_frames_collected += 1
                
                if self.calibration_frames_collected >= self.CALIBRATION_TARGET_FRAMES:
                    if self.posture_enabled:
                        self.posture_detector.finalize_calibration()
                    if self.fatigue_enabled:
                        self.fatigue_detector.finalize_calibration()
                    
                    self.needs_calibration = False
                    self.calibration_signal.emit("done")
                
            # --- Analysis Phase ---
            else:
                current_time = time.time()
                
                # Posture Analysis
                if self.posture_enabled and pose_results and pose_results.pose_landmarks:
                    p_res = self.posture_detector.analyze(pose_results.pose_landmarks[0])
                    
                    # Slouching
                    if p_res.get('is_slouching'):
                        self.consecutive_slouch += 1
                    else:
                        self.consecutive_slouch = max(0, self.consecutive_slouch - 1)
                        
                    # Too Close
                    if p_res.get('is_too_close'):
                        self.consecutive_close += 1
                    else:
                        self.consecutive_close = max(0, self.consecutive_close - 1)

                    # Trigger Alerts
                    if self.consecutive_slouch >= self.ALERT_THRESHOLD:
                        if current_time - self.cooldowns['slouching'] > self.COOLDOWN_SECONDS:
                            self.alert_signal.emit("Posture Alert", "You're slouching! Sit up straight.")
                            self.cooldowns['slouching'] = current_time
                        self.consecutive_slouch = 0
                        
                    if self.consecutive_close >= self.ALERT_THRESHOLD:
                        if current_time - self.cooldowns['too_close'] > self.COOLDOWN_SECONDS:
                            self.alert_signal.emit("Posture Alert", "You're too close to the screen.")
                            self.cooldowns['too_close'] = current_time
                        self.consecutive_close = 0

                # Fatigue Analysis
                if self.fatigue_enabled and face_results and face_results.face_landmarks:
                    f_res = self.fatigue_detector.analyze(face_results.face_landmarks[0])
                    
                    if f_res.get('is_yawning'):
                        self.consecutive_yawn += 1
                    else:
                        self.consecutive_yawn = max(0, self.consecutive_yawn - 1)
                        
                    if self.consecutive_yawn >= self.ALERT_THRESHOLD:
                        if current_time - self.cooldowns['yawning'] > self.COOLDOWN_SECONDS:
                            self.alert_signal.emit("Fatigue Alert", "Yawning detected. Consider taking a break.")
                            self.cooldowns['yawning'] = current_time
                        self.consecutive_yawn = 0

            # Maintain 5 FPS (200ms per frame)
            elapsed = time.time() - loop_start_time
            sleep_time = max(0.01, 0.2 - elapsed)
            time.sleep(sleep_time)

        # Cleanup on exit
        if cap is not None and cap.isOpened():
            cap.release()
        pose_landmarker.close()
        face_landmarker.close()