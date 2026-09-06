import cv2
import mediapipe as mp
import requests
import time
import numpy as np

# ===== Configuration =====
FLASK_URL = "http://localhost:5000/gesture"
DEBOUNCE_TIME = 0.5

# ===== MediaPipe Setup =====
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

last_gesture = None
last_command_time = 0

def count_fingers(hand_landmarks):
    fingers = []
    # Thumb
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
    thumb_extended = np.sqrt(
        (thumb_tip.x - index_mcp.x)**2 + 
        (thumb_tip.y - index_mcp.y)**2
    ) > 0.1
    fingers.append(thumb_extended)
    
    # Other fingers
    for finger in [
        mp_hands.HandLandmark.INDEX_FINGER_TIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        mp_hands.HandLandmark.RING_FINGER_TIP,
        mp_hands.HandLandmark.PINKY_TIP
    ]:
        tip = hand_landmarks.landmark[finger]
        pip = hand_landmarks.landmark[finger - 2]
        fingers.append(tip.y < pip.y)
    
    return sum(fingers)

def detect_gesture(hand_landmarks):
    fingers = count_fingers(hand_landmarks)
    if fingers >= 5:
        return "open"
    elif fingers <= 1:
        return "closed"
    return None

def send_gesture(gesture):
    try:
        response = requests.post(FLASK_URL, json={"gesture": gesture}, timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    global last_gesture, last_command_time
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("❌ Cannot open webcam")
        return
    
    print("🖐️ Gesture Control Started")
    print("   → Open palm: Turn all lights ON")
    print("   → Closed palm: Turn all lights OFF")
    print("   → Press 'q' to quit")
    
    while True:
        success, frame = cap.read()
        if not success:
            continue
        
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        overlay = frame.copy()
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    overlay,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style()
                )
                
                gesture = detect_gesture(hand_landmarks)
                current_time = time.time()
                
                if gesture and gesture != last_gesture and current_time - last_command_time > DEBOUNCE_TIME:
                    print(f"🖐️ Gesture: {gesture.upper()}")
                    if send_gesture(gesture):
                        last_gesture = gesture
                        last_command_time = current_time
                        cv2.putText(
                            overlay,
                            f"{gesture.upper()} PALM!",
                            (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 0) if gesture == "open" else (0, 0, 255),
                            2
                        )
        
        cv2.putText(
            overlay,
            f"Gesture: {last_gesture or 'None'}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        cv2.imshow('🖐️ Jarvis Gesture Control', overlay)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if __name__ == "__main__":
    main()