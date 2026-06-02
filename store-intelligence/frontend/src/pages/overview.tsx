import { motion } from 'framer-motion';
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, BarChart3, CheckCircle2, ShoppingBag, Sparkles, TrendingUp, Users } from 'lucide-react';
import { getMetrics, getFunnel, getHeatmap } from '@/services/api';
import type { MetricsResponse, FunnelResponse, HeatmapResponse } from '@/types';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import FunnelChart from '@/components/charts/FunnelChart';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

interface OverviewPageProps {
  storeId: string;
  date: string;
}

const cards = [
  { label: 'Unique Visitors', icon: Users, key: 'unique_visitors' as const },
  { label: 'Converted Visitors', icon: CheckCircle2, key: 'converted_visitors' as const },
  { label: 'Conversion Rate', icon: Sparkles, key: 'conversion_rate' as const },
  { label: 'Transactions', icon: ShoppingBag, key: 'total_transactions' as const },
  { label: 'Queue Depth', icon: Activity, key: 'current_queue_depth' as const },
  { label: 'Abandonment Rate', icon: TrendingUp, key: 'queue_abandonment_rate' as const },
] as const;

export default function OverviewPage({ storeId, date }: OverviewPageProps) {
  const metricsQuery = useQuery<MetricsResponse, Error, MetricsResponse>({
    queryKey: ['metrics', storeId, date],
    queryFn: () => getMetrics(storeId, date),
    refetchInterval: 15000,
    staleTime: 10000,
  });

  const funnelQuery = useQuery<FunnelResponse, Error, FunnelResponse>({
    queryKey: ['funnel', storeId, date],
    queryFn: () => getFunnel(storeId, date),
    refetchInterval: 15000,
    staleTime: 10000,
  });

  const heatmapQuery = useQuery<HeatmapResponse, Error, HeatmapResponse>({
    queryKey: ['heatmap', storeId, date],
    queryFn: () => getHeatmap(storeId, date),
    refetchInterval: 15000,
    staleTime: 10000,
  });

  const { data: metrics, isLoading: metricsLoading, isError: metricsError } = metricsQuery;
  const { data: funnel, isLoading: funnelLoading } = funnelQuery;
  const { data: heatmap, isLoading: heatmapLoading } = heatmapQuery;

  // Debugging: log API responses to console for tracing
  useEffect(() => {
    if (metrics) console.info('[ui] metrics', metrics);
  }, [metrics]);
  useEffect(() => {
    if (funnel) console.info('[ui] funnel', funnel);
  }, [funnel]);
  useEffect(() => {
    if (heatmap) console.info('[ui] heatmap', heatmap);
  }, [heatmap]);

  // Chart data for zones
  const zoneChartData = heatmap?.zones
    .sort((a, b) => b.visit_count - a.visit_count)
    .slice(0, 6)
    .map((zone) => ({
      name: zone.zone_id,
      visits: zone.visit_count,
      dwell: zone.avg_dwell_sec,
      score: zone.score_0_100,
    })) || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Dashboard</p>
        <h1 className="text-3xl font-semibold">Retail Intelligence Command Center</h1>
        <p className="max-w-2xl text-slate-600 dark:text-slate-400">
          Real-time KPIs for ST1008 with conversion, queue, traffic, and transaction performance. Auto-refreshes every 15 seconds.
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          const value = metrics
            ? card.key === 'conversion_rate' || card.key === 'queue_abandonment_rate'
              ? `${((metrics[card.key] as number) * 100).toFixed(1)}%`
              : metrics[card.key]
            : null;
          return (
            <Card
              key={card.key}
              className={`group overflow-hidden transition ${
                card.key === 'conversion_rate' ? 'ring-2 ring-emerald-400/30' : ''
              }`}
            >
              <div className="flex items-center justify-between gap-4 p-6">
                <div className="flex-1">
                  <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
                    {card.label}
                  </p>
                  {metricsLoading ? (
                    <Skeleton className="mt-3 h-12 w-40 rounded-2xl" />
                  ) : metricsError ? (
                    <p className="mt-3 text-sm text-rose-500">Failed to load</p>
                  ) : (
                    <motion.p
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="mt-3 text-3xl font-semibold text-slate-900 dark:text-slate-100"
                    >
                      {value}
                    </motion.p>
                  )}
                </div>
                <div className="flex h-14 w-14 items-center justify-center rounded-3xl bg-gradient-to-br from-slate-100 to-slate-200 text-slate-700 transition group-hover:from-sky-100 group-hover:to-blue-100 group-hover:text-sky-700 dark:from-slate-800 dark:to-slate-700 dark:text-slate-200 dark:group-hover:from-sky-900 dark:group-hover:to-blue-800 dark:group-hover:text-sky-300">
                  <Icon size={24} />
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid gap-4 xl:grid-cols-2">
        {/* Funnel Chart */}
        {funnelLoading ? (
          <Skeleton className="h-96 rounded-3xl" />
        ) : funnel ? (
          <FunnelChart stages={funnel.stages} />
        ) : null}

        {/* Zone Rankings */}
        {heatmapLoading ? (
          <Skeleton className="h-96 rounded-3xl" />
        ) : (
          <Card className="p-6">
            <div className="mb-4">
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Zone Activity</p>
              <h2 className="text-xl font-semibold">Top zones by visits</h2>
            </div>
            {zoneChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={zoneChartData} margin={{ top: 8, right: 16, left: 0, bottom: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #475569',
                      borderRadius: '12px',
                      color: '#f1f5f9',
                    }}
                  />
                  <Bar dataKey="visits" fill="#38bdf8" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center text-slate-600 dark:text-slate-400">No zone data available</p>
            )}
          </Card>
        )}
      </div>

      {/* Info Section */}
      <Card className="p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Dataset</p>
            <h2 className="text-xl font-semibold">Live analytics snapshot</h2>
            <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-400">
              All metrics are pulled from the live CV pipeline and update every 15 seconds. Funnel data includes ENTRY, ZONE_VISIT, BILLING_QUEUE, and PURCHASE stages.
            </p>
            {!metricsLoading && !metricsError && metrics && metrics.unique_visitors === 0 && metrics.total_transactions === 0 ? (
              <p className="mt-4 rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-500/30 dark:bg-amber-900/20 dark:text-amber-200">
                No data found for {date}. Please select a date with events, such as 2026-04-10.
              </p>
            ) : null}
          </div>
          <div className="flex flex-col gap-2">
            <div className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-900">
              <span className="font-semibold text-slate-800 dark:text-slate-100">Date:</span> {date}
            </div>
            <div className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-900">
              <span className="font-semibold text-slate-800 dark:text-slate-100">Store:</span> {storeId}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

