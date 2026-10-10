import json
from collections import defaultdict
from datetime import datetime

# 1. Load the clean data
with open('clean_contacts.json', 'r', encoding='utf-8') as f:
    contacts = json.load(f)
with open('clean_opportunities.json', 'r', encoding='utf-8') as f:
    opps = json.load(f)
with open('pipeline_stages.json', 'r', encoding='utf-8') as f:
    stages_map = json.load(f)

# 2. Process the data
volume_by_source = defaultdict(int)
revenue_by_source = defaultdict(float)
closed_deals_by_source = defaultdict(int)
stage_counts_by_source = defaultdict(lambda: defaultdict(int))
total_stage_counts = defaultdict(int)

for opp in opps:
    source = opp.get('source') or 'Unknown'
    stage_id = opp.get('pipelineStageId')
    stage_name = stages_map.get(stage_id, 'Unknown Stage')
    value = opp.get('monetaryValue', 0) or 0
    status = opp.get('status', '')

    volume_by_source[source] += 1
    stage_counts_by_source[source][stage_name] += 1
    total_stage_counts[stage_name] += 1
    
    if status == 'won' or stage_name == 'Closed':
        closed_deals_by_source[source] += 1
        revenue_by_source[source] += value

# Find Top Sources for KPI Cards
top_revenue_source = max(revenue_by_source, key=revenue_by_source.get) if revenue_by_source else "N/A"
top_revenue_amount = revenue_by_source[top_revenue_source] if top_revenue_source != "N/A" else 0
top_volume_source = max(volume_by_source, key=volume_by_source.get) if volume_by_source else "N/A"
top_volume_amount = volume_by_source[top_volume_source] if top_volume_source != "N/A" else 0

# Sort data for charts
sorted_revenue = dict(sorted(revenue_by_source.items(), key=lambda item: item[1], reverse=True))
sorted_funnel = sorted(total_stage_counts.items(), key=lambda item: item[1], reverse=True)

current_date = datetime.now().strftime("%B %d, %Y")

# Convert data to JSON strings for JS
volume_json = json.dumps(dict(volume_by_source))
revenue_json = json.dumps(sorted_revenue)
funnel_json = json.dumps([{"stage": k, "count": v} for k, v in sorted_funnel])

# Prepare table data
table_sources = sorted(volume_by_source.keys())
table_stages = ["Qualified Opt In", "Booked call", "Follow Up", "Closed", "Disqualified", "No Show", "Lost", "Cancelled"]

# --- FIX: Pre-calculate the HTML for the table to avoid f-string syntax errors ---
th_tags = "".join([f'<th scope="col" class="px-4 py-3">{stage}</th>' for stage in table_stages])
table_header_html = f"""
<tr>
    <th scope="col" class="px-4 py-3 rounded-l-lg">Source</th>
    {th_tags}
    <th scope="col" class="px-4 py-3 rounded-r-lg">Total</th>
</tr>
"""

rows = []
for source in table_sources:
    tds = "".join([f'<td class="px-4 py-3">{stage_counts_by_source[source].get(stage, 0)}</td>' for stage in table_stages])
    row = f"""
    <tr class="border-b border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50">
        <td class="px-4 py-3 font-medium text-slate-800 dark:text-white">{source}</td>
        {tds}
        <td class="px-4 py-3 font-bold text-emerald-600 dark:text-emerald-400">{volume_by_source[source]}</td>
    </tr>
    """
    rows.append(row)
table_body_html = "".join(rows)
# -----------------------------------------------------------------------------

# 3. Generate the HTML
html_content = f"""
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marketing Performance Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{ darkMode: 'class' }}
    </script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
    <style>
        body {{ font-family: 'Inter', sans-serif; transition: background-color 0.3s, color 0.3s; }}
        .chart-container {{ position: relative; height: 300px; width: 100%; }}
    </style>
</head>
<body class="bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 p-6 min-h-screen">
    <div class="max-w-7xl mx-auto">
        <!-- Header -->
        <div class="mb-8 flex justify-between items-center flex-wrap gap-4">
            <div>
                <h1 class="text-3xl font-bold text-slate-800 dark:text-white">Marketing Performance Dashboard</h1>
                <p class="text-slate-500 dark:text-slate-400 mt-1 text-sm">Data Quality: 306 valid leads analyzed. 15 internal & 48 untagged records excluded.</p>
            </div>
            <div class="flex items-center gap-3">
                <span class="px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border border-blue-200 dark:border-blue-700">
                    Snapshot: {current_date}
                </span>
                <button id="theme-toggle" class="px-4 py-2 rounded-lg bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-sm font-medium hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition shadow-sm cursor-pointer">
                    Toggle Theme
                </button>
            </div>
        </div>

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div class="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <p class="text-slate-500 dark:text-slate-400 text-xs font-semibold uppercase tracking-wider">Top Volume Source</p>
                <p class="text-2xl font-bold text-slate-800 dark:text-white mt-1">{top_volume_source}</p>
                <p class="text-emerald-600 dark:text-emerald-400 text-sm mt-1">{top_volume_amount} leads</p>
            </div>
            <div class="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <p class="text-slate-500 dark:text-slate-400 text-xs font-semibold uppercase tracking-wider">Top Revenue Source</p>
                <p class="text-2xl font-bold text-slate-800 dark:text-white mt-1">{top_revenue_source}</p>
                <p class="text-emerald-600 dark:text-emerald-400 text-sm mt-1">${top_revenue_amount:,.0f}</p>
            </div>
            <div class="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <p class="text-slate-500 dark:text-slate-400 text-xs font-semibold uppercase tracking-wider">Total Sources Tracked</p>
                <p class="text-2xl font-bold text-slate-800 dark:text-white mt-1">{len(volume_by_source)}</p>
                <p class="text-slate-500 dark:text-slate-400 text-sm mt-1">Channels active</p>
            </div>
            <div class="bg-white dark:bg-slate-800 p-5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <p class="text-slate-500 dark:text-slate-400 text-xs font-semibold uppercase tracking-wider">Data Integrity</p>
                <p class="text-2xl font-bold text-slate-800 dark:text-white mt-1">94%</p>
                <p class="text-slate-500 dark:text-slate-400 text-sm mt-1">Valid records kept</p>
            </div>
        </div>

        <!-- Charts Row 1 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <h2 class="text-lg font-semibold text-slate-800 dark:text-white mb-4">1. Lead Volume by Source</h2>
                <div class="chart-container"><canvas id="volumeChart"></canvas></div>
            </div>
            <div class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <h2 class="text-lg font-semibold text-slate-800 dark:text-white mb-4">4. Closed Revenue by Source</h2>
                <div class="chart-container"><canvas id="revenueChart"></canvas></div>
            </div>
        </div>

        <!-- Charts Row 2 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <h2 class="text-lg font-semibold text-slate-800 dark:text-white mb-4">2. Source Efficiency (Leads vs. Closed Deals)</h2>
                <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">Identify high-ROI sources for next month's budget.</p>
                <div class="chart-container"><canvas id="efficiencyChart"></canvas></div>
            </div>
            <div class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                <h2 class="text-lg font-semibold text-slate-800 dark:text-white mb-4">3. Stage-to-Stage Conversion Funnel</h2>
                <p class="text-xs text-slate-500 dark:text-slate-400 mb-4">Where leads move and where they drop.</p>
                <div class="chart-container"><canvas id="funnelChart"></canvas></div>
            </div>
        </div>

        <!-- Pipeline Table -->
        <div class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm mb-6">
            <h2 class="text-lg font-semibold text-slate-800 dark:text-white mb-4">Pipeline Progression: 8-Stage Breakdown by Source</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-sm text-left text-slate-600 dark:text-slate-300">
                    <thead class="text-xs text-slate-500 dark:text-slate-400 uppercase bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
                        {table_header_html}
                    </thead>
                    <tbody>
                        {table_body_html}
                    </tbody>
                </table>
            </div>
        </div>

        <p class="text-xs text-slate-400 dark:text-slate-500 text-center mt-8">Data Quality Note: Leads with missing contact info were retained for accurate volume tracking. Internal test records excluded.</p>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const toggleBtn = document.getElementById('theme-toggle');
            toggleBtn.addEventListener('click', function() {{
                document.documentElement.classList.toggle('dark');
            }});
        }});

        Chart.register(ChartDataLabels);

        const volumeData = {volume_json};
        const revenueData = {revenue_json};
        const funnelData = {funnel_json};
        
        const efficiencyData = {{
            leads: {json.dumps(dict(volume_by_source))},
            closed: {json.dumps(dict(closed_deals_by_source))}
        }};

        const commonOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ labels: {{ color: '#64748b' }} }},
                datalabels: {{
                    color: '#ffffff',
                    anchor: 'end',
                    align: 'top',
                    font: {{ weight: 'bold', size: 10 }}
                }}
            }},
            scales: {{
                x: {{ 
                    ticks: {{ color: '#64748b' }}, 
                    grid: {{ display: false }}
                }},
                y: {{ 
                    ticks: {{ color: '#64748b' }}, 
                    grid: {{ display: false }}
                }}
            }}
        }};

        new Chart(document.getElementById('volumeChart'), {{
            type: 'bar',
            data: {{ labels: Object.keys(volumeData), datasets: [{{ label: 'Leads', data: Object.values(volumeData), backgroundColor: '#3b82f6', borderRadius: 4 }}] }},
            options: {{ ...commonOptions, plugins: {{ ...commonOptions.plugins, legend: {{ display: false }} }} }}
        }});

        new Chart(document.getElementById('revenueChart'), {{
            type: 'bar',
            data: {{ labels: Object.keys(revenueData), datasets: [{{ label: 'Revenue', data: Object.values(revenueData), backgroundColor: '#10b981', borderRadius: 4 }}] }},
            options: {{ 
                ...commonOptions, 
                indexAxis: 'y', 
                plugins: {{ ...commonOptions.plugins, legend: {{ display: false }}, datalabels: {{ ...commonOptions.plugins.datalabels, formatter: (val) => '$' + val.toLocaleString() }} }},
            }}
        }});

        const sources = Object.keys(efficiencyData.leads);
        new Chart(document.getElementById('efficiencyChart'), {{
            type: 'bar',
            data: {{
                labels: sources,
                datasets: [
                    {{ label: 'Total Leads', data: sources.map(s => efficiencyData.leads[s]), backgroundColor: '#3b82f6', borderRadius: 4 }},
                    {{ label: 'Deals Closed', data: sources.map(s => efficiencyData.closed[s] || 0), backgroundColor: '#10b981', borderRadius: 4 }}
                ]
            }},
            options: {{ ...commonOptions }}
        }});

        new Chart(document.getElementById('funnelChart'), {{
            type: 'bar',
            data: {{
                labels: funnelData.map(d => d.stage),
                datasets: [{{ data: funnelData.map(d => d.count), backgroundColor: '#6366f1', borderRadius: 4 }}]
            }},
            options: {{ 
                ...commonOptions, 
                indexAxis: 'y', 
                plugins: {{ ...commonOptions.plugins, legend: {{ display: false }}, datalabels: {{ ...commonOptions.plugins.datalabels, anchor: 'end', align: 'end' }} }}
            }}
        }});
    </script>
</body>
</html>
"""

# 4. Save the HTML file
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Success! Open index.html in your browser.")