import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

function StatCard({ label, value, icon, color }: { label: string; value: string | number; icon: string; color: string }) {
  return (
    <div className={`rounded-xl border border-[#2a2a45] bg-[#13131f] px-5 py-4 flex items-center gap-4`}>
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-xl ${color}`}>
        {icon}
      </div>
      <div>
        <div className="text-2xl font-bold text-[#e2e8f0] font-mono">{value}</div>
        <div className="text-xs text-[#475569] mt-0.5">{label}</div>
      </div>
    </div>
  )
}

function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${ok ? 'border-[#22c55e]/30 bg-[#22c55e]/10 text-[#22c55e]' : 'border-[#ef4444]/30 bg-[#ef4444]/10 text-[#ef4444]'}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-[#22c55e] animate-pulse' : 'bg-[#ef4444]'}`} />
      {label}
    </div>
  )
}

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

export default function Dashboard() {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: api.health,
    refetchInterval: 15000,
  })
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: api.stats,
    refetchInterval: 30000,
  })

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="text-xs font-mono text-[#475569] uppercase tracking-widest mb-2">Mission Control</div>
        <h1 className="text-2xl font-semibold text-[#e2e8f0]">Dashboard</h1>
        <p className="text-sm text-[#475569] mt-1">Статус системы в реальном времени</p>
      </div>

      {/* System status row */}
      <div className="flex flex-wrap gap-3 mb-8">
        {healthLoading ? (
          <div className="text-xs text-[#475569] animate-pulse">Проверка соединения...</div>
        ) : health ? (
          <>
            <StatusBadge ok={health.bot_running} label={health.bot_running ? 'Bot Online' : 'Bot Offline'} />
            <StatusBadge ok={health.scheduler_running} label={health.scheduler_running ? 'Scheduler Active' : 'Scheduler Off'} />
            <StatusBadge ok={health.status === 'ok'} label={`API ${health.status}`} />
          </>
        ) : (
          <StatusBadge ok={false} label="Backend Unreachable" />
        )}
      </div>

      {/* Stats grid */}
      {statsLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="rounded-xl border border-[#2a2a45] bg-[#13131f] px-5 py-4 h-20 animate-pulse" />
          ))}
        </div>
      ) : stats ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Всего сообщений" value={stats.total_messages} icon="💬" color="bg-[#3b82f6]/10" />
          <StatCard label="Активных напоминаний" value={stats.active_reminders} icon="⏰" color="bg-[#f97316]/10" />
          <StatCard label="Всего напоминаний" value={stats.total_reminders} icon="📋" color="bg-[#a855f7]/10" />
          <StatCard label="Uptime" value={formatUptime(stats.uptime_seconds)} icon="🟢" color="bg-[#22c55e]/10" />
        </div>
      ) : (
        <div className="rounded-xl border border-[#2a2a45] bg-[#13131f] p-6 mb-8 text-center">
          <div className="text-[#475569] text-sm">Нет данных — бэкенд недоступен</div>
          <div className="text-xs text-[#2a2a45] mt-1 font-mono">GET /api/stats → 503</div>
        </div>
      )}

      {/* Info panel */}
      <div className="rounded-xl border border-[#2a2a45] bg-[#13131f] p-6">
        <div className="text-xs font-mono text-[#475569] uppercase tracking-widest mb-4">System Info</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div className="flex justify-between">
            <span className="text-[#475569]">Backend</span>
            <span className="font-mono text-[#e2e8f0]">:8001</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#475569]">Transport</span>
            <span className="font-mono text-[#e2e8f0]">Long Polling</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#475569]">Database</span>
            <span className="font-mono text-[#e2e8f0]">SQLite</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#475569]">AI Provider</span>
            <span className="font-mono text-[#e2e8f0]">OpenRouter</span>
          </div>
        </div>
      </div>
    </div>
  )
}
