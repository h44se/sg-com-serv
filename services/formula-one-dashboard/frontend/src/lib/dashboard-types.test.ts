import { describe, expect, it } from "vitest";
import type {
  DashboardSnapshot,
  LapSample,
  Meeting,
  PositionSample,
  RaceControlMessage,
} from "@/lib/dashboard-types";

describe("dashboard type contract", () => {
  it("keeps DTO helper types assignable", () => {
    const meeting: Meeting = {
      meeting_key: 1,
      meeting_name: "Monaco Grand Prix",
      meeting_official_name: null,
      location: "Monte Carlo",
      country_code: "MON",
      country_name: "Monaco",
    };

    const latestPosition: PositionSample = {
      date_utc: "2026-06-05T11:30:00Z",
      session_key: 10,
      meeting_key: 1,
      driver_number: 16,
      position: 1,
    };

    const latestLap: LapSample = {
      meeting_key: 1,
      session_key: 10,
      driver_number: 16,
      lap_number: 18,
      date_start_utc: "2026-06-05T11:35:00Z",
      payload: { sector_1_ms: 28123 },
    };

    const raceControlMessage: RaceControlMessage = {
      meeting_key: 1,
      session_key: 10,
      date_utc: "2026-06-05T11:36:00Z",
      category: "Flag",
      message: "Yellow flag in sector 2",
    };

    const snapshot: DashboardSnapshot = {
      meeting,
      sessions: [],
      latest_positions: [latestPosition],
      latest_laps: [latestLap],
      race_control: [raceControlMessage],
      latest_results: [],
      driver_standings: [],
      constructor_standings: [],
      venue: null,
      generated_at_utc: "2026-06-05T11:40:00Z",
    };

    expect(snapshot.latest_positions).toHaveLength(1);
    expect(snapshot.latest_laps[0]?.payload).toEqual({ sector_1_ms: 28123 });
    expect(snapshot.race_control[0]?.message).toContain("Yellow flag");
  });
});
