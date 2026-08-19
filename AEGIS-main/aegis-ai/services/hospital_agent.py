import math
from typing import Any, Dict, Optional
from services.data_loader import get_hospitals

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth's surface in km."""
    # Earth radius in kilometers
    R = 6371.0
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def recommend_hospital(
    latitude: Optional[float],
    longitude: Optional[float],
    severity: Optional[str] = None,
    requires_trauma: bool = False,
    requires_icu: bool = False
) -> Dict[str, Any]:
    """
    Recommend the best hospital based on location, severity, trauma requirement, and ICU requirement.
    Uses deterministic suitability scoring and distance ranking.
    """
    if latitude is None or longitude is None:
        return {
            "hospital": None,
            "distance_km": None,
            "available": False,
            "trauma_capable": False,
            "icu_available": False,
            "reason": "Hospital recommendation requires valid location coordinates."
        }
    hospitals = get_hospitals()
    if not hospitals:
        return {
            "hospital": None,
            "distance_km": None,
            "available": False,
            "trauma_capable": False,
            "icu_available": False,
            "reason": "No hospital data available."
        }

    eligible_hospitals = []

    for h in hospitals:
        # Extract hospital fields with defaults for defensive handling of missing data
        h_id = h.get("hospital_id")
        h_name = h.get("hospital_name", f"Hospital {h_id}")
        h_lat = h.get("latitude")
        h_lon = h.get("longitude")
        status = (h.get("emergency_status") or "UNKNOWN").upper()
        
        # Parse capacity metrics, converting None/NaN to 0
        def safe_int(val) -> int:
            if val is None:
                return 0
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        avail_beds = safe_int(h.get("available_beds"))
        total_beds = safe_int(h.get("total_beds"))
        icu_beds = safe_int(h.get("icu_beds"))
        avail_icu_beds = safe_int(h.get("available_icu_beds"))
        trauma_cap = safe_int(h.get("trauma_capacity"))
        avail_trauma_beds = safe_int(h.get("available_trauma_beds"))
        ambulance_bay = bool(h.get("ambulance_bay_available", False))
        specialty = (h.get("specialty") or "").lower()

        # Hard filters:
        # 1. Location must be valid
        if h_lat is None or h_lon is None:
            continue
        try:
            h_lat = float(h_lat)
            h_lon = float(h_lon)
        except (ValueError, TypeError):
            continue

        # 2. General availability (Must have available beds & status != CLOSED)
        if avail_beds <= 0 or status == "CLOSED":
            continue

        # 3. ICU requirements
        if requires_icu and avail_icu_beds <= 0:
            continue

        # 4. Trauma requirements
        if requires_trauma and (avail_trauma_beds <= 0 or trauma_cap <= 0):
            continue

        # Calculate distance
        dist = haversine_distance(latitude, longitude, h_lat, h_lon)

        # Suitability Scoring
        # A higher score is more suitable
        suitability_score = 0.0

        # Status priority: OPEN > BUSY > CRITICAL
        if status == "OPEN":
            suitability_score += 10.0
        elif status == "BUSY":
            suitability_score += 5.0
        elif status == "CRITICAL":
            suitability_score += 1.0

        # Specialty matching
        if requires_trauma:
            if "trauma" in specialty or "multi-special" in specialty:
                suitability_score += 5.0
        else:
            if "general emergency" in specialty or "multi-special" in specialty:
                suitability_score += 2.0

        # Ambulance bay availability
        if ambulance_bay:
            suitability_score += 2.0

        # Bed capacity tie-breaker
        if total_beds > 0:
            suitability_score += (avail_beds / float(total_beds))

        eligible_hospitals.append({
            "hospital_id": h_id,
            "hospital_name": h_name,
            "distance_km": round(dist, 2),
            "available": status in ["OPEN", "BUSY", "CRITICAL"],
            "trauma_capable": avail_trauma_beds > 0 and trauma_cap > 0,
            "icu_available": avail_icu_beds > 0,
            "suitability_score": suitability_score,
            "emergency_status": status
        })

    if not eligible_hospitals:
        return {
            "hospital": None,
            "distance_km": None,
            "available": False,
            "trauma_capable": False,
            "icu_available": False,
            "reason": "No available hospitals matching the specified requirements were found."
        }

    # Sort: suitability_score DESC, distance_km ASC
    eligible_hospitals.sort(key=lambda x: (-x["suitability_score"], x["distance_km"]))
    best = eligible_hospitals[0]

    # Build structured reason
    reason_parts = []
    if requires_trauma:
        reason_parts.append("trauma-capable")
    if requires_icu:
        reason_parts.append("ICU capacity")
    if not requires_trauma and not requires_icu:
        reason_parts.append("emergency capacity")

    reqs_desc = " and ".join(reason_parts)
    
    # Simple, clear and informative reason
    if best["emergency_status"] == "OPEN":
        reason = f"Nearest available {reqs_desc} hospital with status OPEN."
    elif best["emergency_status"] == "BUSY":
        reason = f"Nearest available {reqs_desc} hospital (status is BUSY, but beds are available)."
    else:
        reason = f"Nearest available {reqs_desc} hospital (status is CRITICAL/busy, but beds are available)."

    return {
        "hospital": best["hospital_name"],
        "distance_km": best["distance_km"],
        "available": best["available"],
        "trauma_capable": best["trauma_capable"],
        "icu_available": best["icu_available"],
        "reason": reason
    }
