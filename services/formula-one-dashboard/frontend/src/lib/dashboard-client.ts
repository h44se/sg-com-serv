import type { DashboardSnapshot } from "./dashboard-types";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://backend:8000";

function resolveDashboardUrl(baseUrl = "") {
  if (baseUrl) {
    return `${baseUrl}/api/dashboard`;
  }

  if (typeof window === "undefined") {
    return `${BACKEND_URL}/api/dashboard`;
  }

  return "/api/dashboard";
}

export async function fetchDashboardSnapshot(
  baseUrl = "",
): Promise<DashboardSnapshot> {
  const response = await fetch(resolveDashboardUrl(baseUrl), {
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
