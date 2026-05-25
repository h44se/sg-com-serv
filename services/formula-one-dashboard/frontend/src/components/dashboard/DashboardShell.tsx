"use client";

import React, { useMemo, useState } from "react";
import type { ClassificationRow, DashboardSnapshot, Session, VenueContext } from "@/lib/dashboard-types";
import { formatUtcInTimeZone } from "@/lib/timezone";
import { CountdownTimer } from "./CountdownTimer";
import { StandingsTable } from "./StandingsTable";

export interface DashboardShellProps {
  snapshot: DashboardSnapshot | null;
  timeZone: string;
}

const RESULTS_PAGE_SIZE = 11;
const STANDINGS_PAGE_SIZE = 11;

function formatMeeting(snapshot: DashboardSnapshot) {
  if (!snapshot.meeting) {
    return "Current Formula 1 season";
  }

  return [snapshot.meeting.meeting_name, snapshot.meeting.location, snapshot.meeting.country_name].filter(Boolean).join(" · ");
}

function renderSessionTime(session: Session, timeZone: string) {
  return formatUtcInTimeZone(session.date_start_utc, timeZone);
}

function resultTitle(rows: ClassificationRow[]) {
  const status = rows[0]?.status ?? "Latest classification";
  return status.split(" · ")[0];
}

function resultMeta(row: ClassificationRow) {
  if (row.points != null) {
    return `${row.team_name ?? "Unknown team"} · ${row.points.toFixed(0)} pts`;
  }
  const [, time] = (row.status ?? "").split(" · ");
  return [row.team_name ?? "Unknown team", time].filter(Boolean).join(" · ");
}

function buildPages(rowCount: number, pageSize: number) {
  return Math.max(Math.ceil(rowCount / pageSize), 1);
}

function VenuePanel({ venue }: { venue: VenueContext | null }) {
  const circuitName = venue?.circuit_name ?? "Circuit map";

  return (
    <article className="panel venue-card">
      <div className="venue-title">
        <p className="eyebrow">Circuit</p>
        <h2 className="panel-title">{circuitName}</h2>
      </div>
      <div className="venue-map" aria-label="Circuit map">
        {venue?.track_map_svg ? <div dangerouslySetInnerHTML={{ __html: venue.track_map_svg }} /> : <span>Track map unavailable</span>}
      </div>
    </article>
  );
}

function SessionsPanel({ sessions, timeZone }: { sessions: Session[]; timeZone: string }) {
  const openSessions = sessions.slice(0, 6);

  return (
    <article className="panel sessions-card">
      <div className="panel-headline">
        <div>
          <p className="eyebrow">Open weekend sessions</p>
          <h2 className="panel-title">Weekend schedule</h2>
        </div>
        <span className="tag">{openSessions.length} open</span>
      </div>
      <div className="session-list">
        {openSessions.length === 0 ? (
          <div className="session-row empty-cell">No upcoming sessions found.</div>
        ) : (
          openSessions.map((session, index) => (
            <div className={`session-row${index === 0 ? " is-next" : ""}`} key={session.session_key}>
              <span className="rank">{session.session_type}</span>
              
              <span>{renderSessionTime(session, timeZone)}</span>
            </div>
          ))
        )}
      </div>
    </article>
  );
}

function ResultPanel({ rows }: { rows: ClassificationRow[] }) {
  const [pageIndex, setPageIndex] = useState(0);
  const pageCount = buildPages(rows.length, RESULTS_PAGE_SIZE);
  const safePageIndex = Math.min(pageIndex, pageCount - 1);
  const startIndex = safePageIndex * RESULTS_PAGE_SIZE;
  const visibleRows = useMemo(() => rows.slice(startIndex, startIndex + RESULTS_PAGE_SIZE), [rows, startIndex]);
  const canPaginate = rows.length > RESULTS_PAGE_SIZE;
  const topCount = Math.min(rows.length, RESULTS_PAGE_SIZE);

  return (
    <section className="table-card">
      <div className="table-head">
        <div>
          <span className="table-label">Latest qualifying/race result</span>
          <h2>{resultTitle(rows)}</h2>
        </div>
        <div className="table-actions">
          {canPaginate ? (
            <div className="pagination-toggle" aria-label="Result pages">
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
      <table className="standings-table result-table">
        <thead>
          <tr>
            <th className="pos-cell">Pos</th>
            <th>Driver</th>
            <th>Team / Result</th>
          </tr>
        </thead>
        <tbody>
          {visibleRows.length === 0 ? (
            <tr>
              <td className="empty-cell" colSpan={3}>
                No qualifying or race result loaded.
              </td>
            </tr>
          ) : (
            visibleRows.map((result, index) => (
              <tr key={`${result.driver_number ?? index}-${result.position ?? "na"}`}>
                <td className="pos-cell">{result.position ?? "—"}</td>
                <td className="competitor-cell">{result.driver_name ?? `Driver ${result.driver_number ?? "—"}`}</td>
                <td className="result-meta-cell">{resultMeta(result)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  );
}

export function DashboardShell({ snapshot, timeZone }: DashboardShellProps) {
  if (!snapshot) {
    return (
      <main className="loading-shell">
        <section className="loading-card">
          <div className="loading-bar" />
          <p className="kicker">Formula One Dashboard</p>
          <h1 className="panel-title">Loading dashboard…</h1>
          <p className="panel-copy">Next session, venue, latest result and standings are being synchronized.</p>
        </section>
      </main>
    );
  }

  const nextSession = snapshot.sessions[0];

  return (
    <main className="dashboard-page single-screen">
      <header className="hero compact-hero">
        <div>
          <p className="kicker">Formula One Dashboard</p>
          <h1>Race Weekend</h1>
          <p className="hero-copy">{formatMeeting(snapshot)}</p>
        </div>
        <div className="hero-meta" aria-label="Dashboard metadata">
          <div className="meta-pill">
            <span className="meta-label">Timezone</span>
            <span className="meta-value">{timeZone}</span>
          </div>
          <div className="meta-pill">
            <span className="meta-label">Updated</span>
            <span className="meta-value">{formatUtcInTimeZone(snapshot.generated_at_utc, timeZone)}</span>
          </div>
        </div>
      </header>

      <section className="overview-row" aria-label="Next session and circuit">
        <div className="next-session-stack">
          {nextSession ? <CountdownTimer targetUtcIso={nextSession.date_start_utc} label={nextSession.session_name} /> : null}
          <SessionsPanel sessions={snapshot.sessions} timeZone={timeZone} />
        </div>
        <VenuePanel venue={snapshot.venue} />
      </section>

      <section className="data-row" aria-label="Latest result and championship standings">
        <ResultPanel rows={snapshot.latest_results} />
        <StandingsTable title="Driver standings" rows={snapshot.driver_standings} pageSize={STANDINGS_PAGE_SIZE} />
        <StandingsTable title="Team standings" rows={snapshot.constructor_standings} pageSize={STANDINGS_PAGE_SIZE} />
      </section>
    </main>
  );
}
