import { ShieldAlert, Flame, Code2 } from 'lucide-react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

// ── Paleta de severidad ───────────────────────────────────────────────────────

const SEV_HEX = {
  Critical: '#ff3d52', High: '#ff7340', Medium: '#ffc107', Low: '#22d48e', Unknown: '#3a4462',
}

function SevBadge({ s }) {
  const key = (s || 'Unknown').toLowerCase()
  return (
    <span className={`sev-badge sev-${key}`}>{s || 'Unknown'}</span>
  )
}

function CvssBadge({ score }) {
  const s = score ?? 0
  const bg = s >= 9 ? '#ff3d52' : s >= 7 ? '#ff7340' : s >= 4 ? '#ffc107' : '#22d48e'
  const fg = s >= 4 && s < 7 ? '#0f1220' : '#fff'
  return (
    <span className="inline-flex items-center justify-center w-12 h-6 rounded-sm text-[11px] font-bold tabular-nums shrink-0"
          style={{ backgroundColor: bg, color: fg }}>
      {s.toFixed(1)}
    </span>
  )
}

// ── Micro-etiqueta de sección ─────────────────────────────────────────────────

function Sect({ label, right }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <span className="micro">{label}</span>
      {right && <span className="text-[10px] text-ink-off">{right}</span>}
    </div>
  )
}

// ── Tarjeta de estadística ────────────────────────────────────────────────────

function StatCard({ label, value, sub, Icon, accentHex, topClass, delay = 0 }) {
  return (
    <div
      className={`animate-fade-up bg-card border border-rim rounded-lg p-4 flex flex-col gap-3 hover:border-rim-hi transition-colors relative overflow-hidden ${topClass}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-3xl font-bold tabular-nums leading-none" style={{ color: accentHex }}>
            {value}
          </div>
          <div className="text-[10px] text-ink tracking-widest uppercase mt-2 leading-tight">{label}</div>
        </div>
        <div className="w-8 h-8 rounded flex items-center justify-center shrink-0 mt-0.5"
             style={{ background: `${accentHex}1a`, border: `1px solid ${accentHex}30` }}>
          <Icon size={14} style={{ color: accentHex }} />
        </div>
      </div>
      {sub && <div className="text-[10px] text-ink-dim leading-snug">{sub}</div>}
    </div>
  )
}

// ── Donut de amenazas ─────────────────────────────────────────────────────────

const TT_STYLE = {
  backgroundColor: '#0f1220',
  border: '1px solid #1a2035',
  borderRadius: 3,
  padding: '5px 10px',
  color: '#dde4f0',
  fontSize: 11,
  fontFamily: "'IBM Plex Mono', monospace",
}

function ThreatDonut({ stats }) {
  const raw = [
    { name: 'Critical', value: stats.critical, hex: '#ff3d52' },
    { name: 'High',     value: stats.high,     hex: '#ff7340' },
    { name: 'Medium',   value: stats.medium,   hex: '#ffc107' },
    { name: 'Low',      value: stats.low,       hex: '#22d48e' },
  ]
  const data = raw.filter(d => d.value > 0)
  const total = stats.totalVulns

  return (
    <div className="animate-fade-up bg-card border border-rim rounded-lg p-5 h-full flex flex-col" style={{ animationDelay: '200ms' }}>
      <Sect label="Distribución de amenazas" right="todos los repos" />
      <div className="flex-1 flex items-center justify-center gap-5">
        {/* Donut */}
        <div className="relative shrink-0" style={{ width: 200, height: 200 }}>
          <ResponsiveContainer width={200} height={200}>
            <PieChart>
              <Pie
                data={data.length > 0 ? data : [{ name: 'empty', value: 1, hex: '#1a2035' }]}
                cx={96} cy={96}
                innerRadius={62} outerRadius={88}
                paddingAngle={data.length > 1 ? 2 : 0}
                dataKey="value"
                startAngle={90} endAngle={-270}
                animationBegin={300} animationDuration={900}
                stroke="none"
              >
                {(data.length > 0 ? data : [{ hex: '#1a2035' }]).map((e, i) => (
                  <Cell key={i} fill={e.hex} stroke="transparent" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={TT_STYLE}
                formatter={(v, name) => [`${v} CVEs`, name]}
                cursor={false}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-2xl font-bold text-ink tabular-nums leading-none">{total}</span>
            <span className="text-[9px] text-ink-off uppercase tracking-widest mt-1">CVEs</span>
          </div>
        </div>

        {/* Breakdown */}
        <div className="flex-1 space-y-3 min-w-0">
          {raw.map(({ name, value, hex }) => {
            const pct = total > 0 ? (value / total) * 100 : 0
            return (
              <div key={name}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[10px] tracking-widest uppercase" style={{ color: hex }}>{name}</span>
                  <span className="text-[11px] font-bold tabular-nums" style={{ color: hex }}>{value}</span>
                </div>
                <div className="h-1 rounded-sm overflow-hidden bg-rim">
                  <div className="h-full bar-seg" style={{ width: `${pct}%`, backgroundColor: hex }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── CVEs de alta prioridad ────────────────────────────────────────────────────

function HighPriority({ vulns }) {
  return (
    <div className="animate-fade-up bg-card border border-rim rounded-lg p-5" style={{ animationDelay: '260ms' }}>
      <Sect label="Alta prioridad — CVSS" right="top 7 · score desc" />
      {!(vulns?.length) ? (
        <p className="text-xs text-ink-dim italic mt-2">Sin datos de CVSS disponibles</p>
      ) : (
        <div className="space-y-1">
          {vulns.map((v, i) => (
            <div key={i} className="flex items-center gap-2.5 py-2 border-b border-rim last:border-0 group">
              <span className="text-[10px] text-ink-off w-4 tabular-nums shrink-0">{i + 1}</span>
              <CvssBadge score={v.cvssScore} />
              <div className="flex-1 min-w-0">
                <div className="text-[11px] font-semibold text-ink truncate group-hover:text-accent transition-colors">
                  {v.id}
                </div>
                <div className="text-[10px] text-ink-dim truncate">{v.pkg} · {v.repo}</div>
              </div>
              <SevBadge s={v.severity} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Barra apilada horizontal ──────────────────────────────────────────────────

function StackedBar({ counts }) {
  const { Critical = 0, High = 0, Medium = 0, Low = 0 } = counts
  const total = Critical + High + Medium + Low || 1
  return (
    <div className="flex h-2 w-full overflow-hidden rounded-sm bg-rim">
      {[['Critical','#ff3d52'], ['High','#ff7340'], ['Medium','#ffc107'], ['Low','#22d48e']].map(([k, hex]) => {
        const v = counts[k] ?? 0
        return v > 0 ? (
          <div key={k} className="bar-seg" style={{ width: `${(v / total) * 100}%`, backgroundColor: hex }} title={`${k}: ${v}`} />
        ) : null
      })}
    </div>
  )
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export default function Dashboard({ data }) {
  const { stats, repoVulnMap, topPackages, topRules, typeMap, topHighPriorityVulns } = data

  const repoRows = Object.entries(repoVulnMap).sort(
    (a, b) =>
      (b[1].Critical * 4 + b[1].High * 3 + b[1].Medium * 2 + b[1].Low) -
      (a[1].Critical * 4 + a[1].High * 3 + a[1].Medium * 2 + a[1].Low)
  )

  const topTypes = Object.entries(typeMap).sort((a, b) => b[1] - a[1]).slice(0, 6)
  const maxType  = topTypes[0]?.[1] || 1
  const totalDeps = stats.totalDeps?.toLocaleString?.() ?? stats.totalDeps

  const CARDS = [
    { label: 'Total CVEs',       value: stats.totalVulns,      sub: `${stats.repos} repos`,                        topClass: 'card-crit', accentHex: '#ff3d52', Icon: ShieldAlert, delay: 0  },
    { label: 'Críticos',         value: stats.critical,        sub: `${stats.high} high · ${stats.medium} medium`, topClass: 'card-hi',   accentHex: '#ff7340', Icon: Flame,       delay: 60 },
    { label: 'Hallazgos CodeQL', value: stats.codeqlFindings,  sub: `${stats.codeqlErrors} errores críticos`,       topClass: 'card-vuln', accentHex: '#a855f7', Icon: Code2,       delay: 120 },
  ]

  return (
    <div className="p-6 space-y-5 max-w-screen-xl mx-auto">

      {/* Header */}
      <div className="animate-fade-up">
        <div className="micro mb-1">Panel de control</div>
        <h1 className="text-xl font-bold text-ink tracking-tight">Security Overview</h1>
        <p className="text-[11px] text-ink-dim mt-1">
          {stats.repos} repositorio{stats.repos !== 1 ? 's' : ''} · Grype + CodeQL + Syft
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {CARDS.map((c, i) => <StatCard key={i} {...c} />)}
      </div>

      {/* Donut + High priority */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ThreatDonut stats={stats} />
        <HighPriority vulns={topHighPriorityVulns} />
      </div>

      {/* Repo breakdown + SBOM types */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

        {/* Repos */}
        <div className="lg:col-span-3 animate-fade-up bg-card border border-rim rounded-lg p-5"
             style={{ animationDelay: '320ms' }}>
          <Sect label="CVEs por repositorio" />

          {/* Leyenda */}
          <div className="flex gap-4 mb-4">
            {[['#ff3d52','Critical'],['#ff7340','High'],['#ffc107','Medium'],['#22d48e','Low']].map(([hex, lbl]) => (
              <span key={lbl} className="flex items-center gap-1.5 text-[10px] text-ink-dim">
                <span className="w-2 h-2 rounded-sm shrink-0" style={{ backgroundColor: hex }} />
                <span className="tracking-widest uppercase">{lbl}</span>
              </span>
            ))}
          </div>

          {repoRows.length === 0 ? (
            <p className="text-xs text-ink-dim italic">Sin datos de Grype</p>
          ) : (
            <div className="space-y-4">
              {repoRows.map(([repo, counts]) => {
                const total = Object.values(counts).reduce((a, b) => a + b, 0)
                return (
                  <div key={repo}>
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-xs text-ink truncate max-w-[65%]">{repo}</span>
                      <span className="text-[10px] text-ink-dim tabular-nums">{total} CVEs</span>
                    </div>
                    <StackedBar counts={counts} />
                    <div className="flex gap-3 mt-1.5 text-[10px]">
                      {counts.Critical > 0 && <span style={{ color: '#ff3d52' }} className="font-bold">{counts.Critical} crit</span>}
                      {counts.High     > 0 && <span style={{ color: '#ff7340' }}>{counts.High} high</span>}
                      {counts.Medium   > 0 && <span style={{ color: '#ffc107' }}>{counts.Medium} med</span>}
                      {counts.Low      > 0 && <span style={{ color: '#22d48e' }}>{counts.Low} low</span>}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* SBOM types */}
        <div className="lg:col-span-2 animate-fade-up bg-card border border-rim rounded-lg p-5"
             style={{ animationDelay: '380ms' }}>
          <Sect label="Dependencias por tipo" right={`${totalDeps} total`} />
          {topTypes.length === 0 ? (
            <p className="text-xs text-ink-dim italic">Sin datos de SBOM</p>
          ) : (
            <div className="space-y-3">
              {topTypes.map(([type, count]) => (
                <div key={type}>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-ink uppercase tracking-widest truncate">{type}</span>
                    <span className="text-ink-dim tabular-nums ml-2 shrink-0">{count.toLocaleString()}</span>
                  </div>
                  <div className="h-1.5 rounded-sm overflow-hidden bg-rim">
                    <div className="h-full bar-seg rounded-sm"
                         style={{ width: `${(count / maxType) * 100}%`, backgroundColor: '#3d7fff' }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Bottom tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Top packages */}
        <div className="animate-fade-up bg-card border border-rim rounded-lg p-5"
             style={{ animationDelay: '440ms' }}>
          <Sect label="Paquetes con más CVEs" right="top 10" />
          {topPackages.length === 0 ? (
            <p className="text-xs text-ink-dim italic">Sin datos</p>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-rim text-[9px] uppercase tracking-[0.15em] text-ink-off">
                  <th className="text-left pb-2 font-medium">#</th>
                  <th className="text-left pb-2 font-medium">Paquete</th>
                  <th className="text-left pb-2 font-medium">Sev</th>
                  <th className="text-right pb-2 font-medium">CVEs</th>
                </tr>
              </thead>
              <tbody>
                {topPackages.map((p, i) => (
                  <tr key={i} className="trow">
                    <td className="py-2 text-[10px] text-ink-off tabular-nums w-6">{i + 1}</td>
                    <td className="py-2 max-w-0">
                      <div className="text-[11px] text-ink truncate">{p.pkg}</div>
                      <div className="text-[10px] text-ink-dim">{p.version}</div>
                    </td>
                    <td className="py-2"><SevBadge s={p.severity} /></td>
                    <td className="py-2 text-right font-bold text-ink tabular-nums text-xs">{p.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Top CodeQL rules */}
        <div className="animate-fade-up bg-card border border-rim rounded-lg p-5"
             style={{ animationDelay: '500ms' }}>
          <Sect label="Reglas CodeQL frecuentes" right="top 10" />
          {topRules.length === 0 ? (
            <p className="text-xs text-ink-dim italic">Sin hallazgos de CodeQL</p>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-rim text-[9px] uppercase tracking-[0.15em] text-ink-off">
                  <th className="text-left pb-2 font-medium">Regla</th>
                  <th className="text-left pb-2 font-medium">Nivel</th>
                  <th className="text-right pb-2 font-medium">N°</th>
                </tr>
              </thead>
              <tbody>
                {topRules.map((r, i) => (
                  <tr key={i} className="trow">
                    <td className="py-2 max-w-0">
                      <div className="text-[11px] text-ink truncate">{r.name || r.rule_id}</div>
                      <div className="text-[10px] text-ink-dim truncate">{r.rule_id}</div>
                    </td>
                    <td className="py-2">
                      <span className={`sev-badge sev-${r.severity}`}>{r.severity}</span>
                    </td>
                    <td className="py-2 text-right font-bold text-ink tabular-nums text-xs">{r.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
