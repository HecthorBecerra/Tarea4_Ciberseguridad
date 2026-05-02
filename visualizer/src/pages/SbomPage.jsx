import { useState, useMemo } from 'react'
import { Package, Search } from 'lucide-react'

const TYPE_PALETTE = ['#3d7fff','#a855f7','#22d48e','#ff7340','#06b6d4','#ffc107','#f472b6','#84cc16']

const SELECT = "ctrl px-3 py-1.5"
const INPUT  = "ctrl pl-8 pr-3 py-1.5 w-full"

export default function SbomPage({ data }) {
  const { allArtifacts, sbomRaw, typeMap, repos } = data
  const [search, setSearch] = useState('')
  const [repoF, setRepoF]   = useState('all')
  const [typeF, setTypeF]   = useState('all')
  const [page,  setPage]    = useState(1)
  const PAGE = 30

  const sortedTypes = useMemo(
    () => Object.entries(typeMap).sort((a, b) => b[1] - a[1]),
    [typeMap]
  )
  const maxCount  = sortedTypes[0]?.[1] || 1
  const uniqueTypes = sortedTypes.map(([t]) => t)

  const depsByRepo = useMemo(
    () => sbomRaw.map(s => ({ repo: s.repo, count: s.artifacts.length }))
      .sort((a, b) => b.count - a.count),
    [sbomRaw]
  )
  const maxRepo = depsByRepo[0]?.count || 1

  const topShared = useMemo(() => {
    const nm = {}
    for (const a of allArtifacts) {
      if (!nm[a.name]) nm[a.name] = new Set()
      nm[a.name].add(a.repo)
    }
    return Object.entries(nm)
      .filter(([, rs]) => rs.size > 1)
      .sort((a, b) => b[1].size - a[1].size)
      .slice(0, 8)
      .map(([name, rs]) => ({ name, repos: [...rs] }))
  }, [allArtifacts])

  const filtered = useMemo(() => {
    let list = allArtifacts
    if (repoF !== 'all') list = list.filter(a => a.repo === repoF)
    if (typeF !== 'all') list = list.filter(a => a.type === typeF)
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(a =>
        (a.name    || '').toLowerCase().includes(q) ||
        (a.version || '').toLowerCase().includes(q)
      )
    }
    return list
  }, [allArtifacts, repoF, typeF, search])

  const totalPages = Math.ceil(filtered.length / PAGE)
  const visible    = filtered.slice((page - 1) * PAGE, page * PAGE)
  const go = p => setPage(p)

  return (
    <div className="p-6 space-y-5 max-w-screen-xl mx-auto">

      {/* Header */}
      <div className="animate-fade-up">
        <div className="micro mb-1">Software Bill of Materials</div>
        <h1 className="text-xl font-bold text-ink flex items-center gap-2">
          <Package size={18} style={{ color: '#3d7fff' }} />
          Dependencias — SBOM
        </h1>
        <p className="text-[11px] text-ink-dim mt-1">
          Generado con Syft ·{' '}
          <span className="text-ink font-semibold">{allArtifacts.length.toLocaleString()}</span> componentes detectados
        </p>
      </div>

      {/* Top charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Type distribution */}
        <div className="animate-fade-up bg-card border border-rim rounded-lg p-5" style={{ animationDelay: '80ms' }}>
          <div className="micro mb-3">Distribución por tipo de paquete</div>
          <div className="space-y-2.5">
            {sortedTypes.slice(0, 8).map(([type, count], i) => (
              <div key={type}>
                <div className="flex justify-between text-[10px] mb-1">
                  <span className="text-ink uppercase tracking-widest truncate">{type}</span>
                  <span className="text-ink-dim ml-2 shrink-0 tabular-nums">
                    {count.toLocaleString()} ({Math.round((count / allArtifacts.length) * 100)}%)
                  </span>
                </div>
                <div className="h-1.5 rounded-sm overflow-hidden bg-rim">
                  <div
                    className="h-full bar-seg rounded-sm"
                    style={{ width: `${(count / maxCount) * 100}%`, backgroundColor: TYPE_PALETTE[i % TYPE_PALETTE.length] }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Deps per repo + shared */}
        <div className="space-y-4">
          <div className="animate-fade-up bg-card border border-rim rounded-lg p-5" style={{ animationDelay: '140ms' }}>
            <div className="micro mb-3">Dependencias por repositorio</div>
            <div className="space-y-2.5">
              {depsByRepo.map(({ repo, count }) => (
                <div key={repo}>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-ink truncate max-w-[70%]">{repo}</span>
                    <span className="text-ink-dim tabular-nums">{count.toLocaleString()}</span>
                  </div>
                  <div className="h-1.5 rounded-sm overflow-hidden bg-rim">
                    <div className="h-full bar-seg rounded-sm" style={{ width: `${(count / maxRepo) * 100}%`, backgroundColor: '#3d7fff' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {topShared.length > 0 && (
            <div className="animate-fade-up bg-card border border-rim rounded-lg p-5" style={{ animationDelay: '200ms' }}>
              <div className="micro mb-3">Paquetes compartidos entre repos</div>
              <div className="space-y-2">
                {topShared.map(({ name, repos: rs }) => (
                  <div key={name} className="flex items-center justify-between gap-2">
                    <span className="text-[11px] text-ink truncate">{name}</span>
                    <div className="flex gap-1 shrink-0 flex-wrap justify-end">
                      {rs.map(r => (
                        <span key={r} className="text-[9px] bg-[#3d7fff]/10 text-[#3d7fff] border border-[#3d7fff]/25 px-1.5 py-0.5 rounded-sm tracking-widest uppercase">
                          {r.split('/').pop()}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="animate-fade-up bg-card border border-rim rounded-lg p-4" style={{ animationDelay: '260ms' }}>
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-52">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-off" />
            <input
              type="text"
              placeholder="Buscar paquete…"
              value={search}
              onChange={e => { setSearch(e.target.value); go(1) }}
              className={INPUT}
            />
          </div>
          <select value={repoF} onChange={e => { setRepoF(e.target.value); go(1) }} className={SELECT}>
            <option value="all">Todos los repos</option>
            {repos.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
          <select value={typeF} onChange={e => { setTypeF(e.target.value); go(1) }} className={SELECT}>
            <option value="all">Todos los tipos</option>
            {uniqueTypes.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <span className="flex items-center text-[11px] text-ink-dim">
            <span className="text-ink font-bold">{filtered.length.toLocaleString()}</span>&nbsp;componente{filtered.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="animate-fade-up bg-card border border-rim rounded-lg overflow-hidden" style={{ animationDelay: '320ms' }}>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-rim text-[9px] uppercase tracking-[0.15em] text-ink-off">
                <th className="text-left px-4 py-3 font-medium">Paquete</th>
                <th className="text-left px-4 py-3 font-medium">Versión</th>
                <th className="text-left px-4 py-3 font-medium">Tipo</th>
                <th className="text-left px-4 py-3 font-medium">Licencia</th>
                <th className="text-left px-4 py-3 font-medium">Repo</th>
              </tr>
            </thead>
            <tbody>
              {visible.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center text-ink-off py-14 micro">
                    Sin componentes para los filtros actuales
                  </td>
                </tr>
              ) : (
                visible.map((a, i) => {
                  const license = a.licenses?.[0]?.value || a.licenses?.[0]?.spdxExpression || '—'
                  return (
                    <tr key={i} className="trow">
                      <td className="px-4 py-2.5 text-ink font-medium">{a.name}</td>
                      <td className="px-4 py-2.5 text-ink-dim">{a.version || '—'}</td>
                      <td className="px-4 py-2.5">
                        <span className="text-[10px] bg-rim text-ink-dim px-2 py-0.5 rounded-sm uppercase tracking-widest">{a.type}</span>
                      </td>
                      <td className="px-4 py-2.5 text-ink-dim truncate max-w-[130px]">{license}</td>
                      <td className="px-4 py-2.5">
                        <span className="text-[10px] bg-[#3d7fff]/10 text-[#3d7fff] border border-[#3d7fff]/25 px-2 py-0.5 rounded-sm">{a.repo}</span>
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
