from contextlib import asynccontextmanager
from typing import Optional, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
import os
import shutil
import tempfile
from services.video_processor import get_video_metadata
from services.frame_processor import process_video_frames
from services.yolo_detector import detect_video_frames
from services.event_interpreter import interpret_detections
from services.vision_incident_adapter import vision_event_to_incident
from services.vision_emergency_pipeline import process_vision_incident_to_command, process_video_to_emergency
from services.vision_orchestrator import process_vision_incident_to_orchestrator

from services.data_loader import (
    DataLoadError,
    get_ambulances,
    get_data_summary,
    get_emergency_scenarios,
    get_hospitals,
    get_incidents,
    load_all_data,
)
from services.hospital_agent import recommend_hospital
from services.ambulance_agent import recommend_ambulance
from services.incident_detection import process_incident
from services.severity_engine import predict_severity
from services.command_agent import generate_response_plan
from services.orchestrator import orchestrate_emergency



@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        load_all_data()
    except FileNotFoundError:
        pass
    except DataLoadError:
        pass
    yield


app = FastAPI(title="AEGIS AI Service", lifespan=lifespan)


@app.get("/")
def root():
    return {
        "service": "AEGIS AI Service",
        "status": "running",
        "phase": "AI Foundation",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/data/summary")
def data_summary():
    try:
        return get_data_summary()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/data/hospitals")
def hospitals():
    try:
        return get_hospitals()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/data/ambulances")
def ambulances():
    try:
        return get_ambulances()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/data/incidents")
def incidents():
    try:
        return get_incidents()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/data/emergency-scenarios")
def emergency_scenarios():
    try:
        return get_emergency_scenarios()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataLoadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --- Pydantic Models for Phase 2 ---

class HospitalRecommendationRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of the incident location")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of the incident location")
    severity: Optional[str] = Field(None, description="Severity level of the incident")
    requires_trauma: bool = Field(False, description="Whether the incident requires trauma capabilities")
    requires_icu: bool = Field(False, description="Whether the incident requires ICU capabilities")


class HospitalRecommendationResponse(BaseModel):
    hospital: Optional[str] = Field(None, description="Recommended hospital name")
    distance_km: Optional[float] = Field(None, description="Distance from the incident in kilometers")
    available: bool = Field(..., description="Availability status of the hospital")
    trauma_capable: bool = Field(..., description="Whether the hospital has trauma capabilities")
    icu_available: bool = Field(..., description="Whether the hospital has ICU capabilities")
    reason: str = Field(..., description="Structured explanation of the recommendation")


class AmbulanceRecommendationRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of the incident location")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of the incident location")
    severity: Optional[str] = Field(None, description="Severity level of the incident")
    required_type: Optional[str] = Field(None, description="Preferred/required ambulance type (ALS, BLS, Trauma)")


class AmbulanceRecommendationResponse(BaseModel):
    ambulance: Optional[str] = Field(None, description="Recommended ambulance ID")
    type: Optional[str] = Field(None, description="Type of the recommended ambulance")
    eta_minutes: Optional[int] = Field(None, description="Estimated ETA in minutes (demo assumption)")
    distance_km: Optional[float] = Field(None, description="Distance to incident in km")
    available: bool = Field(..., description="Availability status of the recommended ambulance")
    reason: str = Field(..., description="Explanation for selection or fallback choice")

class IncidentDetectionRequest(BaseModel):
    incident_type: str = Field(..., description="Type of the incident (e.g., ROAD_ACCIDENT, FIRE, etc.)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of the incident")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of the incident")
    casualties: Optional[int] = Field(None, ge=0, description="Number of casualties")
    fire: Optional[bool] = Field(None, description="Whether fire is present")
    road_blocked: Optional[bool] = Field(None, description="Whether the road is blocked")
    vehicles: Optional[int] = Field(None, ge=0, description="Number of vehicles involved")
    incident_id: Optional[str] = Field(None, description="Supplied incident ID to validate and preserve")
    timestamp: Optional[str] = Field(None, description="Timestamp of the incident")
    source: Optional[str] = Field(None, description="Source of the incident report")


class IncidentDetectionResponse(BaseModel):
    incident_id: str = Field(..., description="Validated or generated incident ID")
    incident_type: str = Field(..., description="Normalized incident type")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    casualties: int = Field(..., description="Validated casualty count")
    fire: bool = Field(..., description="Whether fire is present")
    road_blocked: bool = Field(..., description="Whether the road is blocked")
    vehicles: int = Field(..., description="Validated vehicle count")
    timestamp: str = Field(..., description="ISO timestamp")
    source: str = Field(..., description="Normalized source of the incident")


class SeverityPredictionRequest(BaseModel):
    incident_type: str = Field(..., description="Type of the incident (e.g., ROAD_ACCIDENT, FIRE, etc.)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of the incident location")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of the incident location")
    casualties: Optional[int] = Field(None, ge=0, description="Number of casualties")
    fire: Optional[bool] = Field(None, description="Whether fire is present")
    road_blocked: Optional[bool] = Field(None, description="Whether the road is blocked")
    vehicles: Optional[int] = Field(None, ge=0, description="Number of vehicles involved")
    incident_id: Optional[str] = Field(None, description="Preserved incident ID, if originally provided")
    timestamp: Optional[str] = Field(None, description="Timestamp of the incident")
    source: Optional[str] = Field(None, description="Source of the incident report")


class SeverityPredictionResponse(BaseModel):
    severity: str = Field(..., description="Predicted severity level (LOW, MEDIUM, HIGH, CRITICAL)")
    score: int = Field(..., description="Deterministic evaluation score")
    factors: list[str] = Field(..., description="List of factors contributing to severity")
    reason: str = Field(..., description="Deterministic natural explanation of the severity prediction")
    incident_id: Optional[str] = Field(None, description="Preserved incident ID, if originally provided")


class CommandPlanRequest(BaseModel):
    incident: IncidentDetectionRequest = Field(..., description="Structured incident report details")
    severity: str = Field(..., description="Severity level of the incident (LOW, MEDIUM, HIGH, CRITICAL)")


class CommandPlanResponse(BaseModel):
    incident_type: str = Field(..., description="Standardized incident type")
    severity: str = Field(..., description="Severity level of the incident")
    response_priority: str = Field(..., description="Response priority (ROUTINE, PRIORITY, URGENT, IMMEDIATE)")
    required_actions: list[str] = Field(..., description="List of actions to initiate")
    required_resources: list[str] = Field(..., description="List of resource categories required")
    reason: str = Field(..., description="Factual description/justification of the plan")


class OrchestrationRequest(BaseModel):
    incident_type: str = Field(..., description="Type of the incident (e.g., ROAD_ACCIDENT, FIRE, etc.)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of the incident")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of the incident")
    casualties: Optional[int] = Field(None, ge=0, description="Number of casualties")
    fire: Optional[bool] = Field(None, description="Whether fire is present")
    road_blocked: Optional[bool] = Field(None, description="Whether the road is blocked")
    vehicles: Optional[int] = Field(None, ge=0, description="Number of vehicles involved")
    incident_id: Optional[str] = Field(None, description="Supplied incident ID to validate and preserve")
    timestamp: Optional[str] = Field(None, description="Timestamp of the incident")
    source: Optional[str] = Field(None, description="Source of the incident report")
    required_type: Optional[str] = Field(None, description="Preferred/required ambulance type (ALS, BLS, Trauma)")
    requires_trauma: Optional[bool] = Field(None, description="Whether the incident requires trauma capabilities")
    requires_icu: Optional[bool] = Field(None, description="Whether the incident requires ICU capabilities")


class ResourceCoordinationDetail(BaseModel):
    required: bool
    status: str
    recommendation: Optional[Any] = None


class ResourceCoordinationMap(BaseModel):
    ambulance: ResourceCoordinationDetail
    hospital: ResourceCoordinationDetail
    traffic_police: ResourceCoordinationDetail
    fire_unit: ResourceCoordinationDetail


class OrchestrationReasoningResponse(BaseModel):
    incident_reason: str
    severity_reason: str
    command_reason: str
    ambulance_reason: str
    hospital_reason: str
    resource_reason: str
    orchestration_reason: str
    overall_reason: str


class DecisionTraceRecord(BaseModel):
    decision_id: str
    decision_type: str
    source_agent: str
    inputs: dict
    factors: list[str]
    decision: Optional[Any] = None
    reason: str
    timestamp: str


class OrchestrationResponse(BaseModel):
    incident: IncidentDetectionResponse
    severity: SeverityPredictionResponse
    command: CommandPlanResponse
    ambulance: Optional[AmbulanceRecommendationResponse] = None
    ambulance_status: str
    hospital: Optional[HospitalRecommendationResponse] = None
    hospital_status: str
    agents_called: list[str]
    agents_skipped: list[str]
    resource_coordination: ResourceCoordinationMap
    reasoning: OrchestrationReasoningResponse
    decision_trace: list[DecisionTraceRecord]
    orchestration_status: str


class VideoInspectionResponse(BaseModel):
    filename: str
    readable: bool
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None
    duration_seconds: Optional[float] = None
    error_detail: Optional[str] = None


class ProcessedFrameMetadata(BaseModel):
    frame_index: int
    timestamp_seconds: Optional[float] = None
    width: int
    height: int


class VideoProcessingResponse(BaseModel):
    success: bool
    filename: str
    frames_processed: int
    source_fps: Optional[float] = None
    frame_interval: int
    frames: list[ProcessedFrameMetadata]
    error_detail: Optional[str] = None


class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class ObjectDetectionRecord(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: BBox


class FrameObjectDetections(BaseModel):
    frame_index: int
    timestamp_seconds: Optional[float] = None
    detections: list[ObjectDetectionRecord]


class VideoDetectionResponse(BaseModel):
    success: bool
    filename: str
    model: Optional[str] = None
    frames_processed: int
    detections: list[FrameObjectDetections]
    error_detail: Optional[str] = None


class FrameDetectionInput(BaseModel):
    frame_index: int
    timestamp_seconds: Optional[float] = None
    detections: list[ObjectDetectionRecord]


class EventInterpretationRequest(BaseModel):
    frames: Optional[list[FrameDetectionInput]] = None
    detections: Optional[list[FrameDetectionInput]] = None


class ObjectSummary(BaseModel):
    vehicles: int
    persons: int
    motorcycles: int
    buses: int
    trucks: int
    cars: int
    bicycles: int


class EventInterpretationResponse(BaseModel):
    event_type: str
    event_score: int
    evidence: list[str]
    object_summary: ObjectSummary
    frames_analyzed: int
    first_timestamp_seconds: Optional[float] = None
    last_timestamp_seconds: Optional[float] = None
    reason: str


class CameraMetadata(BaseModel):
    camera_id: Optional[str] = None
    camera_location: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class VisionObjectSummary(BaseModel):
    vehicles: int
    persons: int
    motorcycles: int
    buses: int
    trucks: int
    cars: int
    bicycles: int


class VisionEventInput(BaseModel):
    event_type: str
    event_score: int
    evidence: list[str]
    object_summary: Optional[VisionObjectSummary] = None
    frames_analyzed: int
    first_timestamp_seconds: Optional[float] = None
    last_timestamp_seconds: Optional[float] = None
    reason: str


class VisionIncidentCreateRequest(BaseModel):
    event: VisionEventInput
    camera: Optional[CameraMetadata] = None


class VisionIncidentDetail(BaseModel):
    incident_id: str
    incident_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    casualties: int
    fire: bool
    road_blocked: bool
    vehicles: int
    timestamp: str
    source: str


class VisionContextResponse(BaseModel):
    event_type: str
    event_score: int
    frames_analyzed: int
    camera_id: Optional[str] = None


class VisionIncidentCreateResponse(BaseModel):
    incident_created: bool
    incident: Optional[VisionIncidentDetail] = None
    vision_context: Optional[VisionContextResponse] = None
    reason: str


class SeverityDetailResponse(BaseModel):
    severity: str
    score: int
    factors: list[str]
    reason: str
    incident_id: Optional[str] = None


class CommandDetailResponse(BaseModel):
    incident_type: str
    severity: str
    response_priority: str
    required_actions: list[str]
    required_resources: list[str]
    reason: str


class VisionIncidentProcessResponse(BaseModel):
    incident_created: bool
    incident: Optional[VisionIncidentDetail] = None
    severity: Optional[SeverityDetailResponse] = None
    command: Optional[CommandDetailResponse] = None
    pipeline_status: str
    reason: str


class VisionOrchestrationResponse(BaseModel):
    incident_created: bool
    incident: Optional[VisionIncidentDetail] = None
    severity: Optional[SeverityDetailResponse] = None
    command: Optional[CommandDetailResponse] = None
    ambulance: Optional[AmbulanceRecommendationResponse] = None
    ambulance_status: str
    hospital: Optional[HospitalRecommendationResponse] = None
    hospital_status: str
    agents_called: list[str]
    agents_skipped: list[str]
    resource_coordination: Optional[ResourceCoordinationMap] = None
    reasoning: Optional[OrchestrationReasoningResponse] = None
    decision_trace: list[DecisionTraceRecord]
    orchestration_status: str
    pipeline_status: str
    reason: str


class VideoDetail(BaseModel):
    filename: str
    frames_processed: int
    source_fps: Optional[float] = None


class VisionEmergencyOrchestrationDetail(BaseModel):
    severity: SeverityDetailResponse
    command: CommandDetailResponse
    ambulance: Optional[AmbulanceRecommendationResponse] = None
    ambulance_status: str
    hospital: Optional[HospitalRecommendationResponse] = None
    hospital_status: str
    resource_coordination: ResourceCoordinationMap
    orchestration_status: str


class VisionEmergencyProcessResponse(BaseModel):
    success: bool
    video: Optional[VideoDetail] = None
    vision_event: Optional[EventInterpretationResponse] = None
    incident_created: bool
    incident: Optional[VisionIncidentDetail] = None
    emergency_response: Optional[VisionEmergencyOrchestrationDetail] = None
    reasoning: Optional[OrchestrationReasoningResponse] = None
    decision_trace: Optional[list[DecisionTraceRecord]] = None
    pipeline_status: str
    reason: str


# --- Phase 2 Endpoints ---

@app.post("/agents/hospital/recommend", response_model=HospitalRecommendationResponse)
def recommend_hospital_endpoint(req: HospitalRecommendationRequest):
    try:
        return recommend_hospital(
            latitude=req.latitude,
            longitude=req.longitude,
            severity=req.severity,
            requires_trauma=req.requires_trauma,
            requires_icu=req.requires_icu
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/agents/ambulance/recommend", response_model=AmbulanceRecommendationResponse)
def recommend_ambulance_endpoint(req: AmbulanceRecommendationRequest):
    try:
        return recommend_ambulance(
            latitude=req.latitude,
            longitude=req.longitude,
            severity=req.severity,
            required_type=req.required_type
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/incidents/detect", response_model=IncidentDetectionResponse)
def detect_incident_endpoint(req: IncidentDetectionRequest):
    try:
        payload = req.dict(exclude_none=True)
        return process_incident(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/incidents/severity", response_model=SeverityPredictionResponse)
def predict_severity_endpoint(req: SeverityPredictionRequest):
    try:
        payload = req.dict(exclude_none=True)
        return predict_severity(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/agents/command/plan", response_model=CommandPlanResponse)
def generate_response_plan_endpoint(req: CommandPlanRequest):
    try:
        # Pass the incident sub-dict and severity directly
        payload = req.incident.dict(exclude_none=True)
        return generate_response_plan(payload, req.severity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/agents/orchestrate", response_model=OrchestrationResponse)
def orchestrate_endpoint(req: OrchestrationRequest):
    try:
        payload = req.dict(exclude_none=True)
        return orchestrate_emergency(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/vision/video/inspect", response_model=VideoInspectionResponse)
def inspect_video_endpoint(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".mp4", ".avi", ".mkv", ".mov", ".flv", ".webm"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension: {ext}"
        )
        
    suffix = ext
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        try:
            shutil.copyfileobj(file.file, tmp)
        except Exception as exc:
            os.unlink(tmp_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save temporary upload: {str(exc)}"
            )

    try:
        meta = get_video_metadata(tmp_path)
        meta["filename"] = file.filename
        return meta
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/vision/video/process", response_model=VideoProcessingResponse)
def process_video_endpoint(
    file: UploadFile = File(...),
    frame_interval: int = Form(1),
    max_frames: int = Form(30),
    resize_width: Optional[int] = Form(None),
    resize_height: Optional[int] = Form(None)
):
    if frame_interval < 1:
        raise HTTPException(status_code=400, detail="frame_interval must be >= 1")
    if max_frames < 1:
        raise HTTPException(status_code=400, detail="max_frames must be >= 1")
    if resize_width is not None and resize_width <= 0:
        raise HTTPException(status_code=400, detail="resize_width must be > 0")
    if resize_height is not None and resize_height <= 0:
        raise HTTPException(status_code=400, detail="resize_height must be > 0")
    if (resize_width is not None and resize_height is None) or (resize_width is None and resize_height is not None):
        raise HTTPException(status_code=400, detail="Both resize_width and resize_height must be provided together.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".mp4", ".avi", ".mkv", ".mov", ".flv", ".webm"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension: {ext}"
        )
        
    suffix = ext
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        try:
            shutil.copyfileobj(file.file, tmp)
        except Exception as exc:
            os.unlink(tmp_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save temporary upload: {str(exc)}"
            )

    try:
        result = process_video_frames(
            path=tmp_path,
            frame_interval=frame_interval,
            max_frames=max_frames,
            resize_width=resize_width,
            resize_height=resize_height
        )
        result["filename"] = file.filename
        return result
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/vision/yolo/detect", response_model=VideoDetectionResponse)
def yolo_detect_endpoint(
    file: UploadFile = File(...),
    frame_interval: int = Form(1),
    max_frames: int = Form(30),
    confidence_threshold: float = Form(0.25),
    resize_width: Optional[int] = Form(None),
    resize_height: Optional[int] = Form(None)
):
    if frame_interval < 1:
        raise HTTPException(status_code=400, detail="frame_interval must be >= 1")
    if max_frames < 1:
        raise HTTPException(status_code=400, detail="max_frames must be >= 1")
    if not (0.0 <= confidence_threshold <= 1.0):
        raise HTTPException(status_code=400, detail="confidence_threshold must be between 0.0 and 1.0")
    if resize_width is not None and resize_width <= 0:
        raise HTTPException(status_code=400, detail="resize_width must be > 0")
    if resize_height is not None and resize_height <= 0:
        raise HTTPException(status_code=400, detail="resize_height must be > 0")
    if (resize_width is not None and resize_height is None) or (resize_width is None and resize_height is not None):
        raise HTTPException(status_code=400, detail="Both resize_width and resize_height must be provided together.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".mp4", ".avi", ".mkv", ".mov", ".flv", ".webm"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension: {ext}"
        )
        
    suffix = ext
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        try:
            shutil.copyfileobj(file.file, tmp)
        except Exception as exc:
            os.unlink(tmp_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save temporary upload: {str(exc)}"
            )

    try:
        result = detect_video_frames(
            path=tmp_path,
            frame_interval=frame_interval,
            max_frames=max_frames,
            confidence_threshold=confidence_threshold,
            resize_width=resize_width,
            resize_height=resize_height
        )
        result["filename"] = file.filename
        return result
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/vision/events/interpret", response_model=EventInterpretationResponse)
def interpret_vision_events_endpoint(req: EventInterpretationRequest):
    frames_list = req.frames if req.frames is not None else req.detections
    if frames_list is None:
        raise HTTPException(
            status_code=400,
            detail="Either 'frames' or 'detections' list must be provided in the request body."
        )
    try:
        frame_dicts = []
        for f in frames_list:
            frame_dicts.append(f.dict(exclude_none=True))
            
        return interpret_detections(frame_dicts)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/vision/incidents/create", response_model=VisionIncidentCreateResponse)
def create_vision_incident_endpoint(req: VisionIncidentCreateRequest):
    try:
        event_dict = req.event.dict(exclude_none=True)
        camera_dict = req.camera.dict(exclude_none=True) if req.camera else None
        
        result = vision_event_to_incident(event_dict, camera_dict)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/vision/incidents/process", response_model=VisionIncidentProcessResponse)
def process_vision_incident_endpoint(req: VisionIncidentCreateRequest):
    try:
        event_dict = req.event.dict(exclude_none=True)
        camera_dict = req.camera.dict(exclude_none=True) if req.camera else None
        
        result = process_vision_incident_to_command(event_dict, camera_dict)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/vision/incidents/orchestrate", response_model=VisionOrchestrationResponse)
def orchestrate_vision_incident_endpoint(req: VisionIncidentCreateRequest):
    try:
        event_dict = req.event.dict(exclude_none=True)
        camera_dict = req.camera.dict(exclude_none=True) if req.camera else None
        
        result = process_vision_incident_to_orchestrator(event_dict, camera_dict)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/vision/emergency/process", response_model=VisionEmergencyProcessResponse)
def process_vision_emergency_endpoint(
    file: UploadFile = File(...),
    camera_id: Optional[str] = Form(None),
    camera_location: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    frame_interval: int = Form(1),
    max_frames: int = Form(30),
    confidence_threshold: float = Form(0.25),
    resize_width: Optional[int] = Form(None),
    resize_height: Optional[int] = Form(None)
):
    # Validations
    if frame_interval < 1:
        raise HTTPException(status_code=400, detail="frame_interval must be >= 1")
    if max_frames < 1:
        raise HTTPException(status_code=400, detail="max_frames must be >= 1")
    if not (0.0 <= confidence_threshold <= 1.0):
        raise HTTPException(status_code=400, detail="confidence_threshold must be between 0.0 and 1.0")
    if latitude is not None and not (-90.0 <= latitude <= 90.0):
        raise HTTPException(status_code=422, detail="Latitude must be between -90.0 and 90.0")
    if longitude is not None and not (-180.0 <= longitude <= 180.0):
        raise HTTPException(status_code=422, detail="Longitude must be between -180.0 and 180.0")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".mp4", ".avi", ".mkv", ".mov", ".flv", ".webm"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")

    camera_metadata = None
    if camera_id or camera_location or (latitude is not None) or (longitude is not None):
        camera_metadata = {
            "camera_id": camera_id,
            "camera_location": camera_location,
            "latitude": latitude,
            "longitude": longitude
        }

    suffix = ext
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        try:
            shutil.copyfileobj(file.file, tmp)
        except Exception as exc:
            os.unlink(tmp_path)
            raise HTTPException(status_code=500, detail=f"Failed to save temporary upload: {str(exc)}")

    try:
        res = process_video_to_emergency(
            video_path=tmp_path,
            filename=file.filename,
            camera_metadata=camera_metadata,
            frame_interval=frame_interval,
            max_frames=max_frames,
            confidence_threshold=confidence_threshold,
            resize_width=resize_width,
            resize_height=resize_height
        )
        return res
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)




