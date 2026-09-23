import { EmptyState } from "@/components/ui";

export function DashboardPage() {
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Dashboard</h1>
      <EmptyState title="Dashboard coming soon" hint="Built in a later phase." />
    </div>
  );
}
