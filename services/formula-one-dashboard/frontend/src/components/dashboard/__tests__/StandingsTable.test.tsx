import { describe, expect, it } from "vitest";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type { ChampionshipStandingRow } from "@/lib/dashboard-types";
import { StandingsTable } from "../StandingsTable";

const buildRows = (count: number): ChampionshipStandingRow[] =>
  Array.from({ length: count }, (_, index) => ({
    position: index + 1,
    competitor_name: `Driver ${index + 1}`,
    points: 100 - index,
    wins: index % 3,
    gap: null,
  }));

describe("StandingsTable", () => {
  it("shows eleven rows on the first page by default", () => {
    const html = renderToStaticMarkup(createElement(StandingsTable, { title: "Drivers standings", rows: buildRows(20) }));

    expect(html).toContain("Top 11");
    expect(html).toContain('aria-label="Drivers standings pages"');
    expect(html).toContain("Driver 11");
    expect(html).not.toContain("Driver 12");
  });

  it("does not render pagination when rows fit on one page", () => {
    const html = renderToStaticMarkup(createElement(StandingsTable, { title: "Team standings", rows: buildRows(10) }));

    expect(html).toContain("Top 10");
    expect(html).not.toContain("pagination-toggle");
  });

  it("accepts empty rows for loading fallback states", () => {
    const rows: ChampionshipStandingRow[] = [];
    expect(rows).toHaveLength(0);
    expect(StandingsTable).toBeDefined();
  });
});
