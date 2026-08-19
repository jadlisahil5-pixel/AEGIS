# AEGIS-AI Stable API Contracts

This document contains the frozen API contracts for the FastAPI emergency intelligence backend, designed to be consumed by the Spring Boot integration layer.

---

## Health & Data Foundation APIs

### 1. GET `/health`
*   **Purpose**: Service health check.
*   **Content-Type**: `application/json`
*   **Response Fields**:
    *   `status`: `string` (e.g., `"healthy"`)
*   **HTTP Error Codes**: `500` (internal server errors)
*   **Example Response**:
    ```json
    {"status": "healthy"}
    ```

### 2. GET `/data/summary`
*   **Purpose**: Get summary of loaded static data.
*   **Content-Type**: `application/json`
*   **Response Fields**:
    *   `hospitals`: `int` (count of hospitals)
    *   `ambulances`: `int` (count of ambulances)
    *   `incidents`: `int` (count of historical incidents)
    *   `emergency_scenarios`: `int` (count of scenarios)
*   **HTTP Error Codes**: `404` (missing excel dataset), `500` (parse/read failure)
*   **Example Response**:
    ```json
    {
      "hospitals": 5,
      "ambulances": 10,
      "incidents": 25,
      "emergency_scenarios": 15
    }
    ```

---

## Core Emergency Recommendation & Orchestration APIs

### 3. POST `/agents/hospital/recommend`
*   **Purpose**: Recommend nearest available hospital matching capabilities.
*   **Content-Type**: `application/json`
*   **Request Schema**:
    *   `latitude`: `float` (Required, validation: `-90.0 <= lat <= 90.0`)
    *   `longitude`: `float` (Required, validation: `-180.0 <= lon <= 180.0`)
    *   `severity`: `string` (Optional)
    *   `requires_trauma`: `boolean` (Optional, default: `false`)
    *   `requires_icu`: `boolean` (Optional, default: `false`)
*   **Response Schema**:
    *   `hospital`: `string` or `null`
    *   `distance_km`: `float` or `null`
    *   `available`: `boolean`
    *   `trauma_capable`: `boolean`
    *   `icu_available`: `boolean`
    *   `reason`: `string`
*   **Example Request**:
    ```json
    {
      "latitude": 28.62,
      "longitude": 77.36,
      "requires_trauma": true
    }
    ```
*   **Example Response**:
    ```json
    {
      "hospital": "Green Valley Medical Centre",
      "distance_km": 8.36,
      "available": true,
      "trauma_capable": true,
      "icu_available": true,
      "reason": "Nearest available trauma-capable hospital with status OPEN."
    }
    ```

### 4. POST `/agents/ambulance/recommend`
*   **Purpose**: Recommend nearest available ambulance matching preferred type.
*   **Content-Type**: `application/json`
*   **Request Schema**:
    *   `latitude`: `float` (Required, validation: `-90.0 <= lat <= 90.0`)
    *   `longitude`: `float` (Required, validation: `-180.0 <= lon <= 180.0`)
    *   `severity`: `string` (Optional)
    *   `required_type`: `string` (Optional, e.g. `"ALS"`, `"BLS"`, `"Trauma"`)
*   **Response Schema**:
    *   `ambulance`: `string` or `null`
    *   `type`: `string` or `null`
    *   `eta_minutes`: `int` or `null`
    *   `distance_km`: `float` or `null`
    *   `available`: `boolean`
    *   `reason`: `string`
*   **Example Request**:
    ```json
    {
      "latitude": 28.62,
      "longitude": 77.36,
      "required_type": "ALS"
    }
    ```
*   **Example Response**:
    ```json
    {
      "ambulance": "AMB-011",
      "type": "ALS",
      "eta_minutes": 15,
      "distance_km": 8.36,
      "available": true,
      "reason": "Nearest available ALS ambulance selected."
    }
    ```

### 5. POST `/incidents/detect`
*   **Purpose**: Validate and normalize a raw incident report.
*   **Content-Type**: `application/json`
*   **Request Schema**:
    *   `incident_type`: `string` (Required)
    *   `latitude`: `float` (Required, validation: `-90.0 <= lat <= 90.0`)
    *   `longitude`: `float` (Required, validation: `-180.0 <= lon <= 180.0`)
    *   `casualties`: `int` (Optional, validation: `>= 0`)
    *   `fire`: `boolean` (Optional)
    *   `road_blocked`: `boolean` (Optional)
    *   `vehicles`: `int` (Optional, validation: `>= 0`)
    *   `incident_id`: `string` (Optional)
    *   `timestamp`: `string` (Optional)
    *   `source`: `string` (Optional)
*   **Response Schema**:
    *   `incident_id`: `string`
    *   `incident_type`: `string`
    *   `latitude`: `float`
    *   `longitude`: `float`
    *   `casualties`: `int`
    *   `fire`: `boolean`
    *   `road_blocked`: `boolean`
    *   `vehicles`: `int`
    *   `timestamp`: `string` (ISO 8601 format)
    *   `source`: `string`
*   **HTTP Error Codes**: `400` (validation failure), `422` (out-of-bounds coords), `500` (internal error)
*   **Example Request**:
    ```json
    {
      "incident_type": "vehicle collision",
      "latitude": 28.62,
      "longitude": 77.36,
      "vehicles": 2
    }
    ```
*   **Example Response**:
    ```json
    {
      "incident_id": "INC-20260818-001",
      "incident_type": "ROAD_ACCIDENT",
      "latitude": 28.62,
      "longitude": 77.36,
      "casualties": 0,
      "fire": false,
      "road_blocked": false,
      "vehicles": 2,
      "timestamp": "2026-08-18T22:45:00",
      "source": "SYSTEM"
    }
    ```

### 6. POST `/agents/orchestrate`
*   **Purpose**: Run E2E emergency coordination (classification $\rightarrow$ severity $\rightarrow$ plan $\rightarrow$ ambulance allocation $\rightarrow$ hospital allocation $\rightarrow$ reasoning $\rightarrow$ decision tracing).
*   **Content-Type**: `application/json`
*   **Request Schema**: Same parameters as `/incidents/detect` + optional coordination parameters:
    *   `required_type`: `string` (Optional)
    *   `requires_trauma`: `boolean` (Optional)
    *   `requires_icu`: `boolean` (Optional)
*   **Response Schema**:
    *   `incident`: IncidentDetectionResponse
    *   `severity`: SeverityPredictionResponse
    *   `command`: CommandPlanResponse
    *   `ambulance`: AmbulanceRecommendationResponse or `null`
    *   `ambulance_status`: `string` (`"ALLOCATED"`, `"NO_SUITABLE_AMBULANCE"`, `"SKIPPED"`)
    *   `hospital`: HospitalRecommendationResponse or `null`
    *   `hospital_status`: `string` (`"RECOMMENDED"`, `"NO_SUITABLE_HOSPITAL"`, `"SKIPPED"`)
    *   `agents_called`: `list[string]`
    *   `agents_skipped`: `list[string]`
    *   `resource_coordination`:
        *   `ambulance`/`hospital`/`traffic_police`/`fire_unit`:
            *   `required`: `boolean`
            *   `status`: `string` (`"ALLOCATED"`, `"RECOMMENDED"`, `"NO_SUITABLE_AMBULANCE"`, `"NO_SUITABLE_HOSPITAL"`, `"NOT_IMPLEMENTED"`, `"SKIPPED"`)
            *   `recommendation`: Optional details
    *   `reasoning`:
        *   `incident_reason`/`severity_reason`/`command_reason`/`ambulance_reason`/`hospital_reason`/`resource_reason`/`orchestration_reason`/`overall_reason`: `string`
    *   `decision_trace`: list of `DecisionTraceRecord`:
        *   `decision_id`: `string`
        *   `decision_type`: `string`
        *   `source_agent`: `string`
        *   `inputs`: `dict`
        *   `factors`: `list[string]`
        *   `decision`: `any`
        *   `reason`: `string`
        *   `timestamp`: `string`
    *   `orchestration_status`: `string` (`"FULLY_COORDINATED"`, `"PARTIALLY_COORDINATED"`, `"RESOURCE_UNAVAILABLE"`)
*   **HTTP Error Codes**: `400` (validation failure), `422` (out-of-bounds coords), `500` (internal error)

---

## Vision & CCTV Processing APIs

### 7. POST `/vision/emergency/process`
*   **Purpose**: The primary entry-point for camera footage ingestion. Uploads a video file, performs sampling, object detection, aggregates event interpreter patterns, converts to incident adapter, and runs standard orchestrator.
*   **Content-Type**: `multipart/form-data`
*   **Request Form Fields**:
    *   `file`: `UploadFile` (Required, binary video stream)
    *   `camera_id`: `string` (Optional)
    *   `camera_location`: `string` (Optional)
    *   `latitude`: `float` (Optional, validation: `-90.0 <= lat <= 90.0`)
    *   `longitude`: `float` (Optional, validation: `-180.0 <= lon <= 180.0`)
    *   `frame_interval`: `int` (Optional, validation: `>= 1`, default: `1`)
    *   `max_frames`: `int` (Optional, validation: `>= 1`, default: `30`)
    *   `confidence_threshold`: `float` (Optional, validation: `0.0 <= threshold <= 1.0`, default: `0.25`)
    *   `resize_width`: `int` (Optional, validation: `> 0`)
    *   `resize_height`: `int` (Optional, validation: `> 0`)
*   **Response Schema**:
    *   `success`: `boolean`
    *   `video`: Optional:
        *   `filename`: `string`
        *   `frames_processed`: `int`
        *   `source_fps`: `float` or `null`
    *   `vision_event`: Optional EventInterpretationResponse (summarizing YOLO detections and persistent frame objects)
    *   `incident_created`: `boolean` (stops if `false` for `NO_SIGNIFICANT_EVENT` scenarios)
    *   `incident`: Optional VisionIncidentDetail
    *   `emergency_response`: Optional:
        *   `severity`: SeverityDetailResponse
        *   `command`: CommandDetailResponse
        *   `ambulance`: AmbulanceRecommendationResponse or `null`
        *   `ambulance_status`: `string`
        *   `hospital`: HospitalRecommendationResponse or `null`
        *   `hospital_status`: `string`
        *   `resource_coordination`: ResourceCoordinationMap
        *   `orchestration_status`: `string`
    *   `reasoning`: Optional OrchestrationReasoningResponse
    *   `decision_trace`: Optional list of `DecisionTraceRecord`
    *   `pipeline_status`: `string` (`"COMPLETED"`, `"NO_INCIDENT_CREATED"`)
    *   `reason`: `string`
*   **Validation Failures**:
    *   Invalid coordinates (latitude=150.0) -> HTTP `422 Unprocessable Entity`
    *   Invalid frame interval / max frames / confidence -> HTTP `400 Bad Request`
    *   Unsupported file format (.txt) -> HTTP `400 Bad Request`
*   **Example Response (Incident Created)**:
    ```json
    {
      "success": true,
      "video": {
        "filename": "traffic_demo.mp4",
        "frames_processed": 5,
        "source_fps": 10.0
      },
      "vision_event": {
        "event_type": "POSSIBLE_ROAD_INCIDENT",
        "event_score": 3,
        "evidence": ["Multiple vehicles detected (count: 3)", "Persons detected (count: 1)", "Vehicle pattern persisted across 3 frames"],
        "object_summary": {"vehicles": 3, "persons": 1, "motorcycles": 0, "buses": 0, "trucks": 0, "cars": 3, "bicycles": 0},
        "frames_analyzed": 5,
        "reason": "Multiple vehicles and persons were detected persistently across sampled frames."
      },
      "incident_created": true,
      "incident": {
        "incident_id": "INC-20260818-010",
        "incident_type": "ROAD_ACCIDENT",
        "latitude": 28.62,
        "longitude": 77.36,
        "casualties": 0,
        "fire": false,
        "road_blocked": false,
        "vehicles": 3,
        "timestamp": "2026-08-18T22:45:00",
        "source": "VISION"
      },
      "emergency_response": {
        "severity": {
          "severity": "HIGH",
          "score": 5,
          "factors": ["multiple vehicles", "road blockage"],
          "reason": "Road blockage and multiple vehicles indicate a high-severity emergency."
        },
        "command": {
          "incident_type": "ROAD_ACCIDENT",
          "severity": "HIGH",
          "response_priority": "URGENT",
          "required_actions": ["DISPATCH_AMBULANCE", "ALERT_HOSPITAL", "ALERT_TRAFFIC_POLICE", "MANAGE_TRAFFIC"],
          "required_resources": ["AMBULANCE", "HOSPITAL", "TRAFFIC_POLICE"],
          "reason": "High road accident requires urgent response."
        },
        "ambulance": {
          "ambulance": "AMB-011",
          "type": "ALS",
          "eta_minutes": 15,
          "distance_km": 8.36,
          "available": true,
          "reason": "Nearest available ALS ambulance selected."
        },
        "ambulance_status": "ALLOCATED",
        "hospital": {
          "hospital": "Green Valley Medical Centre",
          "distance_km": 20.01,
          "available": true,
          "trauma_capable": true,
          "icu_available": true,
          "reason": "Nearest available emergency capacity hospital."
        },
        "hospital_status": "RECOMMENDED",
        "resource_coordination": {
          "ambulance": {"required": true, "status": "ALLOCATED"},
          "hospital": {"required": true, "status": "RECOMMENDED"},
          "traffic_police": {"required": true, "status": "NOT_IMPLEMENTED"},
          "fire_unit": {"required": false, "status": "SKIPPED"}
        },
        "orchestration_status": "PARTIALLY_COORDINATED"
      },
      "reasoning": {
        "incident_reason": "Incident type 'ROAD_ACCIDENT' was already normalized.",
        "severity_reason": "Road blockage and multiple vehicles indicate a high-severity emergency.",
        "command_reason": "Command plan generated.",
        "ambulance_reason": "Ambulance 'AMB-011' allocated.",
        "hospital_reason": "Hospital 'Green Valley Medical Centre' recommended.",
        "resource_reason": "Ambulance: ALLOCATED. Hospital: RECOMMENDED. Traffic Police: NOT_IMPLEMENTED.",
        "orchestration_reason": "Some resources coordinated.",
        "overall_reason": "Urgent response required."
      },
      "decision_trace": [
        {
          "decision_id": "DEC-INC-20260818-010-01",
          "decision_type": "INCIDENT_CLASSIFICATION",
          "source_agent": "IncidentDetection",
          "inputs": {"incident_type": "ROAD_ACCIDENT"},
          "factors": ["normalization"],
          "decision": "ROAD_ACCIDENT",
          "reason": "Preserved incident type.",
          "timestamp": "2026-08-18T22:45:00"
        }
      ],
      "pipeline_status": "COMPLETED",
      "reason": "Vision input was processed through the complete AEGIS emergency response pipeline."
    }
    ```

---

## Full Endpoints Index Table

| Method | Route | Request Type | Response Type | Validation Rules | Error Codes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/health` | None | `{"status": "healthy"}` | None | 500 |
| **GET** | `/data/summary` | None | `dict` | None | 404, 500 |
| **GET** | `/data/hospitals` | None | `list[dict]` | None | 404, 500 |
| **GET** | `/data/ambulances` | None | `list[dict]` | None | 404, 500 |
| **GET** | `/data/incidents` | None | `list[dict]` | None | 404, 500 |
| **GET** | `/data/emergency-scenarios` | None | `list[dict]` | None | 404, 500 |
| **POST** | `/incidents/detect` | `json` | `IncidentDetectionResponse` | `latitude` `longitude` ranges | 400, 422, 500 |
| **POST** | `/incidents/severity` | `json` | `SeverityPredictionResponse` | `casualties` `>=0` | 400, 500 |
| **POST** | `/agents/command/plan` | `json` | `CommandPlanResponse` | Valid incident dictionary | 400, 500 |
| **POST** | `/agents/ambulance/recommend` | `json` | `AmbulanceRecommendationResponse` | Coordinates range | 422, 500 |
| **POST** | `/agents/hospital/recommend` | `json` | `HospitalRecommendationResponse` | Coordinates range | 422, 500 |
| **POST** | `/agents/orchestrate` | `json` | `OrchestrationResponse` | Valid payload | 400, 422, 500 |
| **POST** | `/vision/video/inspect` | `multipart` | `VideoInspectionResponse` | Video extensions check | 400, 500 |
| **POST** | `/vision/video/process` | `multipart` | `VideoProcessingResponse` | `frame_interval >= 1`, `max_frames >= 1` | 400, 500 |
| **POST** | `/vision/yolo/detect` | `multipart` | `VideoDetectionResponse` | `confidence_threshold` in `[0,1]` | 400, 500 |
| **POST** | `/vision/events/interpret` | `json` | `EventInterpretationResponse` | `frames`/`detections` presence | 400, 500 |
| **POST** | `/vision/incidents/create` | `json` | `VisionIncidentCreateResponse` | Event fields present | 500 |
| **POST** | `/vision/incidents/process` | `json` | `VisionIncidentProcessResponse` | Event fields present | 500 |
| **POST** | `/vision/incidents/orchestrate` | `json` | `VisionOrchestrationResponse` | Event fields present | 500 |
| **POST** | `/vision/emergency/process` | `multipart` | `VisionEmergencyProcessResponse` | Interval, max_frames, coordinate boundaries | 400, 422, 500 |
