import os
import json
import time
import urllib.request
import cv2
import numpy as np
import mediapipe as mp
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
from core.detectors import PostureDetector, FatigueDetector
from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions  # <-- Corrected modern import layout

MODELS_DIR = "models"
CONFIG_FILE = "config.json"
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
    Background worker thread running at 15 FPS.
    Implements a state machine for alerting, OpenCV skeleton drawing,
    and QImage emission for a live preview window.
    """
    alert_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(dict)
    calibration_signal = pyqtSignal(str)
    
    # UI Notification Signals
    frame_signal = pyqtSignal(QImage)
    hide_alert_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True
        
        # Feature toggles
        self.posture_enabled = True
        self.fatigue_enabled = True
        
        # Detectors
        self.posture_detector = PostureDetector()
        self.fatigue_detector = FatigueDetector()
        
        # State Machine Flags
        self.is_alert_state = False
        
        # State
        self.needs_calibration = True
        self.calibration_frames_collected = 0
        self.CALIBRATION_TARGET_FRAMES = 45  # 3 seconds at 15 FPS
        
        # Alert tracking
        self.consecutive_bad = 0
        self.consecutive_good = 0
        self.ALERT_THRESHOLD = 10  # ~0.6 seconds at 15 FPS
        self.GOOD_THRESHOLD = 5    # ~0.3 seconds at 15 FPS
        
        # Load config if exists
        self._load_config()

    def _load_config(self):
        """Load calibration baselines from config.json."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.posture_detector.from_dict(data.get('posture', {}))
                    self.fatigue_detector.from_dict(data.get('fatigue', {}))
                    
                    if self.posture_detector.is_calibrated or self.fatigue_detector.is_calibrated:
                        self.needs_calibration = False
                        print("Loaded baselines from config.json")
            except Exception as e:
                print(f"Failed to load config: {e}")

    def _save_config(self):
        """Save calibration baselines to config.json."""
        data = {
            'posture': self.posture_detector.to_dict(),
            'fatigue': self.fatigue_detector.to_dict()
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def force_recalibrate(self):
        """Manually trigger a 3-second calibration phase."""
        self.needs_calibration = True
        self.calibration_frames_collected = 0
        self.posture_detector.is_calibrated = False
        self.fatigue_detector.is_calibrated = False

    def set_posture_enabled(self, enabled):
        self.posture_enabled = enabled

    def set_fatigue_enabled(self, enabled):
        self.fatigue_enabled = enabled

    def stop(self):
        self._is_running = False

    def _draw_skeleton(self, rgb_frame, landmarks, is_bad, is_pose=True):
        """
        Draw anti-aliased skeletal lines and indicators on the RGB frame array.
        Uses clean proportional rendering rules and visual feedback overlays.
        """
        h, w, _ = rgb_frame.shape
        
        # High-visibility primary configurations (RGB Format since drawn directly onto rgb_frame)
        color = (255, 0, 0) if is_bad else (0, 255, 0) # Vibrant Red vs Electric Green
        text_msg = "CORRECT YOUR POSTURE" if is_bad else "POSTURE OK"
        
        # Helper lambda to map raw floating points safely into pixel coordinates
        def to_pixel(lm):
            return (int(lm.x * w), int(lm.y * h))
            
        # Draw tech-forward anti-aliased vectors
        if is_pose and len(landmarks) >= 13:
            nose = to_pixel(landmarks[0])
            l_eye = to_pixel(landmarks[2])
            r_eye = to_pixel(landmarks[5])
            l_shoulder = to_pixel(landmarks[11])
            r_shoulder = to_pixel(landmarks[12])
            
            # Key joints
            for pt in [nose, l_eye, r_eye, l_shoulder, r_shoulder]:
                cv2.circle(rgb_frame, pt, 3, color, -1, lineType=cv2.LINE_AA)
                
            # Inter-skeletal structural links
            cv2.line(rgb_frame, l_shoulder, r_shoulder, color, 2, lineType=cv2.LINE_AA)
            mid_shoulder = ((l_shoulder[0] + r_shoulder[0]) // 2, (l_shoulder[1] + r_shoulder[1]) // 2)
            cv2.line(rgb_frame, mid_shoulder, nose, color, 2, lineType=cv2.LINE_AA)
            cv2.line(rgb_frame, l_eye, r_eye, color, 2, lineType=cv2.LINE_AA)
            
        elif not is_pose and len(landmarks) >= 468:
            pts = [10, 152, 234, 454, 13, 14, 78, 308]
            for idx in pts:
                pt = to_pixel(landmarks[idx])
                cv2.circle(rgb_frame, pt, 3, color, -1, lineType=cv2.LINE_AA)
                
            # Bounds lines 
            cv2.line(rgb_frame, to_pixel(landmarks[10]), to_pixel(landmarks[152]), color, 1, lineType=cv2.LINE_AA)
            cv2.line(rgb_frame, to_pixel(landmarks[234]), to_pixel(landmarks[454]), color, 1, lineType=cv2.LINE_AA)
            cv2.line(rgb_frame, to_pixel(landmarks[13]), to_pixel(landmarks[14]), color, 2, lineType=cv2.LINE_AA)

        # Render subtle, polished semi-transparent status HUD text
        cv2.putText(rgb_frame, text_msg, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, color, 2, lineType=cv2.LINE_AA)

    def _emit_frame(self, rgb_frame):
        """Convert numpy array to QImage and emit it to the UI window thread securely."""
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.frame_signal.emit(q_img.copy())

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
        app_start_time = time.time()

        while self._is_running:
            loop_start_time = time.time()

            # Camera resource manager
            if not self.posture_enabled and not self.fatigue_enabled:
                if cap is not None and cap.isOpened():
                    cap.release()
                    cap = None
                time.sleep(0.1)
                continue
            
            if cap is None or not cap.isOpened():
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    time.sleep(1)
                    continue

            ret, frame = cap.read()
            if not ret:
                time.sleep(0.066)
                continue

            # In-memory stack RGB frame array mapping
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
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
                    self._save_config()
                    self.calibration_signal.emit("done")
                
            # --- Analysis Phase ---
            else:
                is_currently_bad = False
                bad_type = None
                draw_landmarks = None
                is_pose_landmark = True
                
                # Analyze Posture
                if self.posture_enabled and pose_results and pose_results.pose_landmarks:
                    p_res = self.posture_detector.analyze(pose_results.pose_landmarks[0])
                    if p_res.get('is_slouching') or p_res.get('is_too_close'):
                        is_currently_bad = True
                        bad_type = "Posture Alert"
                        draw_landmarks = p_res.get('landmarks')
                
                # Analyze Fatigue
                if self.fatigue_enabled and face_results and face_results.face_landmarks:
                    f_res = self.fatigue_detector.analyze(face_results.face_landmarks[0])
                    if f_res.get('is_yawning'):
                        is_currently_bad = True
                        bad_type = "Fatigue Alert"
                        draw_landmarks = f_res.get('landmarks')
                        is_pose_landmark = False

                # State Machine Tracking Thresholds
                if is_currently_bad:
                    self.consecutive_bad += 1
                    self.consecutive_good = 0
                else:
                    self.consecutive_bad = 0
                    self.consecutive_good += 1

                # Handle Alerts Entry Transitions
                if not self.is_alert_state and self.consecutive_bad >= self.ALERT_THRESHOLD:
                    self.is_alert_state = True
                    msg = "Sit up straight!" if bad_type == "Posture Alert" else "Yawning detected."
                    self.alert_signal.emit(bad_type, msg)

                # Process Frame Streaming pipelines while Alert is Active
                if self.is_alert_state:
                    if draw_landmarks:
                        self._draw_skeleton(rgb_frame, draw_landmarks, is_currently_bad, is_pose_landmark)
                    
                    self._emit_frame(rgb_frame)
                    
                    # Dismiss Window automatically when Posture is corrected 
                    if self.consecutive_good >= self.GOOD_THRESHOLD:
                        self.is_alert_state = False
                        self.hide_alert_signal.emit()

            # Maintain exactly 15 FPS (~66.6ms frame intervals)
            elapsed = time.time() - loop_start_time
            sleep_time = max(0.001, (1.0 / 15.0) - elapsed)
            time.sleep(sleep_time)

        # Resource Cleanup
        if cap is not None and cap.isOpened():
            cap.release()
        pose_landmarker.close()
        face_landmarker.close()