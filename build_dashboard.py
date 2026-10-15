import json
from collections import defaultdict
from datetime import datetime

# ---------- 1. Load clean data ----------
with open('clean_contacts.json', encoding='utf-8') as f:
    contacts = json.load(f)
with open('clean_opportunities.json', encoding='utf-8') as f:
    opps = json.load(f)
with open('pipeline_stages.json', encoding='utf-8') as f:
    stages_map = json.load(f)

PROGRESSION = ["Qualified Opt In", "Booked call", "Follow Up", "Closed"]
EXITS = ["Disqualified", "No Show", "Lost", "Cancelled"]
NOT_BUYABLE = {"Referral", "Website Form"}   # can't be scaled with ad budget
MIN_DEALS = 5                                # below this, results are anecdotal

# ---------- 2. Aggregate per source ----------
S = defaultdict(lambda: {"leads": 0, "won": 0, "revenue": 0.0, "stages": defaultdict(int)})
closed_not_won = 0
for opp in opps:
    src = opp.get('source') or 'Unknown'
    stage = stages_map.get(opp.get('pipelineStageId'), 'Unknown Stage')
    d = S[src]
    d["leads"] += 1
    d["stages"][stage] += 1
    if opp.get('status') == 'won':           # revenue = won deals only
        d["won"] += 1
        d["revenue"] += opp.get('monetaryValue') or 0
    elif stage == 'Closed':
        closed_not_won += 1                  # sanity check, shown in footer

for d in S.values():
    d["close_rate"] = d["won"] / d["leads"] if d["leads"] else 0
    d["rpl"] = d["revenue"] / d["leads"] if d["leads"] else 0
    d["avg_deal"] = d["revenue"] / d["won"] if d["won"] else 0
    # Cumulative progression: "reached at least stage X"
    d["reached"] = [d["leads"]] + [
        sum(d["stages"].get(s, 0) for s in PROGRESSION[i:]) for i in range(len(PROGRESSION))
    ]

total_leads = sum(d["leads"] for d in S.values())
total_won = sum(d["won"] for d in S.values())

# ---------- 3. Budget recommendation ----------
paid = sorted([s for s in S if s not in NOT_BUYABLE and s != 'Unknown'],
              key=lambda s: S[s]["rpl"], reverse=True)
n = len(paid)
increase = paid[:max(1, n // 4)] if n else []
review = paid[-max(1, n // 3):] if n >= 3 else []
for s in S:
    if s in NOT_BUYABLE:
        S[s]["rec"] = "Not budget-driven"
    elif s == 'Unknown':
        S[s]["rec"] = "Fix tracking"
    elif s in increase:
        S[s]["rec"] = "Increase"
    elif s in review:
        S[s]["rec"] = "Review"
    else:
        S[s]["rec"] = "Hold"

BADGE = {"Increase": "bg-emerald-600", "Hold": "bg-blue-600", "Review": "bg-amber-600",
         "Not budget-driven": "bg-slate-500", "Fix tracking": "bg-slate-500"}

def names(rec):
    items = [s for s in sorted(S, key=lambda x: S[x]["rpl"], reverse=True) if S[s]["rec"] == rec]
    return ", ".join(items) or "None"

rec_panel = "".join(
    f'<div class="rounded-lg p-4 {BADGE[r]} bg-opacity-20 border border-slate-300 dark:border-slate-600">'
    f'<p class="text-xs font-semibold uppercase tracking-wider">{r}</p>'
    f'<p class="text-lg font-bold mt-1">{names(r)}</p></div>'
    for r in ["Increase", "Hold", "Review"])

low_sample = [s for s in S if S[s]["won"] < MIN_DEALS]
tot_rev = sum(d["revenue"] for d in S.values())
top2 = sum(sorted((d["revenue"] for d in S.values()))[-2:]) / tot_rev if tot_rev else 0
caveat = (f"Caution: {len(low_sample)} of {len(S)} sources have fewer than {MIN_DEALS} won deals, "
          f"and the top 2 sources hold {top2:.0%} of revenue. Treat these as directional, not final. "
          "Ranking is by revenue per lead; there is no ad spend data, so cost efficiency is unknown.")

# ---------- 4. Tables ----------
by_rpl = sorted(S, key=lambda s: S[s]["rpl"], reverse=True)
rank_rows = "".join(f"""
<tr class="border-b border-slate-200 dark:border-slate-700">
  <td class="px-4 py-3 font-medium">{s}</td><td class="px-4 py-3">{S[s]['leads']}</td>
  <td class="px-4 py-3">{S[s]['won']}</td><td class="px-4 py-3">{S[s]['close_rate']:.1%}</td>
  <td class="px-4 py-3">${S[s]['revenue']:,.0f}</td><td class="px-4 py-3">${S[s]['rpl']:,.0f}</td>
  <td class="px-4 py-3">${S[s]['avg_deal']:,.0f}</td>
  <td class="px-4 py-3"><span class="px-2 py-1 rounded text-xs text-white {BADGE[S[s]['rec']]}">{S[s]['rec']}</span></td>
</tr>""" for s in by_rpl)

def prog_cells(s):
    r, out = S[s]["reached"], f'<td class="px-4 py-3 font-bold">{S[s]["reached"][0]}</td>'
    for i in range(1, len(r)):
        pct = r[i] / r[i - 1] if r[i - 1] else 0
        out += (f'<td class="px-4 py-3" style="background:rgba(16,185,129,{0.08 + 0.5 * pct:.2f})">'
                f'{r[i]} <span class="text-xs opacity-70">({pct:.0%})</span></td>')
    return out + "".join(f'<td class="px-4 py-3">{S[s]["stages"].get(e, 0)}</td>' for e in EXITS)

prog_head = "".join(f'<th class="px-4 py-3">{h}</th>' for h in
                    ["Source", "Entered"] + PROGRESSION + EXITS)
prog_rows = "".join(
    f'<tr class="border-b border-slate-200 dark:border-slate-700">'
    f'<td class="px-4 py-3 font-medium">{s}</td>{prog_cells(s)}</tr>' for s in sorted(S))

known = set(PROGRESSION + EXITS)
unmapped = sum(c for d in S.values() for st, c in d["stages"].items() if st not in known)
warn = (f'<br><span class="text-amber-500">Warning: {unmapped} opportunities sit in stages not shown above (unrecognised stage name).</span>' if unmapped else "")
unk = 'Untagged records appear as "Unknown".' if "Unknown" in S else ""

# ---------- 5. Chart data (each sorted descending) ----------
def series(key):
    order = sorted(S, key=lambda s: S[s][key], reverse=True)
    return {"labels": order, "values": [round(S[s][key], 4) for s in order]}

DATA = json.dumps({k: series(k) for k in ["leads", "revenue", "rpl", "close_rate"]})
top_vol = max(S, key=lambda s: S[s]["leads"])
top_rev = max(S, key=lambda s: S[s]["revenue"])
top_rpl = by_rpl[0]
top_cr = max(S, key=lambda s: S[s]["close_rate"])

# ---------- 6. HTML (plain template, no f-string brace escaping) ----------
TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="dark"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Marketing Performance Dashboard</title>
<script src="https://cdn.tailwindcss.com/3.4.17"></script>
<script>tailwind.config = { darkMode: 'class' }</script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0"></script>
<style>body{font-family:'Inter',sans-serif}.cc{position:relative;height:340px;width:100%}</style></head>
<body class="bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 p-6 min-h-screen">
<div class="max-w-7xl mx-auto">
 <div class="mb-8 flex justify-between items-center flex-wrap gap-4">
  <div><h1 class="text-3xl font-bold">Marketing Performance Dashboard</h1>
   <p class="text-slate-500 dark:text-slate-400 mt-1 text-sm">__N__ opportunities across __K__ sources (from __C__ contacts loaded). __UNK__</p></div>
  <div class="flex items-center gap-3">
   <span class="px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border border-blue-200 dark:border-blue-700">Static snapshot: __DATE__</span>
   <button id="tt" class="px-4 py-2 rounded-lg bg-white dark:bg-slate-800 text-sm font-medium border border-slate-200 dark:border-slate-700 shadow-sm">Toggle Theme</button></div></div>

 <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
  __KPIS__</div>

 <div class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm mb-6">
  <h2 class="text-lg font-semibold mb-1">Where to put next month's budget</h2>
  <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">Ranked by revenue per lead among budget-driven channels (Referral and Website Form excluded).</p>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">__REC__</div>
  <p class="text-xs text-amber-600 dark:text-amber-400">__CAVEAT__</p></div>

 <div class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm mb-6">
  <h2 class="text-lg font-semibold mb-4">Source scorecard</h2>
  <div class="overflow-x-auto"><table class="w-full text-left text-sm">
   <thead class="text-xs uppercase text-slate-500 dark:text-slate-400"><tr>
    <th class="px-4 py-3">Source</th><th class="px-4 py-3">Leads</th><th class="px-4 py-3">Closed</th><th class="px-4 py-3">Close rate</th>
    <th class="px-4 py-3">Revenue</th><th class="px-4 py-3">Revenue / lead</th><th class="px-4 py-3">Avg deal</th><th class="px-4 py-3">Action</th></tr></thead>
   <tbody>__RANK__</tbody></table></div></div>

 <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
  <div class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm"><h2 class="text-lg font-semibold mb-4">1. Lead Volume by Source</h2><div class="cc"><canvas id="c1"></canvas></div></div>
  <div class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm"><h2 class="text-lg font-semibold mb-4">2. Closed Revenue by Source</h2><div class="cc"><canvas id="c2"></canvas></div></div>
  <div class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm"><h2 class="text-lg font-semibold mb-4">3. Revenue per Lead</h2><div class="cc"><canvas id="c3"></canvas></div></div>
  <div class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm"><h2 class="text-lg font-semibold mb-4">4. Close Rate by Source</h2><div class="cc"><canvas id="c4"></canvas></div></div></div>

 <div class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm mb-6">
  <h2 class="text-lg font-semibold mb-1">Pipeline progression and stage-to-stage conversion, by source</h2>
  <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">Each cell = leads that reached at least that stage, with the % of the previous column in brackets. Exit outcomes are shown separately as current counts.</p>
  <div class="overflow-x-auto"><table class="w-full text-left text-sm">
   <thead class="text-xs uppercase text-slate-500 dark:text-slate-400"><tr>__PHEAD__</tr></thead>
   <tbody>__PROWS__</tbody></table></div></div>

 <p class="text-xs text-slate-400 dark:text-slate-500 text-center mt-8">Static snapshot taken __DATE__. Revenue counts won deals only (__CNW__ opportunities in the Closed stage are not marked won and are excluded).
 Leads that exited (Disqualified, No Show, Lost, Cancelled) can't be placed in the sequence, so conversion rates are conservative.__WARN__</p>
</div>
<script>
Chart.register(ChartDataLabels);
const D = __DATA__;
let tick = '#94a3b8', lab = '#ffffff';
const charts = [];
function mk(id, s, color, fmt) {
  charts.push(new Chart(document.getElementById(id), {type: 'bar',
    data: {labels: s.labels, datasets: [{data: s.values, backgroundColor: color, borderRadius: 4}]},
    options: {indexAxis: 'y', responsive: true, maintainAspectRatio: false, layout: {padding: {right: 70}},
      plugins: {legend: {display: false}, datalabels: {color: lab, anchor: 'end', align: 'end', formatter: fmt, font: {weight: 'bold', size: 12}}},
      scales: {x: {ticks: {color: tick}, grid: {display: false}}, y: {ticks: {color: tick}, grid: {display: false}}}}}));
}
mk('c1', D.leads, '#3b82f6', v => v);
mk('c2', D.revenue, '#10b981', v => '$' + v.toLocaleString());
mk('c3', D.rpl, '#8b5cf6', v => '$' + Math.round(v).toLocaleString());
mk('c4', D.close_rate, '#f59e0b', v => (v * 100).toFixed(1) + '%');
document.getElementById('tt').addEventListener('click', () => {
  const dark = document.documentElement.classList.toggle('dark');
  lab = dark ? '#ffffff' : '#1e293b'; tick = dark ? '#94a3b8' : '#64748b';
  charts.forEach(c => { c.options.plugins.datalabels.color = lab;
    c.options.scales.x.ticks.color = tick; c.options.scales.y.ticks.color = tick; c.update(); });
});
</script></body></html>"""

def kpi(title, big, sub):
    return (f'<div class="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">'
            f'<p class="text-slate-500 dark:text-slate-400 text-xs font-semibold uppercase tracking-wider">{title}</p>'
            f'<p class="text-3xl font-extrabold mt-1">{big}</p>'
            f'<p class="text-lg font-bold text-emerald-600 dark:text-emerald-400 mt-1">{sub}</p></div>')

kpis = (kpi("Top Volume Source", top_vol, f"{S[top_vol]['leads']} leads")
        + kpi("Top Revenue Source", top_rev, f"${S[top_rev]['revenue']:,.0f}")
        + kpi("Best Revenue / Lead", top_rpl, f"${S[top_rpl]['rpl']:,.0f}")
        + kpi("Best Close Rate", top_cr, f"{S[top_cr]['close_rate']:.1%}"))

html = TEMPLATE
for key, val in {
    "__N__": total_leads, "__K__": len(S), "__C__": len(contacts),
    "__DATE__": datetime.now().strftime("%B %d, %Y"), "__KPIS__": kpis,
    "__REC__": rec_panel, "__CAVEAT__": caveat, "__RANK__": rank_rows,
    "__PHEAD__": prog_head, "__PROWS__": prog_rows, "__CNW__": closed_not_won,
    "__DATA__": DATA, "__WARN__": warn, "__UNK__": unk,
}.items():
    html = html.replace(key, str(val))

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Success! {total_leads} opportunities, {len(S)} sources. Open index.html in your browser.")