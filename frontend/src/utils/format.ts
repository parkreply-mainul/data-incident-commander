export function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown time";
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date) + " UTC";
}

export function requesterLabel(requester: Record<string, unknown> | null): string {
  if (!requester) return "Not provided";
  const name = typeof requester.name === "string" ? requester.name : "";
  const team = typeof requester.team === "string" ? requester.team : "";
  return [name, team].filter(Boolean).join(" · ") || "Not provided";
}
