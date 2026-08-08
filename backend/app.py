# backend/app.py

from flask import Flask, render_template, send_from_directory, Response, request, jsonify
import os
from datetime import datetime
import cv2
import time
import backend.shared as shared

# Absolute Paths for exact folder matching with main.py
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EVENT_FOLDER = os.path.join(BASE_DIR, "events")
THUMB_FOLDER = os.path.join(BASE_DIR, "thumbs")

os.makedirs(EVENT_FOLDER, exist_ok=True)
os.makedirs(THUMB_FOLDER, exist_ok=True)

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

def format_filename(filename):
    """Converts event_20260731_143210.mp4 -> 31-07-2026 14:32:10"""
    try:
        parts = filename.replace(".mp4", "").split("_")
        date_str = parts[1]
        time_str = parts[2]
        dt = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
        return dt.strftime("%d-%m-%Y %H:%M:%S")
    except Exception:
        return filename

# --- Generator function for live video stream ---
def generate_frames():
    while True:
        frame = shared.get_latest_frame()
        if frame is None:
            time.sleep(0.05)
            continue
            
        success, buffer = cv2.imencode('.jpg', frame)
        if not success:
            continue
            
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route("/")
def index():
    # Fetch recorded events (.mp4 files)
    video_files = [f for f in os.listdir(EVENT_FOLDER) if f.endswith(".mp4")]
    video_files.sort(reverse=True)
    
    events = []
    for f in video_files:
        event_time = format_filename(f)
        thumb_name = f.replace(".mp4", ".jpg")
        
        events.append({
            "snapshot": f"/thumb/{thumb_name}",
            "time": event_time,
            "source": "CCTV Stream",
            "status": "UNATTENDED",
            "video": f"/video/{f}"
        })

    # Fetch snapshot images (.jpg / .png files)
    snap_files = [f for f in os.listdir(THUMB_FOLDER) if f.endswith((".jpg", ".png"))]
    snap_files.sort(reverse=True)
    snapshots = [f"/thumb/{f}" for f in snap_files]

    return render_template(
        "index.html",
        events=events,
        snapshots=snapshots,
        events_count=len(events),
        current_source="Active CCTV / Video"
    )
@app.route("/api/events")
def api_events():

    video_files = [
        f for f in os.listdir(EVENT_FOLDER)
        if f.endswith(".mp4")
    ]
    video_files.sort(reverse=True)

    events = []

    for f in video_files:

        event_time = format_filename(f)
        thumb_name = f.replace(".mp4", ".jpg")

        events.append({
            "snapshot": f"/thumb/{thumb_name}",
            "time": event_time,
            "source": "CCTV Stream",
            "status": "UNATTENDED",
            "video": f"/video/{f}"
        })

    snap_files = [
        f for f in os.listdir(THUMB_FOLDER)
        if f.endswith((".jpg", ".png"))
    ]
    snap_files.sort(reverse=True)

    snapshots = [
        f"/thumb/{f}"
        for f in snap_files
    ]

    return jsonify({
        "events": events,
        "snapshots": snapshots,
        "events_count": len(events)
    })
# --- Routes for Stream and Static Media ---

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/video/<path:filename>")
def video(filename):
    return send_from_directory(EVENT_FOLDER, filename)

@app.route("/thumb/<path:filename>")
def thumb(filename):
    return send_from_directory(THUMB_FOLDER, filename)

# --- NEW: Route to Handle Dynamic Source Switching ---
@app.route('/set_source', methods=['POST'])
def set_source():
    data = request.get_json()
    new_source = data.get('source')
    
    # If the user clicks '0', '1', convert string '0' to integer 0 for webcam
    if str(new_source).isdigit():
        new_source = int(new_source)
        
    # Update the shared variable so the main loop captures the new source
    shared.current_source = new_source
    
    # Optional: If you have a specific function in shared.py to apply this immediately:
    if hasattr(shared, 'update_camera_source'):
        shared.update_camera_source(new_source)
        
    return jsonify({"status": "success", "source": str(new_source)})

if __name__ == "__main__":
    app.run(debug=True)