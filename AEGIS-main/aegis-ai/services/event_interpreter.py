import os
from typing import Any, Dict, List, Optional

# Rule constants
ROAD_INCIDENT_VEHICLE_THRESHOLD = 2
ROAD_INCIDENT_PERSON_THRESHOLD = 1
ROAD_INCIDENT_PERSISTENT_FRAMES = 2

CROWD_EVENT_PERSON_THRESHOLD = 5
CROWD_EVENT_PERSISTENT_FRAMES = 2


def interpret_detections(frame_detections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes list of frame detections to classify vision events.
    - Counts maximum visible objects in any single frame.
    - Verifies temporal persistence of objects across frames.
    - Applies deterministic rules to classify events.
    - Produces factual evidence without fabricating spatial or event data.
    """
    if not frame_detections:
        return {
            "event_type": "NO_SIGNIFICANT_EVENT",
            "event_score": 0,
            "evidence": [],
            "object_summary": {
                "vehicles": 0,
                "persons": 0,
                "motorcycles": 0,
                "buses": 0,
                "trucks": 0,
                "cars": 0,
                "bicycles": 0
            },
            "frames_analyzed": 0,
            "first_timestamp_seconds": None,
            "last_timestamp_seconds": None,
            "reason": "No frame detections were provided for analysis."
        }

    # Aggregate counts
    max_vehicles = 0
    max_persons = 0
    max_motorcycles = 0
    max_buses = 0
    max_trucks = 0
    max_cars = 0
    max_bicycles = 0
    max_fire_or_smoke = 0
    
    frames_with_vehicles = 0
    frames_with_persons = 0
    frames_with_fire_or_smoke = 0
    
    timestamps = []
    
    for frame in frame_detections:
        # Check timestamp
        ts = frame.get("timestamp_seconds")
        if ts is not None:
            timestamps.append(ts)
            
        # Count objects in current frame
        num_vehicles = 0
        num_persons = 0
        num_motorcycles = 0
        num_buses = 0
        num_trucks = 0
        num_cars = 0
        num_bicycles = 0
        num_fire_or_smoke = 0
        
        detections = frame.get("detections", [])
        for det in detections:
            cls_name = str(det.get("class_name", "")).lower()
            if cls_name == "person":
                num_persons += 1
            elif cls_name == "car":
                num_cars += 1
                num_vehicles += 1
            elif cls_name == "motorcycle":
                num_motorcycles += 1
                num_vehicles += 1
            elif cls_name == "bus":
                num_buses += 1
                num_vehicles += 1
            elif cls_name == "truck":
                num_trucks += 1
                num_vehicles += 1
            elif cls_name == "bicycle":
                num_bicycles += 1
            elif cls_name in {"fire", "smoke"}:
                num_fire_or_smoke += 1

        # Maxima
        max_vehicles = max(max_vehicles, num_vehicles)
        max_persons = max(max_persons, num_persons)
        max_motorcycles = max(max_motorcycles, num_motorcycles)
        max_buses = max(max_buses, num_buses)
        max_trucks = max(max_trucks, num_trucks)
        max_cars = max(max_cars, num_cars)
        max_bicycles = max(max_bicycles, num_bicycles)
        max_fire_or_smoke = max(max_fire_or_smoke, num_fire_or_smoke)

        # Persistence counts
        if num_vehicles >= 1:
            frames_with_vehicles += 1
        if num_persons >= 1:
            frames_with_persons += 1
        if num_fire_or_smoke >= 1:
            frames_with_fire_or_smoke += 1

    first_ts = min(timestamps) if timestamps else None
    last_ts = max(timestamps) if timestamps else None
    
    # 2. Rule evaluation
    event_type = "NO_SIGNIFICANT_EVENT"
    event_score = 0
    evidence = []
    reason = ""

    # Rule A: Fire/smoke classes present in detections (must be verified!)
    if max_fire_or_smoke > 0 and frames_with_fire_or_smoke >= 1:
        event_type = "POSSIBLE_FIRE_EVENT"
        event_score = 5
        evidence = [f"Fire/smoke indicators detected (count: {max_fire_or_smoke})"]
        reason = "Fire/smoke signature was detected in the frames, indicating a possible fire event."
    # Rule B: Road incident (vehicles >= 2 AND persons >= 1 AND persistent across >= 2 frames)
    elif (max_vehicles >= ROAD_INCIDENT_VEHICLE_THRESHOLD and 
          max_persons >= ROAD_INCIDENT_PERSON_THRESHOLD and 
          frames_with_vehicles >= ROAD_INCIDENT_PERSISTENT_FRAMES and 
          frames_with_persons >= ROAD_INCIDENT_PERSISTENT_FRAMES):
        event_type = "POSSIBLE_ROAD_INCIDENT"
        # Scoring
        score = 2
        if max_vehicles >= 3:
            score += 1
        if max_persons >= 2:
            score += 1
        event_score = score
        evidence = [
            f"Multiple vehicles detected (count: {max_vehicles})",
            f"Persons detected (count: {max_persons})",
            f"Vehicle pattern persisted across {frames_with_vehicles} frames",
            f"Person pattern persisted across {frames_with_persons} frames"
        ]
        reason = "Multiple vehicles and persons were detected persistently across sampled frames, producing a possible road incident pattern."
    # Rule C: Crowd (persons >= 5 AND persistent across >= 2 frames)
    elif (max_persons >= CROWD_EVENT_PERSON_THRESHOLD and 
          frames_with_persons >= CROWD_EVENT_PERSISTENT_FRAMES):
        event_type = "POSSIBLE_CROWD_EVENT"
        score = 2
        if max_persons >= 8:
            score += 1
        event_score = score
        evidence = [
            f"High number of persons detected (count: {max_persons})",
            f"Person pattern persisted across {frames_with_persons} frames"
        ]
        reason = f"A crowd of {max_persons} persons was detected persistently across multiple frames, indicating a possible crowd event."
    else:
        event_type = "NO_SIGNIFICANT_EVENT"
        # Determine some basic evidence for no significant event
        if max_vehicles > 0 or max_persons > 0:
            event_score = 1
            if max_vehicles > 0:
                evidence.append(f"Vehicles observed (count: {max_vehicles})")
            if max_persons > 0:
                evidence.append(f"Persons observed (count: {max_persons})")
        else:
            event_score = 0
            
        reason = "No sufficiently strong emergency-related object pattern was identified in the supplied detections."

    return {
        "event_type": event_type,
        "event_score": event_score,
        "evidence": evidence,
        "object_summary": {
            "vehicles": max_vehicles,
            "persons": max_persons,
            "motorcycles": max_motorcycles,
            "buses": max_buses,
            "trucks": max_trucks,
            "cars": max_cars,
            "bicycles": max_bicycles
        },
        "frames_analyzed": len(frame_detections),
        "first_timestamp_seconds": first_ts,
        "last_timestamp_seconds": last_ts,
        "reason": reason
    }
