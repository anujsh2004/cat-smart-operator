import { ArrowLeft, CheckCircle2, Clock, ExternalLink, PlayCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { DEFAULT_OPERATOR_ID } from "@/api/client";
import { useSaveProgress } from "@/api/hooks";
import type { Module, TrainingProgress } from "@/api/types";
import { Button, Card, ProgressBar, StatusBadge } from "@/components/ui";
import { CATEGORY_LABEL, FORMAT_LABEL } from "@/lib/format";
import { InstructorBooking } from "./InstructorBooking";
import { FORMAT_ICON, TRAINING_STATUS } from "./meta";
import { QuizPlayer } from "./QuizPlayer";

function VideoLesson({ module, progress }: { module: Module; progress: TrainingProgress }) {
  const save = useSaveProgress();
  return (
    <div className="space-y-4">
      <div className="flex aspect-video flex-col items-center justify-center gap-3 rounded-xl border border-line bg-raised text-center">
        <PlayCircle className="size-16 text-accent" aria-hidden />
        <p className="text-lg font-semibold">{module.title}</p>
        <p className="text-sm text-muted">{module.duration_min} min video lesson</p>
        {module.content_url ? (
          <a href={module.content_url} target="_blank" rel="noreferrer" className="inline-flex min-h-12 items-center gap-2 text-accent hover:underline">
            <ExternalLink className="size-5" aria-hidden /> Open video
          </a>
        ) : (
          <p className="text-sm text-muted">Video content placeholder</p>
        )}
      </div>
      <Button
        variant="primary"
        icon={CheckCircle2}
        disabled={save.isPending || progress.status === "completed"}
        onClick={() => save.mutate({ operator_id: DEFAULT_OPERATOR_ID, module_id: module.module_id, progress_pct: 100 })}
      >
        {progress.status === "completed" ? "Watched" : "Mark as watched"}
      </Button>
      {save.isError && <p className="text-sm text-danger" role="alert">{save.error.message}</p>}
    </div>
  );
}

export function ModuleDetail({ module, progress }: { module: Module; progress: TrainingProgress }) {
  const Icon = FORMAT_ICON[module.format];
  const st = TRAINING_STATUS[progress.status];

  return (
    <div className="space-y-5">
      <Link to="/training" className="inline-flex min-h-12 items-center gap-2 text-muted hover:text-ink">
        <ArrowLeft className="size-5" aria-hidden /> All modules
      </Link>

      <Card>
        <div className="flex flex-wrap items-start gap-4">
          <span className="flex size-14 items-center justify-center rounded-xl bg-accent/15 text-accent">
            <Icon className="size-7" aria-hidden />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-muted">
              {module.module_id} · {FORMAT_LABEL[module.format]} · {CATEGORY_LABEL[module.category]}
            </p>
            <h1 className="text-3xl font-bold">{module.title}</h1>
            <p className="mt-1 flex items-center gap-1.5 text-muted"><Clock className="size-4" aria-hidden />{module.duration_min} min</p>
          </div>
          <div className="w-56 space-y-2">
            <div className="flex items-center justify-between">
              <StatusBadge tone={st.tone} label={st.label} />
              <span className="tabular font-mono font-bold">{progress.progress_pct}%</span>
            </div>
            <ProgressBar value={progress.progress_pct} tone={progress.status === "completed" ? "good" : "accent"} label="Module progress" />
            {progress.score != null && <p className="text-sm text-muted">Best score {Math.round(progress.score)}%</p>}
          </div>
        </div>
        <p className="mt-4 text-lg">{module.description}</p>
      </Card>

      <Card title={module.format === "instructor" ? "Book a session" : module.format === "video" ? "Lesson" : "Check your knowledge"}>
        {module.format === "video" && <VideoLesson module={module} progress={progress} />}
        {(module.format === "quiz" || module.format === "simulation") && <QuizPlayer moduleId={module.module_id} />}
        {module.format === "instructor" && <InstructorBooking />}
      </Card>

      {module.format === "video" && (
        <Card title="Quick check">
          <QuizPlayer moduleId={module.module_id} />
        </Card>
      )}
    </div>
  );
}
