import React, { useState, useEffect, useRef } from "react";
import { PipelineStep, PipelineStepId } from "../types";
import { FolderOpen, Activity, Database, GitMerge, CheckCircle, Play, Loader2 } from "lucide-react";

interface EnginePipelineProps {
  steps: readonly PipelineStep[] | PipelineStep[];
  currentStepId: PipelineStepId;
  setCurrentStepId: (id: PipelineStepId) => void;
  onRunStep: (id: PipelineStepId, onLog?: (log: string) => void) => Promise<string[]>;
  isRunning: boolean;
}

export default function EnginePipeline({
  steps,
  currentStepId,
  setCurrentStepId,
  onRunStep,
  isRunning,
}: EnginePipelineProps) {
  const [pipelineLogs, setPipelineLogs] = useState<string[]>([
    "[SYSTEM] KaRar AI Engine v0.2 initialization ready.",
    "[SYSTEM] Loaded GÜZELCE 467 ADA 3 PARSEL blueprint.",
  ]);

  const logContainerRef = useRef<HTMLDivElement>(null);

  // Autoscroll to bottom when new logs are added
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [pipelineLogs]);

  const runFullPipeline = async () => {
    setPipelineLogs((l) => [...l, `[PROCESS] Full pipeline execution triggered...`]);
    for (const step of steps) {
      setCurrentStepId(step.id);
      setPipelineLogs((l) => [
        ...l,
        `[${step.title.toUpperCase()}] Running ${step.subtitle}...`,
      ]);
      const logs = await onRunStep(step.id, (log) => {
        setPipelineLogs((l) => [...l, `[${step.title.toUpperCase()}] ${log}`]);
      });
      
      const hasError = logs.some(log => log.includes("[ERROR]"));

      if (hasError) {
        setPipelineLogs((l) => [
          ...l,
          `[${step.title.toUpperCase()}] HALTED DUE TO ERROR.`
        ]);
        return;
      }

      setPipelineLogs((l) => [
        ...l,
        `[${step.title.toUpperCase()}] Step complete.`
      ]);
    }
    setPipelineLogs((l) => [...l, `[SUCCESS] Full BIM generation pipeline run complete!`]);
  };

  const runSingleStep = async (stepId: PipelineStepId) => {
    const step = steps.find(s => s.id === stepId);
    if (!step) return;

    setPipelineLogs((l) => [...l, `[${step.title.toUpperCase()}] Triggering manually...`]);
    
    const logs = await onRunStep(stepId, (log) => {
      setPipelineLogs((l) => [...l, `[${step.title.toUpperCase()}] ${log}`]);
    });
    
    setPipelineLogs((l) => [
      ...l,
      `[${step.title.toUpperCase()}] Execution complete.`
    ]);
  };

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case "FolderOpen":
        return <FolderOpen className="w-5 h-5" />;
      case "Activity":
        return <Activity className="w-5 h-5" />;
      case "Database":
        return <Database className="w-5 h-5" />;
      case "GitMerge":
        return <GitMerge className="w-5 h-5" />;
      default:
        return <Activity className="w-5 h-5" />;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* 4 Engine Steps Cards */}
      <div className="lg:col-span-2 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold tracking-wider uppercase text-zinc-400 font-mono">
            MİMARİ YAPAY ZEKÂ MOTORLARI
          </h2>
          <button
            onClick={runFullPipeline}
            disabled={isRunning}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-all shadow-md font-mono"
            id="btn_run_full_pipeline"
          >
            {isRunning ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5" />
            )}
            <span>TÜMÜNÜ ÇALIŞTIR (AUTO-BIM)</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {steps.map((step) => {
            const isSelected = currentStepId === step.id;
            return (
              <div
                key={step.id}
                onClick={() => setCurrentStepId(step.id)}
                className={`group p-4 border rounded-xl cursor-pointer transition-all ${
                  isSelected
                    ? "bg-zinc-900 border-emerald-500/50 shadow-lg shadow-emerald-500/5"
                    : "bg-zinc-900/40 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900/60"
                }`}
                id={`card_step_${step.id}`}
              >
                <div className="flex items-start justify-between">
                  <div
                    className={`p-2.5 rounded-lg border transition-colors ${
                      isSelected
                        ? "bg-emerald-950/40 border-emerald-800 text-emerald-400"
                        : "bg-zinc-800 border-zinc-700 text-zinc-400 group-hover:text-zinc-200"
                    }`}
                  >
                    {getIcon(step.icon)}
                  </div>
                  <div className="flex items-center space-x-1.5 font-mono text-[10px]">
                    <span className="text-zinc-500">{step.duration}ms</span>
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                </div>

                <div className="mt-3">
                  <h3 className="text-xs font-mono font-bold tracking-wider text-zinc-400 group-hover:text-zinc-200 uppercase">
                    {step.title}
                  </h3>
                  <p className="text-xs font-semibold text-zinc-200 mt-1">
                    {step.subtitle}
                  </p>
                  <p className="text-[11px] text-zinc-500 mt-1.5 leading-relaxed">
                    {step.description}
                  </p>
                </div>

                {isSelected && (
                  <div className="mt-4 pt-3 border-t border-zinc-800/80 animate-fade-in space-y-3">
                    <button
                      disabled={isRunning}
                      onClick={(e) => {
                        e.stopPropagation();
                        runSingleStep(step.id);
                      }}
                      className="w-full flex items-center justify-center space-x-1.5 py-1.5 px-3 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-zinc-200 hover:text-white rounded text-xs font-mono font-bold transition-all border border-zinc-700/60 shadow-sm cursor-pointer"
                    >
                      {isRunning ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
                      ) : (
                        <Play className="w-3.5 h-3.5 text-emerald-400" />
                      )}
                      <span>ADIMI ÇALIŞTIR</span>
                    </button>

                    <div>
                      <p className="text-[10px] font-mono uppercase text-emerald-400 tracking-wider">
                        Sonuç Analizleri:
                      </p>
                      <ul className="mt-2 space-y-1">
                        {step.insights.map((ins, idx) => (
                          <li
                            key={idx}
                            className="text-[11px] text-zinc-400 flex items-start"
                          >
                            <span className="text-emerald-500 mr-1.5 font-mono">
                              •
                            </span>
                            <span>{ins}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Terminal Logger & Output stream */}
      <div className="flex flex-col h-full bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 overflow-hidden">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-2 mb-3">
          <span className="font-mono text-xs text-zinc-400">
            ENGINE OUTPUT LOGS
          </span>
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
        </div>

        <div ref={logContainerRef} className="flex-1 font-mono text-[10px] text-zinc-400 space-y-1.5 overflow-y-auto max-h-[360px] pr-2">
          {pipelineLogs.map((log, idx) => {
            let color = "text-zinc-500";
            if (log.includes("[SYSTEM]")) color = "text-sky-400";
            else if (log.includes("[PROCESS]")) color = "text-yellow-400";
            else if (log.includes("[SUCCESS]")) color = "text-emerald-400";
            else if (log.includes("[INSIGHT]")) color = "text-zinc-300";
            return (
              <div key={idx} className={`${color} leading-relaxed break-words`}>
                {log}
              </div>
            );
          })}
        </div>

        <div className="mt-3 pt-2 border-t border-zinc-800 flex justify-between text-[10px] font-mono text-zinc-500">
          <span>HAZIR / READY</span>
          <button
            onClick={() =>
              setPipelineLogs([
                "[SYSTEM] logs cleared.",
                "[SYSTEM] KaRar AI Engine ready.",
              ])
            }
            className="hover:text-zinc-300 transition-colors"
            id="btn_clear_logs"
          >
            TEMİZLE
          </button>
        </div>
      </div>
    </div>
  );
}
