import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, Skill } from '../api/client'

export default function Skills() {
  const queryClient = useQueryClient()
  const { data: skills = [], isLoading, isError } = useQuery({
    queryKey: ['skills'],
    queryFn: api.skills.list,
    refetchInterval: 30_000,
  })

  const syncMutation = useMutation({
    mutationFn: api.skills.list,
    onSuccess: (data) => {
      queryClient.setQueryData(['skills'], data)
    },
  })

  return (
    <div className="p-8">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <div className="text-xs font-mono text-[#475569] uppercase tracking-widest mb-2">Mission Control</div>
          <h1 className="text-2xl font-semibold text-[#e2e8f0]">Skills</h1>
          <p className="text-sm text-[#475569] mt-1">Модули расширения возможностей агента</p>
        </div>
        <button
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#1a1a2e] border border-[#2a2a45] text-[#94a3b8] hover:text-[#e2e8f0] hover:border-[#7c3aed] transition-colors text-sm disabled:opacity-50"
        >
          <span className={syncMutation.isPending ? 'animate-spin inline-block' : ''}>↻</span>
          Синхронизировать
        </button>
      </div>

      {isLoading && (
        <div className="text-center text-[#475569] py-16">Загрузка скиллов...</div>
      )}

      {isError && (
        <div className="rounded-xl border border-red-900/40 bg-red-950/20 p-6 text-red-400 text-sm">
          Ошибка загрузки скиллов. Убедитесь, что бэкенд запущен.
        </div>
      )}

      {!isLoading && !isError && skills.length === 0 && (
        <div className="rounded-xl border border-dashed border-[#2a2a45] p-12 text-center">
          <div className="text-4xl mb-3">🧠</div>
          <div className="text-[#475569] text-sm">Скиллы ещё не загружены</div>
          <div className="text-xs text-[#2a2a45] mt-1">Добавьте папку с SKILL.md в директорию skills/</div>
        </div>
      )}

      {skills.length > 0 && (
        <>
          <div className="text-xs text-[#475569] mb-4 font-mono">
            {skills.length} скилл{skills.length !== 1 ? 'ов' : ''} загружено
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {skills.map((skill) => (
              <SkillCard key={skill.name} skill={skill} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function SkillCard({ skill }: { skill: Skill }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="rounded-xl border border-[#2a2a45] bg-[#0f0f1a] p-5 flex flex-col gap-3 hover:border-[#7c3aed]/60 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-xs font-mono text-[#7c3aed] mb-1">{skill.name}</div>
          <div className="text-[#e2e8f0] font-medium text-sm leading-snug">
            {skill.title ?? skill.name}
          </div>
        </div>
        <div className="w-8 h-8 rounded-lg bg-[#7c3aed]/10 flex items-center justify-center text-lg flex-shrink-0">🧩</div>
      </div>

      <p className="text-xs text-[#64748b] leading-relaxed">{skill.description}</p>

      {skill.content && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-[#475569] hover:text-[#94a3b8] text-left transition-colors"
        >
          {expanded ? '▲ Скрыть' : '▼ Инструкции'}
        </button>
      )}

      {expanded && skill.content && (
        <pre className="text-xs text-[#64748b] bg-[#0a0a14] rounded-lg p-3 overflow-auto max-h-48 whitespace-pre-wrap">
          {skill.content}
        </pre>
      )}
    </div>
  )
}
