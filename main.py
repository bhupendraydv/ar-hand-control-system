#!/usr/bin/env python3
"""
AR Hand Control System - Main Application
Combines AR UI overlay with gesture recognition
Authors: Bhupendra YDV
Date: November 2025
"""

import cv2
import mediapipe as mp
import numpy as np
import math
import time

# ============ CONFIGURATION ============
MAX_NUM_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.7
CAMERA_ID = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
HUD_COLOR = (255, 255, 255)  # White
HUD_THICKNESS = 2
SMOOTH_FACTOR = 0.3

# ============ UTILITY FUNCTIONS ============
def smooth_value(prev, new, factor=SMOOTH_FACTOR):
    if prev is None:
        return new
    return prev * (1 - factor) + new * factor

def calculate_distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

# ============ GESTURE RECOGNIZER ============
class GestureRecognizer:
    def recognize(self, landmarks):
        fingers = self._get_fingers_up(landmarks)
        
        if all(fingers):
            return "Open Hand"
        elif not any(fingers):
            return "Closed Fist"
        elif fingers[1] and not any(fingers[2:]):
            return "Pointing"
        elif fingers[1] and fingers[2] and not any(fingers[3:]):
            return "Peace Sign"
        elif fingers[0] and not any(fingers[1:]):
            return "Thumbs Up"
        elif fingers[0] and fingers[1]:
            thumb_tip = landmarks.landmark[4]
            index_tip = landmarks.landmark[8]
            dist = calculate_distance(thumb_tip, index_tip)
            if dist < 0.05:
                return "Pinch"
        return "Unknown"
    
    def _get_fingers_up(self, landmarks):
        fingers = []
        # Thumb
        fingers.append(landmarks.landmark[4].x < landmarks.landmark[3].x)
        # Other fingers
        for tip, pip in [(8,6), (12,10), (16,14), (20,18)]:
            fingers.append(landmarks.landmark[tip].y < landmarks.landmark[pip].y)
        return fingers

# ============ AR OVERLAY ============
class AROverlay:
    def __init__(self):
        self.prev_palm = None
        self.prev_angle = 0
    
    def draw(self, frame, landmarks, gesture):
        h, w = frame.shape[:2]
        
        # Get palm center
        wrist = landmarks.landmark[0]
        middle_mcp = landmarks.landmark[9]
        palm_x = int((wrist.x + middle_mcp.x) / 2 * w)
        palm_y = int((wrist.y + middle_mcp.y) / 2 * h)
        
        # Smooth movement
        if self.prev_palm:
            palm_x = int(smooth_value(self.prev_palm[0], palm_x))
            palm_y = int(smooth_value(self.prev_palm[1], palm_y))
        self.prev_palm = (palm_x, palm_y)
        
        # Draw components
        self._draw_radial_hud(frame, self.prev_palm)
        self._draw_finger_bones(frame, landmarks, w, h)
        self._draw_rotation(frame, landmarks, self.prev_palm, w, h)
        self._draw_gesture_label(frame, gesture, self.prev_palm)
        self._draw_3d_cube(frame, self.prev_palm)
        
        return frame
    
    def _draw_radial_hud(self, frame, center):
        # Concentric circles
        for radius in [40, 70, 100]:
            cv2.circle(frame, center, radius, HUD_COLOR, HUD_THICKNESS)
        
        # Radial ticks
        for i in range(12):
            angle = math.radians(i * 30)
            x1 = int(center[0] + 100 * math.cos(angle))
            y1 = int(center[1] + 100 * math.sin(angle))
            x2 = int(center[0] + 115 * math.cos(angle))
            y2 = int(center[1] + 115 * math.sin(angle))
            cv2.line(frame, (x1,y1), (x2,y2), HUD_COLOR, 2)
        
        # Center cross
        cv2.line(frame, (center[0]-10,center[1]), (center[0]+10,center[1]), HUD_COLOR, 2)
        cv2.line(frame, (center[0],center[1]-10), (center[0],center[1]+10), HUD_COLOR, 2)
    
    def _draw_finger_bones(self, frame, landmarks, w, h):
        connections = [
            [0,1,2,3,4], [0,5,6,7,8], [0,9,10,11,12],
            [0,13,14,15,16], [0,17,18,19,20]
        ]
        
        for finger in connections:
            for i in range(len(finger)-1):
                p1 = landmarks.landmark[finger[i]]
                p2 = landmarks.landmark[finger[i+1]]
                pt1 = (int(p1.x*w), int(p1.y*h))
                pt2 = (int(p2.x*w), int(p2.y*h))
                cv2.line(frame, pt1, pt2, HUD_COLOR, 2)
                cv2.circle(frame, pt1, 4, HUD_COLOR, -1)
    
    def _draw_rotation(self, frame, landmarks, center, w, h):
        wrist = landmarks.landmark[0]
        middle = landmarks.landmark[9]
        dx = (middle.x - wrist.x) * w
        dy = (middle.y - wrist.y) * h
        angle = math.degrees(math.atan2(dy, dx))
        
        # Draw arrow
        rad = math.radians(angle)
        end_x = int(center[0] + 80 * math.cos(rad))
        end_y = int(center[1] + 80 * math.sin(rad))
        cv2.arrowedLine(frame, center, (end_x, end_y), (0,255,255), 2, tipLength=0.3)
        
        # Display angle
        cv2.putText(frame, f"{int(angle)}deg", (center[0]+20, center[1]-120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, HUD_COLOR, 2)
    
    def _draw_gesture_label(self, frame, gesture, center):
        cv2.putText(frame, gesture, (center[0]-50, center[1]-150),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    
    def _draw_3d_cube(self, frame, center):
        size = 25
        points_3d = [
            [-size,-size,-size], [size,-size,-size], [size,size,-size],
            [-size,size,-size], [-size,-size,size], [size,-size,size],
            [size,size,size], [-size,size,size]
        ]
        
        # Project to 2D
        points_2d = []
        for p in points_3d:
            x = int(center[0] + p[0] + p[2]*0.5)
            y = int(center[1] + p[1] + p[2]*0.5)
            points_2d.append((x,y))
        
        # Draw cube edges
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),
                (0,4),(1,5),(2,6),(3,7)]
        for edge in edges:
            cv2.line(frame, points_2d[edge[0]], points_2d[edge[1]], (100,255,100), 1)

# ============ MAIN APPLICATION ============
def main():
    print("\n" + "="*50)
    print("🎯 AR HAND CONTROL SYSTEM")
    print("="*50)
    print("Controls:")
    print("  q or ESC - Quit")
    print("  h - Toggle HUD")
    print("  g - Toggle Gesture Recognition")
    print("  d - Toggle Debug Mode")
    print("="*50 + "\n")
    
    # Initialize MediaPipe
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=MAX_NUM_HANDS,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE
    )
    
    # Initialize components
    ar_overlay = AROverlay()
    gesture_recognizer = GestureRecognizer()
    
    # Open camera
    cap = cv2.VideoCapture(CAMERA_ID)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    
    if not cap.isOpened():
        print("❌ Error: Could not open camera")
        return
    
    print("✅ Camera initialized")
    print("✅ Starting AR Hand Tracking...\n")
    
    # Control flags
    show_hud = True
    show_gestures = True
    show_debug = False
    
    # FPS calculation
    prev_time = 0
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue
        
        # Flip horizontally for mirror view
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        # Calculate FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time > 0 else 0
        prev_time = curr_time
        
        # Process hands
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Debug mode - show landmarks
                if show_debug:
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                    )
                
                # Gesture recognition
                gesture = "Unknown"
                if show_gestures:
                    gesture = gesture_recognizer.recognize(hand_landmarks)
                
                # Draw AR HUD
                if show_hud:
                    frame = ar_overlay.draw(frame, hand_landmarks, gesture)
        
        # Display info
        cv2.putText(frame, f"FPS: {int(fps)}", (20,40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.putText(frame, f"HUD: {'ON' if show_hud else 'OFF'}", (20,80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        cv2.putText(frame, f"Gestures: {'ON' if show_gestures else 'OFF'}", (20,110),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        
        # Show frame
        cv2.imshow('AR Hand Control System', frame)
        
        # Handle keyboard
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('h'):
            show_hud = not show_hud
            print(f"HUD: {'ON' if show_hud else 'OFF'}")
        elif key == ord('g'):
            show_gestures = not show_gestures
            print(f"Gestures: {'ON' if show_gestures else 'OFF'}")
        elif key == ord('d'):
            show_debug = not show_debug
            print(f"Debug: {'ON' if show_debug else 'OFF'}")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ System closed successfully")

if __name__ == "__main__":
    main()
