import {
  Clock,
  Cloud,
  CloudFog,
  CloudRain,
  Sun,
  Truck,
  User,
  Wind,
  Wifi,
  WifiOff,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { USE_MOCKS } from "@/api/client";
import { useHealth, useOperatorContext } from "@/api/hooks";
import type { Weather } from "@/api/types";
import { cx } from "@/components/ui";

export const WEATHER_ICON: Record<Weather, LucideIcon> = {
  Sunny: Sun,
  Cloudy: Cloud,
  Windy: Wind,
  Rainy: CloudRain,
  Foggy: CloudFog,
};

function Item({ icon: Icon, children }: { icon: LucideIcon; children: ReactNode }) {
  return (
    <div className="flex min-w-0 items-center gap-2">
      <Icon className="size-5 shrink-0 text-muted" aria-hidden />
      <div className="min-w-0 truncate">{children}</div>
    </div>
  );
}

function LiveClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <span className="tabular font-mono text-lg font-bold">
      {now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
    </span>
  );
}

export function TopBar({ actions }: { actions?: ReactNode }) {
  const { data: ctx } = useOperatorContext();
  const health = useHealth();
  const online = health.data?.status === "ok";
  const WeatherIcon = ctx ? WEATHER_ICON[ctx.weather.condition] : Cloud;

  return (
    <header className="flex min-h-16 flex-wrap items-center gap-x-5 gap-y-2 border-b border-line bg-bg/95 px-6 py-3 backdrop-blur">
      <Item icon={User}>
        <span className="font-semibold">{ctx?.operator.name ?? "—"}</span>
        <span className="ml-2 hidden text-sm text-muted 2xl:inline">{ctx?.operator.skill_level}</span>
      </Item>
      <Item icon={Truck}>
        <span className="font-semibold">{ctx?.machine.machine_id ?? "—"}</span>
        <span className="ml-2 text-sm text-muted">{ctx?.machine.model}</span>
      </Item>
      <Item icon={Clock}>
        <span className="font-semibold">{ctx?.shift.name ?? "—"} shift</span>
        <span className="ml-2 text-sm text-muted">{ctx && `${ctx.shift.start}–${ctx.shift.end}`}</span>
      </Item>
      <Item icon={WeatherIcon}>
        <span className="font-semibold">{ctx?.weather.condition ?? "—"}</span>
        <span className="ml-2 text-sm text-muted">
          {ctx && `${Math.round(ctx.weather.temperature_c)}°C · ${ctx.ground_condition} ground`}
        </span>
      </Item>

      <div className="ml-auto flex items-center gap-3">
        {USE_MOCKS && (
          <span className="rounded-md border border-accent/50 px-2 py-0.5 text-xs font-semibold text-accent">MOCK DATA</span>
        )}
        <LiveClock />
        <span
          className={cx("flex items-center gap-1.5 text-sm font-medium", online ? "text-good" : "text-danger")}
          title={online ? `API connected (ML ${health.data?.ml_mode})` : "API unreachable"}
        >
          <span className={cx("size-2.5 rounded-full", online ? "bg-good" : "bg-danger")} aria-hidden />
          {online ? <Wifi className="size-4" aria-hidden /> : <WifiOff className="size-4" aria-hidden />}
          {online ? "Online" : "Offline"}
        </span>
        {actions}
      </div>
    </header>
  );
}
