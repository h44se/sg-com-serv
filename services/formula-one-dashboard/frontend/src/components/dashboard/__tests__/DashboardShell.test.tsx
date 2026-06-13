import { describe, expect, it } from "vitest";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type { DashboardSnapshot } from "@/lib/dashboard-types";
import { DashboardShell } from "../DashboardShell";

const snapshot: DashboardSnapshot = {
  meeting: {
    meeting_key: 1,
    meeting_name: "Monaco Grand Prix",
    meeting_official_name: null,
    location: "Monte Carlo",
    country_code: "MON",
    country_name: "Monaco",
  },
  sessions: [
    {
      session_key: 10,
      meeting_key: 1,
      session_name: "Practice 1",
      session_type: "Practice",
      date_start_utc: "2026-06-05T11:30:00Z",
      date_end_utc: "2026-06-05T12:30:00Z",
    },
  ],
  latest_positions: [],
  latest_laps: [],
  race_control: [],
  latest_results: [],
  driver_standings: [],
  constructor_standings: [],
  venue: {
    circuit_name: "Circuit de Monaco",
    circuit_short_name: "Monaco",
    circuit_image_url: null,
    circuit_wiki_url: null,
    track_map_svg: "<svg viewBox='0 0 10 10'><path d='M1 1 L9 9'/></svg>",
    track_length_km: null,
    fastest_lap_seconds: null,
    average_pit_stop_seconds: null,
    weather_forecast: [
      {
        date: "2026-06-04",
        label: "Thu",
        summary: "Dry",
        is_wet: false,
        precipitation_probability_max: 0,
        precipitation_sum_mm: 0,
        rain_sum_mm: 0,
        showers_sum_mm: 0,
        snowfall_sum_mm: 0,
        temperature_max_c: 24,
        temperature_min_c: 18,
      },
      {
        date: "2026-06-05",
        label: "Fri",
        summary: "Dry",
        is_wet: false,
        precipitation_probability_max: 10,
        precipitation_sum_mm: 0,
        rain_sum_mm: 0,
        showers_sum_mm: 0,
        snowfall_sum_mm: 0,
        temperature_max_c: 25,
        temperature_min_c: 19,
      },
      {
        date: "2026-06-06",
        label: "Sat",
        summary: "Wet",
        is_wet: true,
        precipitation_probability_max: 70,
        precipitation_sum_mm: 4.5,
        rain_sum_mm: 4.5,
        showers_sum_mm: 0,
        snowfall_sum_mm: 0,
        temperature_max_c: 21,
        temperature_min_c: 17,
      },
      {
        date: "2026-06-07",
        label: "Sun",
        summary: "Dry",
        is_wet: false,
        precipitation_probability_max: 20,
        precipitation_sum_mm: 0.2,
        rain_sum_mm: 0.2,
        showers_sum_mm: 0,
        snowfall_sum_mm: 0,
        temperature_max_c: 23,
        temperature_min_c: 18,
      },
    ],
  },
  generated_at_utc: "2026-06-04T10:00:00Z",
};

describe("DashboardShell weather panel", () => {
  it("renders only Friday to Sunday forecast entries", () => {
    const html = renderToStaticMarkup(
      createElement(DashboardShell, { snapshot }),
    );

    expect(html).toContain("Circuit de Monaco");
    expect(html).toContain("Weekend weather");
    expect(html).toContain("Weekend forecast");
    expect(html).not.toContain("Fri / Sat / Sun");
    expect(html).toContain("Fri");
    expect(html).toContain("Sat");
    expect(html).toContain("Sun");
    expect(html).not.toContain("Thu");
    expect(html).toContain("25C / 19C");
    expect(html).toContain("Rain 70%");
  });

  it("renders an ongoing session card when the first open session is already live", () => {
    const html = renderToStaticMarkup(
      createElement(DashboardShell, {
        snapshot: {
          ...snapshot,
          generated_at_utc: "2026-06-05T12:00:00Z",
        },
      }),
    );

    expect(html).toContain("Ongoing session");
    expect(html).toContain("Practice 1");
    expect(html).toContain("Now live");
    expect(html).not.toContain("Countdown to next session");
  });

  it("renders the countdown as fixed time fields", () => {
    const html = renderToStaticMarkup(
      createElement(DashboardShell, {
        snapshot,
      }),
    );

    expect(html).toContain("Countdown to next session");
    expect(html).toContain("TAGE");
    expect(html).toContain("STD");
    expect(html).toContain("MIN");
    expect(html).toContain("SEK");
    expect(html).toContain("Weekend");
    expect(html).not.toContain("Race Weekend");
    expect(html).not.toContain("Formula One Dashboard");
  });

  it("renders a fallback session card when schedule data is unavailable", () => {
    const html = renderToStaticMarkup(
      createElement(DashboardShell, {
        snapshot: {
          ...snapshot,
          sessions: [],
        },
      }),
    );

    expect(html).toContain("Weekend session data unavailable");
    expect(html).toContain("Waiting for cached or live schedule data");
  });
});
