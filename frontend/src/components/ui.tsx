// Shared building blocks: Card, KpiTile, Button, StatusBadge, EmptyState, ErrorState, Skeleton.
import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  Circle,
  Info,
  Inbox,
  Minus,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(" ");

// --- Card ---

export function Card({
  title,
  icon: Icon,
  action,
  children,
  className,
  tone,
}: {
  title?: ReactNode;
  icon?: LucideIcon;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  tone?: "danger";
}) {
  return (
    <section
      className={cx(
        "rounded-2xl border p-5",
        tone === "danger" ? "border-danger bg-danger/15" : "border-line bg-card",
        className,
      )}
    >
      {(title || action) && (
        <header className="mb-4 flex items-center justify-between gap-3">
          <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-muted">
            {Icon && <Icon className="size-5" aria-hidden />}
            {title}
          </h2>
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

// --- Status tones ---

export type Tone = "good" | "warn" | "danger" | "info" | "neutral";

const TONE_CLASS: Record<Tone, string> = {
  good: "bg-good/15 text-good border-good/40",
  warn: "bg-warn/15 text-warn border-warn/40",
  danger: "bg-danger/15 text-danger border-danger/50",
  info: "bg-info/15 text-info border-info/40",
  neutral: "bg-raised text-muted border-line",
};

const TONE_ICON: Record<Tone, LucideIcon> = {
  good: CheckCircle2,
  warn: AlertTriangle,
  danger: AlertOctagon,
  info: Info,
  neutral: Circle,
};

const TONE_BORDER: Record<Tone, string> = {
  good: "border-good/50",
  warn: "border-warn/60",
  danger: "border-danger/70",
  info: "border-info/50",
  neutral: "border-line",
};

export const TONE_TEXT: Record<Tone, string> = {
  good: "text-good",
  warn: "text-warn",
  danger: "text-danger",
  info: "text-info",
  neutral: "text-muted",
};

/** Colour + icon + text: status is never shown by colour alone. */
export function StatusBadge({
  tone,
  label,
  icon,
  size = "md",
}: {
  tone: Tone;
  label: string;
  icon?: LucideIcon;
  size?: "md" | "lg";
}) {
  const Icon = icon ?? TONE_ICON[tone];
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border font-semibold",
        size === "lg" ? "px-4 py-1.5 text-base" : "px-2.5 py-0.5 text-sm",
        TONE_CLASS[tone],
      )}
    >
      <Icon className={size === "lg" ? "size-5" : "size-4"} aria-hidden />
      {label}
    </span>
  );
}

function ToneIcon({ tone }: { tone: Tone }) {
  const Icon = TONE_ICON[tone];
  return <Icon className={cx("size-4", TONE_TEXT[tone])} aria-label={tone} />;
}

// --- KPI tile ---

export function KpiTile({
  label,
  value,
  unit,
  tone = "neutral",
  trend,
  hint,
}: {
  label: string;
  value: ReactNode;
  unit?: string;
  tone?: Tone;
  trend?: { direction: "up" | "down" | "flat"; text: string; good?: boolean };
  hint?: ReactNode;
}) {
  const TrendIcon = trend?.direction === "up" ? TrendingUp : trend?.direction === "down" ? TrendingDown : Minus;
  return (
    <div
      className={cx(
        "flex min-h-28 flex-col justify-between rounded-2xl border bg-card p-4",
        TONE_BORDER[tone],
      )}
    >
      <div className="flex items-center justify-between gap-2 text-sm text-muted">
        <span>{label}</span>
        {tone !== "neutral" && <ToneIcon tone={tone} />}
      </div>
      <div className="mt-2 flex items-baseline gap-1.5">
        <span className={cx("tabular font-mono text-4xl font-bold leading-none", tone !== "neutral" && TONE_TEXT[tone])}>
          {value}
        </span>
        {unit && <span className="text-base text-muted">{unit}</span>}
      </div>
      {(trend || hint) && (
        <div className="mt-2 flex items-center gap-1 text-sm text-muted">
          {trend && (
            <>
              <TrendIcon
                className={cx("size-4", trend.good === undefined ? "" : trend.good ? "text-good" : "text-warn")}
                aria-hidden
              />
              <span>{trend.text}</span>
            </>
          )}
          {hint}
        </div>
      )}
    </div>
  );
}

// --- Button ---

type Variant = "primary" | "secondary" | "danger" | "ghost";
const VARIANT: Record<Variant, string> = {
  primary: "bg-accent text-accent-ink hover:brightness-110 font-semibold",
  secondary: "bg-raised text-ink border border-line hover:border-muted",
  danger: "bg-danger text-white hover:brightness-110 font-semibold",
  ghost: "text-muted hover:text-ink hover:bg-raised",
};

export function Button({
  variant = "secondary",
  icon: Icon,
  className,
  children,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; icon?: LucideIcon }) {
  return (
    <button
      type="button"
      className={cx(
        "inline-flex min-h-12 items-center justify-center gap-2 rounded-xl px-4 text-base transition",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
        "disabled:cursor-not-allowed disabled:opacity-50",
        VARIANT[variant],
        className,
      )}
      {...rest}
    >
      {Icon && <Icon className="size-5" aria-hidden />}
      {children}
    </button>
  );
}

// --- Loading / empty / error states ---

export function Skeleton({ className }: { className?: string }) {
  return <div className={cx("animate-pulse rounded-xl bg-raised", className ?? "h-24")} aria-hidden />;
}

export function EmptyState({ icon: Icon = Inbox, title, hint }: { icon?: LucideIcon; title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-8 text-center text-muted">
      <Icon className="size-8" aria-hidden />
      <p className="font-medium text-ink">{title}</p>
      {hint && <p className="text-sm">{hint}</p>}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : "Something went wrong";
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-6 text-center" role="alert">
      <AlertTriangle className="size-8 text-warn" aria-hidden />
      <p className="font-medium">Couldn't load this</p>
      <p className="max-w-sm text-sm text-muted">{message}</p>
      {onRetry && (
        <Button icon={RefreshCw} onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

/** Renders loading / error / content for one query. */
export function QueryBlock<T>({
  query,
  skeleton,
  children,
}: {
  query: { data: T | undefined; isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown };
  skeleton?: ReactNode;
  children: (data: T) => ReactNode;
}) {
  if (query.data !== undefined) return <>{children(query.data)}</>;
  if (query.isError) return <ErrorState error={query.error} onRetry={() => query.refetch()} />;
  return <>{skeleton ?? <Skeleton />}</>;
}

// --- Progress bar ---

export function ProgressBar({ value, tone = "accent", label }: { value: number; tone?: "accent" | "good"; label?: string }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div
      className="h-3 w-full overflow-hidden rounded-full bg-raised"
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
    >
      <div
        className={cx("h-full rounded-full transition-[width] duration-700", tone === "good" ? "bg-good" : "bg-accent")}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

// --- Form fields ---

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5 text-sm text-muted">
      {label}
      {children}
    </label>
  );
}

export const inputClass =
  "min-h-12 rounded-xl border border-line bg-raised px-3 text-base text-ink focus:border-accent focus:outline-none";

export function Select<T extends string>({
  value,
  options,
  onChange,
  labels,
}: {
  value: T;
  options: readonly T[];
  onChange: (v: T) => void;
  labels?: Partial<Record<T, string>>;
}) {
  return (
    <select className={inputClass} value={value} onChange={(e) => onChange(e.target.value as T)}>
      {options.map((o) => (
        <option key={o} value={o}>
          {labels?.[o] ?? o}
        </option>
      ))}
    </select>
  );
}
