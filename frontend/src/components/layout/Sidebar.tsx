import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Briefcase, Send, Globe, User, Zap } from 'lucide-react'

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/applications', label: 'Applications', icon: Send },
  { to: '/sources', label: 'Sources', icon: Globe },
  { to: '/profile', label: 'Profile', icon: User },
]

export default function Sidebar() {
  return (
    <aside className="w-56 bg-gray-900 text-gray-300 flex flex-col shrink-0">
      <div className="flex items-center gap-2 px-5 py-4 border-b border-gray-800">
        <Zap className="h-6 w-6 text-amber-400" />
        <span className="text-lg font-bold text-white">JobHunter</span>
      </div>
      <nav className="flex-1 py-4 space-y-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-5 py-2.5 text-sm transition-colors ${
                isActive
                  ? 'bg-gray-800 text-white border-r-2 border-amber-400'
                  : 'hover:bg-gray-800/50 hover:text-white'
              }`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 py-3 text-xs text-gray-500 border-t border-gray-800">
        JobHunter Pro v0.1
      </div>
    </aside>
  )
}
