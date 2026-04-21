## 23. Business Analytics & Executive Intelligence

### 23.1 Customer Experience & Digital Analytics

**Primary App/TA:** Splunk Add-on for Apache Web Server (Splunkbase 3186), Splunk Add-on for Nginx (Splunkbase 3258), Splunk DB Connect (Splunkbase 2686), Splunk Add-on for Google Analytics (HEC), Splunk Stream (Splunkbase 1809), Splunk ITSI (Splunkbase 1841).

**Data Sources:** Web access logs (`sourcetype="access_combined"`, `sourcetype="access_combined_wcookie"`), application event logs (HEC), CDN logs (Cloudflare, Akamai, Fastly), CRM records via DB Connect (`dbx:salesforce`, `dbx:hubspot`), POS transaction logs, mobile app analytics (HEC), customer feedback/NPS data (HEC/CSV lookup).

---

### UC-23.1.1 · Website Conversion Funnel Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🐢 crawl
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
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Apache Web Server](https://splunkbase.splunk.com/app/3186)

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
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Apache Web Server](https://splunkbase.splunk.com/app/3186)

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
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Apache Web Server](https://splunkbase.splunk.com/app/3186)

---

### UC-23.1.4 · Customer Satisfaction Score (CSAT/NPS) Trend Dashboard
- **Criticality:** 🟡 Medium
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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [Splunk Add-on for Apache Web Server](https://splunkbase.splunk.com/app/3186)

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
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-23.1.7 · Site Search Effectiveness and Zero-Result Rate
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Measures how often on-site searches return no results or no clicks, which usually means frustrated shoppers or support deflection failure. We help merchandising and content teams fix synonyms and catalog gaps before abandonment rises.
- **App/TA:** Splunk Add-on for Apache Web Server (Splunkbase 3186), HEC
- **Data Sources:** `index=web` `sourcetype="access_combined"` (uri, status, query), `index=app_events` `sourcetype="site_search"` (search_term, result_count, clicked_result)
- **SPL:**
```spl
index=app_events sourcetype="site_search" earliest=-14d
| eval zero_results=if(result_count=0 OR isnull(result_count),1,0)
| eval no_click=if(clicked_result="none" OR isnull(clicked_result),1,0)
| stats count as searches, sum(zero_results) as zero_hits, sum(no_click) as no_click by search_term
| eval zero_rate_pct=round(100*zero_hits/searches,1)
| eval no_click_rate_pct=round(100*no_click/searches,1)
| where searches>=20
| sort - zero_rate_pct
| head 40
| table search_term, searches, zero_hits, zero_rate_pct, no_click_rate_pct
```
- **Implementation:** (1) Log each search with term, count of results, and whether the user clicked a hit using HEC from your storefront or portal; (2) filter bots from web logs if you also infer search from query strings; (3) send the top twenty high-volume zero-result terms weekly to the product content owner with suggested catalog checks.
- **Visualization:** Bar chart (zero-result rate by term), Table (top problem searches), Line chart (overall zero-result trend), Single value (searches with no click percent).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Apache Web Server](https://splunkbase.splunk.com/app/3186)

---

### UC-23.1.8 · Form Abandonment and Field-Level Drop-Off
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Shows which form fields correlate with users leaving before submit so teams can shorten lead flows and improve compliance without guessing. We help growth leaders recover more sign-ups from the same traffic volume.
- **App/TA:** HEC (form analytics)
- **Data Sources:** `index=app_events` `sourcetype="form_analytics"` (form_id, field_name, event_type, session_id, dwell_ms)
- **SPL:**
```spl
index=app_events sourcetype="form_analytics" earliest=-30d
| where event_type="abandon"
| stats count as abandons by form_id, field_name
| sort - abandons
| head 25
| table form_id, field_name, abandons
```
- **Implementation:** (1) Instrument blur, focus, submit, and abandon events with field names and session identifiers through HEC; (2) define abandon as leaving the page without submit after interacting with the form; (3) prioritise redesign of the top three field-and-form pairs every sprint until abandon counts fall by the agreed target.
- **Visualization:** Bar chart (abandons by last field), Table (form and field ranking), Funnel chart (started vs submitted), Single value (overall form completion rate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-23.1.9 · Third-Party Tag and API Latency Impact on Engagement
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Correlates slow marketing tags or partner application programming interface calls with shorter sessions and fewer conversions. We help digital teams decide which vendors to keep, async load, or remove based on customer impact, not vendor promises alone.
- **App/TA:** HEC (RUM or browser telemetry), Splunk Add-on for Apache Web Server (Splunkbase 3186)
- **Data Sources:** `index=app_events` `sourcetype="rum:resource"` (session_id, resource_host, duration_ms, initiator_type), `index=app_events` `sourcetype="app:ecommerce"` (session_id, event_type)
- **SPL:**
```spl
index=app_events sourcetype="rum:resource" initiator_type="script" earliest=-7d
| stats perc95(duration_ms) as p95_ms, avg(duration_ms) as avg_ms, count as loads,
        dc(session_id) as affected_sessions by resource_host
| eval slow_tag=if(p95_ms>500,"SLOW","OK")
| sort - p95_ms
| head 25
| table resource_host, affected_sessions, loads, avg_ms, p95_ms, slow_tag
```
- **Implementation:** (1) Capture real user monitoring resource timings with host and initiator type via HEC; (2) map session identifiers consistently with commerce events; (3) review monthly with marketing technology owners and defer or replace any third-party host above the latency budget for two consecutive weeks.
- **Visualization:** Bar chart (ninety-fifth percentile duration by host), Table (slow tag list), Scatter plot (loads vs latency), Single value (count of hosts over budget).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Apache Web Server](https://splunkbase.splunk.com/app/3186), [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### 23.2 Revenue & Sales Operations

**Primary App/TA:** Splunk DB Connect (Splunkbase 2686), HEC (CRM/ERP integration).

**Data Sources:** CRM records via DB Connect (Salesforce opportunities, HubSpot deals), ERP order data (`dbx:sap`, `dbx:oracle`), billing system events, subscription management platform data, POS transaction logs.

---

### UC-23.2.1 · Sales Pipeline Velocity and Forecast Accuracy
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🐢 crawl
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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.2.3 · Customer Churn Prediction and Early Warning
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Wave:** 🐢 crawl
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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.2.5 · Pricing and Discount Effectiveness Analysis
- **Criticality:** 🟡 Medium
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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.2.6 · Quota Attainment and Capacity Coverage
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Compares booked revenue to quota by rep and region so leaders see who is on track before the quarter ends. We help you move deals, coaching, and territory support to the teams with the largest gap to plan.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:crm_opportunities"` (owner, region, stage, amount, close_date), `sales_quota.csv` (owner, quarter, quota_amount)
- **SPL:**
```spl
index=business sourcetype="dbx:crm_opportunities" stage="Closed Won" earliest=-90d
| eval qn=ceil(tonumber(strftime(strptime(close_date,"%Y-%m-%d"),"%m"))/3)
| eval quarter=strftime(strptime(close_date,"%Y-%m-%d"),"%Y")."-Q".tostring(qn)
| stats sum(amount) as booked by owner, region, quarter
| lookup sales_quota.csv owner quarter OUTPUT quota_amount
| eval attainment_pct=if(quota_amount>0, round(100*booked/quota_amount,1), null())
| eval gap_to_quota=quota_amount-booked
| where gap_to_quota>0
| sort - gap_to_quota
| table owner, region, quarter, quota_amount, booked, attainment_pct, gap_to_quota
```
- **Implementation:** (1) Export closed-won revenue and owner keys from your customer relationship management system on a nightly DB Connect schedule; (2) maintain `sales_quota.csv` with fiscal quarter and approved quota amounts; (3) email sales leadership each Monday with reps below eighty percent attainment entering the final month of the quarter.
- **Visualization:** Bar chart (attainment by rep), Table (gap to quota), Heatmap (region × quarter), Single value (team blended attainment).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.2.7 · Average Contract Value and Deal Size Mix
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Business
- **Industry:** SaaS, Professional Services
- **Splunk Pillar:** Observability
- **Value:** Tracks whether new business is trending larger or smaller so product and packaging teams can adjust offers before average contract value drifts. We help finance stress-test forecasts when the mix shifts toward many small deals or a few giants.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:crm_opportunities"` (opportunity_id, deal_type, amount, stage, product_line, close_date)
- **SPL:**
```spl
index=business sourcetype="dbx:crm_opportunities" stage="Closed Won" deal_type="New Business" earliest=-180d
| eval close_epoch=strptime(close_date,"%Y-%m-%d")
| eval month=strftime(close_epoch,"%Y-%m")
| eval deal_band=case(
    amount < 10000, "<10k",
    amount < 50000, "10k-50k",
    amount < 250000, "50k-250k",
    1=1, "250k+")
| stats count as deals, sum(amount) as revenue, avg(amount) as acv by month, deal_band
| sort month, deal_band
| table month, deal_band, deals, revenue, acv
```
- **Implementation:** (1) Require deal type and product line on closed opportunities in your source system; (2) import history for at least six months to see mix shifts; (3) review monthly with revenue operations and adjust campaign targeting when small-deal share spikes unexpectedly.
- **Visualization:** Stacked bar (revenue by deal band over time), Line chart (average contract value trend), Table (mix percentages), Single value (current quarter average contract value).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.2.8 · Win–Loss Reason Coding and Competitive Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Summarises why deals are won or lost and how often named competitors appear so product and enablement invest in the right battlecards. We help you reduce repeated losses to the same objection without relying on anecdotal win stories alone.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:crm_opportunities"` (stage, loss_reason, win_reason, competitor, amount, region)
- **SPL:**
```spl
index=business sourcetype="dbx:crm_opportunities" stage="Closed Lost" earliest=-180d
| where isnotnull(loss_reason)
| stats count as deals, sum(amount) as pipeline by loss_reason, competitor
| eventstats sum(deals) as total_lost
| eval share_pct=round(100*deals/total_lost,1)
| sort - deals
| head 30
| table loss_reason, competitor, deals, pipeline, share_pct
```
- **Implementation:** (1) Enforce structured loss and competitor picklists in your customer relationship management close workflow; (2) replicate closed opportunity rows including reasons via DB Connect; (3) run a bi-weekly review with product marketing when any single loss reason exceeds ten percent of losses for two periods in a row.
- **Visualization:** Bar chart (top loss reasons), Table (competitor × reason), Pie chart (loss reason mix), Single value (losses with competitor tagged percent).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [Splunk Add-on for Apache Web Server](https://splunkbase.splunk.com/app/3186)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.3.3 · Email Campaign Performance and Engagement
- **Criticality:** 🟡 Medium
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
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-23.3.4 · Website Traffic Source and SEO Performance
- **Criticality:** 🟡 Medium
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
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Apache Web Server](https://splunkbase.splunk.com/app/3186)

---

### UC-23.3.5 · Paid Media Cost Per Acquisition and Quality Score
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Divides advertising spend by attributed sign-ups or qualified leads so paid media teams stop optimising for cheap clicks that never buy. We help you reallocate budget toward campaigns that bring customers who actually convert downstream.
- **App/TA:** HEC (ad platform), Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="ad_spend"` (campaign_id, spend, impressions, clicks, date), `index=business` `sourcetype="dbx:crm_leads"` (lead_id, campaign_id, status)
- **SPL:**
```spl
index=business sourcetype="ad_spend" earliest=-30d
| stats sum(spend) as spend, sum(clicks) as clicks, sum(impressions) as impressions by campaign_id
| join type=left campaign_id [
    search index=business sourcetype="dbx:crm_leads" earliest=-30d
    | eval qualified=if(match(lower(status),"qualified|mql"),1,0)
    | stats dc(lead_id) as leads, sum(qualified) as qualified_leads by campaign_id
]
| fillnull value=0 leads qualified_leads
| eval cpa_spend=if(leads>0, round(spend/leads,2), null())
| eval cpq=if(qualified_leads>0, round(spend/qualified_leads,2), null())
| eval ctr_pct=if(impressions>0, round(100*clicks/impressions,2), null())
| sort - spend
| table campaign_id, spend, clicks, ctr_pct, leads, qualified_leads, cpa_spend, cpq
```
- **Implementation:** (1) Land daily campaign cost and click files from your advertising APIs into Splunk using HEC; (2) join leads on a shared campaign identifier from your marketing automation or customer relationship management system; (3) alert marketing when cost per qualified lead doubles week over week for any active campaign.
- **Visualization:** Scatter plot (spend vs qualified leads), Table (campaign efficiency), Bar chart (cost per qualified lead), Single value (blended cost per acquisition).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.3.6 · Content Engagement and Lead Conversion Lift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Links blog and resource centre engagement to lead creation so editorial investments can be judged like performance channels. We help you retire low-traffic pages that consume effort without pipeline impact.
- **App/TA:** Splunk Add-on for Apache Web Server (Splunkbase 3186), Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=web` `sourcetype="access_combined"` (uri, clientip, status), `index=business` `sourcetype="dbx:crm_leads"` (lead_id, landing_page, created_date)
- **SPL:**
```spl
index=web sourcetype="access_combined" status=200 uri="/blog/*" earliest=-30d
| eval session=clientip."_".useragent
| stats dc(session) as sessions, count as views by uri
| join type=left uri [
    search index=business sourcetype="dbx:crm_leads" earliest=-30d
    | stats dc(lead_id) as leads by landing_page
    | rename landing_page as uri
]
| fillnull value=0 leads
| eval views_per_lead=if(leads>0, round(views/leads,0), null())
| sort - views
| head 25
| table uri, sessions, views, leads, views_per_lead
```
- **Implementation:** (1) Standardise landing page URLs on forms so they match blog paths where possible; (2) import lead timestamps and landing page from customer relationship management nightly; (3) review monthly with content marketing to double down on topics with strong lead lift and archive thin content.
- **Visualization:** Bar chart (views by article), Table (lead conversion proxy), Line chart (sessions vs leads), Single value (blog-sourced leads).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Apache Web Server](https://splunkbase.splunk.com/app/3186), [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.3.7 · Webinar and Event Pipeline Contribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Attributes opportunities and revenue to webinars and field events so field marketing proves return beyond attendance counts. We help leadership compare expensive programmes to simpler digital motions using the same pipeline currency.
- **App/TA:** HEC (event platform), Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="event_registration"` (event_id, registrant_id, attended_flag), `index=business` `sourcetype="dbx:crm_opportunities"` (opportunity_id, campaign_source, amount, stage)
- **SPL:**
```spl
index=business sourcetype="event_registration" earliest=-90d
| stats dc(registrant_id) as registrations, sum(eval(if(attended_flag="yes",1,0))) as attendees by event_id
| join type=left event_id [
    search index=business sourcetype="dbx:crm_opportunities" earliest=-90d
    | eval from_event=if(match(campaign_source,"(?i)webinar|event|field"),1,0)
    | where from_event=1
    | stats sum(amount) as pipeline, sum(eval(if(stage="Closed Won",amount,0))) as won_revenue by campaign_source
    | rename campaign_source as event_id
]
| fillnull value=0 pipeline won_revenue
| eval attendance_rate=if(registrations>0, round(100*attendees/registrations,1), null())
| sort - won_revenue
| table event_id, registrations, attendees, attendance_rate, pipeline, won_revenue
```
- **Implementation:** (1) Send registration and attendance webhooks from your event tool into Splunk with identifiers that match customer relationship management campaigns; (2) require opportunities to carry the originating programme code; (3) publish a quarterly event portfolio review sorted by won revenue and pipeline efficiency.
- **Visualization:** Bar chart (won revenue by event), Table (attendance and pipeline), Single value (events-sourced pipeline), Line chart (attendance rate trend).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.4.2 · Time-to-Hire and Recruiting Pipeline Health
- **Criticality:** 🟡 Medium
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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.4.3 · Diversity and Inclusion Metrics Dashboard
- **Criticality:** 🟡 Medium
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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.4.5 · Absence and Leave Pattern Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Surfaces unusual absence spikes by team or location so managers can offer support or adjust rosters before service levels suffer. We help people leaders spot burnout or local illness trends early while respecting privacy aggregation.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC
- **Data Sources:** `index=business` `sourcetype="dbx:time_attendance"` (employee_id, department, absence_hours, date, absence_type)
- **SPL:**
```spl
index=business sourcetype="dbx:time_attendance" absence_hours>0 earliest=-90d
| eval week=strftime(strptime(date,"%Y-%m-%d"),"%Y-%U")
| stats sum(absence_hours) as total_absence_hours, dc(employee_id) as absentees by department, week
| eventstats avg(total_absence_hours) as org_avg
| eval variance_pct=if(org_avg>0, round(100*(total_absence_hours-org_avg)/org_avg,1), null())
| where variance_pct>25
| sort - total_absence_hours
| table department, week, absentees, total_absence_hours, variance_pct
```
- **Implementation:** (1) Import anonymised time and attendance extracts without attaching medical reasons unless legally approved; (2) roll up to department and week by default; (3) alert human resources when any department exceeds twenty-five percent above the company average for two consecutive weeks.
- **Visualization:** Line chart (absence hours trend by department), Table (outlier weeks), Heatmap (department × week), Single value (organisation absence hours).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.4.6 · Internal Mobility and Promotion Velocity
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Tracks how often people move roles internally and how long promotions take after eligibility. We help talent leaders prove whether career paths are real or blocked, which affects engagement and retention.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:hris_employees"` (employee_id, department, role, hire_date, promotion_date, job_change_type)
- **SPL:**
```spl
index=business sourcetype="dbx:hris_employees" earliest=-730d
| where isnotnull(promotion_date)
| eval promo_epoch=strptime(promotion_date,"%Y-%m-%d")
| eval hire_epoch=strptime(hire_date,"%Y-%m-%d")
| eval months_to_promo=round((promo_epoch-hire_epoch)/(86400*30),1)
| eval internal_move=if(job_change_type IN ("Transfer","Promotion","Lateral"),1,0)
| stats count as events, sum(internal_move) as internal_moves, avg(months_to_promo) as avg_months_to_promo by department
| eval internal_move_rate=round(100*internal_moves/events,1)
| sort - internal_move_rate
| table department, events, internal_moves, internal_move_rate, avg_months_to_promo
```
- **Implementation:** (1) Ensure job change events carry a type flag from your human resources information system feed; (2) refresh monthly after payroll close; (3) review with business unit heads when promotion velocity lengthens materially versus the prior year.
- **Visualization:** Bar chart (internal move rate by department), Table (promotion timing), Line chart (average months to promotion), Single value (company internal move rate).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.4.7 · Overtime Cost and Burnout Risk Indicator
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Manufacturing, Retail, Healthcare
- **Splunk Pillar:** Observability
- **Value:** Aggregates overtime hours and premium pay by cost centre so finance controls labour inflation while people teams watch burnout signals. We help you intervene when a few teams carry an unsustainable load.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:time_attendance"` (employee_id, cost_centre, overtime_hours, pay_week, hourly_rate)
- **SPL:**
```spl
index=business sourcetype="dbx:time_attendance" overtime_hours>0 earliest=-56d
| eval ot_pay=overtime_hours*hourly_rate*1.5
| stats sum(overtime_hours) as total_ot_hours, sum(ot_pay) as total_ot_pay,
        dc(employee_id) as employees_with_ot by cost_centre, pay_week
| eventstats perc90(total_ot_pay) as p90_pay by pay_week
| eval high_cost=if(total_ot_pay>=p90_pay,"YES","NO")
| where high_cost="YES"
| sort - total_ot_pay
| table cost_centre, pay_week, employees_with_ot, total_ot_hours, total_ot_pay
```
- **Implementation:** (1) Load approved time cards with overtime and base rates through DB Connect using payroll rules your controller validates; (2) group by cost centre and pay week for privacy-preserving views; (3) trigger a fortnightly review when any cost centre repeatedly lands in the top decile of overtime pay.
- **Visualization:** Bar chart (overtime pay by cost centre), Table (high-cost weeks), Line chart (total overtime hours trend), Single value (total overtime pay period).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [Splunk Add-on for ServiceNow](https://splunkbase.splunk.com/app/1928)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.5.5 · Perfect Order Rate and Customer Impact
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Retail, Manufacturing, Distribution
- **Splunk Pillar:** Observability
- **Value:** Combines on-time, in-full, and damage-free delivery into one perfect order score so sales and operations share one customer-facing metric. We help you see when service looks acceptable on paper but customers still receive wrong or damaged goods.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC
- **Data Sources:** `index=business` `sourcetype="dbx:shipments"` (order_id, customer_tier, sla_met, damage_flag, short_ship_flag), `index=business` `sourcetype="returns_log"` (order_id, return_reason)
- **SPL:**
```spl
index=business sourcetype="dbx:shipments" earliest=-30d
| eval on_time=sla_met
| eval in_full=if(short_ship_flag="no",1,0)
| eval no_damage=if(damage_flag="no",1,0)
| join type=left order_id [
    search index=business sourcetype="returns_log" earliest=-30d
    | stats count as return_count by order_id
]
| fillnull value=0 return_count
| eval perfect=if(on_time=1 AND in_full=1 AND no_damage=1 AND return_count=0,1,0)
| stats count as orders, sum(perfect) as perfect_orders by customer_tier
| eval perfect_order_rate=round(100*perfect_orders/orders,1)
| sort - perfect_order_rate
| table customer_tier, orders, perfect_orders, perfect_order_rate
```
- **Implementation:** (1) Align shipment, quality, and returns feeds on a common order identifier ingested through DB Connect or HEC; (2) define “perfect” with commercial and logistics leaders; (3) publish weekly to account teams when any customer tier drops below the agreed perfect-order threshold.
- **Visualization:** Bar chart (perfect order rate by tier), Single value (overall perfect order %), Table (tier detail), Line chart (weekly trend).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.5.6 · Capacity Utilisation vs Demand Forecast
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Manufacturing, Logistics
- **Splunk Pillar:** Observability
- **Value:** Compares production or warehouse throughput to forecast demand so planners see under-used lines before capital is wasted or overloaded sites before service fails. We help you align staffing and shifts with expected volume swings.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC
- **Data Sources:** `index=business` `sourcetype="mes:throughput"` (line_id, units_produced, shift_date), `demand_forecast.csv` (line_id, week, forecast_units)
- **SPL:**
```spl
index=business sourcetype="mes:throughput" earliest=-14d
| eval week=strftime(_time,"%Y-%U")
| stats sum(units_produced) as actual_units by line_id, week
| lookup demand_forecast.csv line_id week OUTPUT forecast_units
| eval utilisation_pct=if(forecast_units>0, round(100*actual_units/forecast_units,1), null())
| eval gap_units=forecast_units-actual_units
| where utilisation_pct<85 OR utilisation_pct>115
| eval abs_gap=abs(gap_units)
| sort - abs_gap
| table line_id, week, forecast_units, actual_units, utilisation_pct, gap_units
```
- **Implementation:** (1) Ingest manufacturing execution system or warehouse throughput events on each shift via HEC; (2) refresh `demand_forecast.csv` from planning each week with matching line and week keys; (3) review exceptions daily with planning and plant managers to rebalance loads or adjust forecasts.
- **Visualization:** Line chart (utilisation vs one hundred percent by line), Table (under and over capacity), Single value (lines out of band), Bar chart (gap units by line).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.5.7 · Returns Rate and Reverse Logistics Cost
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Business
- **Industry:** Retail, E-Commerce
- **Splunk Pillar:** Observability
- **Value:** Tracks return counts and refund value against shipped units so merchandising sees which products drive margin leakage. We help you trigger quality reviews or sizing guides before return rates damage the brand.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="returns_log"` (sku, return_date, refund_amount, reason_code), `index=business` `sourcetype="dbx:shipments"` (sku, shipped_qty, ship_date)
- **SPL:**
```spl
index=business sourcetype="returns_log" earliest=-30d
| stats count as returns, sum(refund_amount) as refund_total by sku, reason_code
| join type=left sku [
    search index=business sourcetype="dbx:shipments" earliest=-30d
    | stats sum(shipped_qty) as shipped_units by sku
]
| eval return_rate_pct=if(shipped_units>0, round(100*returns/shipped_units,2), null())
| sort - refund_total
| table sku, reason_code, shipped_units, returns, return_rate_pct, refund_total
```
- **Implementation:** (1) Load returns authorisations and shipment facts from order management with a shared stock keeping unit key; (2) normalise reason codes to a small taxonomy for reporting; (3) schedule weekly and invite category managers when any stock keeping unit exceeds the agreed return rate.
- **Visualization:** Bar chart (return rate by SKU), Table (reason code breakdown), Single value (portfolio return %), Pie chart (reason mix).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [Splunk Enterprise Security](https://splunkbase.splunk.com/app/263)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
    if(tonumber(strftime(strptime(expense_date,"%Y-%m-%d"),"%u"))>=6, "WEEKEND", null()),
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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-23.6.5 · Purchase Order Cycle Time and Maverick Spend
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Measures how long purchase requests take from submission to approval and flags orders placed outside preferred suppliers. We help procurement protect negotiated savings and shorten delays that stall projects.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=business` `sourcetype="dbx:purchase_orders"` (po_number, request_date, approved_date, supplier, preferred_flag, amount)
- **SPL:**
```spl
index=business sourcetype="dbx:purchase_orders" earliest=-90d
| eval req=strptime(request_date,"%Y-%m-%d")
| eval appr=strptime(approved_date,"%Y-%m-%d")
| eval cycle_days=if(isnotnull(appr), round((appr-req)/86400,0), null())
| eval maverick=if(preferred_flag="no",1,0)
| stats avg(cycle_days) as avg_cycle_days, perc95(cycle_days) as p95_cycle_days,
        sum(amount) as total_spend, sum(eval(if(maverick=1,amount,0))) as maverick_spend,
        count as po_count by supplier
| eval maverick_pct=if(total_spend>0, round(100*maverick_spend/total_spend,1), null())
| sort - maverick_spend
| table supplier, po_count, avg_cycle_days, p95_cycle_days, total_spend, maverick_spend, maverick_pct
```
- **Implementation:** (1) Replicate purchase order lifecycle fields from enterprise resource planning or procurement workflow into Splunk using DB Connect; (2) maintain a preferred supplier flag on each vendor record; (3) alert procurement when maverick spend exceeds policy for two consecutive weeks.
- **Visualization:** Bar chart (maverick spend by supplier), Table (cycle time and maverick detail), Single value (overall maverick %), Line chart (average cycle days trend).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [Splunk Add-on for ServiceNow](https://splunkbase.splunk.com/app/1928)

---

### UC-23.6.6 · Intercompany Reconciliation Exception Queue
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Surfaces journal entries that fail intercompany matching rules so the close team clears exceptions before statutory reporting deadlines. We help finance reduce manual spreadsheet chasing during month-end.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:ic_reconciliation"` (ic_pair_id, entity_a, entity_b, amount_a, amount_b, status, posting_date)
- **SPL:**
```spl
index=business sourcetype="dbx:ic_reconciliation" status!="matched" earliest=-60d
| eval variance=abs(amount_a-amount_b)
| eval severity=case(variance>10000,"HIGH", variance>1000,"MEDIUM", 1=1,"LOW")
| stats count as open_items, sum(variance) as total_variance, max(variance) as max_variance by entity_a, entity_b, severity
| sort - total_variance
| table entity_a, entity_b, severity, open_items, total_variance, max_variance
```
- **Implementation:** (1) Export unmatched intercompany lines nightly from the general ledger or reconciliation tool via DB Connect; (2) classify severity bands with your controller; (3) assign a daily saved search that emails the shared services inbox when high severity open items exceed the agreed cap.
- **Visualization:** Table (exceptions by entity pair), Bar chart (open items by severity), Single value (total unmatched variance), Pie chart (severity mix).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [Splunk Add-on for ServiceNow](https://splunkbase.splunk.com/app/1928)

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
- **CIM Models:** N/A

- **References:** [Splunk Add-on for ServiceNow](https://splunkbase.splunk.com/app/1928)

---

### UC-23.7.2 · First Contact Resolution Rate and Escalation Patterns
- **Criticality:** 🟡 Medium
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
- **CIM Models:** N/A

- **References:** [Splunk Add-on for ServiceNow](https://splunkbase.splunk.com/app/1928)

---

### UC-23.7.3 · Customer Effort Score and Support Channel Effectiveness
- **Criticality:** 🟡 Medium
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
- **CIM Models:** N/A

- **References:** [Splunk Add-on for ServiceNow](https://splunkbase.splunk.com/app/1928)

---

### UC-23.7.4 · Backlog Age and Breach Risk Forecast
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Highlights tickets that have been open longer than your policy allows before they breach service promises. We help capacity planners see how much work is aging so they can add shifts or shift topics before customers feel ignored.
- **App/TA:** Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=itsm` `sourcetype="snow:incident"` (number, opened_at, closed_at, priority, assignment_group)
- **SPL:**
```spl
index=itsm sourcetype="snow:incident" state!="Closed" earliest=-30d
| eval opened_epoch=strptime(opened_at, "%Y-%m-%d %H:%M:%S")
| eval age_hours=round((now()-opened_epoch)/3600,1)
| eval sla_target_hours=case(priority="1",4, priority="2",8, priority="3",24, 1=1,72)
| eval pct_of_sla=round(100*age_hours/sla_target_hours,0)
| eval breach_risk=case(pct_of_sla>=100,"BREACHED", pct_of_sla>=80,"AT RISK", 1=1,"OK")
| stats count as tickets, avg(age_hours) as avg_age_h, max(age_hours) as max_age_h by assignment_group, breach_risk
| sort assignment_group, breach_risk
| table assignment_group, breach_risk, tickets, avg_age_h, max_age_h
```
- **Implementation:** (1) Ingest open incidents with accurate opened timestamps from ServiceNow; (2) align `sla_target_hours` with your contractual response and resolve clocks; (3) schedule every two hours and route “AT RISK” queues to team leads before breaches hit customer reports.
- **Visualization:** Stacked bar (tickets by risk band and team), Table (oldest tickets), Single value (count at risk), Line chart (backlog age trend).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for ServiceNow](https://splunkbase.splunk.com/app/1928)

---

### UC-23.7.5 · Agent Occupancy and Schedule Adherence
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Relates logged-in and productive handle time to published schedules so workforce leaders see understaffing before service levels collapse. We help you balance labour cost with customer wait times using facts instead of anecdotal busy signals.
- **App/TA:** HEC (contact centre platform), Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="acd:agent_state"` (agent_id, state, duration_sec, queue), `agent_schedule.csv` (agent_id, scheduled_seconds, work_date)
- **SPL:**
```spl
index=business sourcetype="acd:agent_state" earliest=-7d
| eval work_states=if(state IN ("On_Call","After_Call_Work","Busy"),1,0)
| eval work_date=strftime(_time,"%Y-%m-%d")
| stats sum(eval(if(work_states=1,duration_sec,0))) as productive_sec,
        sum(duration_sec) as logged_sec by agent_id, work_date
| lookup agent_schedule.csv agent_id work_date OUTPUT scheduled_seconds
| fillnull value=28800 scheduled_seconds
| eval occupancy_pct=if(logged_sec>0, round(100*productive_sec/logged_sec,1), null())
| eval adherence_pct=if(scheduled_seconds>0, round(100*logged_sec/scheduled_seconds,1), null())
| stats avg(occupancy_pct) as avg_occupancy, avg(adherence_pct) as avg_adherence, dc(agent_id) as agents
| table agents, avg_occupancy, avg_adherence
```
- **Implementation:** (1) Stream agent state changes from your automatic call distributor into Splunk using HEC with consistent state names; (2) publish `agent_schedule.csv` with per-agent scheduled seconds per work date from workforce management; (3) review weekly with operations and adjust forecasts when adherence drifts more than five points from target.
- **Visualization:** Bar chart (occupancy by agent), Table (adherence exceptions), Single value (team average occupancy), Heatmap (hour-of-day occupancy).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.7.6 · Knowledge Base Deflection and Self-Service ROI
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Compares article views and successful searches to ticket volume so content owners see which topics actually reduce contacts. We help you justify investment in help articles by linking usage to fewer paid support minutes.
- **App/TA:** HEC (help centre analytics), Splunk Add-on for ServiceNow (Splunkbase 1928)
- **Data Sources:** `index=web` `sourcetype="access_combined"` (uri, status, clientip), `index=itsm` `sourcetype="snow:incident"` (category, opened_at)
- **SPL:**
```spl
index=web sourcetype="access_combined" status=200 uri="/help/*" earliest=-30d
| eval session=clientip."_".useragent
| stats dc(session) as help_sessions, count as article_views by uri
| appendcols [
    search index=itsm sourcetype="snow:incident" earliest=-30d
    | stats count as tickets_30d
]
| sort - article_views
| head 20
| table uri, help_sessions, article_views, tickets_30d
```
- **Implementation:** (1) Ensure help centre URLs are structured so `/help/` paths are easy to filter in web logs; (2) join or correlate weekly ticket counts by category with top article topics using a shared topic tag if available; (3) publish a monthly readout to the knowledge team listing articles with high views and categories where tickets remain high.
- **Visualization:** Bar chart (top articles by views), Table (URI performance), Line chart (help sessions vs tickets), Single value (help sessions per thousand tickets).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for ServiceNow](https://splunkbase.splunk.com/app/1928), [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### 23.8 Executive Dashboards & Business KPIs

**Primary App/TA:** Splunk DB Connect (Splunkbase 2686), Splunk ITSI (Splunkbase 1841), HEC.

**Data Sources:** Aggregated data from all business indexes, KV store with KPI definitions and targets, ERP/CRM/HRIS summary data via DB Connect.

---

### UC-23.8.1 · CEO/CFO Business Health Scorecard
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🐢 crawl
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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

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
- **CIM Models:** N/A

- **References:** [Splunk Enterprise Security](https://splunkbase.splunk.com/app/263), [Splunk ITSI](https://splunkbase.splunk.com/app/1841), [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.8.4 · Rule-of-40 and SaaS Unit Economics
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** SaaS, Technology
- **Splunk Pillar:** Observability
- **Value:** Combines revenue growth with profit margin into a single investor-friendly score so boards can see whether the company balances growth and discipline. We help finance and strategy teams spot quarters where efficiency slips without waiting for the full close package.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:erp_orders"` (revenue, order_date, order_status), `index=business` `sourcetype="dbx:gl_transactions"` (ebitda_amount, revenue_amount, period)
- **SPL:**
```spl
index=business sourcetype="dbx:erp_orders" order_status="booked" earliest=-270d latest=now()
| eval qn=ceil(tonumber(strftime(_time,"%m"))/3)
| eval quarter=strftime(_time,"%Y")."-Q".tostring(qn)
| stats sum(revenue) as q_revenue by quarter
| sort quarter
| streamstats window=1 current=f last(q_revenue) as prev_rev
| eval growth_pct=if(isnotnull(prev_rev) AND prev_rev>0, round(100*(q_revenue-prev_rev)/prev_rev,1), null())
| join type=left quarter [
    search index=business sourcetype="dbx:gl_transactions" earliest=-270d latest=now()
    | eval pe=coalesce(strptime(period,"%Y-%m-%d"),strptime(period."-01","%Y-%m-%d"))
    | eval qn=ceil(tonumber(strftime(pe,"%m"))/3)
    | eval quarter=strftime(pe,"%Y")."-Q".tostring(qn)
    | stats sum(ebitda_amount) as q_ebitda, sum(revenue_amount) as q_rev_gl by quarter
    | eval margin_pct=if(q_rev_gl>0, round(100*q_ebitda/q_rev_gl,1), null())
    | fields quarter, margin_pct
]
| eval rule_of_40=round(coalesce(growth_pct,0)+coalesce(margin_pct,0),1)
| table quarter, q_revenue, growth_pct, margin_pct, rule_of_40
```
- **Implementation:** (1) Align revenue and profit data from your enterprise resource planning system on the same fiscal calendar via DB Connect; (2) map the earnings before interest accounts used for margin; (3) refresh each quarter and compare rule-of-40 to board targets and peer benchmarks from your planning lookup.
- **Visualization:** Line chart (rule-of-40 over quarters), Table (growth and margin components), Single value (latest rule-of-40), Bar chart (margin vs growth stacked).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.8.5 · Customer Acquisition Cost and Payback Period
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Divides sales and marketing spend by new customers won so leadership sees whether growth is efficient or expensive. We help you estimate how many months a typical customer must stay to repay that investment, which guides budget cuts and pricing decisions.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC
- **Data Sources:** `index=business` `sourcetype="dbx:crm_opportunities"` (stage, customer_id, close_date, amount), `marketing_spend.csv` (month, spend)
- **SPL:**
```spl
index=business sourcetype="dbx:crm_opportunities" stage="Closed Won" earliest=-90d
| eval month=strftime(strptime(close_date,"%Y-%m-%d"),"%Y-%m")
| stats dc(customer_id) as new_customers, sum(amount) as booked_revenue by month
| join type=left month [
    | inputlookup marketing_spend.csv
    | stats sum(marketing_spend) as marketing_spend, sum(sales_spend) as sales_spend by month
]
| fillnull value=0 marketing_spend sales_spend
| eval total_spend=marketing_spend+sales_spend
| eval cac=if(new_customers>0, round(total_spend/new_customers,0), null())
| eval avg_first_year_revenue=if(new_customers>0, round(booked_revenue/new_customers,2), null())
| eval payback_months=if(avg_first_year_revenue>0 AND cac>0, round(cac/(avg_first_year_revenue/12),1), null())
| sort month
| table month, new_customers, total_spend, cac, avg_first_year_revenue, payback_months
```
- **Implementation:** (1) Load closed-won customers with first-order dates from customer relationship management via DB Connect; (2) combine marketing and allocated sales costs in `marketing_spend.csv` or separate lookups by month; (3) review monthly with the chief marketing officer and finance partner and set alert thresholds when payback months exceed policy.
- **Visualization:** Line chart (CAC and payback trend), Table (monthly detail), Single value (blended CAC), Bar chart (spend vs new customers).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.8.6 · Working Capital and Cash Conversion Cycle
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Business
- **Industry:** Manufacturing, Retail, Distribution
- **Splunk Pillar:** Observability
- **Value:** Combines days inventory outstanding, days sales outstanding, and days payables outstanding into a cash conversion view so treasury can see how long cash is tied up in operations. We help you prioritise collections, stock, and supplier terms when liquidity is tight.
- **App/TA:** Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="dbx:inventory"` (sku, qty_on_hand, unit_cost), `index=business` `sourcetype="dbx:ar_invoices"` (amount, status), `index=business` `sourcetype="dbx:ap_invoices"` (amount, status), `index=business` `sourcetype="dbx:gl_transactions"` (revenue_amount, period)
- **SPL:**
```spl
index=business sourcetype="dbx:inventory" earliest=-1d@d latest=now()
| stats sum(eval(qty_on_hand*unit_cost)) as inventory_value
| appendcols [
    search index=business sourcetype="dbx:ar_invoices" status="open" earliest=-1d@d
    | stats sum(amount) as ar_open
]
| appendcols [
    search index=business sourcetype="dbx:ap_invoices" status="open" earliest=-1d@d
    | stats sum(amount) as ap_open
]
| appendcols [
    search index=business sourcetype="dbx:gl_transactions" earliest=-30d
    | stats sum(revenue_amount) as revenue_30d
]
| eval dio=if(revenue_30d>0, round(inventory_value/(revenue_30d/30),0), null())
| eval dso=if(revenue_30d>0, round(ar_open/(revenue_30d/30),0), null())
| eval dpo=if(revenue_30d>0, round(ap_open/(revenue_30d/30),0), null())
| eval ccc=round(dio+dso-dpo,0)
| table inventory_value, ar_open, ap_open, revenue_30d, dio, dso, dpo, ccc
```
- **Implementation:** (1) Schedule a daily snapshot from inventory, receivables, and payables tables through DB Connect using consistent valuation rules; (2) use trailing thirty-day revenue as the activity denominator unless your controller specifies otherwise; (3) alert treasury when the cash conversion cycle moves more than five days away from the rolling average.
- **Visualization:** Single value (CCC, DIO, DSO, DPO), Waterfall (components), Line chart (CCC trend), Table (daily snapshot history).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686), [Splunk ITSI](https://splunkbase.splunk.com/app/1841)

---

### 23.9 ESG & Sustainability Reporting

**Primary App/TA:** Splunk DB Connect (Splunkbase 2686), HEC (IoT/BMS integration), Splunk ITSI (Splunkbase 1841).

**Data Sources:** Building management system data (power meters, HVAC sensors via BACnet/Modbus), cloud provider sustainability APIs, fleet management telematics, travel booking system data, waste management logs, HR diversity data (anonymised).

---

### UC-23.9.1 · Carbon Footprint Tracking and Reduction Progress
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Wave:** 🐢 crawl
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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.9.2 · Energy Consumption and Efficiency by Facility
- **Criticality:** 🟡 Medium
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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.9.3 · Waste Diversion and Recycling Rate Tracking
- **Criticality:** 🟡 Medium
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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.9.4 · Water Consumption Monitoring and Conservation
- **Criticality:** 🟡 Medium
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
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.9.6 · Renewable Energy Share and Green Tariff Attribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Business, Compliance
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Shows what share of your electricity came from renewable contracts or on-site generation versus grid mix, so leaders can prove progress to investors and regulators. We help you tie tariff decisions to reported carbon outcomes instead of guessing after the fact.
- **App/TA:** Splunk DB Connect (Splunkbase 2686), HEC (utility data)
- **Data Sources:** `index=facilities` `sourcetype="power_meter"` (site, kwh, contract_type, timestamp), `renewable_contracts.csv` (site, renewable_pct, period)
- **SPL:**
```spl
index=facilities sourcetype="power_meter" earliest=-30d
| bin _time span=1d
| stats sum(kwh) as daily_kwh by _time, site, contract_type
| stats sum(daily_kwh) as total_kwh by site, contract_type
| lookup renewable_contracts.csv site OUTPUT renewable_pct
| eval renewable_kwh=round(total_kwh * coalesce(renewable_pct,0) / 100, 2)
| eval grid_kwh=total_kwh-renewable_kwh
| stats sum(renewable_kwh) as sum_renewable, sum(grid_kwh) as sum_grid, sum(total_kwh) as sum_total by site
| eval renewable_share_pct=if(sum_total>0, round(100*sum_renewable/sum_total, 1), null())
| sort - renewable_share_pct
| table site, sum_total, sum_renewable, sum_grid, renewable_share_pct
```
- **Implementation:** (1) Tag each meter or site with contract type and ingest utility invoices or supplier files via DB Connect; (2) maintain `renewable_contracts.csv` with the certified renewable percentage per site and period; (3) schedule monthly and compare renewable share to your science-based or net-zero milestones.
- **Visualization:** Stacked bar (renewable vs grid kWh by site), Single value (portfolio renewable %), Table (site-level mix), Line chart (renewable share trend).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---

### UC-23.9.7 · Scope 3 Commuting and Hybrid Work Emissions
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Business, Compliance
- **Industry:** Cross-industry
- **Splunk Pillar:** Observability
- **Value:** Estimates emissions from employee commuting and hybrid office attendance using badge and survey data, which many disclosure frameworks now ask for under Scope 3. We help workplace and sustainability teams see which locations and commute modes drive the largest footprint so travel and office policies can be adjusted fairly.
- **App/TA:** HEC (badge/HR systems), Splunk DB Connect (Splunkbase 2686)
- **Data Sources:** `index=business` `sourcetype="commute_survey"` (employee_id, site, mode, distance_km, days_per_week), `commute_emission_factors.csv` (mode, kg_co2_per_km)
- **SPL:**
```spl
index=business sourcetype="commute_survey" earliest=-90d
| eval weekly_km=distance_km*days_per_week
| lookup commute_emission_factors.csv mode OUTPUT kg_co2_per_km
| eval weekly_kg_co2=round(weekly_km * coalesce(kg_co2_per_km, 0.12), 2)
| stats sum(weekly_kg_co2) as total_kg_co2, dc(employee_id) as respondents, avg(weekly_km) as avg_weekly_km by site, mode
| eval tonnes_co2=round(total_kg_co2/1000, 2)
| sort - tonnes_co2
| table site, mode, respondents, avg_weekly_km, tonnes_co2
```
- **Implementation:** (1) Send anonymised commute surveys or badge-based attendance summaries to Splunk via HEC on a schedule employees understand; (2) keep `commute_emission_factors.csv` aligned with your country’s published factors; (3) run quarterly and review results with facilities and people leaders before publishing ESG narratives.
- **Visualization:** Bar chart (tonnes CO2 by commute mode), Table (site and mode breakdown), Pie chart (mode share), Single value (total estimated commuting tonnes).
- **CIM Models:** N/A

- **References:** [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)

---
