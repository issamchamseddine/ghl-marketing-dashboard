import json

# Load the clean data
with open('clean_opportunities.json', 'r', encoding='utf-8') as f:
    opps = json.load(f)
with open('pipeline_stages.json', 'r', encoding='utf-8') as f:
    stages_map = json.load(f)

print("--- DATA VALIDATION REPORT ---\n")

# 1. Check Total Volume
total_opps = len(opps)
print(f"1. TOTAL OPPORTUNITIES: {total_opps}")

# 2. Check Consistency Rule (Do the 8 stages sum to the total?)
stage_counts = {}
for opp in opps:
    stage_name = stages_map.get(opp.get('pipelineStageId'), 'Unknown')
    stage_counts[stage_name] = stage_counts.get(stage_name, 0) + 1

sum_of_stages = sum(stage_counts.values())
print(f"2. SUM OF ALL 8 STAGES: {sum_of_stages}")

if total_opps == sum_of_stages:
    print("   [PASS] Consistency Rule: Total matches the sum of all stages!")
else:
    print(f"   [FAIL] Consistency Rule: Mismatch! Difference is {total_opps - sum_of_stages}")

# 3. Check Source Breakdown
source_counts = {}
for opp in opps:
    source = opp.get('source') or 'Unknown'
    source_counts[source] = source_counts.get(source, 0) + 1

print(f"\n3. SOURCE BREAKDOWN (Sum should equal {total_opps}):")
sum_of_sources = 0
for source, count in sorted(source_counts.items()):
    print(f"   - {source}: {count}")
    sum_of_sources += count

if sum_of_sources == total_opps:
    print("   [PASS] Source Breakdown sums correctly!")
else:
    print(f"   [FAIL] Source breakdown mismatch!")

# 4. Check Revenue Logic
closed_revenue = 0
closed_count = 0
for opp in opps:
    stage_name = stages_map.get(opp.get('pipelineStageId'), 'Unknown')
    status = opp.get('status', '')
    value = opp.get('monetaryValue', 0) or 0
    
    # Check how we are defining "Closed"
    if status == 'won' or stage_name == 'Closed':
        closed_count += 1
        closed_revenue += value

print(f"\n4. REVENUE LOGIC CHECK:")
print(f"   - Deals marked as 'Won' or in 'Closed' stage: {closed_count}")
print(f"   - Total Calculated Revenue: ${closed_revenue:,.2f}")

print("\n--- END OF REPORT ---")