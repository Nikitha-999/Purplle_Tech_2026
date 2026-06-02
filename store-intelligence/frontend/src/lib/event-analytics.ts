import type { EventRecord } from '@/types';

export type CameraStatus = {
  camera_id: string;
  count: number;
  last_seen: string;
};

export type ZoneSummary = {
  zone_id: string;
  visit_count: number;
  avg_dwell_sec: number;
  score: number;
};

export type EventInsights = {
  title: string;
  description: string;
};

const EXIT_EVENTS = new Set(['EXIT']);

export function parseEventStream(text: string): EventRecord[] {
  return text
    .split('\n')
    .filter((line) => line.trim().length > 0)
    .map((line) => JSON.parse(line) as EventRecord);
}

export function getLiveVisitorIds(events: EventRecord[]) {
  const lastByVisitor = new Map<string, EventRecord>();
  events
    .slice()
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .forEach((event) => {
      lastByVisitor.set(event.visitor_id, event);
    });

  const insideVisitors = new Set<string>();
  const queueVisitors = new Set<string>();

  lastByVisitor.forEach((event, visitor_id) => {
    if (!EXIT_EVENTS.has(event.event_type)) {
      insideVisitors.add(visitor_id);
    }
    if (event.zone_id === 'BILLING_QUEUE' || event.metadata?.sku_zone === 'QUEUE') {
      queueVisitors.add(visitor_id);
    }
  });

  return {
    insideVisitors: Array.from(insideVisitors),
    queueVisitors: Array.from(queueVisitors),
  };
}

export function getCameraStatuses(events: EventRecord[]): CameraStatus[] {
  const cameraMap = new Map<string, { count: number; lastSeen: string }>();
  events.forEach((event) => {
    const existing = cameraMap.get(event.camera_id) ?? { count: 0, lastSeen: event.timestamp };
    existing.count += 1;
    if (new Date(event.timestamp) > new Date(existing.lastSeen)) {
      existing.lastSeen = event.timestamp;
    }
    cameraMap.set(event.camera_id, existing);
  });

  return Array.from(cameraMap.entries())
    .map(([camera_id, payload]) => ({
      camera_id,
      count: payload.count,
      last_seen: payload.lastSeen,
    }))
    .sort((a, b) => b.count - a.count);
}

export function getZoneSummaries(events: EventRecord[]) {
  const byZone = new Map<string, { visits: number; dwellTotal: number; dwellCount: number }>();

  events.forEach((event) => {
    if (!event.zone_id) return;
    const current = byZone.get(event.zone_id) ?? { visits: 0, dwellTotal: 0, dwellCount: 0 };
    if (event.event_type === 'ZONE_ENTER' || event.event_type === 'ZONE_EXIT') {
      current.visits += 1;
    }
    if (typeof event.dwell_ms === 'number' && event.dwell_ms > 0) {
      current.dwellTotal += event.dwell_ms;
      current.dwellCount += 1;
    }
    byZone.set(event.zone_id, current);
  });

  const totals = Array.from(byZone.values()).reduce((sum, value) => sum + value.visits, 0) || 1;

  return Array.from(byZone.entries()).map(([zone_id, payload]) => ({
    zone_id,
    visit_count: payload.visits,
    avg_dwell_sec: payload.dwellCount ? payload.dwellTotal / payload.dwellCount / 1000 : 0,
    score: Math.round((payload.visits / totals) * 100),
  }));
}

export function getInsights(events: EventRecord[], conversionRate?: number, anomalyCount?: number): EventInsights[] {
  const zones = getZoneSummaries(events);
  const totalVisits = zones.reduce((sum, zone) => sum + zone.visit_count, 0);
  const average = zones.length ? totalVisits / zones.length : 0;
  const sortedByVisits = [...zones].sort((a, b) => b.visit_count - a.visit_count);
  const sortedByDwell = [...zones].sort((a, b) => b.avg_dwell_sec - a.avg_dwell_sec);
  const topZone = sortedByVisits[0];
  const topDwell = sortedByDwell[0];
  const queueStrength = zones.find((zone) => zone.zone_id === 'BILLING_QUEUE')?.visit_count ?? 0;

  const insights: EventInsights[] = [];

  if (topZone) {
    const delta = average ? Math.round(((topZone.visit_count - average) / average) * 100) : 0;
    insights.push({
      title: `${topZone.zone_id} received the most traffic`,
      description: `${topZone.zone_id} attracted ${delta}% more visits than the average zone today.`,
    });
  }

  if (queueStrength > 4) {
    insights.push({
      title: 'Billing queue congestion detected',
      description: `There are ${queueStrength} visitors currently queued at the billing counter, signaling potential checkout delays.`,
    });
  }

  if (topDwell) {
    insights.push({
      title: `${topDwell.zone_id} generated the highest dwell time`,
      description: `Average dwell is ${topDwell.avg_dwell_sec.toFixed(0)} seconds in ${topDwell.zone_id}.`,
    });
  }

  if (typeof conversionRate === 'number') {
    insights.push({
      title: 'Conversion rate snapshot',
      description: `Current store conversion is ${(conversionRate * 100).toFixed(0)}% today.`,
    });
  }

  if (typeof anomalyCount === 'number' && anomalyCount > 0) {
    insights.push({
      title: 'Anomaly summary',
      description: `There are ${anomalyCount} active alerts. Review the command center for urgent issues.`,
    });
  }

  return insights.slice(0, 5);
}
