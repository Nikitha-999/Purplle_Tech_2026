import { type HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

const severityStyles: Record<string, string> = {
  info: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-200',
  warn: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200',
  critical: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-200',
};

export function Badge({ className, children, ...props }: HTMLAttributes<HTMLSpanElement> & { children: React.ReactNode; }) {
  return (
    <span
      className={cn(
        'inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em]',
        severityStyles[children ? children.toString().toLowerCase() : ''] ?? 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200',
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
