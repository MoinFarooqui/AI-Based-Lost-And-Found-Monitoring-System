# backend/main.py

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

os.environ["ULTRALYTICS_SETTINGS"] = "false"
os.environ["YOLO_OFFLINE"] = "true"

import cv2
import numpy as np
import time
import threading
import logging
from collections import deque, Counter
from ultralytics import YOLO
import supervision as sv

from logic.object_memory import ObjectMemory
from logic.state_machine import update_state
from utils.geometry import centroid

# Flask integration imports
from backend.app import app
import backend.shared as shared

# ================= PATHS =================

INPUT_DIR = os.path.join(BASE_DIR, "input")
EVENT_DIR = os.path.join(BASE_DIR, "events")
THUMB_DIR = os.path.join(BASE_DIR, "thumbs")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(EVENT_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)

# ================= CONFIG =================

CONF_THRESHOLD = 0.15
FRAME_SKIP = 4

PERSON_BAG_DISTANCE = 220
PERSON_MEMORY_TIME = 4.0
STATIONARY_DISTANCE = 15
STATIONARY_TIME = 5.0
MIN_STATE_TIME = 3.0

VALID_CLASSES = [0, 24, 26, 28]  # person, backpack, handbag, suitcase

CLASS_NAMES = {
    0: "Person",
    24: "Backpack",
    26: "Handbag",
    28: "Suitcase",
}

WINDOW = "AI-Based Lost & Found Monitoring System"

LOOP_VIDEO = True

PRE_EVENT_SECONDS = 1.5
POST_EVENT_SECONDS = 2.0

# ================= MODEL =================

model = YOLO(os.path.join(os.path.dirname(__file__), "yolov8s.pt"))

tracker = None

object_memory = ObjectMemory(distance_threshold=60)

# ================= STATE =================

recording = {"active": False, "frames": [], "start_time": 0, "ts": None}

frame_count = 0
last_persons = []
last_bags = []

track_class_history = {}
track_last_seen = {}
CLASS_HISTORY_LEN = 15
CLASS_LOCK_TIMEOUT = 2.0

# ================= HELPER FUNCTIONS =================

def is_source_live(source):
    """Check if the given source is a webcam or live stream feed."""
    if isinstance(source, int):
        return True
    if isinstance(source, str):
        if source.isdigit():
            return True
        if source.lower().startswith(("rtsp://", "http://", "https://")):
            return True
    return False

# ================= IMAGE ENHANCEMENT =================

def enhance_frame(frame):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    frame = cv2.filter2D(frame, -1, kernel)
    frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=10)
    return frame


def normalize_frame(frame):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(2.0, (8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

# ================= DRAWING =================

STATE_COLORS = {
    "ATTENDED": (0, 200, 0),
    "POTENTIALLY_UNATTENDED": (0, 210, 255),
    "UNATTENDED": (0, 0, 255),
}
PERSON_COLOR = (255, 100, 0)

LABEL_FONT = cv2.FONT_HERSHEY_SIMPLEX
LABEL_SCALE = 0.5
LABEL_THICKNESS = 1
LABEL_LINE_HEIGHT = 18
LABEL_PADDING = 6
LABEL_RADIUS = 8


def draw_rounded_label(frame, x, y, lines, color):
    widths = [cv2.getTextSize(line, LABEL_FONT, LABEL_SCALE, LABEL_THICKNESS)[0][0] for line in lines]
    box_w = max(widths) + LABEL_PADDING * 2
    box_h = LABEL_LINE_HEIGHT * len(lines) + LABEL_PADDING

    x1, x2 = x, x + box_w
    y2 = y
    y1 = y2 - box_h
    if y1 < 0:
        y1, y2 = y, y + box_h

    r = min(LABEL_RADIUS, box_h // 2, box_w // 2)

    overlay = frame.copy()
    cv2.rectangle(overlay, (x1 + r, y1), (x2 - r, y2), color, -1)
    cv2.rectangle(overlay, (x1, y1 + r), (x2, y2 - r), color, -1)
    for cx, cy in [(x1 + r, y1 + r), (x2 - r, y1 + r), (x1 + r, y2 - r), (x2 - r, y2 - r)]:
        cv2.circle(overlay, (cx, cy), r, color, -1)
    cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

    for i, line in enumerate(lines):
        ty = y1 + LABEL_PADDING + (i + 1) * LABEL_LINE_HEIGHT - 5
        cv2.putText(frame, line, (x1 + LABEL_PADDING, ty),
                    LABEL_FONT, LABEL_SCALE, (255, 255, 255), LABEL_THICKNESS, cv2.LINE_AA)


def draw_box(frame, box, color, lines):
    x1, y1, x2, y2 = [int(v) for v in box]
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)
    draw_rounded_label(frame, x1, y1, lines, color)


def render_detections(frame, persons, render_bags):
    for p in persons:
        lines = ["PERSON", f"ID : {p['id']:02d}", f"{int(round(p['conf'] * 100))}%"]
        draw_box(frame, p["box"], PERSON_COLOR, lines)

    for b in render_bags:
        cls_name = CLASS_NAMES.get(b["cls"], "OBJECT").upper()
        if b["state"] == "UNATTENDED":
            color = STATE_COLORS["UNATTENDED"]
            lines = ["[ALERT] UNATTENDED OBJECT", f"ID : {b['id']:02d}"]
        elif b["state"] == "POTENTIALLY_UNATTENDED":
            color = STATE_COLORS["POTENTIALLY_UNATTENDED"]
            lines = ["[!] POTENTIALLY UNATTENDED", f"ID : {b['id']:02d}"]
        else:
            color = STATE_COLORS["ATTENDED"]
            lines = [cls_name, f"ID : {b['id']:02d}", f"{int(round(b['conf'] * 100))}%"]
        draw_box(frame, b["box"], color, lines)

    return frame

# ================= VIDEO WRITER =================

def get_video_writer(path, w, h, fps):
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(path, fourcc, fps, (w, h))
    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(path, fourcc, fps, (w, h))
    return out


def save_event_video(fps):
    ts = recording["ts"]
    path = os.path.join(EVENT_DIR, f"event_{ts}.mp4")
    frames = [f for f in recording["frames"] if f is not None]
    if not frames:
        return
    h, w = frames[0].shape[:2]
    out = get_video_writer(path, w, h, fps)
    for f in frames:
        out.write(f)
    out.release()
    print(f"🎬 Saved event video: {path}")


def save_snapshot(frame):
    ts = recording["ts"]
    path = os.path.join(THUMB_DIR, f"event_{ts}.jpg")
    cv2.imwrite(path, frame)
    print(f"📸 Saved snapshot: {path}")

# ================= PROCESS =================

def process_frame(frame, frame_buffer):
    """Run detection/tracking (every FRAME_SKIP frames) and unattended-object logic."""

    global frame_count, last_persons, last_bags

    frame_count += 1
    now = time.time()

    if frame_count % FRAME_SKIP == 0:

        results = model(frame, conf=CONF_THRESHOLD, imgsz=512, verbose=False)[0]

        detections = sv.Detections.from_ultralytics(results)

        if detections.class_id is not None:
            detections = detections[np.isin(detections.class_id, VALID_CLASSES)]

        detections = tracker.update_with_detections(detections)

        persons, bags = [], []

        for box, cls, conf, tid in zip(
            detections.xyxy, detections.class_id, detections.confidence, detections.tracker_id
        ):
            tid = int(tid)

            if tid not in track_class_history:
                track_class_history[tid] = deque(maxlen=CLASS_HISTORY_LEN)
            track_class_history[tid].append(int(cls))
            track_last_seen[tid] = now

            stable_cls = Counter(track_class_history[tid]).most_common(1)[0][0]

            item = {"box": box, "conf": float(conf), "id": tid, "cls": stable_cls}
            if stable_cls == 0:
                persons.append(item)
            else:
                bags.append(item)

        stale_ids = [t for t, seen in track_last_seen.items() if now - seen > CLASS_LOCK_TIMEOUT]
        for t in stale_ids:
            track_class_history.pop(t, None)
            track_last_seen.pop(t, None)

        last_persons, last_bags = persons, bags

    persons = last_persons
    bags = last_bags

    persons_centroids = [centroid(p["box"]) for p in persons]

    render_bags = []

    for d in bags:
        bag_center = centroid(d["box"])
        obj = object_memory.match_or_create(bag_center)

        movement = np.linalg.norm(np.array(bag_center) - np.array(obj.last_position))

        person_near = any(
            np.linalg.norm(np.array(p) - np.array(bag_center)) < PERSON_BAG_DISTANCE
            for p in persons_centroids
        )

        if movement > 50 or person_near:
            obj.state = "ATTENDED"
            obj.event_triggered = False
            obj.last_person_near_time = now
            obj.stationary_since = None
            obj.potential_since = None
            obj.update_position(bag_center)
            render_bags.append({**d, "state": obj.state})
            continue

        if movement < STATIONARY_DISTANCE:
            if obj.stationary_since is None:
                obj.stationary_since = now
        else:
            obj.stationary_since = None

        is_stationary = obj.stationary_since and (now - obj.stationary_since) >= STATIONARY_TIME

        obj.update_position(bag_center)

        person_absent = (now - obj.last_person_near_time) >= PERSON_MEMORY_TIME

        if not hasattr(obj, "potential_since"):
            obj.potential_since = None

        if obj.state == "ATTENDED":
            if is_stationary and person_absent:
                obj.state = "POTENTIALLY_UNATTENDED"
                obj.potential_since = now

        elif obj.state == "POTENTIALLY_UNATTENDED":
            if not (is_stationary and person_absent):
                obj.state = "ATTENDED"
                obj.potential_since = None
            elif now - obj.potential_since >= 5.0:
                obj.state = "UNATTENDED"

        if obj.state == "UNATTENDED" and not obj.event_triggered:
            obj.event_triggered = True
            print("\n🚨 EVENT: unattended object detected")
            recording["active"] = True
            recording["frames"] = list(frame_buffer)
            recording["start_time"] = now
            recording["ts"] = time.strftime("%Y%m%d_%H%M%S")
            save_snapshot(frame)

        render_bags.append({**d, "state": obj.state})

    frame = render_detections(frame, persons, render_bags)
    return frame

# ================= MAIN =================

def main():
    global tracker

    # Mute default Flask logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    # Start Flask server in background daemon thread
    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False),
        daemon=True
    )
    flask_thread.start()
    print("🌐 Flask dashboard running at http://localhost:5000")

    # Initial capture setup from shared state
    current_source = shared.get_current_source()
    if isinstance(current_source, str) and current_source.isdigit():
        current_source = int(current_source)

    cap = cv2.VideoCapture(current_source)
    is_live = is_source_live(current_source)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 1:
        fps = 25

    effective_fps = max(1.0, fps / FRAME_SKIP)

    tracker = sv.ByteTrack(
        track_activation_threshold=0.3,
        lost_track_buffer=60,
        minimum_matching_threshold=0.7,
        frame_rate=effective_fps,
        minimum_consecutive_frames=2,
    )

    pre_event_frames = max(1, int(fps * PRE_EVENT_SECONDS))
    post_event_seconds = POST_EVENT_SECONDS

    frame_buffer = deque(maxlen=pre_event_frames)

    print(f"📡 Initial Processing Source: {current_source}")

    while True:
        # --- DYNAMIC SOURCE SWITCHING CHECK ---
        if shared.check_and_reset_source_changed():
            new_source = shared.get_current_source()
            if isinstance(new_source, str) and new_source.isdigit():
                new_source = int(new_source)

            print(f"🔄 Switching video feed to: {new_source}")
            cap.release()
            cap = cv2.VideoCapture(new_source)
            is_live = is_source_live(new_source)
            
            # Clear old tracking history on source change
            if hasattr(object_memory, "objects"):
                object_memory.objects.clear()
            track_class_history.clear()
            track_last_seen.clear()

        ret, frame = cap.read()

        if not ret:
            if (not is_live) and LOOP_VIDEO:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            elif is_live:
                time.sleep(0.05)
                continue
            else:
                time.sleep(0.1)
                continue

        raw_frame = frame.copy()
        frame_buffer.append(raw_frame)

        processed = enhance_frame(frame)
        processed = normalize_frame(processed)

        processed = process_frame(processed, frame_buffer)

        # Send frame to Flask endpoint for dashboard display
        shared.set_latest_frame(processed)

        if recording["active"]:
            recording["frames"].append(raw_frame)
            if time.time() - recording["start_time"] > post_event_seconds:
                save_event_video(fps)
                recording["active"] = False

        cv2.imshow(WINDOW, processed)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()