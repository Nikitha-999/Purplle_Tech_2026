import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Database, ShieldCheck, Wifi, Zap } from 'lucide-react';
import { getHealth } from '@/services/api';
import type { HealthResponse } from '@/types';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useInterval } from '@/hooks/useInterval';

export default function PipelinePage() {
  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: false,
    staleTime: 10000,
  });

  useInterval(() => {
    refetch();
  }, 5000);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const healthStatus = data?.status ?? 'unknown';
  const store = data?.stores?.[0];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col gap-2">
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Pipeline monitor</p>
          <h1 className="text-3xl font-semibold">Backend and ingestion health</h1>
        </div>
        <Card className="grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-40 rounded-3xl" />
          ))}
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Pipeline monitor</p>
        <h1 className="text-3xl font-semibold">Live backend health status</h1>
        <p className="max-w-2xl text-slate-600 dark:text-slate-400">
          Automatic polling keeps the dashboard aligned with backend health and queue status.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="flex items-start gap-4 p-6">
          <Wifi size={28} className="text-sky-500" />
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Service</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900 dark:text-slate-100">{healthStatus}</p>
          </div>
        </Card>
        <Card className="flex items-start gap-4 p-6">
          <Database size={28} className="text-emerald-500" />
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Database</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900 dark:text-slate-100">{data?.database ?? 'unknown'}</p>
          </div>
        </Card>
        <Card className="flex items-start gap-4 p-6">
          <ShieldCheck size={28} className="text-amber-500" />
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Warnings</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900 dark:text-slate-100">{data?.warnings.length ?? 0}</p>
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_0.9fr]">
        <Card className="space-y-4 p-6">
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Store health</p>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-3xl bg-slate-50 p-5 dark:bg-slate-900">
              <p className="text-sm text-slate-500 dark:text-slate-400">Last event time</p>
              <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-slate-100">{store?.last_event_at ?? 'N/A'}</p>
            </div>
            <div className="rounded-3xl bg-slate-50 p-5 dark:bg-slate-900">
              <p className="text-sm text-slate-500 dark:text-slate-400">Store ID</p>
              <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-slate-100">{store?.store_id ?? 'ST1008'}</p>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Health details</p>
          <div className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-400">
            <p>Backend version: <span className="font-semibold text-slate-900 dark:text-slate-100">{data?.version}</span></p>
            <p>Stores monitored: <span className="font-semibold text-slate-900 dark:text-slate-100">{data?.stores.length ?? 0}</span></p>
            <p>Auto refresh interval: <span className="font-semibold text-slate-900 dark:text-slate-100">5 seconds</span></p>
          </div>
        </Card>
      </div>

      <Card className="space-y-4 p-6">
        <h2 className="text-xl font-semibold">Active warnings</h2>
        {data?.warnings.length ? (
          <ul className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
            {data.warnings.map((warning) => (
              <li key={warning} className="rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
                {warning}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-600 dark:text-slate-400">No active warnings at this time.</p>
        )}
      </Card>
    </div>
  );
}
