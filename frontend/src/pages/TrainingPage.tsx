import { GraduationCap, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useModules, useProgress, useRecommendations } from "@/api/hooks";
import type { ModuleCategory, ModuleFormat } from "@/api/types";
import { ModuleCard } from "@/components/training/ModuleCard";
import { ModuleDetail } from "@/components/training/ModuleDetail";
import { FORMAT_ICON, PRIORITY_TONE, progressFor } from "@/components/training/meta";
import { Card, EmptyState, Field, QueryBlock, Select, Skeleton, StatusBadge } from "@/components/ui";
import { CATEGORY_LABEL, FORMAT_LABEL, titleCase } from "@/lib/format";

type CategoryFilter = "all" | ModuleCategory;
type FormatFilter = "all" | ModuleFormat;
const CATEGORIES: CategoryFilter[] = ["all", "safety", "efficiency", "technique", "incident_response"];
const FORMATS: FormatFilter[] = ["all", "video", "quiz", "simulation", "instructor"];

function Recommended() {
  const recs = useRecommendations();
  return (
    <Card title="Recommended for you" icon={Sparkles}>
      <QueryBlock query={recs} skeleton={<Skeleton className="h-32" />}>
        {(list) =>
          list.length === 0 ? (
            <EmptyState icon={GraduationCap} title="Nothing urgent" hint="No recent incidents or unusual behaviour need follow-up training." />
          ) : (
            <ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {list.map(({ module, reason, priority }) => {
                const Icon = FORMAT_ICON[module.format];
                return (
                  <li key={module.module_id}>
                    <Link
                      to={`/training/${module.module_id}`}
                      className="flex h-full flex-col gap-2 rounded-xl border border-line bg-raised p-4 transition hover:border-accent"
                    >
                      <div className="flex items-center gap-2">
                        <Icon className="size-5 text-accent" aria-hidden />
                        <span className="font-semibold">{module.title}</span>
                      </div>
                      <p className="text-sm text-muted">{reason}</p>
                      <div className="mt-auto flex items-center justify-between pt-1">
                        <StatusBadge tone={PRIORITY_TONE[priority]} label={`${titleCase(priority)} priority`} />
                        <span className="text-sm text-muted">{module.duration_min} min</span>
                      </div>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )
        }
      </QueryBlock>
    </Card>
  );
}

export function TrainingPage() {
  const { moduleId } = useParams();
  const modules = useModules();
  const progress = useProgress();
  const [category, setCategory] = useState<CategoryFilter>("all");
  const [format, setFormat] = useState<FormatFilter>("all");

  if (moduleId) {
    return (
      <QueryBlock query={modules} skeleton={<Skeleton className="h-96" />}>
        {(list) => {
          const module = list.find((m) => m.module_id === moduleId);
          if (!module) return <EmptyState title={`Module ${moduleId} not found`} />;
          return <ModuleDetail key={module.module_id} module={module} progress={progressFor(progress.data, module.module_id)} />;
        }}
      </QueryBlock>
    );
  }

  return (
    <div className="space-y-5">
      <Recommended />
      <Card
        title="All modules"
        icon={GraduationCap}
        action={
          <div className="flex flex-wrap gap-3">
            <Field label="Category">
              <Select value={category} options={CATEGORIES} labels={{ all: "All categories", ...CATEGORY_LABEL }} onChange={setCategory} />
            </Field>
            <Field label="Format">
              <Select value={format} options={FORMATS} labels={{ all: "All formats", ...FORMAT_LABEL }} onChange={setFormat} />
            </Field>
          </div>
        }
      >
        <QueryBlock query={modules} skeleton={<Skeleton className="h-64" />}>
          {(list) => {
            const shown = list.filter((m) => (category === "all" || m.category === category) && (format === "all" || m.format === format));
            if (shown.length === 0) return <EmptyState title="No modules match these filters" />;
            return (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {shown.map((m) => (
                  <ModuleCard key={m.module_id} module={m} progress={progressFor(progress.data, m.module_id)} />
                ))}
              </div>
            );
          }}
        </QueryBlock>
      </Card>
    </div>
  );
}
