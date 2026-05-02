import { useState, useEffect, useCallback } from 'react'

const RESULTS = '/results'
const REFRESH_MS = 30_000

const SEV_RANK = { Critical: 4, High: 3, Medium: 2, Low: 1 }

async function fetchJSON(url) {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`HTTP ${r.status} — ${url}`)
  return r.json()
}

async function loadData() {
  const report = await fetchJSON(`${RESULTS}/consolidated-report.json`)

  const grypeEntries = (report.grype || []).filter(e => e.status === 'success')
  const codeqlEntries = (report.codeql || []).filter(e =>
    e.status === 'success' || e.status === 'partial'
  )
  const sbomEntries = (report.sbom || []).filter(e => e.status === 'success')

  const [grypeRaw, codeqlRaw, sbomRaw] = await Promise.all([
    Promise.all(
      grypeEntries.map(async e => {
        try {
          const d = await fetchJSON(`${RESULTS}/${e.repo}-grype.json`)
          return (d.matches || []).map(m => {
            const cvssArr = m.vulnerability?.cvss ?? []
            const cvssScore = cvssArr.reduce((max, c) => Math.max(max, c.metrics?.baseScore ?? 0), 0)
            return {
              repo: e.repo,
              id: m.vulnerability?.id ?? 'N/A',
              severity: m.vulnerability?.severity ?? 'Unknown',
              pkg: m.artifact?.name ?? 'unknown',
              version: m.artifact?.version ?? '?',
              pkgType: m.artifact?.type ?? '?',
              fixState: m.vulnerability?.fix?.state ?? 'unknown',
              fixVersions: m.vulnerability?.fix?.versions ?? [],
              description: m.vulnerability?.description ?? '',
              cvssScore,
            }
          })
        } catch {
          return []
        }
      })
    ),
    Promise.all(
      codeqlEntries.map(async e => {
        try {
          const d = await fetchJSON(`${RESULTS}/${e.repo}-codeql.json`)
          return (d.findings || []).map(f => ({ ...f, repo: e.repo }))
        } catch {
          return []
        }
      })
    ),
    Promise.all(
      sbomEntries.map(async e => {
        try {
          const d = await fetchJSON(`${RESULTS}/${e.repo}-sbom.json`)
          return { repo: e.repo, artifacts: d.artifacts || [] }
        } catch {
          return { repo: e.repo, artifacts: [] }
        }
      })
    ),
  ])

  const allVulns = grypeRaw
    .flat()
    .sort((a, b) => (SEV_RANK[b.severity] ?? 0) - (SEV_RANK[a.severity] ?? 0))

  const allFindings = codeqlRaw.flat()
  const allArtifacts = sbomRaw.flatMap(s => s.artifacts.map(a => ({ ...a, repo: s.repo })))

  // Severity counts per repo
  const repoVulnMap = {}
  for (const v of allVulns) {
    if (!repoVulnMap[v.repo]) repoVulnMap[v.repo] = { Critical: 0, High: 0, Medium: 0, Low: 0 }
    repoVulnMap[v.repo][v.severity] = (repoVulnMap[v.repo][v.severity] ?? 0) + 1
  }

  // CodeQL findings per repo
  const repoCodeqlMap = {}
  for (const f of allFindings) {
    if (!repoCodeqlMap[f.repo]) repoCodeqlMap[f.repo] = { error: 0, warning: 0, note: 0 }
    const lvl = f.severity ?? 'warning'
    repoCodeqlMap[f.repo][lvl] = (repoCodeqlMap[f.repo][lvl] ?? 0) + 1
  }

  // SBOM type distribution
  const typeMap = {}
  for (const a of allArtifacts) {
    const t = a.type ?? 'unknown'
    typeMap[t] = (typeMap[t] ?? 0) + 1
  }

  // Top repeated packages (by CVE count)
  const pkgVulnCount = {}
  for (const v of allVulns) {
    const key = `${v.pkg}@${v.version}`
    pkgVulnCount[key] = (pkgVulnCount[key] ?? 0) + 1
  }
  const topPackages = Object.entries(pkgVulnCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([key, count]) => {
      const [pkg, version] = key.split('@')
      const worst = allVulns.find(v => v.pkg === pkg && v.version === version)
      return { pkg, version, count, severity: worst?.severity ?? 'Unknown', repo: worst?.repo ?? '' }
    })

  // CodeQL top rules
  const ruleCount = {}
  for (const f of allFindings) {
    ruleCount[f.rule_id] = (ruleCount[f.rule_id] ?? 0) + 1
  }
  const topRules = Object.entries(ruleCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([rule_id, count]) => {
      const ex = allFindings.find(f => f.rule_id === rule_id)
      return { rule_id, count, name: ex?.name ?? rule_id, severity: ex?.severity ?? 'warning' }
    })

  // Top high-priority vulns by CVSS score (deduplicated by CVE id)
  const vulnById = {}
  for (const v of allVulns) {
    if (!vulnById[v.id] || v.cvssScore > vulnById[v.id].cvssScore) {
      vulnById[v.id] = v
    }
  }
  const topHighPriorityVulns = Object.values(vulnById)
    .filter(v => v.cvssScore > 0)
    .sort((a, b) => b.cvssScore - a.cvssScore)
    .slice(0, 7)

  const fixableCount = allVulns.filter(v => v.fixState === 'fixed').length
  const fixPct = allVulns.length > 0 ? Math.round((fixableCount / allVulns.length) * 100) : 0

  const repos = [...new Set([
    ...grypeEntries.map(e => e.repo),
    ...codeqlEntries.map(e => e.repo),
    ...sbomEntries.map(e => e.repo),
  ])]

  return {
    report,
    repos,
    allVulns,
    allFindings,
    allArtifacts,
    sbomRaw,
    repoVulnMap,
    repoCodeqlMap,
    typeMap,
    topPackages,
    topRules,
    topHighPriorityVulns,
    fixPct,
    stats: {
      repos: repos.length,
      totalVulns: allVulns.length,
      critical: allVulns.filter(v => v.severity === 'Critical').length,
      high: allVulns.filter(v => v.severity === 'High').length,
      medium: allVulns.filter(v => v.severity === 'Medium').length,
      low: allVulns.filter(v => v.severity === 'Low').length,
      codeqlFindings: allFindings.length,
      codeqlErrors: allFindings.filter(f => f.severity === 'error').length,
      totalDeps: allArtifacts.length,
      fixPct,
    },
  }
}

export function useData() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const reload = useCallback(async () => {
    try {
      const d = await loadData()
      setData(d)
      setLastUpdated(new Date())
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    reload()
    const id = setInterval(reload, REFRESH_MS)
    return () => clearInterval(id)
  }, [reload])

  return { data, loading, error, lastUpdated, reload }
}
