import { useEffect, useMemo, useState } from 'react';
import { Play, RefreshCcw, StopCircle, Video, Zap } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { EventRecord } from '@/types';
import { useInterval } from '@/hooks/useInterval';

const cameras = [
  { camera_id: 'CAM_SKINCARE', name: 'Video 1', role: 'Skincare Floor' },
  { camera_id: 'CAM_MAKEUP', name: 'Video 2', role: 'Makeup Floor' },
  { camera_id: 'CAM_ENTRY', name: 'Video 3', role: 'Entry Gate' },
  { camera_id: 'CAM_BACKROOM', name: 'Video 4', role: 'Backroom' },
  { camera_id: 'CAM_BILLING', name: 'Video 5', role: 'Billing' },
];

const assetMap: Record<string, string> = {
  'CAM_SKINCARE': '/videos/VIDEO 1.mp4',
  'CAM_MAKEUP': '/videos/VIDEO 2.mp4',
  'CAM_ENTRY': '/videos/VIDEO 3.mp4',
  'CAM_BACKROOM': '/videos/VIDEO 4.mp4',
  'CAM_BILLING': '/videos/VIDEO 5.mp4',
};

export default function ViewerPage() {
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [activeCamera, setActiveCamera] = useState(cameras[0].camera_id);
  const [replayIndex, setReplayIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/events.jsonl')
      .then(async (response) => {
        if (!response.ok) throw new Error('Unable to load event timeline');
        const text = await response.text();
        const parsed = text
          .split('\n')
          .filter(Boolean)
          .map((line) => JSON.parse(line) as EventRecord);
        setEvents(parsed);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useInterval(
    () => {
      if (!playing) return;
      setReplayIndex((current) => Math.min(current + 1, events.length - 1));
    },
    playing ? 1000 : null,
  );

  const activeEvents = useMemo(
    () => events.filter((event) => event.camera_id === activeCamera).slice(0, replayIndex + 1),
    [events, activeCamera, replayIndex],
  );

  const generatedCount = activeEvents.length;
  const staffCount = activeEvents.filter((event) => event.is_staff).length;
  const visitorCount = new Set(activeEvents.filter((event) => !event.is_staff).map((event) => event.visitor_id)).size;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Video intelligence viewer</p>
        <h1 className="text-3xl font-semibold">CCTV stream and event timeline</h1>
        <p className="max-w-2xl text-slate-600 dark:text-slate-400">
          Explore camera feeds, event counts, and replay the live visitor stream.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.9fr_0.55fr]">
        <Card className="space-y-4 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Camera selector</p>
              <h2 className="text-xl font-semibold">Browse video feeds</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                className="inline-flex items-center gap-2 rounded-3xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-900 transition hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
                onClick={() => setPlaying(!playing)}
              >
                {playing ? <StopCircle size={16} /> : <Play size={16} />}
                {playing ? 'Pause replay' : 'Play replay'}
              </button>
              <button
                onClick={() => {
                  setReplayIndex(0);
                  setPlaying(false);
                }}
                className="inline-flex items-center gap-2 rounded-3xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-900 transition hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
              >
                <RefreshCcw size={16} />
                Reset
              </button>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            {cameras.map((camera) => (
              <button
                key={camera.camera_id}
                onClick={() => setActiveCamera(camera.camera_id)}
                className={`rounded-3xl border px-4 py-3 text-sm font-semibold transition ${
                  camera.camera_id === activeCamera
                    ? 'border-slate-900 bg-slate-900 text-white dark:border-slate-100 dark:bg-slate-100 dark:text-slate-950'
                    : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800'
                }`}
              >
                {camera.name}
              </button>
            ))}
          </div>

          {loading ? (
            <Skeleton className="h-[420px] rounded-3xl" />
          ) : error ? (
            <div className="rounded-3xl border border-rose-200 bg-rose-50 p-8 text-slate-900 dark:border-rose-800 dark:bg-rose-950/20 dark:text-rose-100">
              <p className="font-semibold">Unable to load event timeline</p>
              <p className="mt-2 text-sm">{error}</p>
            </div>
          ) : (
            <div className="grid gap-4 lg:grid-cols-[1.6fr_0.9fr]">
              <div className="space-y-4 rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
                <div className="relative overflow-hidden rounded-3xl bg-slate-950/90 text-white">
                  <video
                    src={assetMap[activeCamera]}
                    controls
                    className="h-[320px] w-full bg-slate-900 object-cover"
                  >
                    Your browser does not support video playback.
                  </video>
                  <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/90 to-transparent p-4">
                    <p className="text-sm uppercase tracking-[0.24em] text-slate-300">Live preview</p>
                    <p className="mt-1 text-lg font-semibold">{cameras.find((camera) => camera.camera_id === activeCamera)?.role}</p>
                  </div>
                </div>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="rounded-3xl bg-white p-4 text-center dark:bg-slate-950">
                    <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Generated events</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">{generatedCount}</p>
                  </div>
                  <div className="rounded-3xl bg-white p-4 text-center dark:bg-slate-950">
                    <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Staff count</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">{staffCount}</p>
                  </div>
                  <div className="rounded-3xl bg-white p-4 text-center dark:bg-slate-950">
                    <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Visitor count</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">{visitorCount}</p>
                  </div>
                </div>
              </div>
              <Card className="space-y-4 p-6">
                <div className="flex items-center gap-3">
                  <Video size={24} className="text-slate-900 dark:text-slate-100" />
                  <h2 className="text-lg font-semibold">Event timeline</h2>
                </div>
                <div className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
                  {activeEvents.slice(-8).map((event) => (
                    <div key={event.event_id} className="rounded-3xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold text-slate-900 dark:text-slate-100">{event.event_type}</p>
                        <span className="text-xs uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">{new Date(event.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Visitor {event.visitor_id} {event.zone_id ? `@ ${event.zone_id}` : ''}</p>
                    </div>
                  ))}
                </div>
                <div className="rounded-3xl bg-slate-50 p-4 text-sm text-slate-600 dark:bg-slate-900 dark:text-slate-300">
                  <Zap size={18} className="inline-block" /> Replay index {replayIndex + 1} / {events.length}
                </div>
              </Card>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
