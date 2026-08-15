import { useEffect, useState } from "react";
import { useCommandDashboard, type CommandIncident, type CommandAmbulance } from "@/hooks/useCommandDashboard";
import { useTrafficSignals, type CorridorStatus } from "@/hooks/useTrafficSignals";
import { hospitalService } from "@/services/hospital.service";
import { emergencyService } from "@/services/emergency.service";
import { routingService } from "@/services/routing.service";
import type { HospitalRecord } from "@/services/types";
import type { RoutePoint } from "@/components/live-map";
import { DEFAULT_LOCATION } from "@/config/constants";

export type SimulationState = "idle" | "running" | "paused";

export interface PoliceUnit {
  id: string;
  lat: number;
  lng: number;
}

export interface DigitalTwinState {
  incidents: CommandIncident[];
  incident: CommandIncident | null;
  ambulances: CommandAmbulance[];
  police: PoliceUnit[]; // MOCK POLICE ADDED
  hospitals: HospitalRecord[];
  trafficSignals: ReturnType<typeof useTrafficSignals>["signals"];
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
  triggerDemoIncident: () => Promise<{ ok: true } | { ok: false; message: string }>;
}

const DEMO_INJURY_TYPES = ["cardiac arrest", "road accident", "fall injury", "breathing difficulty"];

export function useDigitalTwinState(): DigitalTwinState & { actions: DigitalTwinActions } {
  const dashboard = useCommandDashboard();
  const traffic = useTrafficSignals();

  const [hospitals, setHospitals] = useState<HospitalRecord[]>([]);
  const [simulationState, setSimulationState] = useState<SimulationState>("idle");
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());
  const [activeRoute, setActiveRoute] = useState<RoutePoint[] | null>(null);
  const [routeError, setRouteError] = useState<string | null>(null);

  // === MOCK POLICE STATE ===
  // TODO: Swap this mock timer out with Ansh's WebSocket API when the backend Police API is ready!
  const [police, setPolice] = useState<PoliceUnit[]>([
    { id: "POL-101", lat: DEFAULT_LOCATION.lat, lng: DEFAULT_LOCATION.lng },
    { id: "POL-202", lat: DEFAULT_LOCATION.lat + 0.02, lng: DEFAULT_LOCATION.lng - 0.02 }
  ]);

  useEffect(() => {
    // Generate slow patrol movement randomly around their starting points
    const interval = setInterval(() => {
      setPolice((current) => 
        current.map(p => ({
          ...p,
          lat: p.lat + (Math.random() - 0.5) * 0.002,
          lng: p.lng + (Math.random() - 0.5) * 0.002,
        }))
      );
    }, 3000); // Update every 3 seconds for smooth gliding
    return () => clearInterval(interval);
  }, []);
  // ==========================

  // Hospitals — real REST fetch, once.
  useEffect(() => {
    let cancelled = false;
    hospitalService
      .list()
      .then((records) => {
        if (!cancelled) setHospitals(records);
      })
      .catch(() => {
        // Non-fatal — Digital Twin still works without hospital markers.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const visibleIncidents = dashboard.incidents.filter((i) => !dismissedIds.has(i.id));
  const incident = visibleIncidents[0] ?? null;

  const assignedAmbulance = dashboard.ambulances.find(
    (a) => a.id === incident?.assignedUnit && typeof a.lat === "number" && typeof a.lng === "number",
  );

  // Real route for the current incident's assigned ambulance
  useEffect(() => {
    if (simulationState === "paused") return;
    if (!incident || typeof incident.lat !== "number" || typeof incident.lng !== "number" || !assignedAmbulance) {
      setActiveRoute(null);
      return;
    }
    let cancelled = false;
    routingService
      .compute({
        origin: { lat: assignedAmbulance.lat!, lng: assignedAmbulance.lng! },
        destination: { lat: incident.lat, lng: incident.lng },
      })
      .then((res) => {
        if (!cancelled) {
          setActiveRoute(res.points);
          setRouteError(null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setActiveRoute(null);
          setRouteError("Live route unavailable");
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incident?.id, assignedAmbulance?.id, assignedAmbulance?.lat, assignedAmbulance?.lng, simulationState]);

  const actions: DigitalTwinActions = {
    pause: () => setSimulationState("paused"),
    resume: () => setSimulationState("running"),
    reset: () => {
      setDismissedIds(new Set(dashboard.allIncidents.map((i) => i.id)));
      setActiveRoute(null);
      setRouteError(null);
      setSimulationState("idle");
    },
    triggerDemoIncident: async () => {
      setSimulationState("running");
      const injuryType = DEMO_INJURY_TYPES[Math.floor(Math.random() * DEMO_INJURY_TYPES.length)];
      const jitter = () => (Math.random() - 0.5) * 0.02;
      try {
        await emergencyService.create({
          citizenId: "demo-simulation-panel",
          location: { lat: DEFAULT_LOCATION.lat + jitter(), lng: DEFAULT_LOCATION.lng + jitter() },
          incidentDescription: `[DEMO] Simulated ${injuryType} for Round 2 demonstration.`,
          victimCount: 1,
          injuryType,
        });
        return { ok: true };
      } catch (err) {
        return {
          ok: false,
          message: err instanceof Error ? err.message : "Could not reach emergency-service.",
        };
      }
    },
  };

  return {
    incidents: visibleIncidents,
    incident,
    ambulances: dashboard.ambulances,
    police, // Include mock police
    hospitals,
    trafficSignals: traffic.signals,
    activeRoute,
    routeError,
    greenCorridor: traffic.corridor,
    simulationState,
    connected: dashboard.connected && traffic.connected,
    actions,
  };
}
