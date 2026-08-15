export interface GeoLocation {
  lat: number;
  lng: number;
}

export interface RouteComputeRequest {
  origin: GeoLocation;
  destination: GeoLocation;
}

export interface RouteComputeResponse {
  origin: GeoLocation;
  destination: GeoLocation;
  points: GeoLocation[];
  distanceMeters: number;
  durationSeconds: number;
  etaMinutes: number;
}

export interface CreateEmergencyPayload {
  citizenId: string;
  location: GeoLocation;
  incidentDescription: string;
  victimCount: number;
  injuryType: string;
}

export interface EmergencyAck {
  emergencyId: string;
  status: string;
  message: string;
  createdAt: string;
}

export interface EmergencySnapshot {
  id: string;
  status: string;
  severity?: string;
  injuryType?: string;
  victimCount?: number;
  location?: GeoLocation;
  assignedAmbulanceId?: string;
  assignedHospitalId?: string;
  assignedHospitalName?: string;
}

export interface AmbulanceRecord {
  id: string;
  vehicleNumber?: string;
  status: string;
  /** Backend returns flat lat/lng, not a nested location object. */
  lat?: number;
  lng?: number;
  driverName?: string;
  driverPhone?: string;
  equipmentLevel?: string;
  emergencyId?: string;
}

export interface HospitalRecord {
  id: string;
  name: string;
  lat?: number;
  lng?: number;
  availableIcuBeds?: number;
  totalIcuBeds?: number;
  specializations?: string;
  phone?: string;
  currentLoadPct?: number;
}

export interface TrafficSignalRecord {
  id: string;
  lat: number;
  lng: number;
  roadSegment?: string;
  currentState: string;
  controlledByCorridorId?: string;
  priorityExpiresAt?: string;
}

export interface DashboardWsEvent {
  type: string;
  emergencyId?: string;
  severity?: string;
  ambulanceId?: string;
  hospitalName?: string;
  hospitalId?: string;
  eta?: number;
  etaMinutes?: number;
  injuryType?: string;
  victimCount?: number;
  location?: GeoLocation;
  [key: string]: unknown;
}
