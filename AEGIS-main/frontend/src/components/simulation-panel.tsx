import { useState } from "react";
import { Play, Pause, RotateCcw, Zap, Loader2 } from "lucide-react";
import { SectionCard, SeverityBadge } from "@/components/design-system";
import type { DigitalTwinState, DigitalTwinActions } from "@/hooks/useDigitalTwinState";

interface SimulationPanelProps {
  state: DigitalTwinState;
  actions: DigitalTwinActions;
}

/**
 * Every field shown here is real data pulled from the Digital Twin state —
 * nothing in this panel is invented. "Trigger Demo Incident" submits a real
 * emergency through the real backend pipeline; Pause/Resume only affect the
 * local display (see useDigitalTwinState's actions), never the real
 * workflow itself.
 */
export function SimulationPanel({ state, actions }: SimulationPanelProps) {
  const [triggering, setTriggering] = useState(false);
  const [triggerError, setTriggerError] = useState<string | null>(null);

  const handleTrigger = async () => {
    setTriggering(true);
    setTriggerError(null);
    const result = await actions.triggerDemoIncident();
    if (!result.ok) setTriggerError(result.message);
    setTriggering(false);
  };

  const assignedAmbulance = state.ambulances.find((a) => a.id === state.incident?.assignedUnit);
  const selectedHospital = state.incident
    ? state.hospitals.find((h) => h.name && state.incident?.status === "en-route")
    : undefined;

  return (
    <SectionCard
      title="AEGIS Simulation"
      description={state.connected ? "Live — connected to backend" : "Disconnected"}
      actions={
        <span
          className={`h-2 w-2 rounded-full ${state.connected ? "bg-green-500 animate-pulse" : "bg-gray-300"}`}
        />
      }
    >
      <div className="space-y-3">
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
          <dt className="font-semibold text-[#525866]">Incident</dt>
          <dd className="text-right font-bold text-[#111111]">
            {state.incident ? state.incident.type : "None active"}
          </dd>

          <dt className="font-semibold text-[#525866]">Severity</dt>
          <dd className="text-right">
            {state.incident ? (
              <SeverityBadge severity={state.incident.severity} />
            ) : (
              <span className="text-[#525866]">—</span>
            )}
          </dd>

          <dt className="font-semibold text-[#525866]">Ambulance</dt>
          <dd className="text-right font-bold text-[#111111]">
            {assignedAmbulance ? assignedAmbulance.callsign : "Unassigned"}
          </dd>

          <dt className="font-semibold text-[#525866]">Hospital</dt>
          <dd className="text-right font-bold text-[#111111]">
            {selectedHospital ? selectedHospital.name : "Pending"}
          </dd>

          <dt className="font-semibold text-[#525866]">Route</dt>
          <dd className="text-right font-bold">
            {state.activeRoute ? (
              <span className="text-green-600">ACTIVE</span>
            ) : (
              <span className="text-[#525866]">{state.routeError ?? "None"}</span>
            )}
          </dd>

          <dt className="font-semibold text-[#525866]">Green Corridor</dt>
          <dd className="text-right font-bold">
            {state.greenCorridor.active ? (
              <span className="text-green-600">ACTIVE ({state.greenCorridor.signalIds.length})</span>
            ) : (
              <span className="text-[#525866]">Inactive</span>
            )}
          </dd>
        </dl>

        <div className="grid grid-cols-3 gap-2 pt-1">
          <button
            onClick={actions.resume}
            disabled={state.simulationState === "running"}
            className="flex items-center justify-center gap-1.5 rounded-xl bg-[#111111] py-2.5 text-xs font-bold text-white transition-opacity disabled:opacity-40"
          >
            <Play className="h-3.5 w-3.5" /> Start
          </button>
          <button
            onClick={actions.pause}
            disabled={state.simulationState !== "running"}
            className="flex items-center justify-center gap-1.5 rounded-xl border border-[#E5E7EB] py-2.5 text-xs font-bold text-[#111111] transition-opacity disabled:opacity-40"
          >
            <Pause className="h-3.5 w-3.5" /> Pause
          </button>
          <button
            onClick={actions.reset}
            className="flex items-center justify-center gap-1.5 rounded-xl border border-[#E5E7EB] py-2.5 text-xs font-bold text-[#111111]"
          >
            <RotateCcw className="h-3.5 w-3.5" /> Reset
          </button>
        </div>

        <button
          onClick={handleTrigger}
          disabled={triggering}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#E63946] py-2.5 text-xs font-bold text-white transition-opacity disabled:opacity-60"
        >
          {triggering ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> Reporting real emergency…
            </>
          ) : (
            <>
              <Zap className="h-3.5 w-3.5" /> Trigger Demo Incident
            </>
          )}
        </button>
        {triggerError && (
          <p className="text-[10px] font-semibold text-[#E63946]">
            Couldn't create demo incident: {triggerError}
          </p>
        )}
        <p className="text-center text-[10px] text-[#525866]">
          Sends a real emergency through the real backend pipeline — not simulated locally.
        </p>
      </div>
    </SectionCard>
  );
}
