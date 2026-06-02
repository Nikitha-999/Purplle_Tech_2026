import { ResponsiveContainer, BarChart, Bar, XAxis, Tooltip, Cell } from 'recharts';
import { Card } from '@/components/ui/card';
import type { FunnelStage } from '@/types';

const colors = ['#22c55e', '#38bdf8', '#f59e0b', '#f43f5e'];

interface FunnelChartProps {
  stages: FunnelStage[];
}

export default function FunnelChart({ stages }: FunnelChartProps) {
  const formatted = stages.map((stage, index) => ({
    name: stage.label,
    value: stage.count,
    drop: stage.drop_off_pct,
    color: colors[index % colors.length],
  }));

  return (
    <Card className="h-[420px] p-4">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Visitor Funnel</p>
          <h2 className="text-xl font-semibold">Funnel Conversion Flow</h2>
        </div>
      </div>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={formatted} layout="vertical" margin={{ top: 12, right: 16, left: 0, bottom: 0 }}>
          <XAxis type="number" hide />
          <Tooltip
            formatter={(value: number, name: string) => [`${value.toLocaleString()}`, name]}
            labelStyle={{ color: '#0f172a' }}
          />
          <Bar dataKey="value" radius={[12, 12, 12, 12]}>
            {formatted.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
