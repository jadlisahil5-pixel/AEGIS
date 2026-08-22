import { useEffect, useState } from "react";
import { config } from "@/config/env";
import { WS_TOPICS } from "@/config/constants";
import { useWebSocket } from "@/hooks/useWebSocket";
import { trafficService } from "@/services/traffic.service";
import type { TrafficSignalRecord } from "@/services/types";

export interface CorridorStatus {
  active: boolean;
  emergencyId?: string;
  signalIds: string[];
  revertAt?: string;
}

/**
 * Real Digital Twin traffic signals. Seeds the current signal states once
 * via the existing REST endpoint, then reacts live to GREEN_CORRIDOR_ACTIVATED
 * / GREEN_CORRIDOR_REVERTED events broadcast by traffic-service.
 *
 * traffic-service runs its own WebSocket endpoint (a separate STOMP
 * connection from emergency-service's), so this connects independently via
 * VITE_TRAFFIC_WS_URL rather than reusing useCommandDashboard's connection —
 * consistent with how the rest of the app already treats each service's
 * WebSocket as its own connection (see MIGRATION_REPORT.md).
 */
export function useTrafficSignals() {
  const { subscribe, connected } = useWebSocket(config.trafficWsUrl);
  const [signals, setSignals] = useState<TrafficSignalRecord[]>([]);
  const [corridor, setCorridor] = useState<CorridorStatus>({ active: false, signalIds: [] });

  useEffect(() => {
    let cancelled = false;
    trafficService
      .listSignals()
      .then((records) => {
        if (!cancelled) setSignals(records);
      })
      .catch(() => {
        // Non-fatal — map still works without signal markers.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    return subscribe(WS_TOPICS.DASHBOARD, (data) => {
      const type = String(data.type ?? "");

      if (type === "GREEN_CORRIDOR_ACTIVATED") {
        const signalIds = Array.isArray(data.trafficSignalIds)
          ? (data.trafficSignalIds as string[])
          : [];
        setCorridor({
          active: true,
          emergencyId: data.emergencyId ? String(data.emergencyId) : undefined,
          signalIds,
          revertAt: data.revertAt ? String(data.revertAt) : undefined,
        });
        setSignals((prev) =>
          prev.map((s) =>
            signalIds.includes(s.id) ? { ...s, currentState: "GREEN_PRIORITY" } : s,
          ),
        );
      }

      if (type === "GREEN_CORRIDOR_REVERTED") {
        const revertedIds = Array.isArray(data.trafficSignalIds)
          ? (data.trafficSignalIds as string[])
          : [];
        setSignals((prev) =>
          prev.map((s) => (revertedIds.includes(s.id) ? { ...s, currentState: "RED" } : s)),
        );
        setCorridor((prev) => (prev.active ? { active: false, signalIds: [] } : prev));
      }
    });
  }, [subscribe]);

  return { signals, corridor, connected };
}
