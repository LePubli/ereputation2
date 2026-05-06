import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
}

export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12 px-4 border border-dashed border-gray-200 rounded-lg bg-gray-50">
      <div className="mb-4 text-gray-400">{icon ?? <Inbox className="w-12 h-12" />}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-gray-500 max-w-md mb-6">{description}</p>
      )}
      {action}
    </div>
  );
}
