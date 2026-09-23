import { EmptyState } from "@/components/ui";

export function MachinePage() {
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Machine</h1>
      <EmptyState title="Machine coming soon" hint="Built in a later phase." />
    </div>
  );
}
