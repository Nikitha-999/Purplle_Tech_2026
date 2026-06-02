import { AnimatePresence, motion } from 'framer-motion';
import { NavLink } from 'react-router-dom';
import {
  AlertTriangle,
  Film,
  Grid,
  Layers,
  Lightbulb,
  MapPin,
  Monitor,
  PlayCircle,
  Server,
  TrendingUp,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const iconMap = {
  Grid: Grid,
  TrendingUp: TrendingUp,
  MapPin: MapPin,
  AlertTriangle: AlertTriangle,
  Server: Server,
  Video: Film,
  Layers: Layers,
  Monitor: Monitor,
  Lightbulb: Lightbulb,
  PlayCircle: PlayCircle,
};

interface RouteItem {
  path: string;
  label: string;
  icon: keyof typeof iconMap;
}

interface SidebarProps {
  routes: RouteItem[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function Sidebar({ routes, open, onOpenChange }: SidebarProps) {
  return (
    <>
      <div className="hidden lg:flex lg:w-80 lg:flex-col lg:border-r lg:border-slate-200 lg:bg-white lg:px-4 lg:pt-6 lg:pb-6 lg:dark:border-slate-800 lg:dark:bg-slate-950">
        <div className="flex items-center gap-3 px-2 pb-6">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-violet-500 text-white shadow-glow">
            <Grid size={20} />
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
              Purplle Intelligence
            </p>
            <p className="text-lg font-semibold">Store Analytics</p>
          </div>
        </div>
        <div className="space-y-2 px-2">
          {routes.map((route) => {
            const Icon = iconMap[route.icon];
            return (
              <NavLink
                key={route.path}
                to={route.path}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-3xl px-4 py-3 text-sm font-medium transition',
                    isActive
                      ? 'bg-slate-900 text-white shadow-glow dark:bg-slate-700'
                      : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white',
                  )
                }
              >
                <Icon className="h-5 w-5" />
                {route.label}
              </NavLink>
            );
          })}
        </div>
      </div>

      <AnimatePresence>
        {open ? (
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            className="fixed inset-y-0 left-0 z-50 w-[88vw] max-w-xs border-r border-slate-200 bg-slate-50 p-4 shadow-2xl dark:border-slate-800 dark:bg-slate-950 lg:hidden"
          >
            <div className="flex items-center justify-between pb-6">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white">
                  <Grid size={18} />
                </div>
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
                    Purplle
                  </p>
                  <p className="text-lg font-semibold">Store dashboard</p>
                </div>
              </div>
              <button
                onClick={() => onOpenChange(false)}
                className="rounded-full p-2 text-slate-700 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                <X size={20} />
              </button>
            </div>
            <div className="space-y-2">
              {routes.map((route) => {
                const Icon = iconMap[route.icon];
                return (
                  <NavLink
                    key={route.path}
                    to={route.path}
                    onClick={() => onOpenChange(false)}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-3 rounded-3xl px-4 py-3 text-sm font-medium transition',
                        isActive
                          ? 'bg-slate-900 text-white dark:bg-slate-700'
                          : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white',
                      )
                    }
                  >
                    <Icon className="h-5 w-5" />
                    {route.label}
                  </NavLink>
                );
              })}
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
