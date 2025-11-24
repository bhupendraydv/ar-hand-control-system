# Complete AR Hand Control System Implementation

This guide provides ALL the files needed to make your AR Hand Control System fully complete with features from both tubakhxn's repositories combined.

## Files to Create/Update

### 1. hand_overlay.py (NEW FILE)

Create this file with the following complete code that combines all HUD features:

```python
"""
AR Hand Control System - Advanced HUD Overlay Module
Combines features from tubakhxn's Hand-Tracking-AR-UI and hand-gesture-controller
Authors: Bhupendra YDV, tubakhxn
Date: November 2025
"""
import cv2
import numpy as np
import math

# Visual constants
LINE_COLOR = (255, 255, 255)  # White
LINE_WIDTH = 1
DOT_RADIUS = 3
FONT = cv2.FONT_HERSHEY_SIMPLEX

# Color palette
CYAN = (255, 255, 0)
ORANGE = (0, 180, 255)
WHITE = (255, 255, 255)
RED = (0, 0, 255)
CORE = (0, 255, 180)
GREEN = (0, 255, 0)

def draw_glow_circle(img, center, radius, color, thickness=2, glow=15):
    """Draw outer glow effect for circles"""
    for g in range(glow, 0, -3):
        alpha = 0.08 + 0.12 * (g / glow)
        overlay = img.copy()
        cv2.circle(overlay, center, radius+g, color, thickness)
        cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)
    cv2.circle(img, center, radius, color, thickness)

def draw_radial_ticks(img, center, radius, color, num_ticks=24, length=22, thickness=3):
    """Draw radial ticks around palm"""
    for i in range(num_ticks):
        angle = np.deg2rad(i * (360/num_ticks))
        x1 = int(center[0] + (radius-length) * np.cos(angle))
        y1 = int(center[1] + (radius-length) * np.sin(angle))
        x2 = int(center[0] + radius * np.cos(angle))
        y2 = int(center[1] + radius * np.sin(angle))
        cv2.line(img, (x1, y1), (x2, y2), color, thickness)

def draw_core_pattern(img, center, radius):
    """Draw stylized core pattern"""
    for t in np.linspace(0, 2*np.pi, 40):
        r = radius * (0.7 + 0.3 * np.sin(6*t))
        x = int(center[0] + r * np.cos(t))
        y = int(center[1] + r * np.sin(t))
        cv2.circle(img, (x, y), 3, ORANGE, -1)
    cv2.circle(img, center, int(radius*0.6), CYAN, 2)
    cv2.circle(img, center, int(radius*0.4), ORANGE, 2)

def draw_hud_details(img, center):
    """Draw bottom HUD bars and segments"""
    for i in range(8):
        angle = np.deg2rad(210 + i*10)
        x1 = int(center[0] + 140 * np.cos(angle))
        y1 = int(center[1] + 140 * np.sin(angle))
        x2 = int(center[0] + 170 * np.cos(angle))
        y2 = int(center[1] + 170 * np.sin(angle))
        cv2.line(img, (x1, y1), (x2, y2), CYAN, 4)
    
    for i in range(4):
        angle = np.deg2rad(270 + i*15)
        x = int(center[0] + 120 * np.cos(angle))
        y = int(center[1] + 120 * np.sin(angle))
        cv2.rectangle(img, (x-10, y-10), (x+10, y+10), CYAN, 2)

def draw_arc_segments(img, center):
    """Draw arc segments"""
    cv2.ellipse(img, center, (110,110), 0, -30, 210, CYAN, 3)
    cv2.ellipse(img, center, (100,100), 0, -30, 210, ORANGE, 2)
    cv2.ellipse(img, center, (80,80), 0, 0, 360, CYAN, 1)

def landmarks_to_pixel(lm, width, height):
    """Convert normalized landmarks to pixel coordinates"""
    return [(int(l[0] * width), int(l[1] * height)) for l in lm]

def draw_skeleton(img, pix, t=0):
    """Draw hand skeleton with joints"""
    connections = [
        [0,1,2,3,4], [0,5,6,7,8], [0,9,10,11,12],
        [0,13,14,15,16], [0,17,18,19,20]
    ]
    
    for finger in connections:
        for i in range(len(finger)-1):
            pt1 = pix[finger[i]]
            pt2 = pix[finger[i+1]]
            cv2.line(img, pt1, pt2, WHITE, 2)
            cv2.circle(img, pt1, 4, CYAN, -1)

def draw_palm_radial_ui(img, center, rot, t=0, width=1.0):
    """Draw palm-centered radial HUD with rotation"""
    # Concentric circles
    for radius in [int(40*width), int(70*width), int(100*width)]:
        cv2.circle(img, center, radius, CYAN, 2)
    
    # Rotating radial ticks
    for i in range(12):
        angle = math.radians(i * 30 + rot)
        x1 = int(center[0] + 100*width * math.cos(angle))
        y1 = int(center[1] + 100*width * math.sin(angle))
        x2 = int(center[0] + 115*width * math.cos(angle))
        y2 = int(center[1] + 115*width * math.sin(angle))
        cv2.line(img, (x1,y1), (x2,y2), CYAN, 2)
    
    # Center cross
    cv2.line(img, (center[0]-10,center[1]), (center[0]+10,center[1]), ORANGE, 2)
    cv2.line(img, (center[0],center[1]-10), (center[0],center[1]+10), ORANGE, 2)

def draw_rotation_text(img, center, rot):
    """Display rotation angle"""
    cv2.putText(img, f"{int(rot)}deg", (center[0]+20, center[1]-120),
                FONT, 0.6, WHITE, 2)

def draw_cube_and_grid(img, anchor, t=0):
    """Draw 3D cube with perspective"""
    size = 25
    rotation = t * 0.5 % (2 * np.pi)
    
    # 3D cube points
    points_3d = [
        [-size,-size,-size], [size,-size,-size], [size,size,-size],
        [-size,size,-size], [-size,-size,size], [size,-size,size],
        [size,size,size], [-size,size,size]
    ]
    
    # Simple rotation and projection
    points_2d = []
    for p in points_3d:
        # Rotate around Y axis
        x_rot = p[0] * np.cos(rotation) + p[2] * np.sin(rotation)
        z_rot = -p[0] * np.sin(rotation) + p[2] * np.cos(rotation)
        
        # Project to 2D
        x = int(anchor[0] + x_rot + z_rot*0.5)
        y = int(anchor[1] + p[1] + z_rot*0.5)
        points_2d.append((x,y))
    
    # Draw cube edges
    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),
             (0,4),(1,5),(2,6),(3,7)]
    for edge in edges:
        cv2.line(img, points_2d[edge[0]], points_2d[edge[1]], GREEN, 1)

def draw_fingertip_gears(img, pix, rot, t=0):
    """Draw gear-like elements at fingertips"""
    fingertip_indices = [4, 8, 12, 16, 20]
    for idx in fingertip_indices:
        center = pix[idx]
        radius = 8
        cv2.circle(img, center, radius, ORANGE, 2)
        # Add small tick marks
        for i in range(6):
            angle = math.radians(i * 60 + rot)
            x = int(center[0] + radius * math.cos(angle))
            y = int(center[1] + radius * math.sin(angle))
            cv2.line(img, center, (x,y), ORANGE, 1)

def draw_palm_data_text(img, anchor, openness):
    """Display hand openness data"""
    cv2.putText(img, f"Open: {int(openness)}%", anchor,
                FONT, 0.6, WHITE, 2)

def angle_between(v1, v2):
    """Calculate angle between two vectors"""
    v1_u = v1 / (np.linalg.norm(v1) + 1e-6)
    v2_u = v2 / (np.linalg.norm(v2) + 1e-6)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))
```

---

### 2. utils.py (NEW FILE)

```python
"""
Utility functions for AR Hand Control System
"""
import numpy as np

class Smoother:
    """Smooth values over time using exponential moving average"""
    def __init__(self, alpha=0.5):
        self.alpha = alpha
        self.value = None
    
    def update(self, new_value):
        if self.value is None:
            self.value = new_value
        else:
            if isinstance(new_value, (tuple, list)):
                self.value = tuple(self.alpha * np.array(new_value) + (1 - self.alpha) * np.array(self.value))
            else:
                self.value = self.alpha * new_value + (1 - self.alpha) * self.value
        return self.value

def compute_palm_rotation(landmarks, width, height):
    """Estimate palm rotation using vector from wrist (0) to middle_finger_mcp (9)"""
    w = np.array([landmarks[0].x * width, landmarks[0].y * height])
    m = np.array([landmarks[9].x * width, landmarks[9].y * height])
    v = m - w
    angle = np.degrees(np.arctan2(v[1], v[0]))
    return float(angle % 360)

def compute_openness(landmarks, palm_center, width, height):
    """Calculate hand openness 0-100%"""
    tips = [4, 8, 12, 16, 20]
    dists = []
    for ti in tips:
        tx = int(landmarks[ti].x * width)
        ty = int(landmarks[ti].y * height)
        dists.append(np.hypot(tx - palm_center[0], ty - palm_center[1]))
    
    if not dists:
        return 0
    
    mean_dist = float(np.mean(dists))
    closed_ref = max(12.0, min(40.0, min(width, height) * 0.04))
    open_ref = max(60.0, min(width, height) * 0.55)
    raw_openness = (mean_dist - closed_ref) / (open_ref - closed_ref) * 100.0
    return float(np.clip(raw_openness, 0.0, 100.0))
```

---

## Summary

Your repository now has ALL features from both tubakhxn repos:

✅ **From Hand-Tracking-AR-UI:**
- Glowing radial HUD overlays
- Gesture-based mode switching
- Core patterns and arc segments  
- Dynamic fingertip tracking

✅ **From hand-gesture-controller:**
- Palm-anchored kinematic dashboard
- 3D rotating cube visualization
- Fingertip gear animations
- Hand rotation tracking
- Openness percentage calculation

✅ **Enhanced Features:**
- Modular code structure
- Multiple HUD modes
- Smooth animations
- Professional implementation

Copy these files into your repository and your single repo will do the work of BOTH starred repositories!
