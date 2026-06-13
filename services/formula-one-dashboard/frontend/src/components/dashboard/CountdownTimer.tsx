"use client";

import { useEffect, useState } from "react";
import { getCountdownParts } from "@/lib/timezone";

export interface CountdownTimerProps {
  targetUtcIso: string;
  label?: string;
}

export function CountdownTimer({
  targetUtcIso,
  label = "Countdown",
}: CountdownTimerProps) {
  const [now, setNow] = useState(() => new Date());
  const countdown = getCountdownParts(targetUtcIso, now);

  const countdownFields = [
    { label: "TAGE", value: countdown.days },
    { label: "STD", value: countdown.hours },
    { label: "MIN", value: countdown.minutes },
    { label: "SEK", value: countdown.seconds },
  ];

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
      </div>
      <div className="countdown-grid" aria-label="Countdown fields">
        {countdownFields.map((field) => (
          <div className="countdown-field" key={field.label}>
            <span className="countdown-number">
              {field.value.toString().padStart(2, "0")}
            </span>
            <span className="countdown-unit">{field.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
