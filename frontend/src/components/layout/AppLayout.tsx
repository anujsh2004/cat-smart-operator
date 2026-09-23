import { useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { SafetyAlertBanner } from "./SafetyAlertBanner";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

const TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/tasks": "Tasks",
  "/safety": "Safety",
  "/machine": "Machine",
  "/training": "Training",
};

export function AppLayout() {
  const { pathname } = useLocation();
  useEffect(() => {
    const section = TITLES["/" + pathname.split("/")[1]] ?? "Dashboard";
    document.title = `${section} · Smart Operator Assistant`;
  }, [pathname]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="sticky top-0 z-20">
          <TopBar />
          <SafetyAlertBanner />
        </div>
        <main className="mx-auto w-full max-w-[1400px] flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
