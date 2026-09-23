import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { MachinePage } from "@/pages/MachinePage";
import { SafetyPage } from "@/pages/SafetyPage";
import { TasksPage } from "@/pages/TasksPage";
import { TrainingPage } from "@/pages/TrainingPage";

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="tasks" element={<TasksPage />} />
        <Route path="safety" element={<SafetyPage />} />
        <Route path="machine" element={<MachinePage />} />
        <Route path="training" element={<TrainingPage />} />
        <Route path="training/:moduleId" element={<TrainingPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
