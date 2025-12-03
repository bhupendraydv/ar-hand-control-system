"""Hand Tracking Optimization Engine.

Optimizes hand tracking performance with:
- Kalman filtering for smooth tracking
- Multi-frame motion prediction
- Occlusion handling
- Performance monitoring
"""

import numpy as np
from collections import deque
from typing import Tuple, Optional, List

class KalmanFilter:
    """Kalman filter for smooth hand tracking."""
    
    def __init__(self, dt=0.033):
        self.dt = dt
        self.q = 0.1  # process noise
        self.r = 0.1  # measurement noise
        self.x = None
        self.p = None
        self.initialized = False
    
    def predict(self) -> np.ndarray:
        if not self.initialized:
            return None
        self.p = self.p + self.q
        return self.x
    
    def update(self, z: np.ndarray) -> np.ndarray:
        if not self.initialized:
            self.x = z
            self.p = 1.0
            self.initialized = True
            return z
        
        k = self.p / (self.p + self.r)
        self.x = self.x + k * (z - self.x)
        self.p = (1 - k) * self.p
        return self.x

class HandTrackingOptimizer:
    """Optimize hand tracking with smoothing and prediction."""
    
    def __init__(self, buffer_size=5):
        self.buffer_size = buffer_size
        self.kalman_filters = [KalmanFilter() for _ in range(21)]
        self.position_buffer = deque(maxlen=buffer_size)
        self.velocity_history = deque(maxlen=buffer_size)
    
    def smooth_landmarks(self, landmarks: np.ndarray) -> np.ndarray:
        """Apply Kalman filtering to smooth landmarks."""
        if landmarks is None:
            return None
        
        smoothed = np.zeros_like(landmarks)
        for i, filter in enumerate(self.kalman_filters):
            filtered = filter.update(landmarks[i])
            smoothed[i] = filter.predict() if filtered is not None else filtered
        
        return smoothed
    
    def predict_next_position(self) -> Optional[np.ndarray]:
        """Predict next hand position based on velocity."""
        if len(self.position_buffer) < 2:
            return None
        
        recent_positions = list(self.position_buffer)[-2:]
        velocity = recent_positions[-1] - recent_positions[-2]
        return recent_positions[-1] + velocity
    
    def handle_occlusion(self, landmarks: np.ndarray, confidence: float) -> np.ndarray:
        """Handle occlusion by using prediction."""
        if confidence < 0.3 and len(self.position_buffer) > 0:
            return self.predict_next_position()
        return landmarks
    
    def get_tracking_quality(self) -> Dict:
        """Get tracking quality metrics."""
        return {
            'smoothness': len(self.position_buffer) / self.buffer_size,
            'stability': 1.0 if len(self.velocity_history) > 1 else 0.0
        }
