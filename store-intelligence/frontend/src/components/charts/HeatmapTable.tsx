import { useMemo, useState } from 'react';
import { ArrowDown, ArrowUp } from 'lucide-react';
import type { HeatmapZone } from '@/types';
import { Card } from '@/components/ui/card';

const sortFields = ['zone_id', 'visit_count', 'avg_dwell_sec', 'score_0_100'] as const;

type SortField = typeof sortFields[number];

interface HeatmapTableProps {
  zones: HeatmapZone[];
}

export default function HeatmapTable({ zones }: HeatmapTableProps) {
  const [sortField, setSortField] = useState<SortField>('score_0_100');
  const [direction, setDirection] = useState<'asc' | 'desc'>('desc');

  const sorted = useMemo(() => {
    return [...zones].sort((a, b) => {
      const left = a[sortField];
      const right = b[sortField];
      if (typeof left === 'string' && typeof right === 'string') {
        return direction === 'asc' ? left.localeCompare(right) : right.localeCompare(left);
      }
      return direction === 'asc' ? (left as number) - (right as number) : (right as number) - (left as number);
    });
  }, [zones, sortField, direction]);

  const toggleSort = (field: SortField) => {
    if (field === sortField) {
      setDirection(direction === 'asc' ? 'desc' : 'asc');
      return;
    }
    setSortField(field);
    setDirection('desc');
  };

  return (
    <Card className="overflow-hidden p-4">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Heatmap table</p>
          <h2 className="text-xl font-semibold">Zone performance details</h2>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-y-3 text-left text-sm">
          <thead>
            <tr className="text-slate-500 dark:text-slate-400">
              <th />
              <th className="px-3 py-3">Zone</th>
              <th className="px-3 py-3">Visits</th>
              <th className="px-3 py-3">Avg dwell</th>
              <th className="px-3 py-3">Score</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((zone) => (
              <tr key={zone.zone_id} className="rounded-3xl border border-slate-200 bg-slate-50 transition hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:hover:bg-slate-800">
                <td className="px-3 py-4 text-slate-400">•</td>
                <td className="px-3 py-4 font-semibold text-slate-900 dark:text-slate-100">{zone.zone_id}</td>
                <td className="px-3 py-4">{zone.visit_count}</td>
                <td className="px-3 py-4">{zone.avg_dwell_sec.toFixed(1)}s</td>
                <td className="px-3 py-4">{zone.score_0_100}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
