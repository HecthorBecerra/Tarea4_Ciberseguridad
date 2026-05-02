import { useState, useMemo } from 'react'
import { ShieldAlert, Search, CheckCircle, XCircle, HelpCircle } from 'lucide-react'

function SevBadge({ s }) {
  const key = (s || 'Unknown').toLowerCase()
  return <span className={`sev-badge sev-${key}`}>{s || 'Unknown'}</span>
}

function FixBadge({ state }) {
  if (state === 'fixed')     return <span className="inline-flex items-center gap-1 text-[10px]" style={{ color: '#22d48e' }}><CheckCircle size={10} /> fixed</span>
  if (state === 'not-fixed') return <span className="inline-flex items-center gap-1 text-[10px]" style={{ color: '#ff3d52' }}><XCircle    size={10} /> no fix</span>
  return                            <span className="inline-flex items-center gap-1 text-[10px] text-ink-off"><HelpCircle size={10} /> unknown</span>
}

const SELECT = "ctrl px-3 py-1.5"
const INPUT  = "ctrl pl-8 pr-3 py-1.5 w-full"

export default function VulnPage({ data }) {
  const { allVulns, repos } = data
  const [search, setSearch] = useState('')
  const [repoF, setRepoF]   = useState('all')
  const [sevF,  setSevF]    = useState('all')
  const [fixF,  setFixF]    = useState('all')
  const [page,  setPage]    = useState(1)
  const PAGE = 25

  const filtered = useMemo(() => {
    let list = allVulns
    if (repoF !== 'all') list = list.filter(v => v.repo === repoF)
    if (sevF  !== 'all') list = list.filter(v => v.severity === sevF)
    if (fixF  !== 'all') list = list.filter(v => v.fixState === fixF)
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(v =>
        v.id.toLowerCase().includes(q) ||
        v.pkg.toLowerCase().includes(q) ||
        (v.description || '').toLowerCase().includes(q)
      )
    }
    return list
  }, [allVulns, repoF, sevF, fixF, search])

  const totalPages = Math.ceil(filtered.length / PAGE)
  const visible = filtered.slice((page - 1) * PAGE, page * PAGE)
  const go = p => setPage(p)

  return (
    <div className="p-6 space-y-5 max-w-screen-xl mx-auto">

      {/* Header */}
      <div className="animate-fade-up">
        <div className="micro mb-1">Análisis de vulnerabilidades</div>
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-ink flex items-center gap-2">
            <ShieldAlert size={18} style={{ color: '#ff3d52' }} />
            CVEs detectados
          </h1>
          <span className="text-[11px] text-ink-dim">
            <span className="text-ink font-bold">{filtered.length.toLocaleString()}</span> resultado{filtered.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="animate-fade-up bg-card border border-rim rounded-lg p-4" style={{ animationDelay: '80ms' }}>
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-52">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-off" />
            <input
              type="text"
              placeholder="CVE-ID, paquete, descripción…"
              value={search}
              onChange={e => { setSearch(e.target.value); go(1) }}
              className={INPUT}
            />
          </div>
          <select value={repoF} onChange={e => { setRepoF(e.target.value); go(1) }} className={SELECT}>
            <option value="all">Todos los repos</option>
            {repos.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
          <select value={sevF} onChange={e => { setSevF(e.target.value); go(1) }} className={SELECT}>
            <option value="all">Severidad</option>
            {['Critical','High','Medium','Low'].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={fixF} onChange={e => { setFixF(e.target.value); go(1) }} className={SELECT}>
            <option value="all">Fix state</option>
            <option value="fixed">Fixed</option>
            <option value="not-fixed">Not fixed</option>
            <option value="unknown">Unknown</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="animate-fade-up bg-card border border-rim rounded-lg overflow-hidden" style={{ animationDelay: '160ms' }}>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-rim text-[9px] uppercase tracking-[0.15em] text-ink-off">
                <th className="text-left px-4 py-3 font-medium">CVE</th>
                <th className="text-left px-4 py-3 font-medium">Sev</th>
                <th className="text-left px-4 py-3 font-medium">Paquete</th>
                <th className="text-left px-4 py-3 font-medium">Versión</th>
                <th className="text-left px-4 py-3 font-medium">Fix</th>
                <th className="text-left px-4 py-3 font-medium">Repo</th>
              </tr>
            </thead>
            <tbody>
              {visible.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center text-ink-off py-14 micro">
                    Sin resultados
                  </td>
                </tr>
              ) : (
                visible.map((v, i) => (
                  <tr key={i} className="trow">
                    <td className="px-4 py-2.5 font-semibold text-ink">{v.id}</td>
                    <td className="px-4 py-2.5"><SevBadge s={v.severity} /></td>
                    <td className="px-4 py-2.5 text-ink max-w-[130px] truncate">{v.pkg}</td>
                    <td className="px-4 py-2.5 text-ink-dim">{v.version}</td>
                    <td className="px-4 py-2.5"><FixBadge state={v.fixState} /></td>
                    <td className="px-4 py-2.5">
                      <span className="text-[10px] bg-rim text-ink-dim px-2 py-0.5 rounded-sm">{v.repo}</span>
                    </td>
                  </tr>
                ))
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
