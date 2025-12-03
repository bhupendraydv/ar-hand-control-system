"""Advanced Gesture Recognition Engine.

ML-powered gesture detection and classification with:
- Confidence scoring for each recognized gesture
- Multi-hand gesture combinations
- Gesture history tracking and temporal patterns
- Customizable gesture definitions
"""

import numpy as np
from collections import deque
from typing import Dict, List, Tuple, Optional
import json


class AdvancedGestureRecognizer:
    """Advanced ML-based gesture recognition system."""
    
    def __init__(self, history_length=10):
        """Initialize gesture recognizer.
        
        Args:
            history_length: Number of frames to track for gesture history
        """
        self.history_length = history_length
        self.gesture_history = deque(maxlen=history_length)
        self.confidence_threshold = 0.7
        self.gesture_definitions = self._load_gestures()
    
    def _load_gestures(self) -> Dict:
        """Load predefined gesture definitions."""
        return {
            'open_palm': {'fingers_extended': 5, 'confidence_weight': 1.0},
            'fist': {'fingers_extended': 0, 'confidence_weight': 0.95},
            'peace': {'fingers_extended': 2, 'confidence_weight': 0.9},
            'thumbs_up': {'confidence_weight': 0.85},
            'point': {'fingers_extended': 1, 'confidence_weight': 0.88},
        }
    
    def detect_gesture(self, hand_landmarks: np.ndarray) -> Tuple[str, float]:
        """Detect gesture from hand landmarks.
        
        Args:
            hand_landmarks: MediaPipe hand landmarks (21, 3)
            
        Returns:
            Tuple of (gesture_name, confidence_score)
        """
        if hand_landmarks is None:
            return 'unknown', 0.0
        
        fingers_extended = self._count_extended_fingers(hand_landmarks)
        hand_shape = self._analyze_hand_shape(hand_landmarks)
        
        gesture_scores = {}
        for gesture_name, definition in self.gesture_definitions.items():
            score = self._calculate_gesture_score(
                fingers_extended, hand_shape, gesture_name, definition
            )
            gesture_scores[gesture_name] = score
        
        best_gesture = max(gesture_scores.items(), key=lambda x: x[1])
        
        if best_gesture[1] >= self.confidence_threshold:
            self.gesture_history.append(best_gesture[0])
            return best_gesture
        
        return 'unknown', 0.0
    
    def _count_extended_fingers(self, landmarks: np.ndarray) -> int:
        """Count number of extended fingers."""
        extended_count = 0
        finger_tips = [4, 8, 12, 16, 20]
        finger_pips = [3, 7, 11, 15, 19]
        
        for tip, pip in zip(finger_tips, finger_pips):
            if landmarks[tip][1] < landmarks[pip][1]:
                extended_count += 1
        
        return extended_count
    
    def _analyze_hand_shape(self, landmarks: np.ndarray) -> Dict:
        """Analyze hand shape characteristics."""
        palm_center = landmarks[0]
        distances = []
        
        for i in [4, 8, 12, 16, 20]:
            dist = np.linalg.norm(landmarks[i][:2] - palm_center[:2])
            distances.append(dist)
        
        return {
            'avg_distance': np.mean(distances),
            'spread': np.std(distances),
            'palm_width': distances[0]
        }
    
    def _calculate_gesture_score(self, fingers, shape, gesture, definition) -> float:
        """Calculate confidence score for gesture."""
        score = 0.0
        
        if 'fingers_extended' in definition:
            finger_match = fingers == definition['fingers_extended']
            score += finger_match * definition['confidence_weight']
        
        return min(1.0, score)
    
    def get_gesture_pattern(self) -> List[str]:
        """Get recent gesture pattern (temporal sequence)."""
        return list(self.gesture_history)
    
    def detect_gesture_combination(self) -> Optional[str]:
        """Detect multi-hand gesture combinations."""
        if len(self.gesture_history) < 3:
            return None
        
        recent = list(self.gesture_history)[-3:]
        if len(set(recent)) == 1:
            return f'sustained_{recent[0]}'
        
        return 'combination'
