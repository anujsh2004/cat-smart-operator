import { Cog, GraduationCap, LayoutDashboard, ListChecks, ShieldCheck, type LucideIcon } from "lucide-react";
import { NavLink } from "react-router-dom";
import { cx } from "@/components/ui";

const NAV: { to: string; label: string; icon: LucideIcon }[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/tasks", label: "Tasks", icon: ListChecks },
  { to: "/safety", label: "Safety", icon: ShieldCheck },
  { to: "/machine", label: "Machine", icon: Cog },
  { to: "/training", label: "Training", icon: GraduationCap },
];

export function Sidebar() {
  return (
    <nav
      aria-label="Main"
      className="sticky top-0 flex h-screen w-24 shrink-0 flex-col items-center gap-2 border-r border-line bg-card py-4"
    >
      <div className="mb-4 flex size-12 items-center justify-center rounded-xl bg-accent font-mono text-lg font-bold text-accent-ink">
        SO
      </div>
      {NAV.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/"}
          className={({ isActive }) =>
            cx(
              "flex min-h-16 w-20 flex-col items-center justify-center gap-1 rounded-xl text-xs font-medium transition",
              isActive ? "bg-accent/15 text-accent" : "text-muted hover:bg-raised hover:text-ink",
            )
          }
        >
          <Icon className="size-6" aria-hidden />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
