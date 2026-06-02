import { useEffect, useMemo, useState } from 'react';
import { MapPin, Square } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface ZoneDefinition {
  zone_id: string;
  sku_zone: string;
  polygon: [number, number][];
}

interface CameraDefinition {
  camera_id: string;
  role: string;
  video_file: string;
  resolution: { width: number; height: number };
  zones: ZoneDefinition[];
}

interface LayoutPayload {
  store_id: string;
  store_name: string;
  cameras: CameraDefinition[];
}

export default function LayoutPage() {
  const [layout, setLayout] = useState<LayoutPayload | null>(null);
  const [hoveredZone, setHoveredZone] = useState<string | null>(null);
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/store_layout.json')
      .then((response) => response.json())
      .then((payload) => setLayout(payload))
      .finally(() => setLoading(false));
  }, []);

  const zones = useMemo(() => {
    if (!layout) return [];
    return layout.cameras.flatMap((camera) => camera.zones.map((zone) => ({ ...zone, camera: camera.camera_id })));
  }, [layout]);

  const effectiveZoneId = selectedZoneId ?? hoveredZone;
  const selectedZone = zones.find((zone) => zone.zone_id === effectiveZoneId) ?? zones[0];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col gap-2">
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Store layout</p>
          <h1 className="text-3xl font-semibold">Zone mapping and overlays</h1>
        </div>
        <Skeleton className="h-[520px] rounded-3xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Store layout</p>
        <h1 className="text-3xl font-semibold">SKIN, Billing, Entry and aisle zones</h1>
        <p className="max-w-2xl text-slate-600 dark:text-slate-400">
          Hover over each zone to highlight the polygon and surface its role in the store.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.4fr_0.6fr]">
        <Card className="p-6">
          <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
            <svg viewBox="0 0 1920 1080" className="h-[460px] w-full">
              <rect width="1920" height="1080" fill="#0f172a" fillOpacity="0.08" />
              {zones.map((zone) => {
                const points = zone.polygon.map(([x, y]) => `${x},${y}`).join(' ');
                const isActive = zone.zone_id === selectedZoneId || zone.zone_id === hoveredZone;
                return (
                  <g key={`${zone.zone_id}-${zone.camera}`}>
                    <polygon
                      points={points}
                      fill={isActive ? 'rgba(59,130,246,0.25)' : 'rgba(14,165,233,0.16)'}
                      stroke={isActive ? '#38bdf8' : '#0ea5e9'}
                      strokeWidth={isActive ? 3 : 2}
                      onMouseEnter={() => setHoveredZone(zone.zone_id)}
                      onMouseLeave={() => setHoveredZone(null)}
                      onClick={() => setSelectedZoneId(zone.zone_id)}
                      style={{ cursor: 'pointer' }}
                    />
                    <text x={zone.polygon[0][0] + 24} y={zone.polygon[0][1] + 34} className="text-sm font-semibold" fill="#0f172a">
                      {zone.zone_id}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </Card>

        <Card className="space-y-4 p-6">
          <div className="flex items-center gap-3">
            <MapPin size={24} className="text-slate-900 dark:text-slate-100" />
            <div>
              <p className="text-sm uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Selected zone</p>
              <h2 className="text-xl font-semibold">{selectedZone?.zone_id ?? 'Tap a zone'}</h2>
            </div>
          </div>
          {selectedZone ? (
            <div className="space-y-3 rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
              <p className="text-sm text-slate-500 dark:text-slate-400">SKU Zone</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">{selectedZone.sku_zone}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">Camera</p>
              <p className="font-medium text-slate-900 dark:text-slate-100">{selectedZone.camera}</p>
            </div>
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400">Hover any zone polygon to see details.</p>
          )}
          <div className="grid gap-3">
            {zones.map((zone) => (
              <button
                key={zone.zone_id}
                onClick={() => setSelectedZoneId(zone.zone_id)}
                className={`flex items-center justify-between rounded-3xl border px-4 py-4 text-left text-sm transition ${
                  selectedZoneId === zone.zone_id ? 'border-sky-500 bg-sky-50/80 text-slate-900 dark:border-sky-400 dark:bg-slate-900' :
                  'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200 dark:hover:bg-slate-900'
                }`}
              >
                <div>
                  <p className="font-semibold">{zone.zone_id}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{zone.sku_zone}</p>
                </div>
                <Square size={20} className="text-slate-400" />
              </button>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
