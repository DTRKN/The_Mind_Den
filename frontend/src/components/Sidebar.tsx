import { NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: '⚡' },
  { to: '/reminders', label: 'Reminders', icon: '⏰' },
  { to: '/history', label: 'History', icon: '💬' },
  { to: '/skills', label: 'Skills', icon: '🧠' },
]

export default function Sidebar() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.health,
    refetchInterval: 15000,
  })

  const isOnline = health?.bot_running === true

  return (
    <aside className="flex flex-col w-60 min-h-screen bg-[#13131f] border-r border-[#2a2a45] px-4 py-6 shrink-0">
      {/* Logo */}
      <div className="mb-8">
        <div className="text-xs font-mono text-[#475569] uppercase tracking-widest mb-1">Mission Control</div>
        <div className="text-white font-semibold text-sm">The Mind Den</div>
        <div className="text-[#475569] text-xs font-mono mt-0.5">v2.0.0</div>
      </div>

      {/* Agent status */}
      <div className={`rounded-xl border px-3 py-3 mb-8 ${isOnline ? 'border-[#22c55e]/30 bg-[#22c55e]/5 glow-green' : 'border-[#2a2a45] bg-[#1a1a2e]'}`}>
        <div className="flex items-center gap-2 mb-1">
          <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-[#22c55e] animate-pulse' : 'bg-[#475569]'}`} />
          <span className="text-xs font-medium text-[#94a3b8]">
            {isOnline ? 'Agent Online' : 'Agent Offline'}
          </span>
        </div>
        <div className="text-xs text-[#475569] font-mono truncate">
          {health ? `${health.version}` : 'Connecting...'}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-1 flex-1">
        {NAV_ITEMS.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ${
                isActive
                  ? 'bg-[#f97316]/10 text-[#f97316] border border-[#f97316]/20'
                  : 'text-[#94a3b8] hover:text-[#e2e8f0] hover:bg-[#1a1a2e]'
              }`
            }
          >
            <span className="text-base">{icon}</span>
            <span className="font-medium">{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Profile */}
      <div className="pt-4 border-t border-[#2a2a45] mt-4">
        <div className="flex items-center gap-3 px-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#f97316] to-[#a855f7] flex items-center justify-center text-xs font-bold text-white">
            U
          </div>
          <div>
            <div className="text-xs font-medium text-[#e2e8f0]">User</div>
            <div className="text-xs text-[#475569]">Personal AI</div>
          </div>
        </div>
      </div>
    </aside>
  )
}
