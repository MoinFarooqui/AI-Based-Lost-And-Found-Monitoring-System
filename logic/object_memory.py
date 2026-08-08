import time
import numpy as np


class TrackedObject:
    def __init__(self, position):

        # Latest object position
        self.last_position = position
        self.last_seen = time.time()

        # ================= OBJECT STATE =================

        # ATTENDED
        # POTENTIALLY_UNATTENDED
        # UNATTENDED
        self.state = "ATTENDED"

        # Last time a person was close to the object
        self.last_person_near_time = time.time()

        # Time when the object became stationary
        self.stationary_since = None

        # Time when object entered POTENTIALLY_UNATTENDED state
        self.potential_since = None

        # Prevent duplicate event generation
        self.event_triggered = False

    def update_position(self, position):
        self.last_position = position
        self.last_seen = time.time()


class ObjectMemory:
    def __init__(self, distance_threshold=60):

        self.distance_threshold = distance_threshold

        self.objects = []

    def match_or_create(self, position):
        """
        Match the detected object with an existing tracked object.
        If no nearby object exists, create a new tracked object.
        """

        for obj in self.objects:

            distance = np.linalg.norm(
                np.array(position) - np.array(obj.last_position)
            )

            if distance < self.distance_threshold:
                obj.update_position(position)
                return obj

        new_object = TrackedObject(position)
        self.objects.append(new_object)

        return new_object

    def cleanup(self, timeout=15):
        """
        Remove objects that have not been seen
        for a long time to prevent memory growth.
        """

        current_time = time.time()

        self.objects = [
            obj
            for obj in self.objects
            if current_time - obj.last_seen < timeout
        ]