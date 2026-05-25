"use client";

import { useEffect, useState } from "react";
import { fetchDashboardSnapshot } from "@/lib/dashboard-client";
import type { DashboardSnapshot } from "@/lib/dashboard-types";
import { DashboardShell } from "./DashboardShell";
import { detectBrowserTimeZone } from "@/lib/timezone";

export function DashboardPageClient() {
  const [timeZone, setTimeZone] = useState("UTC");
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | null>(null);

  useEffect(() => {
    setTimeZone(detectBrowserTimeZone());
    fetchDashboardSnapshot()
      .then(setSnapshot)
      .catch(() => setSnapshot(null));
  }, []);

  return <DashboardShell snapshot={snapshot} timeZone={timeZone} />;
}
