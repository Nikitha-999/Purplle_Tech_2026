import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, BarChart3, ShieldCheck } from 'lucide-react';
import { getAnomalies } from '@/services/api';
import type { AnomalyResponse } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface AnomaliesPageProps {
  storeId: string;
  date: string;
}

const severityLabel = (severity: string) => {
  const lower = severity.toLowerCase();
  if (lower.includes('high') || lower.includes('critical')) return 'CRITICAL';
  if (lower.includes('medium') || lower.includes('warn')) return 'WARN';
  return 'INFO';
};

const suggestedActions: Record<string, string> = {
  QUEUE_SPIKE: 'Review queue staffing and optimize billing throughput.',
  CONVERSION_DROP: 'Investigate customer flow and promotional placement.',
  DEAD_ZONE: 'Refresh assortment or signage in the quiet zone.',
};

export default function AnomaliesPage({ storeId, date }: AnomaliesPageProps) {
  const { data, isLoading, isError } = useQuery<AnomalyResponse, Error, AnomalyResponse>({
    queryKey: ['anomalies', storeId, date],
    queryFn: () => getAnomalies(storeId, date),
    refetchInterval: 15000,
    staleTime: 10000,
  });

  useEffect(() => {
    if (data) console.info('[ui] anomalies', { storeId, date, data });
  }, [data, storeId, date]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Anomalies center</p>
        <h1 className="text-3xl font-semibold">Operational risks and alerts</h1>
        <p className="max-w-2xl text-slate-600 dark:text-slate-400">
          Detect warnings across queue, conversion, and zone activity at a glance.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card className="p-6">
          <div className="flex items-center gap-3">
            <ShieldCheck size={24} className="text-sky-500" />
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Policy status</p>
              <p className="mt-1 text-xl font-semibold">{data?.anomalies.length ?? 0} alerts</p>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center gap-3">
            <AlertTriangle size={24} className="text-amber-500" />
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Latest report</p>
              <p className="mt-1 text-xl font-semibold">{date}</p>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center gap-3">
            <BarChart3 size={24} className="text-emerald-500" />
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Healthy signals</p>
              <p className="mt-1 text-xl font-semibold">{data?.anomalies.filter((entry) => entry.severity.toLowerCase() !== 'high').length ?? 0}</p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-48 rounded-3xl" />
          ))
        ) : isError || !data ? (
          <Card className="p-8 text-center text-slate-500 dark:text-slate-400">Unable to load anomalies.</Card>
        ) : data.anomalies.length === 0 ? (
          <Card className="p-8 text-center text-slate-700 dark:text-slate-300">No anomalies detected for this date.</Card>
        ) : (
          data.anomalies.map((item) => (
            <Card key={`${item.anomaly_type}-${item.zone_id ?? 'none'}`} className="space-y-4 p-6">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">{item.anomaly_type}</p>
                  <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">{item.description}</h2>
                </div>
                <Badge>{severityLabel(item.severity)}</Badge>
              </div>
              <div className="rounded-3xl bg-slate-50 p-4 text-sm text-slate-600 dark:bg-slate-900 dark:text-slate-300">
                <p className="font-semibold">Suggested action</p>
                <p className="mt-2">{suggestedActions[item.anomaly_type] ?? 'Review the store alert and investigate operational flow.'}</p>
              </div>
              <div className="flex flex-wrap gap-3 text-sm text-slate-500 dark:text-slate-400">
                <span>{item.zone_id ? `Zone ${item.zone_id}` : 'General'}</span>
                <span>Detected: {new Date().toLocaleString()}</span>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
