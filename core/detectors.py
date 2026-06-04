import math

def distance(p1, p2):
    """Calculate Euclidean distance between two landmark points."""
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

class PostureDetector:
    """
    Detects slouching and leaning close using MediaPipe Pose landmarks.
    """
    def __init__(self):
        self.calibration_samples = []
        self.baseline_nose_y = 0.0
        self.baseline_shoulder_nose_dist = 0.0
        self.baseline_eye_dist = 0.0
        self.is_calibrated = False

    def calibrate(self, landmarks):
        """Accumulate samples during the calibration phase."""
        if not landmarks or len(landmarks) < 13:
            return

        nose = landmarks[0]
        left_eye = landmarks[2]
        right_eye = landmarks[5]
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]

        # Calculate mid-shoulder point
        mid_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2.0
        
        # Distance from mid-shoulder to nose
        shoulder_nose_dist = abs(mid_shoulder_y - nose.y)
        
        # Inter-eye distance
        eye_dist = distance(left_eye, right_eye)

        self.calibration_samples.append({
            'nose_y': nose.y,
            'shoulder_nose_dist': shoulder_nose_dist,
            'eye_dist': eye_dist
        })

    def finalize_calibration(self):
        """Average the accumulated samples to lock the baseline."""
        if not self.calibration_samples:
            return False
            
        n = len(self.calibration_samples)
        self.baseline_nose_y = sum(s['nose_y'] for s in self.calibration_samples) / n
        self.baseline_shoulder_nose_dist = sum(s['shoulder_nose_dist'] for s in self.calibration_samples) / n
        self.baseline_eye_dist = sum(s['eye_dist'] for s in self.calibration_samples) / n
        
        self.is_calibrated = True
        self.calibration_samples.clear()
        return True

    def analyze(self, landmarks):
        """Analyze current landmarks against baseline."""
        results = {'is_slouching': False, 'is_too_close': False}
        if not self.is_calibrated or not landmarks or len(landmarks) < 13:
            return results

        nose = landmarks[0]
        left_eye = landmarks[2]
        right_eye = landmarks[5]

        # 1. Slouching check
        # If nose drops (y increases) by more than 15% of the baseline shoulder-to-nose distance
        drop_threshold = self.baseline_shoulder_nose_dist * 0.15
        if (nose.y - self.baseline_nose_y) > drop_threshold:
            results['is_slouching'] = True

        # 2. Leaning too close check
        # If inter-eye distance increases by more than 30% from baseline
        current_eye_dist = distance(left_eye, right_eye)
        if current_eye_dist > (self.baseline_eye_dist * 1.3):
            results['is_too_close'] = True

        return results


class FatigueDetector:
    """
    Detects yawning using MediaPipe Face Mesh landmarks.
    """
    def __init__(self):
        self.is_calibrated = False

    def calibrate(self, landmarks):
        """Fatigue uses absolute ratios, so no extensive calibration is needed, 
        but we maintain the interface."""
        pass

    def finalize_calibration(self):
        """Mark as calibrated."""
        self.is_calibrated = True
        return True

    def analyze(self, landmarks):
        """Analyze current face mesh landmarks to detect yawning."""
        results = {'is_yawning': False}
        if not self.is_calibrated or not landmarks or len(landmarks) < 468:
            return results
        
        # Indices based on standard MediaPipe Face Mesh
        # 13: Upper lip inner
        # 14: Lower lip inner
        # 78: Left mouth corner
        # 308: Right mouth corner
        
        upper_lip = landmarks[13]
        lower_lip = landmarks[14]
        left_corner = landmarks[78]
        right_corner = landmarks[308]

        # Vertical distance between inner lips
        lip_distance = distance(upper_lip, lower_lip)
        
        # Horizontal distance between mouth corners
        mouth_width = distance(left_corner, right_corner)

        # Lip Aperture Ratio
        if mouth_width > 0:
            lar = lip_distance / mouth_width
            if lar > 0.6:
                results['is_yawning'] = True

        return results
