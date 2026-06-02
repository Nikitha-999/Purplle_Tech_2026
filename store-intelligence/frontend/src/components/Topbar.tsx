import { Menu, RefreshCcw, SunMoon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface TopbarProps {
  currentStore: string;
  selectedDate: string;
  darkMode: boolean;
  onStoreChange: (store: string) => void;
  onDateChange: (date: string) => void;
  onRefresh: () => void;
  onToggleTheme: () => void;
  onMenuClick: () => void;
}

export function Topbar({
  currentStore,
  selectedDate,
  darkMode,
  onStoreChange,
  onDateChange,
  onRefresh,
  onToggleTheme,
  onMenuClick,
}: TopbarProps) {
  return (
    <div className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95">
      <div className="mx-auto flex max-w-8xl items-center gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <button
          onClick={onMenuClick}
          className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 text-slate-700 transition hover:border-slate-300 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800 lg:hidden"
        >
          <Menu size={18} />
        </button>

        <div className="flex-1 space-y-2 text-sm sm:text-base">
          <p className="font-semibold text-slate-900 dark:text-slate-100">Store ST1008 / STORE_BLR_002</p>
          <p className="text-slate-500 dark:text-slate-400">Retail intelligence for Bangalore boutique operations.</p>
        </div>

        <div className="hidden gap-3 lg:flex">
          <div className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-900">
            <label className="block text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Store</label>
            <select
              value={currentStore}
              onChange={(event) => onStoreChange(event.target.value)}
              className="mt-2 w-full bg-transparent text-slate-900 outline-none dark:text-slate-100"
            >
              <option value="ST1008">ST1008</option>
              <option value="STORE_BLR_002">STORE_BLR_002</option>
            </select>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-900">
            <label className="block text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Date</label>
            <input
              type="date"
              value={selectedDate}
              onChange={(event) => onDateChange(event.target.value)}
              className="mt-2 w-full bg-transparent text-slate-900 outline-none dark:text-slate-100"
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            className={cn(
              'inline-flex h-11 items-center gap-2 rounded-3xl border px-4 font-medium transition',
              'border-slate-200 bg-slate-50 text-slate-800 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800',
            )}
          >
            <RefreshCcw size={16} />
            Refresh
          </button>
          <button
            onClick={onToggleTheme}
            className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 text-slate-700 transition hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
          >
            <SunMoon size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
