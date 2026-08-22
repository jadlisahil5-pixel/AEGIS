import { useEffect, useState, useRef } from "react";

export type SimulationState = "idle" | "running" | "paused";

export interface PoliceUnit {
  id: string;
  lat: number;
  lng: number;
}

export interface RoutePoint {
  lat: number;
  lng: number;
}

export interface CommandIncident {
  id: string;
  type: string;
  severity: string;
  status: string;
  location: string;
  lat: number;
  lng: number;
  assignedUnit?: string;
}

export interface CommandAmbulance {
  id: string;
  callsign: string;
  driver: string;
  status: string;
  lat: number;
  lng: number;
  speed: number;
}

export interface HospitalRecord {
  id: string;
  name: string;
  lat: number;
  lng: number;
  totalIcuBeds: number;
  availableIcuBeds: number;
  emergencyLevel: string;
}

export interface CorridorStatus {
  active: boolean;
  signalIds: string[];
}

export interface ScenarioPayload {
  incident: CommandIncident;
  hospital: HospitalRecord;
  ambulance: CommandAmbulance;
  triggerGreenCorridor: boolean;
}

export interface DigitalTwinState {
  incidents: CommandIncident[];
  incident: CommandIncident | null;
  ambulances: CommandAmbulance[];
  police: PoliceUnit[]; 
  hospitals: HospitalRecord[];
  trafficSignals: any[];
  activeRoute: RoutePoint[] | null;
  routeError: string | null;
  greenCorridor: CorridorStatus;
  simulationState: SimulationState;
  connected: boolean;
}

export interface DigitalTwinActions {
  pause: () => void;
  resume: () => void;
  reset: () => void;
  playScenario: (payload: ScenarioPayload) => void;
}

export function useDigitalTwinState(): DigitalTwinState & { actions: DigitalTwinActions } {
  const [simulationState, setSimulationState] = useState<SimulationState>("idle");
  const [activeRoute, setActiveRoute] = useState<RoutePoint[] | null>(null);
  const [routeError, setRouteError] = useState<string | null>(null);

  const [demoIncident, setDemoIncident] = useState<CommandIncident | null>(null);
  const [demoAmbulance, setDemoAmbulance] = useState<CommandAmbulance | null>(null);
  const [demoHospital, setDemoHospital] = useState<HospitalRecord | null>(null);
  const [demoCorridor, setDemoCorridor] = useState<CorridorStatus>({ active: false, signalIds: [] });

  const [police, setPolice] = useState<PoliceUnit[]>([
    { id: "POL-101", lat: 28.6139, lng: 77.2090 },
    { id: "POL-202", lat: 28.6339, lng: 77.1890 }
  ]);



  const actions: DigitalTwinActions = {
    pause: () => setSimulationState("paused"),
    resume: () => setSimulationState("running"),
    reset: () => {
      setDemoIncident(null);
      setDemoAmbulance(null);
      setDemoHospital(null);
      setDemoCorridor({ active: false, signalIds: [] });
      setActiveRoute(null);
      setRouteError(null);
      setSimulationState("idle");
    },
    playScenario: (payload: ScenarioPayload) => {
      setSimulationState("running");
      setDemoIncident(payload.incident);
      setDemoHospital(payload.hospital);
      setDemoAmbulance(payload.ambulance);
      if (payload.triggerGreenCorridor) {
        setDemoCorridor({ active: true, signalIds: ["sig-1", "sig-2", "sig-3"] });
      } else {
        setDemoCorridor({ active: false, signalIds: [] });
      }
    }
  };

  return {
    incidents: demoIncident ? [demoIncident] : [],
    incident: demoIncident,
    ambulances: demoAmbulance ? [demoAmbulance] : [],
    police,
    hospitals: demoHospital ? [demoHospital] : [],
    trafficSignals: [],
    activeRoute,
    routeError,
    greenCorridor: demoCorridor,
    simulationState,
    connected: true,
    actions,
  };
}
