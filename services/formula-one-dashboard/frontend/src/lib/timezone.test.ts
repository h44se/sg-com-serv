import { describe, expect, it } from "vitest";
import { formatCountdown } from "@/lib/timezone";

describe("formatCountdown", () => {
  it("shows days and hours for distant targets", () => {
    const result = formatCountdown("2026-05-24T20:30:00Z", new Date("2026-05-22T20:30:00Z"));
    expect(result).toBe("2d 0h");
  });

  it("shows minutes and seconds when less than one hour remains", () => {
    const result = formatCountdown("2026-05-22T20:31:30Z", new Date("2026-05-22T20:30:00Z"));
    expect(result).toBe("1m 30s");
  });
});
