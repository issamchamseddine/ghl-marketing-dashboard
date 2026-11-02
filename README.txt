                                         Marketing Performance Dashboard: Project Submission

Author: Issam Chamseddine
Dashboard link: https://ghl-marketing-dashboard-ten.vercel.app/
Loom Video Link: https://go.screenpal.com/watch/cO6DDQnyItJ

• Purpose
An agency has run paid acquisition for three months with no consolidated view
of what is working. This dashboard lets the owner open one page and see where
to put next month's budget. All data comes from GoHighLevel (GHL): leads,
sources and an 8-stage sales pipeline.

• How it works
1. A Python script pulls contacts, opportunities and pipeline stages from the
   GHL sandbox API.
2. The data is cleaned to keep only this agency's records

The page is static by design: no API key or contact data is exposed in the
browser. Only aggregated numbers are published.

• Record selection
The sandbox is shared with other students' records. Records were kept or
excluded using this rule: records tagged with "dash-project". Records with no source are shown
as "Unknown" rather than hidden.

• What the dashboard shows
- "Lead volume:" bar chart, sorted high to low.
- "Pipeline progression through the 8 stages:" table per source.
- "Stage-to-stage conversion rates:" heatmap table, % of the previous stage.
- "Closed revenue:" bar chart and scorecard.
- "Budget recommendation:" Increase / Hold / Review panel.
- "Extras:" revenue per lead, close rate, average deal size.

• Key design decisions
- "Cumulative progression:" each stage counts leads that reached at least
  that stage, because the data is a snapshot of each lead's current stage.
- "Exit states shown separately:" Disqualified, No Show, Lost and Cancelled
  are outcomes, not steps in the sequence.
- "Revenue:" sums only deals with status "won".
- "Budget logic:" with no ad spend data, budget-driven sources are ranked by
  revenue per lead. Top group = Increase, bottom group = Review, others = Hold.
  Referral and Website Form are labelled "Not budget-driven".
- "No combined totals:" every metric is broken out by source.

• Limitations and assumptions
- No ad spend data, so cost efficiency (cost per lead, ROI) cannot be calculated.
- Most sources have fewer than five won deals, and revenue is concentrated in
  a few sources, so recommendations are directional.
- Leads that exited the pipeline cannot be placed in the sequence, so
  conversion rates are conservative.
- Lead volume currently counts opportunities, not contacts. [Update once
  confirmed.]

• Planned improvements
- Scheduled extraction every Monday before opening so the
  Vercel page refreshes automatically, with credentials kept in secrets.
 (The Python code that extracts the data and holds the API key and Location ID, should reside on
  the owner's computer  and a schedulaed run of this file on Mobnday morning right when the 
  company opens its doors will ensure up-to-date info in the dashboard).
- Data-quality strip showing how many records were included and excluded.
- Data pull timestamp and a stale-data warning banner.
- Resolve the contact vs opportunity definition of lead volume.