import { Clock } from "lucide-react";
import { Link } from "react-router-dom";
import type { Module, TrainingProgress } from "@/api/types";
import { ProgressBar, StatusBadge } from "@/components/ui";
import { CATEGORY_LABEL, FORMAT_LABEL } from "@/lib/format";
import { FORMAT_ICON, TRAINING_STATUS } from "./meta";

export function ModuleCard({ module, progress }: { module: Module; progress: TrainingProgress }) {
  const Icon = FORMAT_ICON[module.format];
  const st = TRAINING_STATUS[progress.status];
  return (
    <Link
      to={`/training/${module.module_id}`}
      className="flex flex-col gap-3 rounded-2xl border border-line bg-card p-5 transition hover:border-accent focus-visible:outline-2 focus-visible:outline-accent"
    >
      <div className="flex items-center gap-3">
        <span className="flex size-12 items-center justify-center rounded-xl bg-accent/15 text-accent">
          <Icon className="size-6" aria-hidden />
        </span>
        <div className="text-sm text-muted">
          <p>{FORMAT_LABEL[module.format]} · {CATEGORY_LABEL[module.category]}</p>
          <p className="flex items-center gap-1"><Clock className="size-4" aria-hidden />{module.duration_min} min</p>
        </div>
        <span className="ml-auto self-start text-sm text-muted">{module.module_id}</span>
      </div>
      <h3 className="text-lg font-semibold">{module.title}</h3>
      <p className="line-clamp-2 text-sm text-muted">{module.description}</p>
      <div className="mt-auto space-y-2">
        <div className="flex items-center justify-between">
          <StatusBadge tone={st.tone} label={st.label} />
          <span className="tabular font-mono text-sm font-bold">
            {progress.progress_pct}%{progress.score != null && ` · score ${Math.round(progress.score)}`}
          </span>
        </div>
        <ProgressBar value={progress.progress_pct} tone={progress.status === "completed" ? "good" : "accent"} label={`${module.title} progress`} />
      </div>
    </Link>
  );
}
