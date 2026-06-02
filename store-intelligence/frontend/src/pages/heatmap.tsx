import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getHeatmap } from '@/services/api';
import type { HeatmapResponse, HeatmapZone } from '@/types';
import { Card } from '@/components/ui/card';
import HeatmapTable from '@/components/charts/HeatmapTable';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface HeatmapPageProps {
  storeId: string;
  date: string;
}

const gradient = (score: number) => {
  if (score >= 70) return 'from-emerald-500 to-lime-400';
  if (score >= 40) return 'from-yellow-300 to-orange-400';
  return 'from-rose-300 to-rose-500';
};

export default function HeatmapPage({ storeId, date }: HeatmapPageProps) {
  const { data, isLoading, isError } = useQuery<HeatmapResponse, Error, HeatmapResponse>({
    queryKey: ['heatmap', storeId, date],
    queryFn: () => getHeatmap(storeId, date),
  });
  const [showScore, setShowScore] = useState(true);
  const [selectedZone, setSelectedZone] = useState<HeatmapZone | null>(null);

  const zones = data?.zones || [];
  const totalVisitCount = useMemo(() => zones.reduce((sum, zone) => sum + zone.visit_count, 0), [zones]);

  useEffect(() => {
    if (data) console.info('[ui] heatmap', { storeId, date, zones: data.zones, data_confidence: data.data_confidence });
  }, [data, storeId, date]);

  useEffect(() => {
    if (!selectedZone && zones.length > 0) {
      setSelectedZone(zones[0]);
    }
  }, [zones, selectedZone]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Heatmap analytics</p>
        <h1 className="text-3xl font-semibold">Zone performance and dwell insights</h1>
        <p className="max-w-2xl text-slate-600 dark:text-slate-400">
          Explore which store zones received traffic and where dwell time is strongest.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="space-y-4 p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Store heatmap</p>
              <h2 className="text-xl font-semibold">Zone metrics</h2>
            </div>
            <button
              onClick={() => setShowScore(!showScore)}
              className="inline-flex items-center gap-2 rounded-3xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
            >
              {showScore ? 'Hide' : 'Show'} score
            </button>
          </div>
          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <Skeleton key={index} className="h-40 rounded-3xl" />
              ))}
            </div>
          ) : isError ? (
            <p className="text-sm text-rose-500">Unable to load heatmap analytics.</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {zones.map((zone) => (
                <button
                  key={zone.zone_id}
                  type="button"
                  onClick={() => setSelectedZone(zone)}
                  className={cn(
                    'rounded-3xl border p-5 shadow-sm transition hover:scale-[1.01] focus:outline-none focus:ring-2 focus:ring-sky-500',
                    selectedZone?.zone_id === zone.zone_id
                      ? 'border-sky-500 bg-slate-100 dark:border-sky-400 dark:bg-slate-900'
                      : 'border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-950',
                  )}
                >
                  <p className="text-sm uppercase tracking-[0.24em] text-slate-800/80 dark:text-slate-400">{zone.zone_id}</p>
                  <div className="mt-4 flex items-end justify-between gap-4">
                    <div>
                      <p className="text-4xl font-semibold">{zone.visit_count}</p>
                      <p className="text-sm text-slate-900/80 dark:text-slate-900/80">visits</p>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-semibold">{zone.avg_dwell_sec.toFixed(1)}s</p>
                      <p className="text-sm text-slate-900/80 dark:text-slate-900/80">avg dwell</p>
                    </div>
                  </div>
                  {showScore && (
                    <div className="mt-4 rounded-3xl bg-white/70 px-4 py-3 text-slate-900 shadow-sm dark:bg-slate-950/90 dark:text-slate-100">
                      <p className="text-xs uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Score</p>
                      <p className="mt-1 text-2xl font-semibold">{zone.score_0_100}</p>
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
            <p className="text-sm text-slate-500 dark:text-slate-400">Total zone visits</p>
            <p className="mt-1 text-3xl font-semibold text-slate-900 dark:text-slate-100">{totalVisitCount}</p>
          </div>
        </Card>
        <Card className="p-6">
          <div className="space-y-4">
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Confidence</p>
              <p className="text-xl font-semibold">{data?.data_confidence ?? 'low'}</p>
            </div>
            <div className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
              <p>Zones are ranked by visit count, dwell, and score intensity.</p>
              <p>Click a tile to see fast zone details.</p>
            </div>
          </div>
        </Card>
      </div>

      <Card className="space-y-4 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Store layout</p>
            <h2 className="text-xl font-semibold">Interactive zone view</h2>
          </div>
          <span className="text-sm text-slate-500 dark:text-slate-400">Click any zone below</span>
        </div>
        <div className="space-y-4">
          {zones.length > 0 ? (
            zones.map((zone) => (
              <button
                key={zone.zone_id}
                type="button"
                onClick={() => setSelectedZone(zone)}
                className={cn(
                  'group flex items-center justify-between rounded-3xl border px-4 py-4 transition',
                  selectedZone?.zone_id === zone.zone_id
                    ? 'border-sky-500 bg-sky-50/80 text-slate-900 dark:border-sky-400 dark:bg-slate-900'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200 dark:hover:border-slate-700 dark:hover:bg-slate-900',
                )}
              >
                <div>
                  <p className="font-semibold">{zone.zone_id}</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{zone.visit_count} visits</p>
                </div>
                <div className="h-3 w-40 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                  <div className="h-full rounded-full bg-gradient-to-r from-sky-500 to-cyan-400" style={{ width: `${Math.max(10, zone.score_0_100)}%` }} />
                </div>
              </button>
            ))
          ) : (
            <p className="text-slate-600 dark:text-slate-400">No zone data available.</p>
          )}
        </div>
        {selectedZone ? (
          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6 dark:border-slate-800 dark:bg-slate-900">
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Zone details</p>
            <h3 className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">{selectedZone.zone_id}</h3>
            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              <div className="rounded-3xl bg-white p-4 dark:bg-slate-950">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Visitors</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">{selectedZone.visit_count}</p>
              </div>
              <div className="rounded-3xl bg-white p-4 dark:bg-slate-950">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Avg dwell</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">{selectedZone.avg_dwell_sec.toFixed(0)}s</p>
              </div>
              <div className="rounded-3xl bg-white p-4 dark:bg-slate-950">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Score</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">{selectedZone.score_0_100}</p>
              </div>
            </div>
          </div>
        ) : null}
      </Card>

      {data && <HeatmapTable zones={data.zones} />}
    </div>
  );
}
