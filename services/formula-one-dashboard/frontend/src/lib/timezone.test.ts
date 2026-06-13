import { describe, expect, it } from "vitest";
import { getCountdownParts } from "@/lib/timezone";

describe("getCountdownParts", () => {
  it("returns days and hours for distant targets", () => {
    const result = getCountdownParts(
      "2026-05-24T20:30:00Z",
      new Date("2026-05-22T20:30:00Z"),
    );

    expect(result).toEqual({
      days: 2,
      hours: 0,
      minutes: 0,
      seconds: 0,
    });
  });

  it("returns minutes and seconds when less than one hour remains", () => {
    const result = getCountdownParts(
      "2026-05-22T20:31:30Z",
      new Date("2026-05-22T20:30:00Z"),
    );

    expect(result).toEqual({
      days: 0,
      hours: 0,
      minutes: 1,
      seconds: 30,
    });
  });

  it("does not go below zero for past targets", () => {
    const result = getCountdownParts(
      "2026-05-22T20:29:00Z",
      new Date("2026-05-22T20:30:00Z"),
    );

    expect(result).toEqual({
      days: 0,
      hours: 0,
      minutes: 0,
      seconds: 0,
    });
  });
});
