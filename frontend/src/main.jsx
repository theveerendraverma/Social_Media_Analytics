import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend } from 'recharts'
import './styles.css'

const nav = [
  ['overview', 'Overview', '⌂'], ['platforms', 'Platform Analytics', '◈'], ['engagement', 'Engagement', '↗'],
  ['content', 'Content Performance', '▤'], ['audience', 'Audience Growth', '◎'], ['sentiment', 'Sentiment', '☻'],
  ['hashtags', 'Hashtags', '#'], ['insights', 'Insights', '✦']
]
const platforms = ['Instagram', 'YouTube', 'Facebook', 'X/Twitter', 'LinkedIn']
const contentTypes = ['Image', 'Video', 'Carousel', 'Reel', 'Text', 'Article', 'Live']
const colors = ['#7c5cff', '#13b8a6', '#f59e0b', '#ef6a9a', '#4f8cff']
const fmt = (v) => v == null ? '—' : Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(v)
const pct = (v) => `${Number(v || 0).toFixed(2)}%`

function useApi(path, filters, enabled = true) {
  const [state, setState] = useState({ loading: true, data: null, error: '' })
  const query = new URLSearchParams(Object.entries(filters).filter(([, v]) => v))
  useEffect(() => {
    if (!enabled) return
    let active = true
    setState({ loading: true, data: null, error: '' })

    fetch(`/api/${path}?${query}`)
      .then(async (r) => {
        const text = await r.text()
        if (!text) {
          throw new Error('No data returned by the server.')
        }

        try {
          const json = JSON.parse(text)
          if (!r.ok) {
            throw new Error(json.detail || json.message || 'Request failed.')
          }
          return json
        } catch (parseError) {
          if (!r.ok) {
            throw new Error('Server returned an invalid response.')
          }
          throw new Error('The server response was not valid JSON.')
        }
      })
      .then((data) => active && setState({ loading: false, data, error: '' }))
      .catch((error) => {
        if (!active) return
        setState({
          loading: false,
          data: null,
          error: error?.message || 'Unable to load data.'
        })
      })

    return () => { active = false }
  }, [path, query.toString(), enabled])

  return state
}

function Card({ title, value, sub, accent = '' }) {
  return <div className={`card metric ${accent}`}><span className="eyebrow">{title}</span><strong>{value}</strong>{sub && <small>{sub}</small>}</div>
}
function Panel({ title, action, children, className = '' }) { return <section className={`panel ${className}`}><div className="panel-head"><h2>{title}</h2>{action}</div>{children}</section> }
function State({ loading, error, empty, children }) {
  if (loading) return <div className="state"><span className="spinner" />Loading analytics…</div>
  if (error) return <div className="state error"><strong>Couldn’t load this view.</strong><small>{error}</small></div>
  if (empty) return <div className="state">No data for the selected filters.</div>
  return children
}
function ChartTip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return <div className="tooltip"><b>{label}</b>{payload.map(p => <div key={p.dataKey} style={{ color: p.color }}>{p.name}: {typeof p.value === 'number' ? fmt(p.value) : p.value}</div>)}</div>
}
function ExportButton({ rows, filename = 'export.csv' }) {
  const exportCsv = () => {
    if (!rows?.length) return
    const keys = Object.keys(rows[0]); const csv = [keys.join(','), ...rows.map(r => keys.map(k => `"${String(r[k] ?? '').replaceAll('"', '""')}"`).join(','))].join('\n')
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); a.download = filename; a.click(); URL.revokeObjectURL(a.href)
  }
  return <button className="button secondary" onClick={exportCsv} disabled={!rows?.length}>↓ Export CSV</button>
}

function Overview({ filters, setPage }) {
  const o = useApi('overview', filters)
  const p = useApi('platforms', filters)
  const overviewData = o.data ?? { metrics: {}, best_platform: '—', best_content_type: '—', best_post: { post_id: '—', engagement_rate: 0 } }
  const metrics = overviewData.metrics ?? {}
  const platformData = p.data?.data ?? []

  return <State {...o} empty={!o.data?.records}><div className="page">
    <div className="welcome"><div><span className="kicker">PERFORMANCE SNAPSHOT</span><h1>Good morning, here’s your pulse.</h1><p>Understand what’s resonating with your audience across every channel.</p></div><ExportButton rows={o.data ? [metrics] : []} filename="overview.csv" /></div>
    <div className="metrics">
      <Card title="Followers" value={fmt(metrics.followers)} sub="Latest platform total" accent="purple" />
      <Card title="Posts" value={fmt(metrics.posts)} sub={`${fmt(metrics.likes)} likes`} accent="teal" />
      <Card title="Reach" value={fmt(metrics.reach)} sub={`${fmt(metrics.impressions)} impressions`} accent="orange" />
      <Card title="Engagement" value={fmt(metrics.engagement)} sub={`${pct(metrics.engagement_rate)} avg. rate`} accent="pink" />
    </div>
    <div className="metrics">
      <Card title="Comments" value={fmt(metrics.comments)} />
      <Card title="Shares" value={fmt(metrics.shares)} />
      <Card title="Net growth" value={fmt(metrics.net_follower_growth)} sub={`+${fmt(metrics.new_followers)} new followers`} accent="teal" />
      <Card title="Best post" value={overviewData.best_post?.post_id ?? '—'} sub={`${pct(overviewData.best_post?.engagement_rate ?? 0)} engagement rate`} accent="orange" />
    </div>
    <div className="grid two"><Panel title="Performance by platform" action={<button className="link" onClick={() => setPage('platforms')}>View details →</button>}><State {...p} empty={!platformData.length}><ResponsiveContainer width="100%" height={280}><BarChart data={platformData}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="platform" tickLine={false} axisLine={false} /><YAxis tickLine={false} axisLine={false} tickFormatter={fmt} /><Tooltip content={<ChartTip />} /><Bar dataKey="engagement" name="Engagement" fill="#7c5cff" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer></State></Panel>
      <Panel title="At a glance"><div className="spotlight"><div className="spot-icon">✦</div><div><span>TOP PLATFORM</span><h3>{overviewData.best_platform}</h3><p>Leading engagement in your selected period.</p></div></div><div className="spotlight"><div className="spot-icon teal">◈</div><div><span>BEST CONTENT TYPE</span><h3>{overviewData.best_content_type}</h3><p>Highest average engagement rate.</p></div></div></Panel></div>
  </div></State>
}

function Platforms({ filters }) {
  const a = useApi('platforms', filters)
  const rows = a.data?.data ?? []
  return <State {...a} empty={!rows.length}><div className="page"><PageIntro title="Platform analytics" text="Compare how each channel contributes to your growth." /><Panel title="Channel comparison" action={<ExportButton rows={rows} filename="platforms.csv" />}><DataTable rows={rows} columns={[['platform','Platform'],['posts','Posts'],['reach','Reach'],['impressions','Impressions'],['engagement','Engagement'],['engagement_rate','Rate'],['followers','New followers']]} /></Panel></div></State>
}
function Engagement({ filters }) {
  const a = useApi('engagement', filters)
  const summary = a.data?.summary ?? {}
  const series = a.data?.timeseries ?? []
  return <State {...a} empty={!series.length}><div className="page"><PageIntro title="Engagement" text="Track interactions and engagement efficiency over time." /><div className="metrics"><Card title="Total engagement" value={fmt(summary.total_engagement)} accent="purple" /><Card title="Average rate" value={pct(summary.average_rate)} accent="teal" /></div><Panel title="Engagement trend"><ResponsiveContainer width="100%" height={340}><AreaChart data={series}><defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7c5cff" stopOpacity=".35" /><stop offset="100%" stopColor="#7c5cff" stopOpacity="0" /></linearGradient></defs><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="period" /><YAxis tickFormatter={fmt} /><Tooltip content={<ChartTip />} /><Area type="monotone" dataKey="engagement" stroke="#7c5cff" fill="url(#fill)" strokeWidth={3} /><Area type="monotone" dataKey="reach" stroke="#13b8a6" fill="none" strokeWidth={2} /></AreaChart></ResponsiveContainer></Panel></div></State>
}
function Content({ filters }) {
  const a = useApi('content-performance', filters), [sort, setSort] = useState('engagement_rate')
  const rows = useMemo(() => [...(a.data?.data ?? [])].sort((x, y) => Number(y[sort] || 0) - Number(x[sort] || 0)), [a.data, sort])
  return <State {...a} empty={!rows.length}><div className="page"><PageIntro title="Content performance" text="Find the formats and posts that earn attention." /><Panel title="Top content" action={<div className="panel-actions"><select className="sort-select" value={sort} onChange={e => setSort(e.target.value)}><option value="engagement_rate">Sort: engagement rate</option><option value="likes">Sort: likes</option><option value="comments">Sort: comments</option><option value="shares">Sort: shares</option><option value="reach">Sort: reach</option><option value="impressions">Sort: impressions</option></select><ExportButton rows={rows} filename="content-performance.csv" /></div>}><DataTable rows={rows} columns={[['date','Date'],['platform','Platform'],['content_type','Format'],['caption','Caption'],['likes','Likes'],['comments','Comments'],['shares','Shares'],['reach','Reach'],['impressions','Impressions'],['engagement_rate','Rate']]} /></Panel></div></State>
}
function Audience({ filters }) {
  const a = useApi('follower-growth', filters)
  const rows = a.data?.data ?? []
  return <State {...a} empty={!rows.length}><div className="page"><PageIntro title="Audience growth" text="See how your community is changing across channels." /><Panel title="Follower movement"><ResponsiveContainer width="100%" height={360}><LineChart data={rows}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="period" /><YAxis tickFormatter={fmt} /><Tooltip content={<ChartTip />} /><Legend /><Line type="monotone" dataKey="new_followers" name="New followers" stroke="#13b8a6" strokeWidth={3} /><Line type="monotone" dataKey="lost_followers" name="Lost followers" stroke="#ef6a9a" strokeWidth={2} /><Line type="monotone" dataKey="net_growth" name="Net growth" stroke="#7c5cff" strokeWidth={3} /></LineChart></ResponsiveContainer></Panel></div></State>
}
function Sentiment({ filters }) {
  const a = useApi('sentiment', filters)
  const rows = a.data?.data ?? []
  return <State {...a} empty={!rows.length}><div className="page"><PageIntro title="Sentiment" text="Understand the emotional tone behind your content." /><Panel title="Sentiment distribution"><div className="chart-row"><ResponsiveContainer width="55%" height={320}><PieChart><Pie data={rows} dataKey="posts" nameKey="sentiment" innerRadius={80} outerRadius={120} paddingAngle={4}>{rows.map((x, i) => <Cell key={x.sentiment} fill={colors[i % colors.length]} />)}</Pie><Tooltip content={<ChartTip />} /></PieChart></ResponsiveContainer><div className="legend-list">{rows.map((x, i) => <div key={x.sentiment}><i style={{ background: colors[i % colors.length] }} /> <span>{x.sentiment}</span><b>{fmt(x.posts)}</b><small>{pct(x.engagement_rate)} rate</small></div>)}</div></div></Panel></div></State>
}
function Hashtags({ filters }) {
  const a = useApi('hashtags', filters)
  const rows = a.data?.data ?? []
  return <State {...a} empty={!rows.length}><div className="page"><PageIntro title="Hashtags" text="Discover the topics driving your reach and interactions." /><Panel title="Hashtag performance" action={<ExportButton rows={rows} filename="hashtags.csv" />}><DataTable rows={rows} columns={[['hashtag','Hashtag'],['posts','Posts'],['engagement','Engagement'],['engagement_rate','Avg. rate']]} /></Panel></div></State>
}
function Insights({ filters }) {
  const a = useApi('insights', filters)
  const insights = a.data?.insights ?? []
  return <State {...a} empty={!insights.length}><div className="page"><PageIntro title="Insights" text="Actionable observations generated from the selected dataset." /><div className="insight-grid">{insights.map((x, i) => <div className="insight card" key={x}><div className="insight-no">0{i + 1}</div><p>{x}</p><span>DATA-DRIVEN OBSERVATION</span></div>)}</div></div></State>
}
function PageIntro({ title, text }) { return <div className="page-intro"><div><span className="kicker">ANALYTICS</span><h1>{title}</h1><p>{text}</p></div></div> }
function DataTable({ rows = [], columns }) { return <div className="table-wrap"><table><thead><tr>{columns.map(([, label]) => <th key={label}>{label}</th>)}</tr></thead><tbody>{rows.map((r, i) => <tr key={i}>{columns.map(([key]) => <td key={key} className={key === 'caption' ? 'caption' : ''}>{key.includes('rate') ? pct(r[key]) : ['reach', 'impressions', 'engagement', 'followers', 'posts'].includes(key) ? fmt(r[key]) : r[key]}</td>)}</tr>)}</tbody></table></div> }

function App() {
  const [page, setPage] = useState('overview'), [dark, setDark] = useState(false)
  const [filters, setFilters] = useState({ platform: '', content_type: '', start_date: '', end_date: '' })
  const [mobile, setMobile] = useState(false)
  const update = (k, v) => setFilters(f => ({ ...f, [k]: v }))
  const pageView = useMemo(() => ({ overview: <Overview filters={filters} setPage={setPage} />, platforms: <Platforms filters={filters} />, engagement: <Engagement filters={filters} />, content: <Content filters={filters} />, audience: <Audience filters={filters} />, sentiment: <Sentiment filters={filters} />, hashtags: <Hashtags filters={filters} />, insights: <Insights filters={filters} /> }[page]), [page, filters])
  return <div className={dark ? 'app dark' : 'app'}>
    <aside className={mobile ? 'sidebar open' : 'sidebar'}>
      <div className="brand"><span className="brand-mark">✦</span><b>pulse</b><button className="close" onClick={() => setMobile(false)}>×</button></div>
      <nav>{nav.map(([id, label, icon]) => <button className={page === id ? 'active' : ''} onClick={() => { setPage(id); setMobile(false) }} key={id}><span>{icon}</span>{label}</button>)}</nav>
      <div className="sidebar-foot"><div className="avatar">SA</div><div><b>Social team</b><small>Workspace</small></div><span>•••</span></div>
    </aside>
    <main>
      <header>
        <button className="hamburger" onClick={() => setMobile(true)}>☰</button>
        <div className="crumb">Workspace <span>/</span> <b>{nav.find(x => x[0] === page)?.[1]}</b></div>
        <div className="header-actions"><button className="icon-btn" onClick={() => setDark(!dark)}>{dark ? '☀' : '☾'}</button><button className="avatar">SA</button></div>
      </header>
      <div className="filters">
        <label>FROM<input type="date" value={filters.start_date} onChange={e => update('start_date', e.target.value)} /></label>
        <label>TO<input type="date" value={filters.end_date} onChange={e => update('end_date', e.target.value)} /></label>
        <label>PLATFORM<select value={filters.platform} onChange={e => update('platform', e.target.value)}><option value="">All platforms</option>{platforms.map(x => <option key={x}>{x}</option>)}</select></label>
        <label>CONTENT TYPE<select value={filters.content_type} onChange={e => update('content_type', e.target.value)}><option value="">All content</option>{contentTypes.map(x => <option key={x}>{x}</option>)}</select></label>
        <button className="reset" onClick={() => setFilters({ platform: '', content_type: '', start_date: '', end_date: '' })}>Reset</button>
      </div>
      {pageView}
    </main>
  </div>
}
createRoot(document.getElementById('root')).render(<App />)
