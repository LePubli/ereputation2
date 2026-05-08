import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Workflow, Users, Puzzle, Settings as SettingsIcon } from 'lucide-react';
import { cn } from '../../lib/utils';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/pipeline', label: 'Pipeline', icon: Workflow },
  { to: '/prospects', label: 'Prospects', icon: Users },
  { to: '/plugins', label: 'Plugins', icon: Puzzle },
  { to: '/settings', label: 'Paramètres', icon: SettingsIcon },
];

export function Sidebar() {
  const appName = import.meta.env.VITE_APP_NAME ?? 'B2B Prospector';
  const appVersion = import.meta.env.VITE_APP_VERSION ?? '1.1.0';

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col h-screen sticky top-0">
      <div className="px-6 py-5 border-b">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-700 rounded text-white flex items-center justify-center font-bold text-sm">
            BP
          </div>
          <div>
            <div className="font-bold text-sm">{appName}</div>
            <div className="text-xs text-gray-500">v{appVersion}</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded text-sm font-medium transition',
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-50',
              )
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t text-xs text-gray-500">
        <p>© Le Publicitaire</p>
        <p className="mt-1">Phase 1 active</p>
      </div>
    </aside>
  );
}
