import { useState, useEffect } from 'react'
import {
  LayoutDashboard, ShieldAlert, Code2, Package,
  RefreshCw, AlertCircle, Loader2, Shield,
} from 'lucide-react'
import { useData } from './hooks/useData'

import Dashboard from './pages/Dashboard.jsx'
import VulnPage from './pages/VulnPage.jsx'
import CodeQLPage from './pages/CodeQLPage.jsx'
import SbomPage from './pages/SbomPage.jsx'

const NAV = [
  { id: 'dashboard', label: 'Dashboard', Icon: LayoutDashboard, accent: '#3d7fff' },
  { id: 'vulnerabilities', label: 'CVEs', Icon: ShieldAlert, accent: '#ff3d52' },
  { id: 'codeql', label: 'CodeQL', Icon: Code2, accent: '#a855f7' },
  { id: 'sbom', label: 'SBOM', Icon: Package, accent: '#22d48e' },
]

function fmt(d) {
  if (!d) return '—'
  return d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function App() {
  const [page, setPage] = useState('dashboard')
  const { data, loading, error, lastUpdated, reload } = useData()

  // 🕒 CONFIGURAR AUTO-REFRESH CADA 5 SEGUNDOS
  useEffect(() => {
    const intervalId = setInterval(reload, 5000);
    return () => clearInterval(intervalId);
  }, [reload]);

  return (
    <div className="grain flex h-screen overflow-hidden bg-base text-ink font-mono">

      {/* ── Sidebar ── */}
      <aside className="flex flex-col w-52 shrink-0 bg-surface border-r border-rim">

        {/* Logo */}
        <div className="px-5 pt-6 pb-5 border-b border-rim">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded flex items-center justify-center"
              style={{ background: 'rgba(61,127,255,0.12)', border: '1px solid rgba(61,127,255,0.25)' }}>
              <Shield size={13} style={{ color: '#3d7fff' }} />
            </div>
            <span className="text-xs font-bold tracking-[0.2em] uppercase text-ink">VulnDash</span>
          </div>
          <div className="micro mt-1.5">Security Analyzer</div>
        </div>

        {/* Nav */}
        <div className="px-3 pt-5 flex-1">
          <div className="micro mb-2 px-2">Módulos</div>
          <nav className="space-y-0.5">
            {NAV.map(({ id, label, Icon, accent }) => {
              const active = page === id
              return (
                <button
                  key={id}
                  onClick={() => setPage(id)}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded text-[11px] font-medium transition-all duration-150 relative ${active ? 'text-ink bg-card' : 'text-ink-dim hover:text-ink hover:bg-card/60'
                    }`}
                >
                  {active && (
                    <span className="absolute left-0 top-1.5 bottom-1.5 w-[2px] rounded-r"
                      style={{ backgroundColor: accent }} />
                  )}
                  <Icon size={13} style={{ color: active ? accent : undefined }} />
                  <span className="tracking-widest uppercase text-[10px]">{label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Status footer */}
        <div className="px-5 py-4 border-t border-rim space-y-2.5">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-safe animate-pulse-dot shrink-0" />
            <span className="text-[10px] text-ink-dim tracking-widest">LIVE</span>
            <span className="text-[10px] text-ink-off ml-auto">{fmt(lastUpdated)}</span>
          </div>
          <button
            onClick={reload}
            className="flex items-center gap-1.5 text-[10px] text-ink-dim hover:text-accent transition-colors tracking-widest uppercase"
          >
            <RefreshCw size={10} />
            Sync
          </button>
          <div className="text-[9px] text-ink-off">Auto-refresh · 30s</div>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex-1 overflow-auto bg-base">

        {loading && !data && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-ink-dim">
            <Loader2 className="animate-spin text-accent" size={28} />
            <p className="micro">Cargando datos del miner…</p>
          </div>
        )}

        {error && !data && (
          <div className="flex flex-col items-center justify-center h-full gap-5 px-8 text-center">
            <div className="w-12 h-12 rounded flex items-center justify-center"
              style={{ background: 'rgba(255,61,82,0.1)', border: '1px solid rgba(255,61,82,0.25)' }}>
              <AlertCircle style={{ color: '#ff3d52' }} size={20} />
            </div>
            <div>
              <p className="text-sm font-semibold text-ink mb-1 tracking-wide">Sin datos disponibles</p>
              <p className="text-xs text-ink-dim mb-3">Ejecuta el miner primero:</p>
              <code className="block bg-card border border-rim rounded px-4 py-2 text-xs text-accent">
                python main.py
              </code>
            </div>
            <button
              onClick={reload}
              className="flex items-center gap-2 text-xs text-accent hover:text-accent/70 transition-colors tracking-widest uppercase"
            >
              <RefreshCw size={12} /> Reintentar
            </button>
          </div>
        )}

        {data && (
          <div className="animate-fade-in">
            {page === 'dashboard' && <Dashboard data={data} />}
            {page === 'vulnerabilities' && <VulnPage data={data} />}
            {page === 'codeql' && <CodeQLPage data={data} />}
            {page === 'sbom' && <SbomPage data={data} />}
          </div>
        )}
      </main>
    </div>
  )
}
