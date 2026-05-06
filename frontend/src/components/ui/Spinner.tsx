import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

interface SpinnerProps {
  className?: string;
  label?: string;
}

export function Spinner({ className, label }: SpinnerProps) {
  return (
    <div className="flex items-center gap-2 text-gray-500" role="status" aria-live="polite">
      <Loader2 className={cn('w-5 h-5 animate-spin', className)} />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}
