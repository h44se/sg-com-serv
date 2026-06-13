export function detectBrowserTimeZone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

export function formatUtcInTimeZone(
  utcIso: string,
  timeZone: string,
  options: Intl.DateTimeFormatOptions = {},
): string {
  const date = new Date(utcIso);
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone,
    ...options,
  }).format(date);
}

export interface CountdownParts {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
}

export function getCountdownParts(
  targetUtcIso: string,
  now: Date = new Date(),
): CountdownParts {
  const target = new Date(targetUtcIso).getTime();
  const diff = Math.max(0, target - now.getTime());
  const totalSeconds = Math.floor(diff / 1000);
  return {
    days: Math.floor(totalSeconds / 86400),
    hours: Math.floor((totalSeconds % 86400) / 3600),
    minutes: Math.floor((totalSeconds % 3600) / 60),
    seconds: totalSeconds % 60,
  };
}
