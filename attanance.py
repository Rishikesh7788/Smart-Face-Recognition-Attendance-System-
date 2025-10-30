import cv2
import os
import face_recognition
import numpy as np
from datetime import datetime
from time import time, sleep
import argparse
from firebase_config import db

# === Command-line Argument ===
parser = argparse.ArgumentParser(description="Smart Face Recognition Attendance System")
parser.add_argument("--mode", choices=["realtime", "surveillance"], default="realtime",
                    help="Choose 'realtime' or 'surveillance' mode.")
args = parser.parse_args()

# === Load Student Images ===
STUDENT_DIR = "students"
print(f"[INFO] Loading student images from: {STUDENT_DIR}")

known_encodings = []
student_names = []

for file in os.listdir(STUDENT_DIR):
    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
        image_path = os.path.join(STUDENT_DIR, file)
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) == 1:
            known_encodings.append(encodings[0])
            student_names.append(os.path.splitext(file)[0])
        elif len(encodings) == 0:
            print(f"[WARNING] No face found in {file}")
        else:
            print(f"[WARNING] Multiple faces found in {file}, skipping.")

if not known_encodings:
    print("[ERROR] No valid student encodings found. Exiting.")
    exit()

# === Webcam Setup ===
print("[INFO] Accessing webcam...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[WARNING] Default webcam not found. Trying index 1...")
    cap = cv2.VideoCapture(1)
    sleep(2)

if not cap.isOpened():
    print("[ERROR] Cannot access any camera.")
    exit()

# === Variables ===
UNKNOWN_DIR = "unknown_faces"
os.makedirs(UNKNOWN_DIR, exist_ok=True)

THRESHOLD = 0.5
COOLDOWN_SECONDS = 60
unknown_counter = 0
marked_today = set()
last_logged_time = {}

print(f"[INFO] Mode: {args.mode.upper()} | Press 'q' to exit.\n")

# === Main Loop ===
while True:
    ret, frame = cap.read()
    if not ret:
        print("[WARNING] Frame not captured. Retrying...")
        continue

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_small)
    face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

    for encoding, loc in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(known_encodings, encoding)
        face_distances = face_recognition.face_distance(known_encodings, encoding)
        best_match_index = np.argmin(face_distances)

        top, right, bottom, left = [v * 4 for v in loc]
        h, w, _ = frame.shape
        top, right, bottom, left = max(0, top), min(w, right), min(h, bottom), max(0, left)

        if matches[best_match_index] and face_distances[best_match_index] < THRESHOLD:
            name = student_names[best_match_index]
            confidence = (1 - face_distances[best_match_index]) * 100
            label = f"{name} ({confidence:.1f}%)"
            color = (0, 255, 0)

            # === Realtime Mode ===
            if args.mode == "realtime":
                date_str = datetime.now().strftime("%Y-%m-%d")
                doc_id = f"{name}_{date_str}"
                if doc_id not in marked_today:
                    marked_today.add(doc_id)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db.collection("attendance").document(doc_id).set({
                        "name": name,
                        "date": date_str,
                        "timestamp": timestamp
                    })
                    print(f"[INFO] ✅ Marked present: {name} at {timestamp}")

            # === Surveillance Mode ===
            elif args.mode == "surveillance":
                current_time = time()
                if name not in last_logged_time or (current_time - last_logged_time[name] > COOLDOWN_SECONDS):
                    last_logged_time[name] = current_time
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db.collection("attendance").add({
                        "name": name,
                        "timestamp": timestamp
                    })
                    print(f"[INFO] 🕒 Logged {name} at {timestamp}")

        else:
            label = "Unknown"
            color = (0, 0, 255)
            unknown_face = frame[top:bottom, left:right]
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            unknown_path = os.path.join(UNKNOWN_DIR, f"unknown_{timestamp_str}_{unknown_counter}.jpg")

            if unknown_face.size > 0:
                cv2.imwrite(unknown_path, unknown_face)
                db.collection("unknown_faces").add({
                    "timestamp": timestamp_str,
                    "filename": f"unknown_{timestamp_str}_{unknown_counter}.jpg"
                })
                print(f"[INFO] ❌ Unknown face saved: {unknown_path}")
                unknown_counter += 1

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

    cv2.imshow(f"Smart Attendance ({args.mode.upper()} Mode)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("[INFO] System stopped manually.")
        break

cap.release()
cv2.destroyAllWindows()
