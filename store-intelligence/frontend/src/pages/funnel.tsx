import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowDownRight, Layers } from 'lucide-react';
import { getFunnel } from '@/services/api';
import type { FunnelResponse } from '@/types';
import { Card } from '@/components/ui/card';
import FunnelChart from '@/components/charts/FunnelChart';
import { Skeleton } from '@/components/ui/skeleton';

interface FunnelPageProps {
  storeId: string;
  date: string;
}

export default function FunnelPage({ storeId, date }: FunnelPageProps) {
  const { data, isLoading, isError } = useQuery<FunnelResponse, Error, FunnelResponse>({
    queryKey: ['funnel', storeId, date],
    queryFn: () => getFunnel(storeId, date),
    refetchInterval: 15000,
    staleTime: 10000,
  });

  // Debug log funnel responses
  useEffect(() => {
    if (data) console.info('[ui] funnel', { storeId, date, data });
  }, [data, storeId, date]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Conversion funnel</p>
        <h1 className="text-3xl font-semibold">Visitor journey and drop-off</h1>
        <p className="max-w-2xl text-slate-600 dark:text-slate-400">
          Track how shoppers move through entry, zone visits, queue, and purchase.
        </p>
      </div>

      {isLoading && (
        <Card className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-32 rounded-3xl" />
          ))}
        </Card>
      )}

      {(!isLoading && (isError || !data)) && (
        <Card className="p-8 text-center text-slate-500 dark:text-slate-400">Unable to load funnel data.</Card>
      )}

      {(!isLoading && data && data.stages.length === 0) && (
        <Card className="p-8 text-center text-slate-600 dark:text-slate-400">No funnel data available for the selected date.</Card>
      )}

      {(!isLoading && data && data.stages.length > 0) && (
        <div className="grid gap-4 xl:grid-cols-[1.4fr_0.6fr]">
          <FunnelChart stages={data.stages} />
          <div className="space-y-4">
            <Card className="p-6">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-3xl bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100">
                  <Layers size={22} />
                </div>
                <div>
                  <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Stage count</p>
                  <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-100">{data.stages.length}</p>
                </div>
              </div>
            </Card>
            <Card className="space-y-3 p-6">
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Drop off insight</p>
              {data.stages.map((stage) => (
                <div key={stage.name} className="rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
                  <p className="font-semibold text-slate-900 dark:text-slate-100">{stage.label}</p>
                  <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                    Count: <span className="font-semibold text-slate-900 dark:text-slate-100">{stage.count}</span>
                  </p>
                  <p className="mt-1 flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                    <ArrowDownRight size={16} /> Drop-off {stage.drop_off_pct.toFixed(1)}%
                  </p>
                </div>
              ))}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
