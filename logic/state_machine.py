def update_state(obj, person_absent, is_stationary, current_time, min_state_time):
    """
    Finite State Machine

    ATTENDED
          │
          ▼
    POTENTIALLY_UNATTENDED
          │ (5 sec)
          ▼
    UNATTENDED

    If a person returns before 5 seconds,
    the object immediately returns to ATTENDED.
    """

    POTENTIAL_THRESHOLD = 5.0  # seconds

    # Object is safe
    if not person_absent or not is_stationary:
        obj.state = "ATTENDED"
        obj.potential_since = None
        return obj.state

    # First time object becomes suspicious
    if obj.state == "ATTENDED":
        obj.state = "POTENTIALLY_UNATTENDED"
        obj.potential_since = current_time
        return obj.state

    # Waiting period
    if obj.state == "POTENTIALLY_UNATTENDED":

        if obj.potential_since is None:
            obj.potential_since = current_time

        elapsed = current_time - obj.potential_since

        if elapsed >= POTENTIAL_THRESHOLD:
            obj.state = "UNATTENDED"

        return obj.state

    return obj.state