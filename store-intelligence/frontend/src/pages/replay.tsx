import { useEffect, useMemo, useState } from 'react';
import { Pause, Play, RefreshCcw, SkipBack, SkipForward, Sparkles, Timer } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useInterval } from '@/hooks/useInterval';
import { parseEventStream } from '@/lib/event-analytics';
import type { EventRecord } from '@/types';

interface ReplayPageProps {
  storeId: string;
  date?: string;
}

const speeds = [1, 2, 4] as const;

export default function ReplayPage({ date }: ReplayPageProps) {
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<typeof speeds[number]>(1);

  useEffect(() => {
    fetch('/events.jsonl')
      .then(async (response) => {
        if (!response.ok) throw new Error('Could not load replay events');
        const text = await response.text();
        setEvents(parseEventStream(text));
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useInterval(
    () => {
      if (!playing || events.length === 0) return;
      setIndex((current) => Math.min(current + 1, events.length - 1));
    },
    playing ? Math.max(100, 1000 / speed) : null,
  );

  const currentEvent = events[index];
  const progress = events.length ? Math.round((index / (events.length - 1)) * 100) : 0;
  const recentEvents = useMemo(() => events.slice(Math.max(0, index - 6), index + 1), [events, index]);

  const summary = useMemo(() => {
    if (!currentEvent) return 'Awaiting playback.';
    return `${currentEvent.event_type} in ${currentEvent.zone_id ?? 'unknown zone'} from ${currentEvent.camera_id}`;
  }, [currentEvent]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Timeline replay</p>
        <h1 className="text-3xl font-semibold">Customer movement replay</h1>
        <p className="max-w-2xl text-slate-600 dark:text-slate-400">Play back the event stream with speed controls and a timeline slider for demo-ready motion analysis.</p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.4fr_0.6fr]">
        <Card className="space-y-6 p-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6 dark:border-slate-800 dark:bg-slate-900">
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Replay progress</p>
              <p className="mt-3 text-4xl font-semibold text-slate-900 dark:text-slate-100">{progress}%</p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6 dark:border-slate-800 dark:bg-slate-900">
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Current speed</p>
              <p className="mt-3 text-4xl font-semibold text-slate-900 dark:text-slate-100">{speed}x</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Live event</p>
                <p className="mt-2 text-lg font-semibold text-slate-900 dark:text-slate-100">{summary}</p>
              </div>
              <div className="rounded-3xl bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-900 dark:bg-slate-900 dark:text-slate-100">
                {currentEvent?.timestamp ? new Date(currentEvent.timestamp).toLocaleTimeString() : '00:00:00'}
              </div>
            </div>

            <div className="rounded-3xl bg-slate-100 p-4 dark:bg-slate-900">
              <input
                type="range"
                min={0}
                max={Math.max(0, events.length - 1)}
                value={index}
                onChange={(event) => setIndex(Number(event.target.value))}
                className="w-full"
              />
              <div className="mt-3 flex items-center justify-between text-xs uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
                <span>0</span>
                <span>{events.length ? events.length - 1 : 0}</span>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => setPlaying(!playing)}
                className="inline-flex items-center gap-2 rounded-3xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-950 dark:hover:bg-slate-200"
              >
                {playing ? <Pause size={16} /> : <Play size={16} />}
                {playing ? 'Pause' : 'Play'}
              </button>
              <button
                onClick={() => setIndex(0)}
                className="inline-flex items-center gap-2 rounded-3xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
              >
                <SkipBack size={16} /> Restart
              </button>
              <button
                onClick={() => setIndex(Math.max(0, events.length - 2))}
                className="inline-flex items-center gap-2 rounded-3xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
              >
                <SkipForward size={16} /> Near End
              </button>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {speeds.map((value) => (
                <button
                  key={value}
                  onClick={() => setSpeed(value)}
                  className={`rounded-3xl px-4 py-3 text-sm font-semibold transition ${
                    speed === value
                      ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-950'
                      : 'border border-slate-200 bg-white text-slate-900 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  {value}x
                </button>
              ))}
            </div>
          </div>
        </Card>

        <Card className="space-y-4 p-6">
          <div className="flex items-center gap-3">
            <Timer size={24} className="text-slate-900 dark:text-slate-100" />
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Event playback</p>
              <h2 className="text-xl font-semibold">Recent customer moves</h2>
            </div>
          </div>

          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, index) => (
                <Skeleton key={index} className="h-16 rounded-3xl" />
              ))}
            </div>
          ) : error ? (
            <p className="text-sm text-rose-500">{error}</p>
          ) : (
            <div className="space-y-3">
              {recentEvents.map((event) => (
                <div key={event.event_id} className="rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-semibold text-slate-900 dark:text-slate-100">{event.event_type}</p>
                    <span className="text-xs uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">{new Date(event.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{event.visitor_id} • {event.camera_id} • {event.zone_id ?? 'No zone'}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
