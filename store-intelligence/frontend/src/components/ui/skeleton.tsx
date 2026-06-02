import { type HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-3xl bg-slate-200/80 dark:bg-slate-800',
        className,
      )}
      {...props}
    />
  );
}
