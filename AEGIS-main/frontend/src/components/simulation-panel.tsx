import { useState } from "react";
import { Play, Loader2, Database } from "lucide-react";
import { SectionCard } from "@/components/design-system";
import type { ScenarioPayload } from "@/hooks/useDigitalTwinState";
import { SCENARIOS_DATASET } from "@/lib/scenarios-dataset";

interface SimulationPanelProps {
  onTrigger: (scenario: ScenarioPayload) => void;
  activeScenarioId?: string | null;
}

export function SimulationPanel({ onTrigger, activeScenarioId }: SimulationPanelProps) {
  const [triggering, setTriggering] = useState<boolean>(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  const handleTrigger = () => {
    setTriggering(true);
    onTrigger(SCENARIOS_DATASET[selectedIndex]);
    setTimeout(() => setTriggering(false), 500);
  };

  return (
    <SectionCard
      title="AEGIS AI Simulator"
      description={`Loaded ${SCENARIOS_DATASET.length} emergency scenarios from dataset`}
      actions={
        <Database className="h-4 w-4 text-gray-500" />
      }
    >
      <div className="space-y-4">
        <div>
          <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2 block">
            Select Scenario
          </label>
          <select
            value={selectedIndex}
            onChange={(e) => setSelectedIndex(Number(e.target.value))}
            className="w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-xs font-bold text-gray-700 outline-none focus:border-red-400 focus:ring-1 focus:ring-red-400"
          >
            {SCENARIOS_DATASET.map((s, idx) => (
              <option key={s.incident.id} value={idx}>
                {s.incident.id} — {s.incident.type.replace(/_/g, " ")} in {s.incident.location} ({s.incident.severity.toUpperCase()})
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleTrigger}
          disabled={triggering}
          className={`flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-bold transition-opacity disabled:opacity-60 bg-[#E63946] text-white hover:bg-[#C32F3A]`}
        >
          {triggering ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
          Trigger Scenario {SCENARIOS_DATASET[selectedIndex].incident.id}
        </button>
      </div>
    </SectionCard>
  );
}
