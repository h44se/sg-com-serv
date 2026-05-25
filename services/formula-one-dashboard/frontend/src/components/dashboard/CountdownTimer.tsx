"use client";

import React from "react";
import { useEffect, useState } from "react";
import { formatCountdown } from "@/lib/timezone";

export interface CountdownTimerProps {
  targetUtcIso: string;
  label?: string;
}

export function CountdownTimer({ targetUtcIso, label = "Countdown" }: CountdownTimerProps) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <section className="countdown-card" aria-label={`${label} countdown`}>
      <div className="countdown-header">
        <div>
          <p className="eyebrow">{label}</p>
          <h2 className="panel-title">Countdown to next session</h2>
        </div>
        <span className="live-dot">Live</span>
      </div>
      <p className="countdown-value">{formatCountdown(targetUtcIso, now)}</p>
    </section>
  );
}
