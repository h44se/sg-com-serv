"use client";

import { useState } from "react";
import type { ChampionshipStandingRow } from "@/lib/dashboard-types";

export interface StandingsTableProps {
  title: string;
  rows: ChampionshipStandingRow[];
  pageSize?: number;
}

function buildPages(rowCount: number, pageSize: number) {
  return Math.max(Math.ceil(rowCount / pageSize), 1);
}

export function StandingsTable({
  title,
  rows,
  pageSize = 11,
}: StandingsTableProps) {
  const [pageIndex, setPageIndex] = useState(0);
  const pageCount = buildPages(rows.length, pageSize);
  const safePageIndex = Math.min(pageIndex, pageCount - 1);
  const startIndex = safePageIndex * pageSize;
  const visibleRows = rows.slice(startIndex, startIndex + pageSize);
  const canPaginate = rows.length > pageSize;

  return (
    <section className="table-card">
      <div className="table-head">
        <div>
          <span className="table-label">Championship</span>
          <h2>{title}</h2>
        </div>
        <div className="table-actions">
          {canPaginate ? (
            <div className="pagination-toggle" aria-label={`${title} pages`}>
              {Array.from({ length: pageCount }, (_, index) => (
                <button
                  aria-current={safePageIndex === index ? "page" : undefined}
                  className="page-button"
                  key={index}
                  type="button"
                  onClick={() => setPageIndex(index)}
                >
                  {index + 1}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      </div>
      <table className="standings-table">
        <thead>
          <tr>
            <th className="pos-cell">Pos</th>
            <th>Competitor</th>
            <th className="points-cell">Pts</th>
          </tr>
        </thead>
        <tbody>
          {visibleRows.length === 0 ? (
            <tr>
              <td className="empty-cell" colSpan={3}>
                No standings available yet.
              </td>
            </tr>
          ) : (
            visibleRows.map((row) => (
              <tr key={`${row.competitor_name}-${row.position ?? "na"}`}>
                <td className="pos-cell">{row.position ?? "—"}</td>
                <td className="competitor-cell">
                  {row.competitor_name}
                  {row.gap ? <p className="item-meta">Gap {row.gap}</p> : null}
                </td>
                <td className="points-cell">{row.points.toFixed(0)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  );
}
