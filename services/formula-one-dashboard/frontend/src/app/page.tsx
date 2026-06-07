import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { fetchDashboardSnapshot } from "@/lib/dashboard-client";

export default async function Page() {
  const snapshot = await fetchDashboardSnapshot().catch(() => null);

  return <DashboardShell snapshot={snapshot} />;
}
