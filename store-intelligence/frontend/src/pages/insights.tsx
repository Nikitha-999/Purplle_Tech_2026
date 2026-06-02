import { useEffect, useMemo, useState } from 'react';
import { BarChart3, Lightbulb, Sparkles, TrendingUp, Zap } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getMetrics, getAnomalies, getHeatmap } from '@/services/api';
import type { AnomalyResponse, HeatmapResponse, MetricsResponse } from '@/types';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { parseEventStream, getInsights, getZoneSummaries } from '@/lib/event-analytics';

interface InsightsPageProps {
  storeId: string;
  date?: string;
}

export default function InsightsPage({ storeId, date }: InsightsPageProps) {
  const [events, setEvents] = useState<string | null>(null);
  const [loadingEvents, setLoadingEvents] = useState(true);
  const [eventError, setEventError] = useState<string | null>(null);

  const metricsQuery = useQuery<MetricsResponse, Error, MetricsResponse>({
    queryKey: ['metrics', storeId, date],
    queryFn: () => getMetrics(storeId, date),
    staleTime: 10000,
  });

  const anomaliesQuery = useQuery<AnomalyResponse, Error, AnomalyResponse>({
    queryKey: ['anomalies', storeId, date],
    queryFn: () => getAnomalies(storeId, date),
    staleTime: 10000,
  });

  const heatmapQuery = useQuery<HeatmapResponse, Error, HeatmapResponse>({
    queryKey: ['heatmap', storeId, date],
    queryFn: () => getHeatmap(storeId, date),
    staleTime: 10000,
  });

  useEffect(() => {
    if (metricsQuery.data) console.info('[ui] insights metrics', { storeId, date, data: metricsQuery.data });
  }, [metricsQuery.data, storeId, date]);
  useEffect(() => {
    if (anomaliesQuery.data) console.info('[ui] insights anomalies', { storeId, date, data: anomaliesQuery.data });
  }, [anomaliesQuery.data, storeId, date]);
  useEffect(() => {
    if (heatmapQuery.data) console.info('[ui] insights heatmap', { storeId, date, data: heatmapQuery.data });
  }, [heatmapQuery.data, storeId, date]);

  useEffect(() => {
    fetch('/events.jsonl')
      .then(async (response) => {
        if (!response.ok) throw new Error('Failed to load replay events');
        return response.text();
      })
      .then(setEvents)
      .catch((err) => setEventError(err.message))
      .finally(() => setLoadingEvents(false));
  }, []);

  const parsedEvents = useMemo(() => (events ? parseEventStream(events) : []), [events]);

  const insights = useMemo(
    () => getInsights(parsedEvents, metricsQuery.data?.conversion_rate, anomaliesQuery.data?.anomalies.length),
    [parsedEvents, metricsQuery.data, anomaliesQuery.data],
  );

  const heatmapZones = heatmapQuery.data?.zones ?? [];
  const zoneSummaries = useMemo(() => getZoneSummaries(parsedEvents), [parsedEvents]);
  const headline = useMemo(() => {
    if (metricsQuery.data?.conversion_rate) {
      return `Conversion is strong at ${(metricsQuery.data.conversion_rate * 100).toFixed(0)}% today.`;
    }
    return 'Insights are generated from live store traffic and anomaly signals.';
  }, [metricsQuery.data]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">AI insights</p>
        <h1 className="text-3xl font-semibold">Automatic retail intelligence</h1>
        <p className="max-w-2xl text-slate-600 dark:text-slate-400">Rule-driven insights that highlight traffic shifts, checkout risk, and captive engagement zones.</p>
      </div>

      <Card className="grid gap-4 xl:grid-cols-[1.4fr_0.6fr] p-6">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Quick glance</p>
          <h2 className="text-xl font-semibold">Executive summary</h2>
          <p className="mt-3 text-slate-600 dark:text-slate-400">{headline}</p>
        </div>
        <div className="grid gap-4">
          <div className="rounded-3xl bg-slate-50 p-4 dark:bg-slate-900">
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Alerts</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900 dark:text-slate-100">{anomaliesQuery.data?.anomalies.length ?? 0}</p>
          </div>
          <div className="rounded-3xl bg-slate-50 p-4 dark:bg-slate-900">
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Heatmap zones</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900 dark:text-slate-100">{heatmapZones.length}</p>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="space-y-4 p-6">
          <div className="flex items-center gap-3">
            <Lightbulb size={24} className="text-slate-900 dark:text-slate-100" />
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Top insights</p>
              <h2 className="text-xl font-semibold">Actionable recommendations</h2>
            </div>
          </div>
          {loadingEvents ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} className="h-24 rounded-3xl" />
              ))}
            </div>
          ) : eventError ? (
            <p className="text-sm text-rose-500">{eventError}</p>
          ) : (
            <div className="space-y-4">
              {insights.map((insight) => (
                <div key={insight.title} className="rounded-3xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{insight.title}</p>
                    </div>
                    <Sparkles size={20} className="text-sky-500" />
                  </div>
                  <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{insight.description}</p>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="space-y-4 p-6">
          <div className="flex items-center gap-3">
            <TrendingUp size={24} className="text-slate-900 dark:text-slate-100" />
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Data signals</p>
              <h2 className="text-xl font-semibold">Zone performance</h2>
            </div>
          </div>
          <div className="space-y-3">
            {heatmapZones.slice(0, 4).map((zone) => (
              <div key={zone.zone_id} className="rounded-3xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-slate-900 dark:text-slate-100">{zone.zone_id}</p>
                    <p className="text-sm text-slate-500 dark:text-slate-400">{zone.visit_count} visits</p>
                  </div>
                  <div className="rounded-3xl bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                    Score {zone.score_0_100}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.4fr_0.6fr]">
        <Card className="space-y-4 p-6">
          <div className="flex items-center gap-3">
            <BarChart3 size={24} className="text-slate-900 dark:text-slate-100" />
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Traffic heatmap</p>
              <h2 className="text-xl font-semibold">Store zone intensity</h2>
            </div>
          </div>
          <div className="space-y-4">
            {heatmapZones.map((zone) => (
              <div key={zone.zone_id} className="space-y-2">
                <div className="flex items-center justify-between text-sm text-slate-700 dark:text-slate-300">
                  <span>{zone.zone_id}</span>
                  <span>{zone.visit_count} visits</span>
                </div>
                <div className="h-4 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                  <div
                    className={`h-full rounded-full bg-gradient-to-r from-sky-500 to-cyan-400`}
                    style={{ width: `${Math.max(12, zone.score_0_100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="space-y-4 p-6">
          <div className="flex items-center gap-3">
            <Zap size={24} className="text-slate-900 dark:text-slate-100" />
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Insight strength</p>
              <h2 className="text-xl font-semibold">High priority zones</h2>
            </div>
          </div>
          <div className="rounded-3xl bg-slate-50 p-4 dark:bg-slate-900">
            <p className="text-sm text-slate-500 dark:text-slate-400">Makeup or Billing dominance gives you a quick read on traffic balance.</p>
            <p className="mt-3 text-xl font-semibold text-slate-900 dark:text-slate-100">{heatmapZones[0]?.zone_id ?? 'No zone data'}</p>
          </div>
          <div className="space-y-3">
            {zoneSummaries.slice(0, 3).map((zone) => (
              <div key={zone.zone_id} className="rounded-3xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
                <p className="font-semibold text-slate-900 dark:text-slate-100">{zone.zone_id}</p>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Avg dwell {zone.avg_dwell_sec.toFixed(0)}s</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
