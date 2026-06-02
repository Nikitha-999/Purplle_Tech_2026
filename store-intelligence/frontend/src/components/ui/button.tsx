import { type ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement>;

const Button = forwardRef<HTMLButtonElement, ButtonProps>(({ className, type = 'button', ...props }, ref) => (
  <button
    ref={ref}
    type={type}
    className={cn(
      'inline-flex items-center justify-center rounded-3xl border border-slate-200 bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-sky-500 dark:hover:bg-sky-600',
      className,
    )}
    {...props}
  />
));

Button.displayName = 'Button';
export { Button };
