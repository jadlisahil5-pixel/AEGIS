import { useEffect, useState } from "react";
import { WS_TOPICS } from "@/config/constants";
import { useWebSocket } from "@/hooks/useWebSocket";
import { displaySeverity, formatTimestamp, mapBackendSeverity } from "@/lib/ws-utils";
import { ambulanceService } from "@/services/ambulance.service";
import type { AmbulanceRecord } from "@/services/types";

export interface CommandIncident {
  id: string;
  type: string;
  severity: "critical" | "high" | "medium" | "low";
  location: string;
  status: string;
  assignedUnit?: string;
  eta?: string;
  lat?: number;
  lng?: number;
}

export interface CommandAmbulance {
  id: string;
  callsign: string;
  driver: string;
  status: string;
  speed: number;
  lat?: number;
  lng?: number;
}

export interface CommandLog {
  timestamp: string;
  message: string;
}

export function useCommandDashboard() {
  const { subscribe, connected } = useWebSocket();
  const [incidents, setIncidents] = useState<CommandIncident[]>([]);
  const [ambulances, setAmbulances] = useState<CommandAmbulance[]>([]);
  const [logs, setLogs] = useState<CommandLog[]>([]);

  const addLog = (message: string) => {
    setLogs((prev) => [{ timestamp: formatTimestamp(new Date()), message }, ...prev.slice(0, 49)]);
  };

  // Seed real ambulance positions once via the existing REST endpoint (not
  // polling — live updates afterwards come exclusively from the WebSocket
  // feed below, same as everything else on this dashboard).
  useEffect(() => {
    let cancelled = false;
    ambulanceService
      .list()
      .then((records: AmbulanceRecord[]) => {
        if (cancelled) return;
        setAmbulances((prev) => {
          const known = new Set(prev.map((a) => a.id));
          const seeded = records
            .filter((r) => !known.has(r.id))
            .map((r) => ({
              id: r.id,
              callsign: r.id.substring(0, 8).toUpperCase(),
              driver: "Crew on standby",
              status: r.status.toLowerCase(),
              speed: 0,
              lat: r.lat,
              lng: r.lng,
            }));
          return [...prev, ...seeded];
        });
      })
      .catch(() => {
        // Non-fatal — dashboard still works from WS-only data if the REST call fails.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    return subscribe(WS_TOPICS.DASHBOARD, (data) => {
      const type = String(data.type ?? "");

      if (type === "AMBULANCE_LOCATION") {
        const aid = String(data.id ?? data.ambulanceId ?? "");
        const loc = data.location as { lat: number; lng: number } | undefined;
        if (aid && loc) {
          setAmbulances((prev) => {
            if (prev.some((a) => a.id === aid)) {
              return prev.map((a) => (a.id === aid ? { ...a, lat: loc.lat, lng: loc.lng } : a));
            }
            return [
              {
                id: aid,
                callsign: aid.substring(0, 8).toUpperCase(),
                driver: "Crew on standby",
                status: "en-route",
                speed: 40,
                lat: loc.lat,
                lng: loc.lng,
              },
              ...prev,
            ];
          });
        }
        return;
      }

      const eid = String(data.emergencyId ?? "");
      if (!eid) return;

      if (type === "EMERGENCY_REPORTED") {
        const injuryType = String(data.injuryType ?? "Emergency");
        const loc = data.location as { lat: number; lng: number } | undefined;
        setIncidents((prev) => {
          if (prev.some((i) => i.id === eid)) return prev;
          return [
            {
              id: eid,
              type: injuryType,
              severity: mapBackendSeverity(String(data.severity ?? "HIGH")),
              location: "Active zone",
              status: "active",
              lat: loc?.lat,
              lng: loc?.lng,
            },
            ...prev,
          ];
        });
        addLog(`Emergency reported: ${injuryType}`);
      }

      if (type === "SEVERITY_ASSESSED") {
        setIncidents((prev) =>
          prev.map((i) =>
            i.id === eid
              ? { ...i, severity: mapBackendSeverity(String(data.severity ?? i.severity)) }
              : i,
          ),
        );
        addLog(`Severity assessed: ${data.severity}`);
      }

      if (type === "AMBULANCE_ASSIGNED") {
        const aid = String(data.ambulanceId ?? "");
        const eta = typeof data.eta === "number" ? `${data.eta}m` : undefined;
        if (aid) {
          setAmbulances((prev) => {
            if (prev.some((a) => a.id === aid)) {
              return prev.map((a) =>
                a.id === aid ? { ...a, status: "on-mission", speed: 45 } : a,
              );
            }
            return [
              {
                id: aid,
                callsign: aid.substring(0, 8).toUpperCase(),
                driver: "Assigned crew",
                status: "on-mission",
                speed: 45,
              },
              ...prev,
            ];
          });
        }
        setIncidents((prev) =>
          prev.map((i) =>
            i.id === eid ? { ...i, status: "en-route", assignedUnit: aid, eta } : i,
          ),
        );
        addLog(`Ambulance dispatched${eta ? ` · ETA ${eta}` : ""}`);
      }

      if (type === "HOSPITAL_NOTIFIED" || type === "HOSPITAL_ASSIGNED") {
        addLog(`Hospital assigned: ${data.hospitalName ?? "unknown"}`);
      }

      if (type === "COMPLETED") {
        setIncidents((prev) =>
          prev.map((i) => (i.id === eid ? { ...i, status: "resolved" } : i)),
        );
        addLog("Emergency completed");
      }
    });
  }, [subscribe]);

  const activeIncidents = incidents.filter((i) => i.status !== "resolved");

  return {
    incidents: activeIncidents,
    allIncidents: incidents,
    ambulances,
    logs,
    connected,
    displaySeverity,
  };
}
