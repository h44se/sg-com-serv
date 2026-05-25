import type { DashboardSnapshot } from "./dashboard-types";

export async function fetchDashboardSnapshot(baseUrl = ""): Promise<DashboardSnapshot> {
  const response = await fetch(`${baseUrl}/api/dashboard`, {
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to load dashboard snapshot: ${response.status}`);
  }

  return (await response.json()) as DashboardSnapshot;
}
