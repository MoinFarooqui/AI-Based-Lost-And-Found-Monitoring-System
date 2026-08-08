# backend/shared.py

import threading

# --- NEW: Shared Video Source State ---
current_source = 0  # Default to webcam
source_changed = False  # Flag to alert the video loop to restart
source_lock = threading.Lock()  # Prevents thread crashes when switching

def update_camera_source(new_source):
    """Called by Flask (app.py) when a dashboard button is clicked."""
    global current_source, source_changed
    with source_lock:
        current_source = new_source
        source_changed = True  # Raise the flag for OpenCV!

def get_current_source():
    """Safely get the current source to use."""
    global current_source
    with source_lock:
        return current_source

def check_and_reset_source_changed():
    """OpenCV loop calls this to check if it needs to restart."""
    global source_changed
    with source_lock:
        if source_changed:
            source_changed = False  # Lower the flag after reading it
            return True
        return False

# --- EXISTING: Frame Sharing ---
# Latest processed frame shared between YOLO and Flask
latest_processed_frame = None

# Lock for thread-safe access to prevent tearing or crashes
frame_lock = threading.Lock()

def set_latest_frame(frame):
    """Update the latest processed frame."""
    global latest_processed_frame
    
    with frame_lock:
        if frame is not None:
            latest_processed_frame = frame.copy()
        else:
            latest_processed_frame = None

def get_latest_frame():
    """Return a safe copy of the latest processed frame."""
    global latest_processed_frame
    
    with frame_lock:
        if latest_processed_frame is None:
            return None
        return latest_processed_frame.copy()