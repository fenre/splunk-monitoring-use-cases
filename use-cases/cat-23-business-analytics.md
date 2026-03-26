## 23. Business Analytics & Executive Intelligence

### 23.1 Customer Experience & Digital Analytics

**Primary App/TA:** Splunk Add-on for Apache Web Server (Splunkbase 3186), Splunk Add-on for Nginx (Splunkbase 3258), Splunk DB Connect (Splunkbase 2686), Splunk Add-on for Google Analytics (HEC), Splunk Stream (Splunkbase 1809), Splunk ITSI (Splunkbase 1841).

**Data Sources:** Web access logs (`sourcetype="access_combined"`, `sourcetype="access_combined_wcookie"`), application event logs (HEC), CDN logs (Cloudflare, Akamai, Fastly), CRM records via DB Connect (`dbx:salesforce`, `dbx:hubspot`), POS transaction logs, mobile app analytics (HEC), customer feedback/NPS data (HEC/CSV lookup).

---

### UC-23.1.1 · Website Conversion Funnel Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Shows where customers drop off in the purchase or signup journey — landing page, product view, cart, checkout, confirmation. Helps marketing and product teams identify which step loses the most revenue so they can prioritise UX improvements with the biggest business impact.
- **App/TA:** Splunk Add-on for Apache Web Server (Splunkbase 3186)
- **Data Sources:** `index=web` `sourcetype="access_combined"` (clientip, uri, status, referer, useragent, bytes, _time)
- **SPL:**
```spl
index=web sourcetype="access_combined" status=200 earliest=-7d
| eval session=clientip."_".useragent
| eval stage=case(
    match(uri,"^/(home|landing|index)"), "1_Landing",
    match(uri,"^/products?/"), "2_Product_View",
    match(uri,"^/cart"), "3_Cart",
    match(uri,"^/checkout"), "4_Checkout",
    match(uri,"^/(confirm|thank|order-complete)"), "5_Confirmation",
    1=1, "0_Other")
| where stage!="0_Other"
| stats dc(session) as unique_sessions by stage
| sort stage
| streamstats current=t window=1 last(unique_sessions) as prev_sessions
| eval drop_off_pct=if(isnotnull(prev_sessions) AND stage!="1_Landing", round(100*(prev_sessions-unique_sessions)/prev_sessions,1), 0)
| table stage, unique_sessions, drop_off_pct
```
- **Implementation:** (1) Map your site's URL patterns to funnel stages in the `case()` statement; (2) for SPAs, use custom event logging via HEC with page/view identifiers; (3) schedule daily and weekly for trend comparison; (4) add revenue estimates per stage using average order value lookup; (5) segment by traffic source (organic, paid, direct) using referer field.
- **Visualization:** Funnel chart or stacked bar, Single value (overall conversion rate), Table (drop-off per stage), Line chart (daily conversion trend).

---

### UC-23.1.2 · Shopping Cart Abandonment Rate and Recovery
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Retail, E-Commerce
- **Splunk Pillar:** Observability
- **Value:** Quantifies revenue left on the table when customers add items to cart but leave without purchasing. Typical abandonment rates are 60-80% — reducing this by even a few points directly increases revenue. Alerts the business team when abandonment spikes, often indicating a payment gateway issue or pricing problem.
- **App/TA:** Splunk Add-on for Apache Web Server (Splunkbase 3186)
- **Data Sources:** `index=web` (web access logs), `index=app_events` (application event logs via HEC with cart and purchase events)
- **SPL:**
```spl
index=app_events sourcetype="app:ecommerce" event_type IN ("cart_add","purchase_complete") earliest=-7d
| eval session=coalesce(session_id, clientip."_".useragent)
| stats earliest(_time) as first_action, latest(event_type) as last_action,
        sum(eval(if(event_type="cart_add",1,0))) as cart_adds,
        sum(eval(if(event_type="purchase_complete",1,0))) as purchases,
        sum(eval(if(event_type="cart_add",item_value,0))) as cart_value by session
| eval abandoned=if(cart_adds>0 AND purchases=0, 1, 0)
| eval abandoned_value=if(abandoned=1, cart_value, 0)
| stats count as total_sessions, sum(abandoned) as abandoned_sessions,
        sum(abandoned_value) as total_abandoned_value,
        sum(eval(if(purchases>0,1,0))) as purchasing_sessions
| eval abandonment_rate=round(100*abandoned_sessions/total_sessions, 1)
| eval conversion_rate=round(100*purchasing_sessions/total_sessions, 1)
| table total_sessions, abandoned_sessions, abandonment_rate, purchasing_sessions, conversion_rate, total_abandoned_value
```
- **Implementation:** (1) Instrument your e-commerce platform to send cart_add and purchase_complete events via HEC with session_id, item_value, and item_sku; (2) alert when daily abandonment rate exceeds baseline by >10 percentage points — this often signals a payment gateway issue; (3) segment by device type (mobile vs desktop) and traffic source; (4) feed abandoned session data to marketing automation for recovery emails.
- **Visualization:** Single value (abandonment rate + trend), Line chart (daily abandonment trend), Bar chart (abandonment by device/source), Single value (abandoned revenue).

---

### UC-23.1.3 · Real-Time Page Load Performance Impact on Revenue
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Research shows every 100ms of page load delay reduces conversion by 1-2%. This use case correlates page response times with business outcomes, quantifying the revenue impact of site performance — giving engineering teams a business case for performance optimization and helping executives understand why infrastructure investment matters.
- **App/TA:** Splunk Add-on for Apache Web Server (Splunkbase 3186), Splunk RUM
- **Data Sources:** `index=web` `sourcetype="access_combined"` (response_time, uri, status), `index=app_events` (purchase events with session linkage)
- **SPL:**
```spl
index=web sourcetype="access_combined" status=200 earliest=-30d
| eval session=clientip."_".useragent
| eval response_ms=response_time*1000
| eval perf_bucket=case(
    response_ms<1000, "Fast (<1s)",
    response_ms<3000, "Moderate (1-3s)",
    response_ms<5000, "Slow (3-5s)",
    1=1, "Very Slow (>5s)")
| join type=left session [
    search index=app_events event_type="purchase_complete" earliest=-30d
    | eval session=coalesce(session_id, clientip."_".useragent)
    | stats sum(order_value) as revenue, count as purchases by session
]
| fillnull value=0 revenue purchases
| stats dc(session) as sessions, sum(purchases) as total_purchases,
        sum(revenue) as total_revenue, avg(response_ms) as avg_response_ms by perf_bucket
| eval conversion_rate=round(100*total_purchases/sessions, 2)
| eval revenue_per_session=round(total_revenue/sessions, 2)
| sort perf_bucket
| table perf_bucket, sessions, avg_response_ms, total_purchases, conversion_rate, total_revenue, revenue_per_session
```
- **Implementation:** (1) Ensure web server logs include response time (Apache: `%D`, Nginx: `$request_time`); (2) link web sessions to purchase events via session ID; (3) run monthly to build the business case for performance investment; (4) alert when average response time degrades past the "Moderate" threshold; (5) calculate the revenue uplift from moving sessions from "Slow" to "Fast" buckets.
- **Visualization:** Bar chart (conversion rate by speed bucket), Table (revenue per session by performance), Line chart (daily avg response time vs daily revenue), Single value (estimated revenue loss from slow pages).

---

### UC-23.1.4 · Customer Satisfaction Score (CSAT/NPS) Trend Dashboard
- **Criticality:** 🟢 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Centralises customer satisfaction metrics — Net Promoter Score, CSAT, CES — alongside operational data, enabling teams to correlate satisfaction dips with specific incidents, releases, or service changes. Executives see customer health at a glance rather than waiting for quarterly survey reports.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC
- **Data Sources:** `index=business` `sourcetype="nps_survey"` (score, verbatim, channel, product, date), CRM data via DB Connect
- **SPL:**
```spl
index=business sourcetype="nps_survey" earliest=-90d
| eval category=case(score>=9,"Promoter", score>=7,"Passive", 1=1,"Detractor")
| bin _time span=1w
| stats count as responses,
        sum(eval(if(category="Promoter",1,0))) as promoters,
        sum(eval(if(category="Detractor",1,0))) as detractors,
        avg(score) as avg_score by _time
| eval nps=round(100*(promoters-detractors)/responses, 0)
| table _time, responses, promoters, detractors, nps, avg_score
| sort _time
```
- **Implementation:** (1) Ingest survey responses via HEC or DB Connect from your survey platform (Qualtrics, Medallia, SurveyMonkey); (2) include product/service and channel fields for segmentation; (3) schedule weekly NPS calculation; (4) alert when NPS drops below threshold or week-over-week decline exceeds 10 points; (5) add text analytics on verbatim comments using `rex` for common complaint themes.
- **Visualization:** Line chart (NPS trend), Single value (current NPS), Pie chart (Promoter/Passive/Detractor split), Word cloud or bar chart (top complaint themes from verbatims).

---

### UC-23.1.5 · Customer Journey Cross-Channel Attribution
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Traces a customer's complete journey across web, mobile app, email, call centre, and in-store touchpoints — showing which channels drive engagement and conversion. Replaces siloed channel reporting with a unified view, helping marketing allocate budget to the channels that actually move customers to purchase.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), Splunk Add-on for Apache Web Server (Splunkbase 3186), HEC
- **Data Sources:** `index=web` (web visits), `index=app_events` (mobile app events), `index=business` (CRM interactions, call centre logs, email engagement, POS transactions)
- **SPL:**
```spl
index=web sourcetype="access_combined" earliest=-30d
| eval channel="Web", customer_id=coalesce(cookie_customer_id, clientip)
| eval touchpoint=uri
| append [search index=app_events sourcetype="app:mobile" earliest=-30d | eval channel="Mobile_App", customer_id=user_id, touchpoint=screen_name]
| append [search index=business sourcetype="email_engagement" earliest=-30d | eval channel="Email", touchpoint=campaign_name]
| append [search index=business sourcetype="call_centre" earliest=-30d | eval channel="Phone", touchpoint=call_reason]
| append [search index=business sourcetype="pos_transaction" earliest=-30d | eval channel="In_Store", touchpoint="Purchase"]
| where isnotnull(customer_id)
| sort customer_id _time
| streamstats values(channel) as journey_channels dc(channel) as channel_count by customer_id
| stats dc(customer_id) as unique_customers, count as total_touchpoints,
        dc(eval(if(channel="In_Store" OR match(touchpoint,"(?i)purchase|confirm"),customer_id,null()))) as converting_customers by channel
| eval conversion_contribution=round(100*converting_customers/unique_customers, 1)
| sort - conversion_contribution
| table channel, unique_customers, total_touchpoints, converting_customers, conversion_contribution
```
- **Implementation:** (1) Unify customer identity across channels using a customer ID or email — use identity resolution lookup if needed; (2) ingest email engagement via HEC from your ESP; (3) import call centre logs from ACD/IVR systems; (4) import POS transactions from retail systems; (5) build multi-touch attribution models (first-touch, last-touch, linear, time-decay) as additional saved searches.
- **Visualization:** Sankey diagram (channel flow), Bar chart (conversion contribution by channel), Table (customer journey paths), Single value (avg touchpoints before conversion).

---

### UC-23.1.6 · Mobile App Crash Rate and User Impact
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Every app crash is a customer experience failure that may lead to churn. This use case tracks crash rates by app version, device, and OS — correlating crashes with user retention and app store ratings. Product managers see which crashes affect the most users and can prioritise fixes based on business impact rather than technical severity alone.
- **App/TA:** HEC (custom app telemetry)
- **Data Sources:** `index=app_events` `sourcetype="app:crash"` (app_version, os_version, device_model, user_id, crash_type, stack_trace)
- **SPL:**
```spl
index=app_events sourcetype IN ("app:crash","app:session") earliest=-7d
| eval is_crash=if(sourcetype="app:crash", 1, 0)
| eval is_session=if(sourcetype="app:session", 1, 0)
| stats sum(is_crash) as crashes, sum(is_session) as sessions, dc(user_id) as affected_users by app_version
| eval crash_rate=round(100*crashes/sessions, 2)
| eval users_pct=round(100*affected_users/sessions, 2)
| sort - crash_rate
| table app_version, sessions, crashes, crash_rate, affected_users, users_pct
```
- **Implementation:** (1) Instrument your mobile app to send crash reports and session start events via HEC; (2) include app version, OS version, device model, and user ID; (3) alert when crash rate for any version exceeds 2%; (4) track crash rate trends after new releases; (5) correlate crash-affected users with churn data to quantify business impact.
- **Visualization:** Line chart (crash rate by version over time), Bar chart (crashes by device/OS), Single value (current crash-free rate %), Table (top crash types with user impact).

---

### 23.2 Revenue & Sales Operations

**Primary App/TA:** Splunk DB Connect (Splunkbase 2686), HEC (CRM/ERP integration).

**Data Sources:** CRM records via DB Connect (Salesforce opportunities, HubSpot deals), ERP order data (`dbx:sap`, `dbx:oracle`), billing system events, subscription management platform data, POS transaction logs.

---

### UC-23.2.1 · Sales Pipeline Velocity and Forecast Accuracy
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Measures how fast deals move through the pipeline and how accurately the team forecasts revenue. Executives see whether the pipeline is healthy enough to hit quarterly targets, which stages are bottlenecks, and whether forecasts consistently over- or under-predict — enabling data-driven sales leadership rather than gut-feel forecasting.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:crm_opportunities"` (opportunity_id, stage, amount, close_date, created_date, owner, probability, forecast_category)
- **SPL:**
```spl
index=business sourcetype="dbx:crm_opportunities" earliest=-90d
| eval days_in_pipeline=round((now()-strptime(created_date,"%Y-%m-%d"))/86400, 0)
| eval is_won=if(stage="Closed Won", 1, 0)
| eval is_lost=if(stage="Closed Lost", 1, 0)
| eval weighted_value=amount*probability/100
| stats sum(amount) as total_pipeline, sum(weighted_value) as weighted_pipeline,
        sum(eval(if(is_won=1,amount,0))) as won_revenue,
        sum(eval(if(is_lost=1,amount,0))) as lost_revenue,
        avg(days_in_pipeline) as avg_days_in_pipeline,
        dc(opportunity_id) as total_deals,
        sum(is_won) as won_deals, sum(is_lost) as lost_deals by forecast_category
| eval win_rate=round(100*won_deals/(won_deals+lost_deals), 1)
| eval pipeline_coverage=round(total_pipeline/won_revenue, 1)
| table forecast_category, total_deals, total_pipeline, weighted_pipeline, won_revenue, win_rate, avg_days_in_pipeline, pipeline_coverage
| sort forecast_category
```
- **Implementation:** (1) Use DB Connect to query CRM opportunities table on a schedule (hourly or daily); (2) map CRM stage names to your pipeline stages; (3) build quarter-over-quarter comparison for forecast accuracy; (4) alert when pipeline coverage drops below 3x target; (5) segment by sales team, region, and product line for management reviews.
- **Visualization:** Funnel (pipeline by stage), Single value (weighted pipeline, win rate, avg deal cycle), Bar chart (pipeline by forecast category), Line chart (pipeline trend over time).

---

### UC-23.2.2 · Revenue Recognition and Booking Trend
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Tracks revenue bookings in near-real-time against targets — daily, weekly, and monthly — giving finance and sales leadership an up-to-the-day view of where the business stands relative to plan. Replaces end-of-month surprises with continuous visibility, enabling mid-course corrections.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:erp_orders"` (order_id, order_date, revenue, product_line, region, customer_id, order_status)
- **SPL:**
```spl
index=business sourcetype="dbx:erp_orders" order_status="booked" earliest=-30d@d
| bin _time span=1d
| stats sum(revenue) as daily_revenue, dc(order_id) as orders, dc(customer_id) as unique_customers by _time
| sort _time
| streamstats sum(daily_revenue) as mtd_revenue, sum(orders) as mtd_orders
| lookup monthly_targets.csv month AS month OUTPUT target_revenue
| eval month=strftime(_time,"%Y-%m")
| lookup monthly_targets.csv month OUTPUT target_revenue
| eval pct_of_target=if(isnotnull(target_revenue), round(100*mtd_revenue/target_revenue,1), null())
| eval days_elapsed=tonumber(strftime(_time,"%d"))
| eval days_in_month=tonumber(strftime(relative_time(now(),"+1mon@mon-1d"),"%d"))
| eval run_rate=round(mtd_revenue/days_elapsed*days_in_month, 0)
| table _time, daily_revenue, mtd_revenue, pct_of_target, run_rate, mtd_orders, unique_customers
```
- **Implementation:** (1) Connect to ERP/billing system via DB Connect; (2) create `monthly_targets.csv` with month and target_revenue columns; (3) schedule every 4 hours for near-real-time visibility; (4) alert when run rate projects a miss of >10% against target; (5) segment by product line, region, and customer segment for management drill-down.
- **Visualization:** Line chart (daily revenue + cumulative MTD), Single value (MTD revenue, % of target, run rate), Bar chart (daily revenue vs same day last month), Gauge (MTD progress to target).

---

### UC-23.2.3 · Customer Churn Prediction and Early Warning
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Business
- **Industry:** SaaS, Subscription, Telecom
- **Splunk Pillar:** Observability
- **Value:** Identifies customers showing churn risk signals — declining usage, reduced logins, support ticket spikes, late payments — before they cancel. Customer success teams get an actionable watchlist so they can intervene while there's still time to save the account. Retaining an existing customer costs 5-25x less than acquiring a new one.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC (product usage telemetry)
- **Data Sources:** `index=app_events` (product usage/login events), `index=business` (subscription data, support tickets, payment history)
- **SPL:**
```spl
index=app_events sourcetype="app:login" earliest=-90d
| stats count as logins_90d, latest(_time) as last_login by customer_id
| eval days_since_login=round((now()-last_login)/86400, 0)
| join type=left customer_id [
    search index=app_events sourcetype="app:feature_use" earliest=-90d
    | stats count as feature_uses, dc(feature_name) as features_used by customer_id
]
| join type=left customer_id [
    search index=business sourcetype="support_ticket" earliest=-90d
    | stats count as tickets_90d, avg(eval(if(priority IN ("high","critical"),1,0))) as pct_high_priority by customer_id
]
| join type=left customer_id [
    search index=business sourcetype="dbx:billing" earliest=-90d
    | stats sum(eval(if(payment_status="late",1,0))) as late_payments by customer_id
]
| fillnull value=0 feature_uses features_used tickets_90d late_payments pct_high_priority
| eval churn_score=0
| eval churn_score=churn_score + if(days_since_login > 30, 25, 0)
| eval churn_score=churn_score + if(logins_90d < 10, 20, 0)
| eval churn_score=churn_score + if(features_used < 3, 15, 0)
| eval churn_score=churn_score + if(tickets_90d > 5, 20, 0)
| eval churn_score=churn_score + if(late_payments > 0, 20, 0)
| eval risk_level=case(churn_score >= 60, "HIGH", churn_score >= 30, "MEDIUM", 1=1, "LOW")
| where churn_score >= 30
| sort - churn_score
| table customer_id, risk_level, churn_score, days_since_login, logins_90d, features_used, tickets_90d, late_payments
```
- **Implementation:** (1) Instrument product usage logging via HEC (logins, feature usage, session duration); (2) import billing and subscription data via DB Connect; (3) import support ticket data from ITSM; (4) tune churn score weights based on historical churn analysis; (5) alert customer success managers daily on new high-risk accounts; (6) track intervention outcomes to refine the scoring model.
- **Visualization:** Table (at-risk customers sorted by churn score), Gauge (portfolio health — % low risk), Bar chart (churn risk distribution), Line chart (weekly churn score trend).

---

### UC-23.2.4 · Subscription Renewal and Expansion Pipeline
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** SaaS, Subscription
- **Splunk Pillar:** Observability
- **Value:** Shows the upcoming renewal pipeline — which subscriptions are due for renewal, their current health, and expansion potential based on usage. Account managers see a prioritised renewal list with risk indicators, helping them focus on the accounts most likely to churn or most ripe for upsell.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:subscriptions"` (customer_id, subscription_id, renewal_date, arr, product_tier, usage_pct)
- **SPL:**
```spl
index=business sourcetype="dbx:subscriptions" earliest=-1d@d latest=now()
| eval renewal_epoch=strptime(renewal_date, "%Y-%m-%d")
| eval days_to_renewal=round((renewal_epoch-now())/86400, 0)
| where days_to_renewal <= 90 AND days_to_renewal >= 0
| eval renewal_urgency=case(days_to_renewal <= 30, "URGENT", days_to_renewal <= 60, "APPROACHING", 1=1, "UPCOMING")
| eval expansion_signal=case(usage_pct >= 80, "EXPAND — high usage", usage_pct >= 50, "HEALTHY", 1=1, "AT RISK — low usage")
| stats sum(arr) as total_arr_at_risk, dc(subscription_id) as subscriptions by renewal_urgency, expansion_signal
| sort renewal_urgency
| table renewal_urgency, expansion_signal, subscriptions, total_arr_at_risk
```
- **Implementation:** (1) Import subscription records via DB Connect including renewal dates, ARR, and product tier; (2) join with product usage data to calculate usage_pct against entitlement; (3) schedule daily and feed to CRM/account management tools; (4) alert when total ARR at risk in the 30-day window exceeds threshold; (5) create a detailed drill-down showing individual accounts with health scores.
- **Visualization:** Table (renewals by urgency and signal), Single value (total ARR renewing in 30/60/90 days), Stacked bar (renewal pipeline by health), Timeline (renewal schedule).

---

### UC-23.2.5 · Pricing and Discount Effectiveness Analysis
- **Criticality:** 🟢 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Analyses whether discounts actually increase win rates or just erode margin. Shows average selling price vs list price by product, region, and sales rep — identifying where discounting is excessive and where it's effective. Helps sales leadership set discount guardrails backed by data.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:crm_opportunities"` (opportunity_id, amount, list_price, discount_pct, stage, product, region, owner)
- **SPL:**
```spl
index=business sourcetype="dbx:crm_opportunities" stage IN ("Closed Won","Closed Lost") earliest=-180d
| eval discount_pct=if(isnotnull(discount_pct), discount_pct, round(100*(list_price-amount)/list_price,1))
| eval discount_band=case(
    discount_pct=0, "No Discount",
    discount_pct<=10, "1-10%",
    discount_pct<=20, "11-20%",
    discount_pct<=30, "21-30%",
    1=1, ">30%")
| eval is_won=if(stage="Closed Won", 1, 0)
| stats count as deals, sum(is_won) as wins, avg(amount) as avg_deal_size, avg(discount_pct) as avg_discount by discount_band
| eval win_rate=round(100*wins/deals, 1)
| eval effective=if(win_rate > 50 AND avg_discount < 15, "Effective", if(win_rate < 30, "Ineffective — not winning", "Margin erosion"))
| sort discount_band
| table discount_band, deals, wins, win_rate, avg_deal_size, avg_discount, effective
```
- **Implementation:** (1) Import opportunity data including list price and actual selling price; (2) calculate discount percentage at deal level; (3) run quarterly for pricing reviews; (4) alert when any rep's average discount exceeds the policy threshold; (5) segment by product, region, and deal size for nuanced analysis.
- **Visualization:** Bar chart (win rate by discount band), Table (discount effectiveness), Scatter plot (discount % vs deal size), Single value (overall average discount).

---

### 23.3 Marketing Performance & Attribution

**Primary App/TA:** Splunk Add-on for Apache Web Server (Splunkbase 3186), Splunk DB Connect (Splunkbase 2686), HEC (marketing platform data).

**Data Sources:** Web access logs (UTM parameters), email marketing platform events (HEC), CRM lead/opportunity records (DB Connect), ad platform spend data (CSV/HEC), marketing automation logs.

---

### UC-23.3.1 · Marketing Campaign ROI by Channel
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Calculates return on investment for each marketing channel — paid search, social, email, events, content — by connecting campaign spend to pipeline generated and revenue closed. CMOs see which channels deliver positive ROI and which are burning budget, enabling real-time budget reallocation rather than waiting for quarterly reports.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC
- **Data Sources:** `index=business` (CRM opportunities with campaign source, ad spend data), `index=web` (UTM-tagged traffic)
- **SPL:**
```spl
index=business sourcetype="dbx:crm_opportunities" earliest=-90d
| stats sum(amount) as pipeline_generated, sum(eval(if(stage="Closed Won",amount,0))) as revenue_closed, dc(opportunity_id) as deals by campaign_source
| join type=left campaign_source [
    | inputlookup marketing_spend.csv
    | stats sum(spend) as total_spend by campaign_source
]
| fillnull value=0 total_spend
| eval roi=if(total_spend>0, round((revenue_closed-total_spend)/total_spend*100, 1), null())
| eval cost_per_deal=if(deals>0, round(total_spend/deals, 0), null())
| eval pipeline_to_spend=if(total_spend>0, round(pipeline_generated/total_spend, 1), null())
| sort - roi
| table campaign_source, total_spend, deals, pipeline_generated, revenue_closed, roi, cost_per_deal, pipeline_to_spend
```
- **Implementation:** (1) Tag CRM opportunities with campaign source using UTM parameters or CRM campaign membership; (2) maintain `marketing_spend.csv` with monthly spend by channel — update from finance/marketing ops; (3) schedule monthly for marketing reviews; (4) add time-to-revenue calculation by comparing opportunity creation date to close date; (5) segment by customer segment (enterprise, mid-market, SMB).
- **Visualization:** Bar chart (ROI by channel), Table (full metrics per channel), Bubble chart (spend vs revenue, bubble size = deals), Single value (blended ROI, total marketing-sourced revenue).

---

### UC-23.3.2 · Lead-to-Revenue Funnel Conversion Rates
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Tracks conversion rates at every stage of the marketing-sales funnel — visitor to lead, lead to MQL, MQL to SQL, SQL to opportunity, opportunity to closed-won. Identifies where the biggest leaks are and whether marketing is delivering quality leads that sales can close — the perennial question in every marketing-sales alignment meeting.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:crm_leads"` and `sourcetype="dbx:crm_opportunities"`
- **SPL:**
```spl
index=business sourcetype="dbx:crm_leads" earliest=-90d
| eval status_norm=lower(status)
| stats dc(lead_id) as total_leads,
        dc(eval(if(match(status_norm,"qualified|mql|marketing.qualified"),lead_id,null()))) as mqls,
        dc(eval(if(match(status_norm,"sql|sales.qualified|accepted"),lead_id,null()))) as sqls,
        dc(eval(if(isnotnull(converted_opportunity_id),lead_id,null()))) as opportunities,
        dc(eval(if(match(status_norm,"closed.won|won"),lead_id,null()))) as closed_won
| eval lead_to_mql=round(100*mqls/total_leads, 1)
| eval mql_to_sql=round(100*sqls/mqls, 1)
| eval sql_to_opp=round(100*opportunities/sqls, 1)
| eval opp_to_won=round(100*closed_won/opportunities, 1)
| eval overall=round(100*closed_won/total_leads, 2)
| table total_leads, mqls, lead_to_mql, sqls, mql_to_sql, opportunities, sql_to_opp, closed_won, opp_to_won, overall
```
- **Implementation:** (1) Import lead and opportunity records via DB Connect; (2) map your CRM status values to the standard funnel stages; (3) schedule weekly; (4) alert when any stage conversion rate drops below historical baseline; (5) segment by lead source, geography, and product interest for actionable insights.
- **Visualization:** Funnel chart, Single values (conversion rate per stage), Line chart (weekly conversion trends), Bar chart (conversion by lead source).

---

### UC-23.3.3 · Email Campaign Performance and Engagement
- **Criticality:** 🟢 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Consolidates email marketing metrics — open rates, click rates, unsubscribes, bounces — across all campaigns into a single dashboard. Marketing teams see which subject lines and content drive engagement and which cause unsubscribes, enabling continuous optimisation of email as a revenue channel.
- **App/TA:** HEC (email platform webhooks)
- **Data Sources:** `index=business` `sourcetype="email_engagement"` (campaign_id, event_type, recipient, timestamp)
- **SPL:**
```spl
index=business sourcetype="email_engagement" earliest=-30d
| stats dc(eval(if(event_type="sent",recipient,null()))) as sent,
        dc(eval(if(event_type="delivered",recipient,null()))) as delivered,
        dc(eval(if(event_type="opened",recipient,null()))) as opened,
        dc(eval(if(event_type="clicked",recipient,null()))) as clicked,
        dc(eval(if(event_type="unsubscribed",recipient,null()))) as unsubscribed,
        dc(eval(if(event_type="bounced",recipient,null()))) as bounced by campaign_id
| eval delivery_rate=round(100*delivered/sent, 1)
| eval open_rate=round(100*opened/delivered, 1)
| eval click_rate=round(100*clicked/delivered, 1)
| eval unsub_rate=round(100*unsubscribed/delivered, 2)
| eval bounce_rate=round(100*bounced/sent, 2)
| sort - click_rate
| table campaign_id, sent, delivered, delivery_rate, open_rate, click_rate, unsub_rate, bounce_rate
```
- **Implementation:** (1) Configure your email platform (Mailchimp, Marketo, HubSpot, Salesforce Marketing Cloud) to send engagement events via webhooks to Splunk HEC; (2) include campaign ID, event type, and recipient; (3) schedule daily summaries; (4) alert on bounce rates >5% or unsubscribe rates >1%; (5) compare A/B test variants using campaign_id segmentation.
- **Visualization:** Table (campaign metrics), Bar chart (open/click rates by campaign), Line chart (engagement trends over time), Single value (avg open rate, avg click rate).

---

### UC-23.3.4 · Website Traffic Source and SEO Performance
- **Criticality:** 🟢 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Breaks down website traffic by source — organic search, paid search, social, direct, referral — showing which channels drive the most visitors and which produce the highest quality engagement (measured by pages per session and time on site). Marketing teams see SEO effectiveness alongside paid performance.
- **App/TA:** Splunk Add-on for Apache Web Server (Splunkbase 3186)
- **Data Sources:** `index=web` `sourcetype="access_combined"` (clientip, uri, referer, status, bytes)
- **SPL:**
```spl
index=web sourcetype="access_combined" status=200 NOT uri IN ("/favicon.ico","robots.txt","/health") earliest=-7d
| eval session=clientip."_".useragent
| eval source=case(
    match(referer,"(?i)google\.(com|co\.\w+)/search"), "Organic — Google",
    match(referer,"(?i)bing\.com/search"), "Organic — Bing",
    match(referer,"(?i)(facebook|linkedin|twitter|instagram)\.com"), "Social",
    match(uri,"[?&]utm_medium=cpc"), "Paid Search",
    match(uri,"[?&]utm_medium=email"), "Email",
    isnull(referer) OR referer="-", "Direct",
    1=1, "Referral")
| stats dc(session) as sessions, dc(clientip) as visitors, count as pageviews by source
| eval pages_per_session=round(pageviews/sessions, 1)
| sort - sessions
| table source, visitors, sessions, pageviews, pages_per_session
```
- **Implementation:** (1) Ensure web server logs capture referer and full URI including query strings; (2) customise source classification for your UTM conventions; (3) schedule daily and weekly comparisons; (4) alert on significant organic traffic drops (possible SEO issue or algorithm change); (5) add landing page analysis by cross-referencing source with first URI per session.
- **Visualization:** Pie chart (sessions by source), Bar chart (visitors by source), Table (quality metrics per source), Line chart (daily traffic by source).

---

### 23.4 HR & People Analytics

**Primary App/TA:** Splunk DB Connect (Splunkbase 2686), HEC (HRIS integration).

**Data Sources:** HRIS records via DB Connect (Workday, SAP SuccessFactors, BambooHR — employee records, position data, compensation), time & attendance system logs, learning management system (LMS) data, applicant tracking system (ATS) data, employee engagement survey data.

---

### UC-23.4.1 · Employee Attrition Analysis and Flight Risk
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Analyses attrition patterns by department, tenure, role, and demographics — identifying where the organisation is losing people fastest and what the common factors are. HR leaders see flight risk indicators (recent role change, tenure milestones, team attrition clusters) so they can proactively engage at-risk employees before resignation.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:hris_employees"` (employee_id, department, hire_date, termination_date, role, manager, location, tenure_months)
- **SPL:**
```spl
index=business sourcetype="dbx:hris_employees" earliest=-365d
| eval is_terminated=if(isnotnull(termination_date), 1, 0)
| eval tenure_months=round((coalesce(strptime(termination_date,"%Y-%m-%d"),now())-strptime(hire_date,"%Y-%m-%d"))/(86400*30), 0)
| eval tenure_band=case(
    tenure_months < 6, "0-6 months",
    tenure_months < 12, "6-12 months",
    tenure_months < 24, "1-2 years",
    tenure_months < 48, "2-4 years",
    1=1, "4+ years")
| stats count as headcount, sum(is_terminated) as departures by department, tenure_band
| eval attrition_rate=round(100*departures/headcount, 1)
| where departures > 0
| sort - attrition_rate
| table department, tenure_band, headcount, departures, attrition_rate
```
- **Implementation:** (1) Import employee records via DB Connect from HRIS; (2) anonymise personal data — use employee IDs, not names; (3) schedule monthly for HR leadership reviews; (4) alert when any department's annual attrition exceeds 20%; (5) add manager-level rollup for people manager coaching; (6) compare voluntary vs involuntary terminations.
- **Visualization:** Heatmap (department × tenure band), Bar chart (attrition by department), Line chart (monthly attrition trend), Single value (organisation-wide attrition rate).

---

### UC-23.4.2 · Time-to-Hire and Recruiting Pipeline Health
- **Criticality:** 🟢 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Tracks how long it takes to fill open positions — from requisition to offer acceptance — by department, role level, and recruiter. Helps talent acquisition leaders identify bottlenecks (slow hiring managers, long interview stages) and predict capacity risks when critical roles remain unfilled too long.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:ats_requisitions"` (req_id, title, department, opened_date, filled_date, stage, recruiter)
- **SPL:**
```spl
index=business sourcetype="dbx:ats_requisitions" earliest=-180d
| eval opened_epoch=strptime(opened_date, "%Y-%m-%d")
| eval filled_epoch=if(isnotnull(filled_date), strptime(filled_date, "%Y-%m-%d"), null())
| eval days_to_fill=if(isnotnull(filled_epoch), round((filled_epoch-opened_epoch)/86400, 0), null())
| eval age_days=round((now()-opened_epoch)/86400, 0)
| eval status=case(isnotnull(filled_date),"Filled", age_days>90,"Stale (>90d)", age_days>60,"Aging (60-90d)", 1=1,"Active")
| stats avg(days_to_fill) as avg_days_to_fill, median(days_to_fill) as median_days,
        dc(eval(if(status="Filled",req_id,null()))) as filled,
        dc(eval(if(status="Stale (>90d)",req_id,null()))) as stale,
        dc(req_id) as total_reqs by department
| eval fill_rate=round(100*filled/total_reqs, 1)
| sort - stale
| table department, total_reqs, filled, fill_rate, stale, avg_days_to_fill, median_days
```
- **Implementation:** (1) Import requisition data from ATS (Greenhouse, Lever, Workday Recruiting) via DB Connect; (2) include stage timestamps for stage-level analysis; (3) schedule weekly for talent acquisition reviews; (4) alert when any critical role is open >60 days; (5) compare recruiter performance (time-to-fill, offer acceptance rate).
- **Visualization:** Bar chart (avg time-to-fill by department), Table (stale requisitions), Line chart (monthly hiring velocity), Single value (overall median time-to-fill).

---

### UC-23.4.3 · Diversity and Inclusion Metrics Dashboard
- **Criticality:** 🟢 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Business, Compliance
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Provides a real-time view of workforce composition by gender, ethnicity, age band, and role level — tracking representation trends over time and measuring progress against diversity goals. HR and executive leadership can see whether hiring and promotion practices are moving the needle on inclusion commitments.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:hris_employees"` (employee_id, gender, ethnicity, age_band, role_level, department, hire_date, promotion_date)
- **SPL:**
```spl
index=business sourcetype="dbx:hris_employees" status="active"
| stats dc(employee_id) as headcount by gender, role_level
| eventstats sum(headcount) as level_total by role_level
| eval representation_pct=round(100*headcount/level_total, 1)
| sort role_level, gender
| table role_level, gender, headcount, representation_pct
```
- **Implementation:** (1) Import anonymised demographic data from HRIS; (2) handle self-reported data sensitively — include "Prefer not to say"; (3) schedule monthly; (4) track representation changes over time with timechart; (5) compare new hire diversity vs existing workforce diversity; (6) measure promotion rates by demographic group to identify glass ceiling patterns.
- **Visualization:** Stacked bar (representation by role level), Line chart (diversity trend over quarters), Table (representation vs targets), Single value (% representation by group).

---

### UC-23.4.4 · Training Completion and Compliance Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Tracks mandatory and optional training completion rates across the organisation — compliance training, security awareness, leadership development, technical certifications. HR and compliance teams see who hasn't completed required training before audit deadlines and can target reminders to specific groups.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC (LMS integration)
- **Data Sources:** `index=business` `sourcetype="lms_completion"` (employee_id, course_id, course_name, completion_date, due_date, status, mandatory)
- **SPL:**
```spl
index=business sourcetype="lms_completion" mandatory="yes"
| eval due_epoch=strptime(due_date, "%Y-%m-%d")
| eval days_until_due=round((due_epoch-now())/86400, 0)
| eval compliance_status=case(
    status="completed", "Completed",
    days_until_due < 0, "OVERDUE",
    days_until_due <= 14, "Due Soon",
    1=1, "Not Started")
| stats dc(employee_id) as employees by course_name, compliance_status
| eventstats sum(employees) as total_assigned by course_name
| eval pct=round(100*employees/total_assigned, 1)
| sort course_name, compliance_status
| table course_name, compliance_status, employees, pct, total_assigned
```
- **Implementation:** (1) Import LMS completion data via HEC webhooks or DB Connect; (2) mark courses as mandatory/optional; (3) alert managers when team members have overdue mandatory training; (4) schedule daily for compliance reporting; (5) produce audit-ready reports showing completion rates by department and deadline.
- **Visualization:** Stacked bar (completion status by course), Table (overdue employees), Single value (overall compliance rate %), Gauge (mandatory training completion).

---

### 23.5 Supply Chain & Operations

**Primary App/TA:** Splunk DB Connect (Splunkbase 2686), Splunk Add-on for ServiceNow (Splunkbase 1928), HEC (WMS/TMS/ERP integration).

**Data Sources:** ERP order/inventory data via DB Connect (SAP, Oracle, NetSuite), warehouse management system logs (HEC), transport management system events, supplier portal data, IoT sensor data from logistics (temperature, location, GPS).

---

### UC-23.5.1 · Order-to-Cash Cycle Time and Bottleneck Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Manufacturing, Retail, Distribution
- **Splunk Pillar:** Observability
- **Value:** Measures the complete order-to-cash cycle — order placement, picking, packing, shipping, delivery, invoicing, payment receipt — identifying which stages take longest and where delays cluster. Operations leaders see exactly where the fulfilment process breaks down and can target improvements to reduce working capital tied up in the cycle.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:erp_orders"` (order_id, customer, stage, stage_timestamp, value)
- **SPL:**
```spl
index=business sourcetype="dbx:erp_orders" earliest=-90d
| eval stage_time=strptime(stage_timestamp, "%Y-%m-%d %H:%M:%S")
| sort order_id, stage_time
| streamstats latest(stage_time) as prev_time latest(stage) as prev_stage by order_id
| eval stage_duration_hours=if(isnotnull(prev_time), round((stage_time-prev_time)/3600, 1), 0)
| stats avg(stage_duration_hours) as avg_hours, perc95(stage_duration_hours) as p95_hours, count as transitions by stage
| eval avg_days=round(avg_hours/24, 1)
| sort stage
| table stage, avg_hours, avg_days, p95_hours, transitions
```
- **Implementation:** (1) Import order lifecycle events from ERP via DB Connect; (2) ensure each stage transition is logged with timestamp; (3) define standard stages (Ordered → Confirmed → Picked → Packed → Shipped → Delivered → Invoiced → Paid); (4) schedule weekly for operations reviews; (5) alert when average cycle time exceeds target; (6) segment by product category, customer tier, and warehouse for targeted improvement.
- **Visualization:** Waterfall chart (time per stage), Bar chart (avg vs P95 by stage), Line chart (cycle time trend), Single value (overall avg order-to-cash days).

---

### UC-23.5.2 · Inventory Level Monitoring and Stockout Risk
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Retail, Manufacturing, Distribution
- **Splunk Pillar:** Observability
- **Value:** Monitors inventory levels against reorder points and forecasted demand — flagging products at risk of stockout before it happens. A stockout means lost sales and disappointed customers. Equally, excess inventory ties up cash and risks obsolescence. This gives supply chain managers a balanced, exception-based view of where to act.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:inventory"` (sku, warehouse, qty_on_hand, reorder_point, daily_demand_avg, lead_time_days)
- **SPL:**
```spl
index=business sourcetype="dbx:inventory" earliest=-1d@d latest=now()
| eval days_of_stock=if(daily_demand_avg>0, round(qty_on_hand/daily_demand_avg, 0), 999)
| eval status=case(
    qty_on_hand <= 0, "STOCKOUT",
    days_of_stock <= lead_time_days, "CRITICAL — below lead time",
    qty_on_hand <= reorder_point, "REORDER NOW",
    days_of_stock > 180, "OVERSTOCK",
    1=1, "OK")
| where status!="OK"
| eval revenue_at_risk=if(status IN ("STOCKOUT","CRITICAL — below lead time"), daily_demand_avg * unit_price * lead_time_days, 0)
| sort status, - revenue_at_risk
| table sku, product_name, warehouse, qty_on_hand, reorder_point, days_of_stock, lead_time_days, status, revenue_at_risk
```
- **Implementation:** (1) Import inventory snapshot via DB Connect daily from ERP/WMS; (2) calculate rolling average daily demand from sales history; (3) include supplier lead times in the lookup; (4) alert purchasing team immediately on STOCKOUT and CRITICAL items; (5) generate a weekly overstock report for markdown/clearance decisions; (6) integrate with demand forecasting model outputs for improved accuracy.
- **Visualization:** Table (exception list), Single value (items in stockout, total revenue at risk), Gauge (% of SKUs at healthy levels), Bar chart (stockout risk by category).

---

### UC-23.5.3 · Supplier On-Time Delivery Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Manufacturing, Retail, Distribution
- **Splunk Pillar:** Observability
- **Value:** Tracks whether suppliers deliver on time, in full (OTIF) — the single most important supplier performance metric. Procurement teams see which suppliers consistently miss delivery dates and can use the data in contract negotiations, sourcing decisions, and supplier development programmes.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:purchase_orders"` (po_number, supplier, promised_date, actual_delivery_date, qty_ordered, qty_received)
- **SPL:**
```spl
index=business sourcetype="dbx:purchase_orders" actual_delivery_date=* earliest=-180d
| eval promised=strptime(promised_date, "%Y-%m-%d")
| eval actual=strptime(actual_delivery_date, "%Y-%m-%d")
| eval days_late=round((actual-promised)/86400, 0)
| eval on_time=if(days_late <= 0, 1, 0)
| eval in_full=if(qty_received >= qty_ordered, 1, 0)
| eval otif=if(on_time=1 AND in_full=1, 1, 0)
| stats count as deliveries, sum(on_time) as on_time_count, sum(in_full) as in_full_count, sum(otif) as otif_count, avg(days_late) as avg_days_late by supplier
| eval otif_pct=round(100*otif_count/deliveries, 1)
| eval on_time_pct=round(100*on_time_count/deliveries, 1)
| eval in_full_pct=round(100*in_full_count/deliveries, 1)
| sort - deliveries
| table supplier, deliveries, on_time_pct, in_full_pct, otif_pct, avg_days_late
```
- **Implementation:** (1) Import purchase order data including promised and actual delivery dates via DB Connect; (2) define your OTIF tolerance (e.g., ±1 day for "on time"); (3) schedule monthly for supplier reviews; (4) alert procurement when any strategic supplier's OTIF drops below 90%; (5) share supplier scorecards via scheduled PDF reports.
- **Visualization:** Table (supplier scorecard), Bar chart (OTIF by supplier), Line chart (OTIF trend over months), Single value (overall OTIF rate).

---

### UC-23.5.4 · Delivery SLA Compliance and Last-Mile Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Business
- **Industry:** Retail, Logistics, E-Commerce
- **Splunk Pillar:** Observability
- **Value:** Measures whether customer orders are delivered within promised timeframes — next-day, 2-day, standard — by carrier and region. Logistics managers see which carriers and routes are failing SLAs, while customer experience teams understand the impact on satisfaction. A single percentage-point improvement in delivery SLA compliance can significantly reduce customer complaints.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC (carrier tracking data)
- **Data Sources:** `index=business` `sourcetype="dbx:shipments"` (shipment_id, carrier, promised_delivery, actual_delivery, origin, destination, service_level)
- **SPL:**
```spl
index=business sourcetype="dbx:shipments" actual_delivery=* earliest=-30d
| eval promised_epoch=strptime(promised_delivery, "%Y-%m-%d")
| eval actual_epoch=strptime(actual_delivery, "%Y-%m-%d")
| eval days_variance=round((actual_epoch-promised_epoch)/86400, 0)
| eval sla_met=if(days_variance <= 0, 1, 0)
| stats count as shipments, sum(sla_met) as on_time, avg(days_variance) as avg_variance by carrier, service_level
| eval sla_compliance=round(100*on_time/shipments, 1)
| sort carrier, service_level
| table carrier, service_level, shipments, on_time, sla_compliance, avg_variance
```
- **Implementation:** (1) Import shipment tracking data from TMS or carrier APIs via HEC; (2) map carrier service levels to your customer-facing delivery promises; (3) schedule daily for logistics team; (4) alert when any carrier/service_level combination drops below 95% compliance; (5) calculate financial impact of late deliveries (refunds, credits, lost customers).
- **Visualization:** Bar chart (SLA compliance by carrier), Table (carrier scorecard), Heatmap (carrier × region), Single value (overall SLA compliance %).

---

### 23.6 Financial Operations & Procurement

**Primary App/TA:** Splunk DB Connect (Splunkbase 2686), Splunk Enterprise Security (Splunkbase 263).

**Data Sources:** ERP financial data via DB Connect (GL transactions, AP/AR, expense reports), procurement system events, payment gateway logs, expense management platform data (Concur, Expensify via HEC).

---

### UC-23.6.1 · Accounts Receivable Aging and Cash Collection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Shows outstanding receivables by aging bucket — current, 30-day, 60-day, 90-day, 120+ day — with customer-level drill-down. CFOs and controllers see cash collection health at a glance, identify customers drifting into bad debt territory, and measure Days Sales Outstanding (DSO) against targets. Early visibility enables proactive collection before debts become uncollectable.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:ar_invoices"` (invoice_id, customer, amount, invoice_date, due_date, payment_date, status)
- **SPL:**
```spl
index=business sourcetype="dbx:ar_invoices" status="open" earliest=-1y
| eval due_epoch=strptime(due_date, "%Y-%m-%d")
| eval days_overdue=round((now()-due_epoch)/86400, 0)
| eval aging_bucket=case(
    days_overdue <= 0, "Current",
    days_overdue <= 30, "1-30 days",
    days_overdue <= 60, "31-60 days",
    days_overdue <= 90, "61-90 days",
    1=1, "90+ days")
| stats sum(amount) as total_outstanding, dc(invoice_id) as invoice_count, dc(customer) as customers by aging_bucket
| eventstats sum(total_outstanding) as grand_total
| eval pct_of_total=round(100*total_outstanding/grand_total, 1)
| sort aging_bucket
| table aging_bucket, invoice_count, customers, total_outstanding, pct_of_total
```
- **Implementation:** (1) Import open AR invoices via DB Connect from ERP; (2) schedule daily; (3) alert collections team when any customer exceeds 60 days overdue; (4) calculate DSO: (AR balance / revenue) × days in period; (5) trend DSO monthly for CFO reporting; (6) segment by customer segment and region for targeted collection strategies.
- **Visualization:** Stacked bar (AR by aging bucket), Table (top overdue customers), Single value (total overdue, DSO), Line chart (DSO trend).

---

### UC-23.6.2 · Expense Report Anomaly Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Security
- **Value:** Detects unusual expense patterns that may indicate policy violations or fraud — round-number claims just below approval thresholds, duplicate submissions, weekend expenses, excessive entertainment spend, or outliers compared to peers. Finance teams get an exception list rather than reviewing every expense, dramatically improving audit efficiency.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC
- **Data Sources:** `index=business` `sourcetype="expense_reports"` (report_id, employee_id, department, category, amount, expense_date, merchant, receipt_attached)
- **SPL:**
```spl
index=business sourcetype="expense_reports" earliest=-90d
| eval anomaly_flags=mvappend(
    if(amount=round(amount,0) AND amount>=100, "ROUND_NUMBER", null()),
    if(amount>=490 AND amount<500, "JUST_BELOW_THRESHOLD", null()),
    if(match(expense_date,".*(Sat|Sun).*") OR tonumber(strftime(strptime(expense_date,"%Y-%m-%d"),"%u"))>=6, "WEEKEND", null()),
    if(receipt_attached="no" AND amount>25, "NO_RECEIPT", null()))
| eventstats avg(amount) as dept_avg, stdev(amount) as dept_stdev by department, category
| eval statistical_outlier=if(amount > dept_avg + 2*dept_stdev, "STATISTICAL_OUTLIER", null())
| eval anomaly_flags=mvappend(anomaly_flags, statistical_outlier)
| where isnotnull(anomaly_flags)
| stats count as flagged_expenses, sum(amount) as total_flagged_amount, values(anomaly_flags) as reasons by employee_id, department
| sort - total_flagged_amount
| table employee_id, department, flagged_expenses, total_flagged_amount, reasons
```
- **Implementation:** (1) Import expense data from expense management system (Concur, Expensify, SAP) via DB Connect or HEC; (2) tune approval threshold amounts to match your policy (e.g., $500); (3) schedule weekly for finance review; (4) compare duplicate merchant/date/amount combinations across employees; (5) build a peer comparison model by role and department for more accurate outlier detection.
- **Visualization:** Table (flagged employees with reasons), Bar chart (anomaly types), Single value (% of expenses flagged), Scatter plot (amount vs department average).

---

### UC-23.6.3 · Budget vs Actual Variance Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Compares actual spending against budget at the cost centre and GL account level — highlighting where departments are over or under budget. Finance teams and department heads see variances in near-real-time rather than waiting for month-end close, enabling earlier corrective action on runaway costs.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:gl_transactions"` (cost_centre, gl_account, amount, period), `budget_plan.csv`
- **SPL:**
```spl
index=business sourcetype="dbx:gl_transactions" earliest=-1mon@mon latest=@mon
| stats sum(amount) as actual_spend by cost_centre, gl_account
| lookup budget_plan.csv cost_centre gl_account OUTPUT budget_amount
| eval variance=actual_spend - budget_amount
| eval variance_pct=if(budget_amount!=0, round(100*variance/budget_amount, 1), null())
| eval status=case(
    variance_pct > 10, "OVER BUDGET",
    variance_pct > 5, "WATCH",
    variance_pct < -20, "UNDERSPEND",
    1=1, "ON TRACK")
| where status!="ON TRACK"
| sort - variance
| table cost_centre, gl_account, budget_amount, actual_spend, variance, variance_pct, status
```
- **Implementation:** (1) Import GL transaction data via DB Connect from ERP; (2) maintain `budget_plan.csv` with approved budget by cost centre and GL account; (3) schedule monthly after period close; (4) add YTD cumulative view alongside monthly; (5) alert department heads when any cost centre exceeds budget by >10%; (6) enable drill-down to individual transactions for variance investigation.
- **Visualization:** Bar chart (variance by cost centre), Table (over-budget items), Gauge (department spend vs budget), Line chart (cumulative spend vs budget over months).

---

### UC-23.6.4 · Payment Processing Success Rate and Revenue Leakage
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Business
- **Industry:** E-Commerce, SaaS, Financial Services
- **Splunk Pillar:** Observability
- **Value:** Monitors payment gateway success, decline, and error rates in real time — every declined payment is potentially lost revenue. Business teams see which payment methods, card types, and regions have the highest failure rates, while engineering teams get immediate alerts on gateway outages. A 1% improvement in payment success rate directly increases revenue.
- **App/TA:** HEC (payment gateway logs)
- **Data Sources:** `index=business` `sourcetype="payment_gateway"` (transaction_id, amount, currency, payment_method, status, decline_reason, country)
- **SPL:**
```spl
index=business sourcetype="payment_gateway" earliest=-24h
| eval success=if(status="approved", 1, 0)
| eval declined=if(status="declined", 1, 0)
| eval errored=if(status="error", 1, 0)
| stats sum(success) as approved, sum(declined) as declined, sum(errored) as errors,
        sum(eval(if(success=1,amount,0))) as approved_revenue,
        sum(eval(if(declined=1,amount,0))) as declined_revenue,
        count as total by payment_method
| eval success_rate=round(100*approved/total, 2)
| eval revenue_lost=declined_revenue
| sort - revenue_lost
| table payment_method, total, approved, declined, errors, success_rate, approved_revenue, revenue_lost
```
- **Implementation:** (1) Forward payment gateway events to Splunk via HEC; (2) include transaction details, decline codes, and amounts; (3) alert immediately when success rate drops below 95% — likely a gateway issue; (4) analyse decline reasons to identify recoverable declines (e.g., retry logic, alternative payment methods); (5) track by country for regional payment method optimisation.
- **Visualization:** Single value (overall success rate, revenue lost today), Line chart (success rate over time), Bar chart (decline reasons), Table (performance by payment method).

---

### 23.7 Customer Support & Service Excellence

**Primary App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928), Splunk DB Connect (Splunkbase 2686), HEC (helpdesk/CRM integration).

**Data Sources:** ServiceNow incident/case records, Zendesk/Freshdesk ticket data via HEC, call centre ACD/IVR logs, customer satisfaction survey responses, chatbot interaction logs.

---

### UC-23.7.1 · Support Ticket Volume and Resolution SLA Dashboard
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Shows support ticket volume, backlog, and SLA compliance in real time — how many tickets are open, how fast they're being resolved, and whether the team is meeting response and resolution targets. Support leaders see whether they need to add staff, redistribute workload, or investigate a spike in a specific issue category.
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=itsm` `sourcetype="snow:incident"` (number, opened_at, closed_at, state, priority, assignment_group, category, short_description)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" earliest=-30d
| eval opened_epoch=strptime(opened_at, "%Y-%m-%d %H:%M:%S")
| eval closed_epoch=if(isnotnull(closed_at), strptime(closed_at, "%Y-%m-%d %H:%M:%S"), null())
| eval resolution_hours=if(isnotnull(closed_epoch), round((closed_epoch-opened_epoch)/3600, 1), null())
| eval sla_target_hours=case(priority="1",4, priority="2",8, priority="3",24, 1=1,72)
| eval sla_met=if(isnotnull(resolution_hours) AND resolution_hours <= sla_target_hours, 1, 0)
| eval is_open=if(isnull(closed_at) OR state IN ("New","In Progress","On Hold"), 1, 0)
| stats count as total_tickets,
        sum(is_open) as open_tickets,
        sum(sla_met) as within_sla,
        avg(resolution_hours) as avg_resolution_h,
        median(resolution_hours) as median_resolution_h by assignment_group
| eval sla_pct=round(100*within_sla/(total_tickets-open_tickets), 1)
| sort - open_tickets
| table assignment_group, total_tickets, open_tickets, avg_resolution_h, median_resolution_h, sla_pct
```
- **Implementation:** (1) Configure ServiceNow TA for incident ingestion; (2) map your SLA targets by priority; (3) schedule every 4 hours for team leads; (4) alert when any team's backlog exceeds capacity threshold; (5) add first-response time tracking alongside resolution time.
- **Visualization:** Single value (open backlog, SLA %), Bar chart (volume by team), Line chart (daily ticket trend), Table (team performance).

---

### UC-23.7.2 · First Contact Resolution Rate and Escalation Patterns
- **Criticality:** 🟢 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Measures how often customer issues are resolved on first contact without escalation or transfer — the gold standard of support efficiency. High FCR means happy customers and lower support costs. Tracking escalation patterns reveals training gaps (topics that always escalate), staffing issues (times when escalation spikes), and product problems (features that generate repeated escalations).
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928), HEC
- **Data Sources:** `index=itsm` `sourcetype="snow:incident"`, `index=business` `sourcetype="support_interaction"` (interaction_id, ticket_id, channel, agent, transferred, escalated)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" state="Closed" earliest=-30d
| eval reassignment_count=if(isnotnull(reassignment_count), reassignment_count, 0)
| eval fcr=if(reassignment_count=0, 1, 0)
| eval escalated=if(reassignment_count >= 2 OR match(lower(work_notes),"(?i)escalat"), 1, 0)
| stats count as resolved_tickets, sum(fcr) as first_contact, sum(escalated) as escalated_tickets by category
| eval fcr_rate=round(100*first_contact/resolved_tickets, 1)
| eval escalation_rate=round(100*escalated_tickets/resolved_tickets, 1)
| sort - escalation_rate
| table category, resolved_tickets, first_contact, fcr_rate, escalated_tickets, escalation_rate
```
- **Implementation:** (1) Track reassignment count and escalation events in your ticketing system; (2) define FCR criteria (resolved by original assignee, no reopens within 48h); (3) schedule weekly; (4) identify top escalation categories for targeted training; (5) compare FCR by channel (phone vs chat vs email) to understand channel effectiveness.
- **Visualization:** Bar chart (FCR rate by category), Table (top escalation categories), Single value (overall FCR rate), Line chart (FCR trend over time).

---

### UC-23.7.3 · Customer Effort Score and Support Channel Effectiveness
- **Criticality:** 🟢 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Measures how much effort customers expend to get their issues resolved — combining post-interaction survey scores with operational metrics like transfers, repeat contacts, and channel switches. Support leaders see which channels and issue types create the most friction, guiding investments in self-service, chatbots, and process simplification.
- **App/TA:** HEC, Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=business` `sourcetype="support_survey"` (ticket_id, ces_score, channel, issue_type), `index=itsm` (ticket lifecycle data)
- **SPL:**
```spl
index=business sourcetype="support_survey" earliest=-90d
| stats avg(ces_score) as avg_ces, count as surveys by channel, issue_type
| join type=left channel issue_type [
    search index=itsm sourcetype="snow:incident" state="Closed" earliest=-90d
    | stats avg(reassignment_count) as avg_transfers, avg(eval(round((strptime(closed_at,"%Y-%m-%d %H:%M:%S")-strptime(opened_at,"%Y-%m-%d %H:%M:%S"))/3600,1))) as avg_resolution_h by channel, category
    | rename category as issue_type
]
| eval effort_index=round(avg_ces + avg_transfers*0.5 + if(avg_resolution_h>24,1,0), 1)
| sort - effort_index
| table channel, issue_type, surveys, avg_ces, avg_transfers, avg_resolution_h, effort_index
```
- **Implementation:** (1) Ingest post-interaction CES surveys via HEC; (2) use a 1-7 scale (lower = less effort = better); (3) correlate with operational data from ticketing system; (4) schedule monthly; (5) identify high-effort combinations (e.g., "Billing + Phone = high effort") for process redesign; (6) track CES trend after implementing improvements.
- **Visualization:** Heatmap (channel × issue type), Bar chart (CES by channel), Table (highest effort combinations), Line chart (CES trend).

---

### 23.8 Executive Dashboards & Business KPIs

**Primary App/TA:** Splunk DB Connect (Splunkbase 2686), Splunk ITSI (Splunkbase 1841), HEC.

**Data Sources:** Aggregated data from all business indexes, KV store with KPI definitions and targets, ERP/CRM/HRIS summary data via DB Connect.

---

### UC-23.8.1 · CEO/CFO Business Health Scorecard
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** A single-page dashboard showing the 8-12 metrics that matter most to the executive team — revenue vs target, customer acquisition cost, churn rate, NPS, employee headcount, operational margin, cash position, and key risk indicators. Replaces the monthly board pack with a live, always-current view that executives can check any time.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), Splunk ITSI (Splunkbase 1841)
- **Data Sources:** `index=business` (aggregated from revenue, customer, HR, and operational data), `executive_kpi_targets.csv`
- **SPL:**
```spl
| inputlookup executive_kpi_targets.csv
| join type=left kpi_name [
    | makeresults count=1
    | eval kpi_data=mvappend("revenue_mtd:".mvindex(split("placeholder",":"),0), "nps_current:0", "churn_rate:0", "headcount:0")
    | mvexpand kpi_data
    | rex field=kpi_data "^(?<kpi_name>[^:]+):(?<current_value>\d+)"
]
| append [
    search index=business sourcetype="dbx:erp_orders" order_status="booked" earliest=-1mon@mon latest=now()
    | stats sum(revenue) as current_value
    | eval kpi_name="revenue_mtd"
]
| append [
    search index=business sourcetype="nps_survey" earliest=-30d
    | eval category=case(score>=9,"Promoter", score>=7,"Passive", 1=1,"Detractor")
    | stats sum(eval(if(category="Promoter",1,0))) as p, sum(eval(if(category="Detractor",1,0))) as d, count as n
    | eval current_value=round(100*(p-d)/n, 0)
    | eval kpi_name="nps_current"
]
| append [
    search index=business sourcetype="dbx:hris_employees" status="active"
    | stats dc(employee_id) as current_value
    | eval kpi_name="headcount"
]
| lookup executive_kpi_targets.csv kpi_name OUTPUT target_value, kpi_label, unit
| eval vs_target=if(target_value>0, round(100*current_value/target_value,1), null())
| eval health=case(vs_target>=95,"GREEN", vs_target>=80,"AMBER", 1=1,"RED")
| table kpi_label, current_value, target_value, unit, vs_target, health
| sort kpi_label
```
- **Implementation:** (1) Define 8-12 executive KPIs in `executive_kpi_targets.csv` with name, target, label, and unit; (2) build individual saved searches for each KPI sourcing from the relevant business data; (3) combine into a unified scorecard using append; (4) schedule refresh every 4 hours; (5) provide drill-down links from each KPI to the detailed dashboard; (6) distribute via scheduled PDF to the executive team.
- **Visualization:** Single value tiles (one per KPI with traffic light colors), Table (KPI vs target), Gauge or bullet charts for each metric.

---

### UC-23.8.2 · Operational Efficiency and Productivity Metrics
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Tracks operational efficiency metrics that COOs care about — revenue per employee, cost per transaction, automation rate, throughput, and error rates across business processes. Shows whether the organisation is getting more productive over time and where manual processes are creating bottlenecks.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` (operational data), `index=app_events` (process automation logs)
- **SPL:**
```spl
index=business sourcetype="dbx:erp_orders" order_status="booked" earliest=-1mon@mon latest=@mon
| stats sum(revenue) as monthly_revenue, count as transactions
| appendcols [
    search index=business sourcetype="dbx:hris_employees" status="active"
    | stats dc(employee_id) as headcount
]
| appendcols [
    search index=app_events sourcetype="process_automation" earliest=-1mon@mon latest=@mon
    | stats sum(eval(if(automated="yes",1,0))) as automated, count as total_processes
]
| eval revenue_per_employee=round(monthly_revenue/headcount, 0)
| eval cost_per_transaction=round(monthly_revenue*0.15/transactions, 2)
| eval automation_rate=if(total_processes>0, round(100*automated/total_processes, 1), null())
| table monthly_revenue, headcount, revenue_per_employee, transactions, cost_per_transaction, automated, total_processes, automation_rate
```
- **Implementation:** (1) Combine revenue, headcount, and process data into a unified view; (2) define "cost per transaction" calculation based on your cost structure; (3) track process automation by tagging automated vs manual processes in application logs; (4) schedule monthly for operations reviews; (5) trend over quarters to show efficiency improvements.
- **Visualization:** Single value (revenue per employee, automation rate), Bar chart (metrics over time), Gauge (automation rate vs target), Table (efficiency metrics).

---

### UC-23.8.3 · Business Risk Heatmap and Early Warning System
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Risk, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Security
- **Value:** Aggregates business risks from multiple domains — financial (revenue miss, cash flow), operational (SLA breaches, supply chain), customer (churn spike, NPS drop), people (attrition spike, hiring delays), and cyber (security incidents) — into a single risk heatmap. Executives see a consolidated risk picture rather than siloed department reports, enabling faster decision-making on risk mitigation.
- **App/TA:** Splunk Enterprise Security (Splunkbase 263), Splunk ITSI (Splunkbase 1841), Splunk DB Connect (Splunkbase 2686)
- **Premium Apps:** Splunk Enterprise Security
- **Data Sources:** All business indexes (aggregated), `business_risk_thresholds.csv`
- **SPL:**
```spl
| inputlookup business_risk_thresholds.csv
| append [
    search index=business sourcetype="dbx:erp_orders" earliest=-30d
    | stats sum(revenue) as value | eval risk_area="Financial", risk_metric="Monthly Revenue", unit="currency"
]
| append [
    search index=business sourcetype="nps_survey" earliest=-30d
    | stats avg(score) as value | eval risk_area="Customer", risk_metric="NPS Score", unit="points"
]
| append [
    search index=business sourcetype="dbx:hris_employees" earliest=-30d
    | eval termed=if(isnotnull(termination_date),1,0) | stats sum(termed) as terminations, dc(employee_id) as headcount
    | eval value=round(100*terminations/headcount*12, 1) | eval risk_area="People", risk_metric="Annualised Attrition %", unit="pct"
]
| append [
    search `notable` urgency IN ("critical","high") earliest=-30d | stats count as value | eval risk_area="Cyber", risk_metric="Critical Security Incidents", unit="count"
]
| lookup business_risk_thresholds.csv risk_metric OUTPUT green_threshold, amber_threshold
| eval risk_level=case(
    unit="currency" AND value >= green_threshold, "GREEN",
    unit="currency" AND value >= amber_threshold, "AMBER",
    unit IN ("pct","count") AND value <= green_threshold, "GREEN",
    unit IN ("pct","count") AND value <= amber_threshold, "AMBER",
    1=1, "RED")
| table risk_area, risk_metric, value, unit, risk_level
| sort risk_area
```
- **Implementation:** (1) Define `business_risk_thresholds.csv` with green/amber/red thresholds per metric; (2) add risk domains relevant to your business; (3) schedule daily for executive team; (4) alert the executive team when any risk moves to RED; (5) add drill-down to the domain-specific dashboard for investigation; (6) maintain risk register notes for board reporting.
- **Visualization:** Heatmap (risk areas × risk level), Single value tiles per domain, Table (risk register with current status), Trend chart (risk movement over time).

---

### 23.9 ESG & Sustainability Reporting

**Primary App/TA:** Splunk DB Connect (Splunkbase 2686), HEC (IoT/BMS integration), Splunk ITSI (Splunkbase 1841).

**Data Sources:** Building management system data (power meters, HVAC sensors via BACnet/Modbus), cloud provider sustainability APIs, fleet management telematics, travel booking system data, waste management logs, HR diversity data (anonymised).

---

### UC-23.9.1 · Carbon Footprint Tracking and Reduction Progress
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Tracks Scope 1, 2, and 3 carbon emissions from energy consumption, fleet operations, business travel, and cloud usage — measuring progress against net-zero commitments. Sustainability officers see which emission sources are largest and whether reduction initiatives are working, while the board gets quarterly ESG reporting data automatically calculated rather than manually assembled.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC (BMS/IoT data)
- **Data Sources:** `index=facilities` (power meter readings, gas consumption), `index=business` (fleet fuel purchases, travel bookings, cloud usage), `carbon_factors.csv` (emission conversion factors)
- **SPL:**
```spl
index=facilities sourcetype="power_meter" earliest=-1mon@mon latest=@mon
| stats sum(kwh_consumed) as total_kwh by site
| eval scope="Scope_2", source="Electricity"
| append [
    search index=facilities sourcetype="gas_meter" earliest=-1mon@mon latest=@mon
    | stats sum(cubic_metres) as total_gas by site
    | eval scope="Scope_1", source="Natural_Gas", total_kwh=total_gas*11.1
]
| append [
    search index=business sourcetype="fleet_fuel" earliest=-1mon@mon latest=@mon
    | stats sum(litres) as total_litres by site
    | eval scope="Scope_1", source="Fleet_Fuel", total_kwh=total_litres*9.7
]
| append [
    search index=business sourcetype="travel_booking" earliest=-1mon@mon latest=@mon
    | stats sum(distance_km) as total_km by site
    | eval scope="Scope_3", source="Business_Travel", total_kwh=total_km*0.255
]
| lookup carbon_factors.csv source OUTPUT kg_co2_per_kwh
| eval tonnes_co2=round(total_kwh * kg_co2_per_kwh / 1000, 2)
| stats sum(tonnes_co2) as total_tonnes by scope, source
| sort scope, source
| table scope, source, total_tonnes
```
- **Implementation:** (1) Install power and gas meters with data logging to Splunk via BMS/IoT integration; (2) maintain `carbon_factors.csv` with region-specific emission factors (update annually); (3) import fleet fuel and travel data from procurement/booking systems; (4) schedule monthly calculation; (5) compare against annual targets and prior year; (6) generate quarterly ESG report data for board and external disclosure.
- **Visualization:** Stacked bar (emissions by scope), Pie chart (emission sources), Line chart (monthly trend vs target), Single value (total CO2e, % reduction YoY).

---

### UC-23.9.2 · Energy Consumption and Efficiency by Facility
- **Criticality:** 🟢 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Monitors energy consumption per building, floor, and system (HVAC, lighting, compute) — showing energy use intensity (EUI) and identifying facilities that are consuming more than expected. Facilities managers see which buildings need efficiency upgrades, while finance sees the cost impact. Reducing energy consumption directly reduces both costs and carbon emissions.
- **App/TA:** HEC (BMS/IoT data), Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=facilities` `sourcetype="power_meter"` (meter_id, site, system, kwh, timestamp), `facility_details.csv` (site, square_metres)
- **SPL:**
```spl
index=facilities sourcetype="power_meter" earliest=-30d
| bin _time span=1d
| stats sum(kwh) as daily_kwh by _time, site, system
| stats avg(daily_kwh) as avg_daily_kwh, sum(daily_kwh) as total_kwh by site, system
| lookup facility_details.csv site OUTPUT square_metres, occupancy
| eval eui=if(square_metres>0, round(total_kwh/square_metres, 2), null())
| eval cost_estimate=round(total_kwh * 0.12, 2)
| stats sum(total_kwh) as site_total_kwh, sum(cost_estimate) as site_total_cost, values(eui) as eui by site, square_metres
| sort - site_total_kwh
| table site, square_metres, site_total_kwh, site_total_cost, eui
```
- **Implementation:** (1) Install sub-metering at system level (HVAC, lighting, compute) where possible; (2) ingest meter data via BACnet/Modbus through Edge Hub or BMS integration; (3) maintain `facility_details.csv` with building size and occupancy; (4) schedule daily; (5) alert when any site's EUI exceeds benchmark by >20%; (6) compare weekday vs weekend consumption to identify waste.
- **Visualization:** Bar chart (EUI by facility), Heatmap (energy by system × site), Line chart (daily consumption trend), Single value (total monthly cost, EUI benchmark).

---

### UC-23.9.3 · Waste Diversion and Recycling Rate Tracking
- **Criticality:** 🟢 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Tracks waste generation by type (landfill, recycling, composting, hazardous) and calculates diversion rates against zero-waste targets. Operations and sustainability teams see which facilities and waste streams need attention, while the data feeds directly into ESG disclosure requirements — many organisations now report waste metrics to investors and rating agencies.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC
- **Data Sources:** `index=business` `sourcetype="waste_manifest"` (site, waste_type, weight_kg, disposal_method, collection_date)
- **SPL:**
```spl
index=business sourcetype="waste_manifest" earliest=-90d
| eval diverted=if(disposal_method IN ("recycled","composted","reused"), 1, 0)
| stats sum(weight_kg) as total_kg, sum(eval(if(diverted=1,weight_kg,0))) as diverted_kg by site
| eval diversion_rate=round(100*diverted_kg/total_kg, 1)
| eval landfill_kg=total_kg-diverted_kg
| sort - landfill_kg
| table site, total_kg, diverted_kg, landfill_kg, diversion_rate
```
- **Implementation:** (1) Import waste manifests from waste management provider via CSV upload or HEC; (2) classify disposal methods consistently; (3) schedule monthly; (4) set diversion rate targets by facility; (5) alert when any site's diversion rate drops below target; (6) trend quarterly for ESG reporting.
- **Visualization:** Bar chart (diversion rate by site), Pie chart (waste by type), Line chart (monthly diversion trend), Single value (overall diversion rate %).

---

### UC-23.9.4 · Water Consumption Monitoring and Conservation
- **Criticality:** 🟢 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Business
- **Industry:** Manufacturing, Data Centers, Hospitality
- **Splunk Pillar:** Observability
- **Value:** Tracks water consumption by facility and usage type (cooling, process, domestic) — identifying sites that consume disproportionately and detecting leaks or waste. Water is increasingly a material ESG metric, especially for data centres (PUE) and manufacturing (process water). Reducing consumption lowers costs and demonstrates environmental responsibility.
- **App/TA:** HEC (IoT/BMS integration)
- **Data Sources:** `index=facilities` `sourcetype="water_meter"` (meter_id, site, usage_type, litres, timestamp)
- **SPL:**
```spl
index=facilities sourcetype="water_meter" earliest=-30d
| bin _time span=1d
| stats sum(litres) as daily_litres by _time, site
| stats avg(daily_litres) as avg_daily, stdev(daily_litres) as stdev_daily, sum(daily_litres) as monthly_total by site
| eval upper_threshold=avg_daily + 2*stdev_daily
| eval anomaly=if(avg_daily > upper_threshold, "INVESTIGATE", "Normal")
| eval monthly_cost=round(monthly_total * 0.003, 2)
| sort - monthly_total
| table site, monthly_total, avg_daily, monthly_cost, anomaly
```
- **Implementation:** (1) Install smart water meters with data logging; (2) ingest readings via Edge Hub or HEC; (3) schedule daily with anomaly detection for leak identification; (4) compare consumption against production output for water intensity metrics; (5) trend quarterly for ESG reporting; (6) set reduction targets by facility.
- **Visualization:** Bar chart (consumption by site), Line chart (daily trend with anomaly markers), Single value (monthly total, cost), Table (sites with anomalies).

---

### UC-23.9.5 · ESG Disclosure Readiness and Data Completeness
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Tracks whether the organisation has complete, auditable data for all required ESG disclosure metrics — from emissions and energy to diversity and governance. As ESG reporting becomes mandatory in many jurisdictions (CSRD, SEC Climate Disclosure), this use case ensures that data collection gaps are identified well before reporting deadlines rather than during last-minute scrambles.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `esg_metric_registry.csv` (required metrics, data sources, owners), all business and facilities indexes
- **SPL:**
```spl
| inputlookup esg_metric_registry.csv
| eval data_available=case(
    data_source="power_meter" AND [search index=facilities sourcetype="power_meter" earliest=-90d | stats count | return $count],  "YES",
    data_source="waste_manifest" AND [search index=business sourcetype="waste_manifest" earliest=-90d | stats count | return $count], "YES",
    data_source="hris" AND [search index=business sourcetype="dbx:hris_employees" earliest=-90d | stats count | return $count], "YES",
    1=1, "MISSING")
| eval readiness=if(data_available="YES" AND isnotnull(last_verified), "READY", "GAP")
| stats count as total_metrics, sum(eval(if(readiness="READY",1,0))) as ready, sum(eval(if(readiness="GAP",1,0))) as gaps by reporting_framework
| eval completeness_pct=round(100*ready/total_metrics, 1)
| table reporting_framework, total_metrics, ready, gaps, completeness_pct
```
- **Implementation:** (1) Build `esg_metric_registry.csv` listing all required ESG metrics by framework (CSRD, GRI, SASB, TCFD); (2) map each metric to its Splunk data source and data owner; (3) schedule quarterly readiness checks; (4) alert data owners when their metrics have data gaps; (5) generate audit trail showing when each metric was last validated; (6) produce a readiness report for the sustainability committee.
- **Visualization:** Table (metric readiness by framework), Gauge (overall completeness %), Bar chart (gaps by framework), Single value (metrics with gaps).
