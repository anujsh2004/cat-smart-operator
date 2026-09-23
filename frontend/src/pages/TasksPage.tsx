import { EmptyState } from "@/components/ui";

export function TasksPage() {
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Tasks</h1>
      <EmptyState title="Tasks coming soon" hint="Built in a later phase." />
    </div>
  );
}
