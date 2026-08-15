"""Design tokens and base styles.

CSS custom properties are the single source of truth. Lifted verbatim from the
pre-restructure web/layout.py so the brand look is unchanged: primary #1e6fb8,
dark #1b2733, accent green #1f9d72.

Deliberately no Tailwind - it would cost a build step, a committed ~540KB
stylesheet and a generated safelist to cover Python-built class strings. Revisit
only if utility classes start being hand-rolled in more than a handful of places.
"""

from fasthtml.common import Style

CSS = """
:root {
  --bg: #f4f8f8;
  --surface: #ffffff;
  --surface-2: #eef4f4;
  --border: #dbe6e6;
  --text: #1b2733;
  --text-dim: #525a61;
  --text-mute: #93a1a1;
  --accent: #1e6fb8;          /* FastClinic primary blue */
  --accent-hover: #185a96;
  --accent-light: #dceaf6;
  --warn: #1f9d72;            /* FastClinic accent green */
  --danger: #dc2626;
  --ok: #1f9d72;
}
* { box-sizing: border-box; }
html, body { margin:0; padding:0; height:100%; background:var(--bg); color:var(--text);
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; font-size:14px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

.app {
  display: grid;
  grid-template-columns: 240px 1fr var(--rail, 340px);
  grid-template-rows: 52px 1fr;
  grid-template-areas: "top top top" "left center right";
  height: 100vh; overflow: hidden;
  transition: grid-template-columns .18s ease;
}
.app.right-expanded { --rail: clamp(420px, 42vw, 720px); }
.app.right-collapsed { --rail: 0px; }
.app.right-collapsed .right-pane { display: none; }
#copilot-reopen {
  position: fixed; right: 0; bottom: 26px; display: none;
  align-items: center; gap: 6px; cursor: pointer; z-index: 60;
  background: var(--accent); color: #fff; font-size: 13px; font-weight: 600;
  padding: 9px 14px; border-radius: 8px 0 0 8px; box-shadow: 0 2px 10px rgba(0,0,0,.18);
}
.app.right-collapsed #copilot-reopen { display: inline-flex; }
.copilot-min, .copilot-exp {
  cursor: pointer; border: 1px solid var(--border); background: var(--surface);
  border-radius: 6px; padding: 4px 9px; font-size: 13px; line-height: 1; color: var(--text-mute);
}
.copilot-min:hover, .copilot-exp:hover { background: var(--surface-2); color: var(--accent); }

/* top bar */
.topbar {
  grid-area: top;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; background: var(--surface); border-bottom: 1px solid var(--border);
}
.brand { font-weight: 700; letter-spacing: 0.3px; display: flex; align-items: center; gap: 8px; }
.brand-dot { width: 10px; height: 10px; background: var(--accent); border-radius: 50%; display: inline-block; }
.topbar .env-pill {
  background: var(--accent-light); color: var(--accent-hover);
  padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.topbar .actions { display: flex; gap: 10px; align-items: center; }
.app-lang-select { width:auto; max-width:150px; margin:0; padding:5px 26px 5px 8px;
  font-size:12px; border:1px solid var(--border); border-radius:6px; background-color:var(--surface); }

/* left nav */
.left-pane {
  grid-area: left;
  background: var(--surface); border-right: 1px solid var(--border);
  padding: 12px 0; overflow-y: auto;
}
.nav-section { margin-bottom: 14px; }
.nav-section h4 {
  margin: 6px 16px 4px; font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.8px; color: var(--text-mute); font-weight: 700;
}
.nav-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px; color: var(--text-dim); cursor: pointer;
  border-left: 3px solid transparent;
}
.nav-item:hover { background: var(--surface-2); color: var(--text); text-decoration: none; }
.nav-item.active { background: var(--accent-light); color: var(--accent-hover);
  border-left-color: var(--accent); font-weight: 600; }
.nav-icon { width: 18px; display: inline-block; text-align: center; }

/* center */
.center-pane {
  grid-area: center; overflow-y: auto; padding: 20px 24px;
}
.page-title { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-title h1 { margin: 0; font-size: 22px; font-weight: 700; }
.page-title .sub { color: var(--text-mute); font-size: 13px; margin-top: 3px; }

/* cards */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
.kpi {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px; position: relative; overflow: hidden;
}
.kpi .label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px;
  color: var(--text-mute); font-weight: 600; }
.kpi .value { font-size: 26px; font-weight: 700; margin-top: 4px; color: var(--text); }
.kpi .trend { font-size: 12px; color: var(--ok); margin-top: 2px; }
.kpi .trend.neg { color: var(--danger); }
.kpi::after {
  content: ''; position: absolute; top: 0; right: 0; bottom: 0; width: 4px;
  background: var(--accent);
}
.kpi.warn::after { background: var(--warn); }
.kpi.neutral::after { background: var(--text-mute); }

.card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 16px 18px; margin-bottom: 16px;
}
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.card-header h3 { margin: 0; font-size: 15px; font-weight: 700; }
.record-actions { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.clinical-narrative { max-height:65vh; overflow:auto; line-height:1.6; overflow-wrap:anywhere; }
.clinical-narrative > div:first-child { margin-top:0; }
.clinical-narrative p { margin:0 0 .72rem; }
.clinical-narrative h1, .clinical-narrative h2, .clinical-narrative h3,
.clinical-narrative h4, .clinical-narrative h5, .clinical-narrative h6 {
  margin:1.2rem 0 .5rem; line-height:1.3; color:var(--text);
}
.clinical-narrative .episode-note h4:first-child { margin-top:0; }
.clinical-narrative ul, .clinical-narrative ol { margin:.4rem 0 .9rem; padding-left:1.5rem; }
.clinical-narrative blockquote { margin:.8rem 0; padding:.5rem .9rem; border-left:3px solid var(--border); color:var(--text-dim); }
.clinical-narrative code { background:var(--surface-2); border-radius:4px; padding:1px 4px; }
.clinical-narrative table { width:100%; border-collapse:collapse; margin:.8rem 0; }
.clinical-narrative th, .clinical-narrative td { border:1px solid var(--border); padding:7px 9px; text-align:left; vertical-align:top; }
.clinical-narrative th { background:var(--surface-2); }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

/* tables */
table.tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
table.tbl th { text-align: left; padding: 8px 10px; background: var(--surface-2);
  color: var(--text-dim); font-weight: 600; border-bottom: 1px solid var(--border); }
table.tbl td { padding: 8px 10px; border-bottom: 1px solid var(--border); }
table.tbl tr:last-child td { border-bottom: 0; }
table.tbl tr:hover td { background: var(--surface-2); }
.status-pill {
  display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600;
  background: var(--surface-2); color: var(--text-dim);
}
.status-pill.new { background: #dbeafe; color: #1d4ed8; }
.status-pill.initial-paid, .status-pill.diag-submitted { background: #fef3c7; color: #92400e; }
.status-pill.diag-approved, .status-pill.final-paid { background: #d1fae5; color: #065f46; }
.status-pill.completed { background: var(--accent-light); color: var(--accent-hover); }
.status-pill.cancelled, .status-pill.expired { background: #fee2e2; color: #991b1b; }
.status-pill.neutral { background: #eef2f2; color: #5a6a6a; }
.callout {
  background: #f1f7f7; border: 1px solid #cfe5e5; border-left: 4px solid var(--accent);
  color: #2c4a4a; padding: 12px 16px; border-radius: 8px; margin-bottom: 18px;
  font-size: 13px; line-height: 1.55;
}
.status-pill.pending { background: #fef3c7; color: #92400e; }
.status-pill.contacted { background: #dbeafe; color: #1d4ed8; }
.status-pill.overdue { background: #fee2e2; color: #991b1b; }
.status-pill.due-soon { background: #ffedd5; color: #9a3412; }
.status-pill.lapsed { background: #fee2e2; color: #991b1b; }
.status-pill.ok, .status-pill.active { background: var(--accent-light); color: var(--accent-hover); }
.status-pill.vaccine { background: #dbeafe; color: #1d4ed8; }
.status-pill.health_plan { background: #dcfce7; color: #166534; }
.status-pill.repeat_prescription { background: #f3e8ff; color: #6b21a8; }

/* activation list rows */
.act-row { display:grid; grid-template-columns: 1fr auto; gap:8px; align-items:center;
  padding:10px 12px; border:1px solid var(--border); border-radius:8px; margin-bottom:8px; background:var(--surface); }
.act-row .muted { color: var(--text-mute); font-size:12px; }
.msg-draft { background: var(--surface-2); border:1px dashed var(--border); border-radius:8px;
  padding:10px 12px; font-size:13px; line-height:1.5; white-space:pre-wrap; margin-top:6px; }
.seg { display:inline-flex; gap:6px; margin-bottom:14px; flex-wrap:wrap; }
.seg a { padding:6px 12px; border:1px solid var(--border); border-radius:8px; color:var(--text-dim);
  background:var(--surface); font-size:13px; }
.seg a.active { background:var(--accent); color:#fff; border-color:var(--accent); }

/* right pane */
.right-pane {
  grid-area: right; background: var(--surface); border-left: 1px solid var(--border);
  display: flex; flex-direction: column; overflow: hidden;
}
.right-header {
  padding: 12px 16px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
}
.right-header h3 { margin: 0; font-size: 14px; font-weight: 700; }
.right-header .tabs { display: flex; gap: 6px; }
.tab-btn {
  padding: 4px 10px; border-radius: 6px; font-size: 12px; cursor: pointer;
  border: 1px solid var(--border); background: var(--surface);
}
.tab-btn.active { background: var(--accent); color: white; border-color: var(--accent); }

/* chat */
.chat-body {
  flex: 1; overflow-y: auto; padding: 14px 16px;
  display: flex; flex-direction: column; gap: 12px;
}
.msg { max-width: 88%; padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.55;
  overflow-wrap: anywhere; word-break: break-word; }
.msg.user { background: var(--accent); color: white; align-self: flex-end; border-bottom-right-radius: 3px; white-space: pre-wrap; }
.msg.assistant { background: var(--surface); border: 1px solid var(--border); color: var(--text); align-self: flex-start; border-bottom-left-radius: 3px; max-width: 94%; }
.msg.system { background: #fef3c7; color: #92400e; align-self: stretch; font-style: italic; font-size: 12px; }
.msg .md > :first-child { margin-top: 0; }
.msg .md > :last-child { margin-bottom: 0; }
.msg code { background: rgba(0,0,0,0.06); padding: 1px 4px; border-radius: 3px; font-size: 12px; overflow-wrap: anywhere; }
.msg pre { background: var(--surface-2); border: 1px solid var(--border); border-radius: 6px; padding: 8px; font-size: 12px; margin: 4px 0; white-space: pre-wrap; overflow-wrap: anywhere; }
.msg pre code { background: none; }
.msg strong { color: var(--accent-hover); }
.msg h1, .msg h2, .msg h3 { margin: 8px 0 3px; font-weight: 600; }
.msg h2 { font-size: 15px; } .msg h3 { font-size: 14px; }
.msg p { margin: 4px 0; }
.msg ul, .msg ol { margin: 4px 0; padding-left: 20px; }
/* chat tables: wrap into the rail width, never scroll horizontally */
.msg table { width: 100%; table-layout: fixed; font-size: 11.5px; border-collapse: collapse;
  border: 1px solid var(--border); border-radius: 6px; margin: 6px 0; }
.msg table th { background: var(--text); color: white; font-weight: 600; font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.02em; }
.msg table th, .msg table td { text-align: left; padding: 5px 7px; border: 1px solid var(--border);
  overflow-wrap: anywhere; word-break: break-word; vertical-align: top; }
.msg table tbody tr:nth-child(even) td { background: var(--surface-2); }
.msg table tbody tr:hover td { background: var(--accent-light); }

.chat-input {
  border-top: 1px solid var(--border); padding: 10px; background: var(--surface);
}
.chat-input-row { display: flex; gap: 8px; align-items: stretch; }
.chat-input-row input { flex: 1; min-width: 0; padding: 10px 12px; border: 1px solid var(--border);
  border-radius: 8px; font-size: 13px; outline: none; }
.chat-input-row input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-light); }
.chat-send-btn { display: inline-flex; align-items: center; gap: 6px; background: var(--accent);
  color: #fff; border: none; border-radius: 8px; padding: 0 16px; font-weight: 600; font-size: 13px;
  cursor: pointer; white-space: nowrap; }
.chat-send-btn:hover { background: var(--accent-hover); }
.chat-send-btn:disabled { background: var(--text-mute); cursor: not-allowed; }
.chat-empty-hint { color: var(--text-mute); font-size: 12.5px; line-height: 1.5; text-align: center;
  padding: 18px 14px; }
/* streaming thinking indicator + tool trace */
.thinking-indicator { display: flex; align-items: center; gap: 8px; padding: 6px 14px;
  font-size: 12.5px; color: var(--text-mute); align-self: flex-start; }
.thinking-indicator .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent);
  animation: pulse 1.2s ease-in-out infinite; }
.thinking-indicator .secs { opacity: .65; }
@keyframes pulse { 0%,100% { opacity:.35; transform:scale(.85); } 50% { opacity:1; transform:scale(1.1); } }
.tool-trace { display: flex; flex-wrap: wrap; gap: 6px; align-self: flex-start; margin: 0 0 2px; padding: 0 4px; }
.tool-chip { font-size: 11px; color: var(--accent-hover); background: var(--accent-light);
  border: 1px solid var(--border); border-radius: 999px; padding: 2px 9px; }
.chat-input textarea {
  width: 100%; resize: none; border: 1px solid var(--border); border-radius: 8px;
  padding: 8px 10px; font-family: inherit; font-size: 13px; outline: none; min-height: 52px;
}
.chat-input textarea:focus { border-color: var(--accent); }
.chat-hint { font-size: 11px; color: var(--text-mute); margin-top: 4px; }
.chat-hint code { background: var(--surface-2); padding: 1px 5px; border-radius: 3px; }

/* buttons */
.btn {
  padding: 6px 12px; border-radius: 6px; border: 1px solid var(--border);
  background: var(--surface); color: var(--text); cursor: pointer; font-size: 13px;
}
.btn:hover { background: var(--surface-2); }
.btn.primary { background: var(--accent); color: white; border-color: var(--accent); }
.btn.primary:hover { background: var(--accent-hover); }

/* login */
.login-wrap {
  height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #e8f1fa 0%, #dceaf6 100%);
}
.login-card {
  background: white; padding: 36px 40px; border-radius: 14px; width: 360px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
}
.login-card h1 { margin: 0 0 4px; font-size: 22px; }
.login-card p { margin: 0 0 20px; color: var(--text-mute); font-size: 13px; }
.login-card input {
  width: 100%; padding: 10px 12px; border: 1px solid var(--border);
  border-radius: 8px; margin-bottom: 10px; font-size: 14px;
}
.login-card button { width: 100%; padding: 10px; font-weight: 600; }
.login-card .error { color: var(--danger); font-size: 12px; margin: 6px 0; }

/* command palette (chat hints) */
.cmd-chip {
  display: inline-block; padding: 3px 10px; margin: 2px; font-size: 11px;
  background: var(--bg); border: 1px solid var(--border); border-radius: 10px;
  cursor: pointer; color: var(--text-dim);
  font-family: ui-monospace, 'SFMono-Regular', monospace; transition: all .15s;
}
.cmd-chip:hover { background: var(--accent-light); color: var(--accent-hover); border-color: var(--accent); }

/* sample cards (pehero-style prompt chips below chat input) */
.sample-cards { padding: .5rem 1rem .8rem; background: var(--surface); border-top: 1px solid var(--border); }
.sample-cards-label { display: inline-block; font-size: 10px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .12em; color: var(--text-mute); margin-bottom: 6px; }
.sample-cards-row { display: flex; flex-direction: column; gap: 6px; }
.sample-card {
  display: flex; align-items: center; gap: 8px;
  background: var(--bg); border: 1px solid var(--border);
  padding: 9px 12px; border-radius: 10px; font-size: 12.5px;
  font-family: inherit; cursor: pointer; color: var(--text-dim);
  width: 100%; text-align: left; line-height: 1.35; transition: all .15s;
}
.sample-card::before { content: "💬"; font-size: 13px; flex-shrink: 0; }
.sample-card:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-light); }
.shortcut-hint { margin-top: 8px; text-align: center; }
.shortcut-hint-btn {
  background: none; border: none; color: var(--text-mute); font-size: 11px; cursor: pointer;
  padding: 2px 4px; text-decoration: underline dotted;
}
.shortcut-hint-btn:hover { color: var(--accent); }

/* chat action buttons (copy, share) */
.chat-action-btn {
  padding: 4px 10px; background: transparent; border: 1px solid var(--border);
  border-radius: 6px; color: var(--text-dim); font-size: 12px; cursor: pointer;
  transition: all .15s;
}
.chat-action-btn:hover { border-color: var(--accent); color: var(--accent); }

/* welcome hero (empty-state suggestions) */
.welcome-hero { text-align: center; padding: 24px 16px 16px; }
.welcome-head { margin-bottom: 16px; }
.welcome-title { font-size: 16px; font-weight: 700; margin: 0 0 4px; }
.welcome-sub { font-size: 12px; color: var(--text-mute); margin: 0; }
.suggestions { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; }
.suggestion-chip {
  display: flex; align-items: center; gap: 6px;
  background: var(--surface-2); border: 1px solid var(--border);
  padding: 6px 12px; border-radius: 10px; font-size: 12px;
  cursor: pointer; color: var(--text-dim); font-family: inherit;
  max-width: 260px; text-align: left;
}
.suggestion-chip:hover { border-color: var(--accent); color: var(--accent-hover); background: var(--accent-light); }
.sugg-icon { font-size: 14px; flex-shrink: 0; }
.sugg-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* table toolbar (CSV copy/download) */
.table-toolbar { display: flex; gap: .35rem; justify-content: flex-end; margin-bottom: .25rem; }
.table-action-btn {
  padding: 2px 8px; font-size: 11px; color: var(--accent);
  background: var(--accent-light); border: 1px solid var(--border);
  border-radius: 4px; cursor: pointer; font-family: inherit;
}
.table-action-btn:hover { background: var(--accent); color: white; border-color: var(--accent); }

/* plotly */
.plot { width: 100%; height: 280px; }
.spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid var(--border);
  border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* treatment calculator */
.calc-form { display:flex; flex-direction:column; gap:14px; padding:16px; }
.calc-form label { display:block; font-size:12px; font-weight:600; text-transform:uppercase;
  letter-spacing:.5px; color:var(--text-mute); margin-bottom:4px; }
.calc-form select {
  width:100%; padding:10px 12px; border:1px solid var(--border); border-radius:8px;
  font-size:14px; background:var(--surface); color:var(--text); cursor:pointer;
  appearance:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23475569' fill='none' stroke-width='1.5'/%3E%3C/svg%3E");
  background-repeat:no-repeat; background-position:right 12px center;
}
.calc-form select:focus { border-color:var(--accent); outline:none; box-shadow:0 0 0 3px var(--accent-light); }
.calc-form select:disabled { background:var(--surface-2); color:var(--text-mute); cursor:not-allowed; }

.calc-result { margin-top:16px; }
.calc-result .kpi-grid { grid-template-columns:repeat(4,1fr); }
.calc-saving {
  background:var(--accent-light); border:2px solid var(--accent); border-radius:10px;
  padding:20px; text-align:center; margin-top:16px;
}
.calc-saving .pct { font-size:36px; font-weight:800; color:var(--accent-hover); }
.calc-saving .lbl { font-size:13px; color:var(--text-dim); margin-top:4px; }
.calc-cta {
  display:block; width:100%; text-align:center; padding:12px 0;
  background:var(--accent); color:white; border-radius:8px;
  font-weight:600; font-size:14px; margin-top:16px; border:none; cursor:pointer;
  text-decoration:none;
}
.calc-cta:hover { background:var(--accent-hover); color:white; }
.calc-note { font-size:12px; color:var(--text-mute); margin-top:8px; line-height:1.5; }

@media (max-width:900px) { .calc-result .kpi-grid { grid-template-columns:repeat(2,1fr); } }
@media (max-width:640px) { .calc-result .kpi-grid { grid-template-columns:1fr; } }

/* sms broadcaster */
.sms-form { display:flex; flex-direction:column; gap:14px; padding:16px; max-width:560px; }
.sms-form label { display:block; font-size:12px; font-weight:600; text-transform:uppercase;
  letter-spacing:.5px; color:var(--text-mute); margin-bottom:4px; }
.sms-form input, .sms-form textarea, .sms-form select {
  width:100%; padding:10px 12px; border:1px solid var(--border); border-radius:8px;
  font-size:14px; background:var(--surface); color:var(--text); font-family:inherit;
}
.sms-form textarea { min-height:100px; resize:vertical; }
.sms-form input:focus, .sms-form textarea:focus, .sms-form select:focus {
  border-color:var(--accent); outline:none; box-shadow:0 0 0 3px var(--accent-light);
}
.sms-form select {
  appearance:none; cursor:pointer;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23475569' fill='none' stroke-width='1.5'/%3E%3C/svg%3E");
  background-repeat:no-repeat; background-position:right 12px center;
}
.sms-send { display:inline-flex; align-items:center; gap:6px; padding:10px 24px;
  background:var(--accent); color:white; border:none; border-radius:8px;
  font-weight:600; font-size:14px; cursor:pointer; }
.sms-send:hover { background:var(--accent-hover); }
.sms-send:disabled { background:var(--text-mute); cursor:not-allowed; }
.sms-result { margin-top:12px; padding:12px 16px; border-radius:8px; font-size:13px; }
.sms-result.success { background:#d1fae5; color:#065f46; border:1px solid #a7f3d0; }
.sms-result.error { background:#fee2e2; color:#991b1b; border:1px solid #fecaca; }
.sms-char-count { font-size:11px; color:var(--text-mute); text-align:right; margin-top:2px; }

/* web user guide (markdown rendered to HTML) */
.guide-doc { max-width: 860px; line-height: 1.6; color: var(--text); }
.guide-doc h1 { color: var(--accent); font-size: 26px; margin: 4px 0 2px; }
.guide-doc h2 { color: var(--text); font-size: 19px; margin: 26px 0 8px;
  border-bottom: 2px solid var(--accent-light); padding-bottom: 4px; }
.guide-doc h3 { font-size: 15px; margin: 18px 0 6px; }
.guide-doc p { margin: 8px 0; }
.guide-doc img { max-width: 100%; height: auto; border: 1px solid var(--border);
  border-radius: 8px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
.guide-doc hr { border: 0; border-top: 1px dashed var(--border); margin: 28px 0; }
.guide-doc blockquote { margin: 12px 0; padding: 8px 14px; border-left: 4px solid var(--accent);
  background: var(--surface-2); color: var(--text-dim); border-radius: 0 8px 8px 0; }
.guide-doc ul, .guide-doc ol { padding-left: 22px; }
.guide-doc li { margin: 4px 0; }
.guide-doc code { background: var(--surface-2); padding: 1px 5px; border-radius: 4px; font-size: 12.5px; }
.guide-doc table { width: 100%; border-collapse: collapse; font-size: 12.5px; margin: 10px 0; }
.guide-doc th { background: var(--surface-2); text-align: left; padding: 6px 9px; border: 1px solid var(--border); }
.guide-doc td { padding: 6px 9px; border: 1px solid var(--border); vertical-align: top; }
"""


# Appended after the restructure rather than edited into the block above, so the
# salvaged stylesheet stays a clean diff against the pre-restructure original.
ADDITIONS = """
/* logged-out shell: no nav, so do not reserve the 240px column */
.app.no-nav { grid-template-columns: 0 1fr var(--rail, 0px); }
.app.no-nav .left-pane { display: none; }
.login-card { max-width: 420px; margin: 48px auto; }
.login-card .btn { margin-right: 8px; }

/* the four states of a data view */
.skeleton { padding: 4px 0; }
.skeleton-row { height: 14px; margin: 10px 0; border-radius: 6px;
  background: linear-gradient(90deg, var(--surface-2) 25%, var(--surface) 50%, var(--surface-2) 75%);
  background-size: 200% 100%; animation: skeleton-shimmer 1.4s infinite; }
@keyframes skeleton-shimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }
@media (prefers-reduced-motion: reduce) { .skeleton-row { animation: none; } }

.state-empty, .state-indeterminate, .state-error {
  border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px;
  background: var(--surface); margin: 12px 0;
}
/* indeterminate and error are visually distinct from a confident "nothing here" */
.state-indeterminate { border-left: 3px solid var(--warn); }
.state-error { border-left: 3px solid var(--danger); }
.empty-title { margin: 0 0 4px; font-weight: 600; color: var(--text); }
.empty-hint { margin: 0; font-size: 13px; color: var(--text-mute); }
.capped-notice { display: block; margin-top: 8px; font-size: 12px; color: var(--text-mute); }

.field-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
.field { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; }
.field-label { display: block; font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.6px; color: var(--text-mute); }
.field-value { display: block; margin-top: 2px; color: var(--text); }
.back-link { display: inline-block; margin-bottom: 8px; font-size: 13px; }
.search-box { margin-bottom: 12px; }
.search-box input { width: 100%; max-width: 380px; padding: 8px 10px;
  border: 1px solid var(--border); border-radius: 8px; background: var(--surface); }
.encounter-row { border-bottom: 1px solid var(--border); padding: 8px 0; }
.encounter-date { margin: 0; font-weight: 600; font-size: 13px; }
.encounter-type { margin: 0; font-size: 13px; color: var(--text-dim); }
"""


def theme_styles() -> Style:
    return Style(CSS + ADDITIONS)
