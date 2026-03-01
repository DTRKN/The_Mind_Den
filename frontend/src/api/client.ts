const BASE_URL = '/api'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function del(path: string): Promise<void> {
  const res = await fetch(`${BASE_URL}${path}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
}

export type HealthResponse = {
  status: string
  bot_running: boolean
  scheduler_running: boolean
  version: string
}

export type StatsResponse = {
  total_messages: number
  total_reminders: number
  active_reminders: number
  uptime_seconds: number
}

export type Message = {
  id: number
  user_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export type Reminder = {
  id: number
  user_id: string
  message: string
  next_run: string
  is_recurring: boolean
  cron_expr: string | null
  is_done: boolean
  created_at: string
}

export const api = {
  health: () => get<HealthResponse>('/health'),
  stats: () => get<StatsResponse>('/stats'),
  messages: () => get<Message[]>('/messages'),
  reminders: {
    list: () => get<Reminder[]>('/reminders'),
    delete: (id: number) => del(`/reminders/${id}`),
    create: (body: { message: string; next_run: string; user_id?: number; is_recurring?: boolean; cron_expr?: string | null }) =>
      apiPost<Reminder>('/reminders', body),
  },
}
