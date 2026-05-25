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

export function formatCountdown(targetUtcIso: string, now: Date = new Date()): string {
  const target = new Date(targetUtcIso).getTime();
  const diff = Math.max(0, target - now.getTime());
  const totalSeconds = Math.floor(diff / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (days > 0) {
    return `${days}d ${hours}h`;
  }
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }
  return `${seconds}s`;
}
