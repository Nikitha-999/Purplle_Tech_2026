import { useEffect, useMemo, useState } from 'react';
import { Bell, Clock3, FileText, Monitor, ShieldAlert, Sparkles, Users } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getAnomalies, getMetrics } from '@/services/api';
import type { AnomalyResponse, MetricsResponse } from '@/types';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { parseEventStream, getCameraStatuses, getInsights, getLiveVisitorIds } from '@/lib/event-analytics';

interface CommandCenterPageProps {
  storeId: string;
  date?: string;
}

export default function CommandCenterPage({ storeId, date }: CommandCenterPageProps) {
  const [events, setEvents] = useState<string | null>(null);
  const [isLoadingEvents, setLoadingEvents] = useState(true);
  const [eventError, setEventError] = useState<string | null>(null);

  const metricsQuery = useQuery<MetricsResponse, Error, MetricsResponse>({
    queryKey: ['metrics', storeId, date],
    queryFn: () => getMetrics(storeId, date),
    staleTime: 10000,
    refetchInterval: 20000,
  });

  const anomaliesQuery = useQuery<AnomalyResponse, Error, AnomalyResponse>({
    queryKey: ['anomalies', storeId, date],
    queryFn: () => getAnomalies(storeId, date),
    staleTime: 10000,
    refetchInterval: 20000,
  });

  useEffect(() => {
    if (metricsQuery.data) console.info('[ui] command-center metrics', { storeId, date, data: metricsQuery.data });
  }, [metricsQuery.data, storeId, date]);
  useEffect(() => {
    if (anomaliesQuery.data) console.info('[ui] command-center anomalies', { storeId, date, data: anomaliesQuery.data });
  }, [anomaliesQuery.data, storeId, date]);

  useEffect(() => {
    fetch('/events.jsonl')
      .then(async (response) => {
        if (!response.ok) throw new Error('Unable to load events');
        return response.text();
      })
      .then((text) => setEvents(text))
      .catch((err) => setEventError(err.message))
      .finally(() => setLoadingEvents(false));
  }, []);

  const parsedEvents = useMemo(() => {
    if (!events) return [];
    return parseEventStream(events);
  }, [events]);

  const visitorState = useMemo(() => getLiveVisitorIds(parsedEvents), [parsedEvents]);
  const cameraStatuses = useMemo(() => getCameraStatuses(parsedEvents).slice(0, 5), [parsedEvents]);
  const insights = useMemo(
    () => getInsights(parsedEvents, metricsQuery.data?.conversion_rate, anomaliesQuery.data?.anomalies.length),
    [parsedEvents, metricsQuery.data, anomaliesQuery.data],
  );

  const activeCameraSummary = cameraStatuses.length > 0 ? `${cameraStatuses.length} cameras active` : 'No camera activity yet';
  const liveVisitors = visitorState.insideVisitors.length;
  const queueLength = visitorState.queueVisitors.length;
  const conversionRate = metricsQuery.data?.conversion_rate ? `${(metricsQuery.data.conversion_rate * 100).toFixed(0)}%` : '--';
  const anomalyCount = anomaliesQuery.data?.anomalies.length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Command center</p>
        <h1 className="text-3xl font-semibold">Real-time store operations</h1>
        <p className="max-w-2xl text-slate-600 dark:text-slate-400">
          Live shopper flow, queue pressure, camera activity, and alert telemetry for ST1008.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="flex items-center justify-between gap-4 p-6">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Visitors inside</p>
            <p className="mt-3 text-4xl font-semibold text-slate-900 dark:text-slate-100">{liveVisitors}</p>
          </div>
          <Users size={32} className="text-sky-500" />
        </Card>
        <Card className="flex items-center justify-between gap-4 p-6">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Queue length</p>
            <p className="mt-3 text-4xl font-semibold text-slate-900 dark:text-slate-100">{queueLength}</p>
          </div>
          <Clock3 size={32} className="text-amber-500" />
        </Card>
        <Card className="flex items-center justify-between gap-4 p-6">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Conversion rate</p>
            <p className="mt-3 text-4xl font-semibold text-slate-900 dark:text-slate-100">{conversionRate}</p>
          </div>
          <Sparkles size={32} className="text-emerald-500" />
        </Card>
        <Card className="flex items-center justify-between gap-4 p-6">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Alerts live</p>
            <p className="mt-3 text-4xl font-semibold text-slate-900 dark:text-slate-100">{anomalyCount}</p>
          </div>
          <Bell size={32} className="text-rose-500" />
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
        <Card className="space-y-6 p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Operational summary</p>
              <h2 className="text-xl font-semibold">Live store telemetry</h2>
            </div>
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-2 rounded-3xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-950 dark:hover:bg-slate-200"
            >
              <FileText size={16} /> Generate Daily Report
            </button>
          </div>

          {isLoadingEvents ? (
            <div className="grid gap-4">
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} className="h-20 rounded-3xl" />
              ))}
            </div>
          ) : eventError ? (
            <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-rose-700 dark:border-rose-800 dark:bg-rose-950/20 dark:text-rose-100">
              {eventError}
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-3xl bg-slate-50 p-6 dark:bg-slate-900">
                <p className="text-sm text-slate-500 dark:text-slate-400">Active camera fleet</p>
                <p className="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">{activeCameraSummary}</p>
              </div>
              <div className="rounded-3xl bg-slate-50 p-6 dark:bg-slate-900">
                <p className="text-sm text-slate-500 dark:text-slate-400">Store occupancy</p>
                <p className="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">{liveVisitors} visitors</p>
              </div>
              <div className="rounded-3xl bg-slate-50 p-6 dark:bg-slate-900">
                <p className="text-sm text-slate-500 dark:text-slate-400">Update cadence</p>
                <p className="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">Every 20s</p>
              </div>
            </div>
          )}
        </Card>

        <Card className="space-y-4 p-6">
          <div className="flex items-center gap-3">
            <Monitor size={24} className="text-slate-900 dark:text-slate-100" />
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Active camera stream</p>
              <h2 className="text-xl font-semibold">Camera performance</h2>
            </div>
          </div>
          <div className="space-y-3">
            {cameraStatuses.map((camera) => (
              <div key={camera.camera_id} className="rounded-3xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold text-slate-900 dark:text-slate-100">{camera.camera_id}</p>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                    {camera.count} events
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Last seen {new Date(camera.last_seen).toLocaleTimeString()}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="space-y-4 p-6">
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Urgent alerts</p>
          {anomaliesQuery.isLoading ? (
            <Skeleton className="h-40 rounded-3xl" />
          ) : anomaliesQuery.isError || !anomaliesQuery.data ? (
            <p className="text-sm text-rose-500">Unable to load alerts.</p>
          ) : anomaliesQuery.data.anomalies.length === 0 ? (
            <p className="text-slate-600 dark:text-slate-400">No active anomalies detected.</p>
          ) : (
            <div className="space-y-3">
              {anomaliesQuery.data.anomalies.slice(0, 3).map((anomaly) => (
                <div key={`${anomaly.anomaly_type}-${anomaly.zone_id ?? 'none'}`} className="rounded-3xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-800 dark:bg-rose-950/10">
                  <p className="text-sm font-semibold text-slate-900 dark:text-rose-100">{anomaly.anomaly_type}</p>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{anomaly.description}</p>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="space-y-4 p-6">
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Insights preview</p>
          {insights.length === 0 ? (
            <p className="text-slate-600 dark:text-slate-400">Processing event signals…</p>
          ) : (
            <div className="space-y-3">
              {insights.map((insight) => (
                <div key={insight.title} className="rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
                  <p className="font-semibold text-slate-900 dark:text-slate-100">{insight.title}</p>
                  <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{insight.description}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
