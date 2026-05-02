import { useState, useMemo } from 'react'
import { Code2, Search, FileCode } from 'lucide-react'

const SELECT = "ctrl px-3 py-1.5"
const INPUT  = "ctrl pl-8 pr-3 py-1.5 w-full"

export default function CodeQLPage({ data }) {
  const { allFindings, repos, stats } = data
  const [search, setSearch] = useState('')
  const [repoF, setRepoF]   = useState('all')
  const [lvlF,  setLvlF]    = useState('all')
  const [page,  setPage]    = useState(1)
  const PAGE = 25

  const filtered = useMemo(() => {
    let list = allFindings
    if (repoF !== 'all') list = list.filter(f => f.repo === repoF)
    if (lvlF  !== 'all') list = list.filter(f => f.severity === lvlF)
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(f =>
        (f.rule_id   || '').toLowerCase().includes(q) ||
        (f.name      || '').toLowerCase().includes(q) ||
        (f.description || '').toLowerCase().includes(q)
      )
    }
    return list.sort((a, b) => {
      const ORDER = { error: 0, warning: 1, note: 2 }
      return (ORDER[a.severity] ?? 3) - (ORDER[b.severity] ?? 3)
    })
  }, [allFindings, repoF, lvlF, search])

  const totalPages = Math.ceil(filtered.length / PAGE)
  const visible    = filtered.slice((page - 1) * PAGE, page * PAGE)
  const go = p => setPage(p)

  const errors   = allFindings.filter(f => f.severity === 'error').length
  const warnings = allFindings.filter(f => f.severity === 'warning').length
  const notes    = allFindings.filter(f => f.severity === 'note').length

  return (
    <div className="p-6 space-y-5 max-w-screen-xl mx-auto">

      {/* Header */}
      <div className="animate-fade-up">
        <div className="micro mb-1">Análisis estático de código</div>
        <div className="flex items-start justify-between">
          <h1 className="text-xl font-bold text-ink flex items-center gap-2">
            <Code2 size={18} style={{ color: '#a855f7' }} />
            Hallazgos CodeQL
          </h1>
          {/* Mini stats */}
          <div className="flex gap-5 text-right shrink-0">
            <div>
              <div className="text-lg font-bold tabular-nums" style={{ color: '#ff3d52' }}>{errors}</div>
              <div className="micro">errores</div>
            </div>
            <div>
              <div className="text-lg font-bold tabular-nums" style={{ color: '#ffc107' }}>{warnings}</div>
              <div className="micro">warnings</div>
            </div>
            <div>
              <div className="text-lg font-bold tabular-nums" style={{ color: '#3d7fff' }}>{notes}</div>
              <div className="micro">notas</div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="animate-fade-up bg-card border border-rim rounded-lg p-4" style={{ animationDelay: '80ms' }}>
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-52">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-off" />
            <input
              type="text"
              placeholder="Regla, descripción…"
              value={search}
              onChange={e => { setSearch(e.target.value); go(1) }}
              className={INPUT}
            />
          </div>
          <select value={repoF} onChange={e => { setRepoF(e.target.value); go(1) }} className={SELECT}>
            <option value="all">Todos los repos</option>
            {repos.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
          <select value={lvlF} onChange={e => { setLvlF(e.target.value); go(1) }} className={SELECT}>
            <option value="all">Nivel</option>
            <option value="error">error</option>
            <option value="warning">warning</option>
            <option value="note">note</option>
          </select>
          <span className="flex items-center text-[11px] text-ink-dim">
            <span className="text-ink font-bold">{filtered.length}</span>&nbsp;hallazgo{filtered.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="animate-fade-up bg-card border border-rim rounded-lg overflow-hidden" style={{ animationDelay: '160ms' }}>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-rim text-[9px] uppercase tracking-[0.15em] text-ink-off">
                <th className="text-left px-4 py-3 font-medium">Nivel</th>
                <th className="text-left px-4 py-3 font-medium">Regla</th>
                <th className="text-left px-4 py-3 font-medium">Descripción</th>
                <th className="text-left px-4 py-3 font-medium">Archivo</th>
                <th className="text-left px-4 py-3 font-medium">Repo</th>
              </tr>
            </thead>
            <tbody>
              {visible.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center text-ink-off py-14 micro">
                    Sin hallazgos para los filtros actuales
                  </td>
                </tr>
              ) : (
                visible.map((f, i) => {
                  const loc  = f.locations?.[0]
                  const file = loc?.file?.split('/').slice(-2).join('/') || '—'
                  const line = loc?.startLine ? `:${loc.startLine}` : ''
                  return (
                    <tr key={i} className="trow">
                      <td className="px-4 py-3 shrink-0">
                        <span className={`sev-badge sev-${f.severity ?? 'warning'}`}>{f.severity ?? '—'}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-[11px]" style={{ color: '#a855f7' }}>{f.rule_id}</div>
                        <div className="text-[10px] text-ink-dim mt-0.5">{f.name || '—'}</div>
                      </td>
                      <td className="px-4 py-3 max-w-xs">
                        <p className="text-[11px] text-ink-dim line-clamp-2">{f.description || '—'}</p>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1 text-[10px] text-ink-dim">
                          <FileCode size={10} className="shrink-0 text-ink-off" />
                          <span className="truncate max-w-[140px]">{file}{line}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[10px] bg-rim text-ink-dim px-2 py-0.5 rounded-sm">{f.repo}</span>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-rim">
            <span className="text-[10px] text-ink-dim">Página {page} / {totalPages}</span>
            <div className="flex gap-2">
              <button onClick={() => go(Math.max(1, page - 1))} disabled={page === 1}
                className="px-3 py-1 text-[10px] border border-rim rounded text-ink-dim hover:text-ink hover:border-rim-hi disabled:opacity-30 transition-colors tracking-widest uppercase">
                Anterior
              </button>
              <button onClick={() => go(Math.min(totalPages, page + 1))} disabled={page === totalPages}
                className="px-3 py-1 text-[10px] border border-rim rounded text-ink-dim hover:text-ink hover:border-rim-hi disabled:opacity-30 transition-colors tracking-widest uppercase">
                Siguiente
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
