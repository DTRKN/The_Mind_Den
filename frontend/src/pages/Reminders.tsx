import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, type Reminder } from '../api/client'

function ReminderCard({ reminder, onDelete }: { reminder: Reminder; onDelete: (id: number) => void }) {
  const dt = new Date(reminder.next_run)
  const timeStr = dt.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
  const isPast = dt < new Date()

  return (
    <div className={`rounded-xl border bg-[#13131f] p-4 flex items-start justify-between gap-4 transition-all ${isPast ? 'border-[#ef4444]/20 opacity-60' : 'border-[#2a2a45] hover:border-[#3b82f6]/30'}`}>
      <div className="flex-1 min-w-0">
        <div className="text-sm text-[#e2e8f0] font-medium truncate">{reminder.message}</div>
        <div className="flex items-center gap-3 mt-2">
          <span className="text-xs font-mono text-[#475569]">⏰ {timeStr}</span>
          {reminder.is_recurring && (
            <span className="text-xs px-2 py-0.5 rounded-full border border-[#a855f7]/30 bg-[#a855f7]/10 text-[#a855f7]">
              Recurring
            </span>
          )}
          {isPast && (
            <span className="text-xs px-2 py-0.5 rounded-full border border-[#ef4444]/30 bg-[#ef4444]/10 text-[#ef4444]">
              Просрочено
            </span>
          )}
        </div>
      </div>
      <button
        onClick={() => onDelete(reminder.id)}
        className="shrink-0 w-7 h-7 rounded-lg border border-[#2a2a45] bg-[#1a1a2e] hover:border-[#ef4444]/40 hover:text-[#ef4444] text-[#475569] text-sm transition-colors flex items-center justify-center"
      >
        ✕
      </button>
    </div>
  )
}

function AddReminderForm({ onAdded }: { onAdded: () => void }) {
  const [msg, setMsg] = useState('')
  const [dt, setDt] = useState('')
  const [open, setOpen] = useState(false)

  const createMutation = useMutation({
    mutationFn: () => api.reminders.create({ message: msg, next_run: dt }),
    onSuccess: () => {
      setMsg(''); setDt(''); setOpen(false); onAdded()
    },
  })

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 px-4 py-2 rounded-lg border border-[#2a2a45] bg-[#13131f] hover:border-[#3b82f6]/40 text-[#475569] hover:text-[#3b82f6] text-sm transition-colors"
      >
        <span className="text-base leading-none">＋</span> Добавить
      </button>
    )
  }

  return (
    <div className="rounded-xl border border-[#3b82f6]/30 bg-[#13131f] p-4 flex flex-col gap-3">
      <input
        type="text"
        placeholder="Текст напоминания..."
        value={msg}
        onChange={e => setMsg(e.target.value)}
        className="bg-[#1a1a2e] border border-[#2a2a45] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] placeholder-[#475569] focus:outline-none focus:border-[#3b82f6]/50"
      />
      <input
        type="datetime-local"
        value={dt}
        onChange={e => setDt(e.target.value)}
        className="bg-[#1a1a2e] border border-[#2a2a45] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] focus:outline-none focus:border-[#3b82f6]/50"
      />
      <div className="flex gap-2">
        <button
          onClick={() => createMutation.mutate()}
          disabled={!msg.trim() || !dt || createMutation.isPending}
          className="flex-1 py-2 rounded-lg bg-[#3b82f6]/20 border border-[#3b82f6]/30 text-[#3b82f6] text-sm hover:bg-[#3b82f6]/30 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {createMutation.isPending ? 'Сохраняю...' : 'Создать'}
        </button>
        <button
          onClick={() => { setOpen(false); setMsg(''); setDt('') }}
          className="px-4 py-2 rounded-lg border border-[#2a2a45] text-[#475569] text-sm hover:text-[#e2e8f0] transition-colors"
        >
          Отмена
        </button>
      </div>
      {createMutation.isError && (
        <div className="text-xs text-[#ef4444]">Ошибка: {(createMutation.error as Error).message}</div>
      )}
    </div>
  )
}

export default function Reminders() {
  const queryClient = useQueryClient()

  const { data: reminders, isLoading, error } = useQuery({
    queryKey: ['reminders'],
    queryFn: api.reminders.list,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.reminders.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reminders'] }),
  })

  const active = reminders?.filter(r => !r.is_done) ?? []

  return (
    <div className="p-8">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <div className="text-xs font-mono text-[#475569] uppercase tracking-widest mb-2">Mission Control</div>
          <h1 className="text-2xl font-semibold text-[#e2e8f0]">Reminders</h1>
          <p className="text-sm text-[#475569] mt-1">Активных: {active.length}</p>
        </div>
        <AddReminderForm onAdded={() => queryClient.invalidateQueries({ queryKey: ['reminders'] })} />
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="rounded-xl border border-[#2a2a45] bg-[#13131f] h-16 animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-xl border border-[#ef4444]/20 bg-[#13131f] p-6 text-center">
          <div className="text-[#ef4444] text-sm">Ошибка загрузки — бэкенд недоступен</div>
        </div>
      ) : active.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[#2a2a45] p-12 text-center">
          <div className="text-4xl mb-3">⏰</div>
          <div className="text-[#475569] text-sm">Нет активных напоминаний</div>
          <div className="text-xs text-[#2a2a45] mt-1">Напишите боту в Telegram чтобы создать</div>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {active.map(r => (
            <ReminderCard
              key={r.id}
              reminder={r}
              onDelete={id => deleteMutation.mutate(id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
