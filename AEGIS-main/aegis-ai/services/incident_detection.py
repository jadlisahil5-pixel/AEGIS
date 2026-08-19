import datetime
import re
import threading
from typing import Any, Dict

# Supported normalized incident types
SUPPORTED_TYPES = {
    "ROAD_ACCIDENT",
    "FIRE",
    "MEDICAL_EMERGENCY",
    "INDUSTRIAL_ACCIDENT",
    "BUILDING_COLLAPSE",
    "MASS_CASUALTY",
    "FLOOD",
    "TRAFFIC_INCIDENT",
    "WOMEN_SAFETY",
    "DISASTER",
    "CROWD_EVENT",
    "OTHER",
}

# Source values allowed
ALLOWED_SOURCES = {"CITIZEN", "CCTV", "POLICE", "AMBULANCE", "SYSTEM", "VISION"}

# Normalization mapping from legacy or common variants to supported types
NORMALIZATION_MAP = {
    "VEHICLE_COLLISION": "ROAD_ACCIDENT",
    "PEDESTRIAN_ACCIDENT": "ROAD_ACCIDENT",
    "ROAD_ACCIDENT": "ROAD_ACCIDENT",
    "FIRE_INCIDENT": "FIRE",
    "FIRE": "FIRE",
    "MEDICAL_EMERGENCY": "MEDICAL_EMERGENCY",
    "CARDIAC_EMERGENCY": "MEDICAL_EMERGENCY",
    "INDUSTRIAL_ACCIDENT": "INDUSTRIAL_ACCIDENT",
    "BUILDING_COLLAPSE": "BUILDING_COLLAPSE",
    "BUILDING_INCIDENT": "BUILDING_COLLAPSE",
    "MASS_CASUALTY": "MASS_CASUALTY",
    "FLOOD": "FLOOD",
    "TRAFFIC_INCIDENT": "TRAFFIC_INCIDENT",
    "WOMEN_SAFETY": "WOMEN_SAFETY",
    "DISASTER": "DISASTER",
    "CROWD_EVENT": "CROWD_EVENT",
    "OTHER": "OTHER",
}

# Thread-safe in-memory sequential incident ID counter
_counter = 0
_counter_lock = threading.Lock()


def generate_incident_id(date_str: str = None) -> str:
    """Generate a unique sequential incident ID in the format INC-YYYYMMDD-XXX."""
    global _counter
    if not date_str:
        date_str = datetime.datetime.now().strftime("%Y%m%d")
    with _counter_lock:
        _counter += 1
        current_val = _counter
    return f"INC-{date_str}-{current_val:03d}"


def validate_incident_id(incident_id: str) -> None:
    """Validate that the supplied incident ID is non-empty and has a valid structure."""
    if not isinstance(incident_id, str):
        raise ValueError("Incident ID must be a string")
    if not incident_id.strip():
        raise ValueError("Incident ID cannot be empty")
    if not re.match(r"^INC-[\w-]+$", incident_id.strip()):
        raise ValueError(f"Invalid incident ID format: '{incident_id}'")


def normalize_incident_type(raw_type: str) -> str:
    """Normalize the raw incident type string to a supported uppercase constant."""
    if not isinstance(raw_type, str):
        raise ValueError("Incident type must be a string")
    
    cleaned = raw_type.strip().upper().replace(" ", "_").replace("-", "_")
    if cleaned in NORMALIZATION_MAP:
        return NORMALIZATION_MAP[cleaned]
    
    raise ValueError(f"Unsupported incident type: '{raw_type}'")


def process_incident(data: Dict[str, Any], allow_null_coords: bool = False) -> Dict[str, Any]:
    """
    Validate, normalize, and standardize incoming incident report data.
    Raises ValueError for validation failures.
    """
    if not isinstance(data, dict):
        raise ValueError("Input data must be a dictionary")

    # 1. Validate and normalize incident_type
    raw_type = data.get("incident_type")
    if raw_type is None:
        raise ValueError("Missing required field: 'incident_type'")
    normalized_type = normalize_incident_type(raw_type)

    # 2. Validate latitude
    raw_lat = data.get("latitude")
    if raw_lat is None:
        if allow_null_coords:
            latitude = None
        else:
            raise ValueError("Missing required field: 'latitude'")
    else:
        try:
            latitude = float(raw_lat)
        except (ValueError, TypeError):
            raise ValueError("Latitude must be a valid float")
        if not (-90.0 <= latitude <= 90.0):
            raise ValueError("Latitude must be between -90.0 and 90.0")

    # 3. Validate longitude
    raw_lon = data.get("longitude")
    if raw_lon is None:
        if allow_null_coords:
            longitude = None
        else:
            raise ValueError("Missing required field: 'longitude'")
    else:
        try:
            longitude = float(raw_lon)
        except (ValueError, TypeError):
            raise ValueError("Longitude must be a valid float")
        if not (-180.0 <= longitude <= 180.0):
            raise ValueError("Longitude must be between -180.0 and 180.0")

    # 4. Normalize and validate numeric fields
    # casualties (default: 0)
    raw_casualties = data.get("casualties")
    if raw_casualties is None:
        casualties = 0
    else:
        try:
            casualties = int(raw_casualties)
        except (ValueError, TypeError):
            raise ValueError("Casualties must be a valid integer")
        if casualties < 0:
            raise ValueError("Casualties must not be negative")

    # vehicles (default: 0)
    raw_vehicles = data.get("vehicles")
    if raw_vehicles is None:
        vehicles = 0
    else:
        try:
            vehicles = int(raw_vehicles)
        except (ValueError, TypeError):
            raise ValueError("Vehicles must be a valid integer")
        if vehicles < 0:
            raise ValueError("Vehicles must not be negative")

    # 5. Validate boolean fields
    # fire (default: False)
    raw_fire = data.get("fire")
    if raw_fire is None:
        fire = False
    elif isinstance(raw_fire, bool):
        fire = raw_fire
    elif isinstance(raw_fire, str):
        if raw_fire.lower() in ("true", "1", "yes"):
            fire = True
        elif raw_fire.lower() in ("false", "0", "no"):
            fire = False
        else:
            raise ValueError("fire field must be a boolean or a valid boolean-like string")
    else:
        raise ValueError("fire field must be a boolean")

    # road_blocked (default: False)
    raw_road_blocked = data.get("road_blocked")
    if raw_road_blocked is None:
        road_blocked = False
    elif isinstance(raw_road_blocked, bool):
        road_blocked = raw_road_blocked
    elif isinstance(raw_road_blocked, str):
        if raw_road_blocked.lower() in ("true", "1", "yes"):
            road_blocked = True
        elif raw_road_blocked.lower() in ("false", "0", "no"):
            road_blocked = False
        else:
            raise ValueError("road_blocked field must be a boolean or a valid boolean-like string")
    else:
        raise ValueError("road_blocked field must be a boolean")

    # 6. Validate/Generate incident_id
    supplied_id = data.get("incident_id")
    if supplied_id is not None:
        validate_incident_id(supplied_id)
        incident_id = supplied_id.strip()
    else:
        incident_id = generate_incident_id()

    # 7. Generate/Validate timestamp
    timestamp = data.get("timestamp")
    if timestamp is None:
        timestamp = datetime.datetime.now().isoformat()
    elif not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("Timestamp must be a non-empty string")
    else:
        timestamp = timestamp.strip()

    # 8. Validate/Normalize source
    raw_source = data.get("source")
    if raw_source is None:
        source = "SYSTEM"
    else:
        if not isinstance(raw_source, str):
            raise ValueError("Source must be a string")
        source = raw_source.strip().upper()
        if source not in ALLOWED_SOURCES:
            raise ValueError(f"Invalid source value: '{raw_source}'")

    return {
        "incident_id": incident_id,
        "incident_type": normalized_type,
        "latitude": latitude,
        "longitude": longitude,
        "casualties": casualties,
        "fire": fire,
        "road_blocked": road_blocked,
        "vehicles": vehicles,
        "timestamp": timestamp,
        "source": source,
    }
