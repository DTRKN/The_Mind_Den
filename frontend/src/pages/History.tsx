import { useQuery } from '@tanstack/react-query'
import { api, type Message } from '../api/client'

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  const dt = new Date(message.created_at)
  const time = dt.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-7 h-7 rounded-full shrink-0 flex items-center justify-center text-xs font-bold ${isUser ? 'bg-gradient-to-br from-[#f97316] to-[#a855f7] text-white' : 'bg-[#1a1a2e] border border-[#2a2a45] text-[#94a3b8]'}`}>
        {isUser ? 'U' : 'AI'}
      </div>
      <div className={`max-w-2xl ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${isUser ? 'bg-[#1a1a2e] border border-[#f97316]/20 text-[#e2e8f0]' : 'bg-[#13131f] border border-[#2a2a45] text-[#e2e8f0]'}`}>
          {message.content}
        </div>
        <span className="text-xs text-[#475569] font-mono px-1">{time}</span>
      </div>
    </div>
  )
}

export default function History() {
  const { data: messages, isLoading, error, refetch } = useQuery({
    queryKey: ['messages'],
    queryFn: api.messages,
  })

  return (
    <div className="p-8">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <div className="text-xs font-mono text-[#475569] uppercase tracking-widest mb-2">Mission Control</div>
          <h1 className="text-2xl font-semibold text-[#e2e8f0]">History</h1>
          <p className="text-sm text-[#475569] mt-1">История диалогов с ботом</p>
        </div>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 rounded-lg border border-[#2a2a45] bg-[#13131f] hover:border-[#3b82f6]/40 text-[#94a3b8] hover:text-[#e2e8f0] text-sm transition-colors"
        >
          ↻ Обновить
        </button>
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className={`flex gap-3 ${i % 2 ? 'flex-row-reverse' : ''}`}>
              <div className="w-7 h-7 rounded-full bg-[#1a1a2e] animate-pulse shrink-0" />
              <div className="h-12 rounded-2xl bg-[#13131f] animate-pulse flex-1 max-w-md" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="rounded-xl border border-[#ef4444]/20 bg-[#13131f] p-6 text-center">
          <div className="text-[#ef4444] text-sm">Ошибка загрузки — бэкенд недоступен</div>
        </div>
      ) : !messages?.length ? (
        <div className="rounded-xl border border-dashed border-[#2a2a45] p-12 text-center">
          <div className="text-4xl mb-3">💬</div>
          <div className="text-[#475569] text-sm">История пуста</div>
          <div className="text-xs text-[#2a2a45] mt-1">Начните диалог с ботом в Telegram</div>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {messages.map(m => (
            <MessageBubble key={m.id} message={m} />
          ))}
        </div>
      )}
    </div>
  )
}
