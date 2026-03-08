## 20. Cost & Capacity Management

### 20.1 Cloud Cost Monitoring

**Splunk Add-on:** Cloud provider TAs, CUR/billing export ingestion

### UC-20.1.1 · Daily Spend Trending

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Cloud costs can spiral without visibility. Daily spend trending by service, account, and tag provides the financial governance foundation — enabling teams to understand where money goes, spot trends early, and make informed optimization decisions.
- **App/TA:** `Splunk Add-on for AWS` (CUR ingestion), `Splunk Add-on for Microsoft Cloud Services`, `Splunk Add-on for Google Cloud Platform`
- **Data Sources:** AWS Cost and Usage Report (CUR), Azure Cost Management export, GCP Billing export
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| timechart span=1d sum(cost) as daily_spend by lineItem_ProductCode
| addtotals
| rename Total as total_daily_spend
```
- **Implementation:** Ingest AWS CUR, Azure Cost export, or GCP billing data daily. Parse cost line items by service, account, region, and tags. Build daily/weekly/monthly spend reports. Set trending alerts when daily spend exceeds 7-day rolling average by >20%. Enable tag-based cost allocation from day one.
- **Visualization:** Timechart (daily spend trending), Stacked bar chart (spend by service), Table (top 10 services by cost), Single value (today's spend vs yesterday).
- **CIM Models:** N/A

### UC-20.1.2 · Cost Anomaly Detection

- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Anomaly
- **Value:** Unexpected cost spikes from runaway instances, misconfigured autoscaling, or crypto-mining attacks can generate thousands in charges within hours. Automated anomaly detection catches these events before they become budget disasters.
- **App/TA:** `Splunk Add-on for AWS`, cloud billing TAs
- **Data Sources:** Billing data with historical trending
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| timechart span=1d sum(cost) as daily_spend by lineItem_UsageAccountId
| foreach * [eval <<FIELD>>=if(<<FIELD>>="", 0, <<FIELD>>)]
| addtotals
| predict Total as predicted_spend algorithm=LLP5 future_timespan=1
| eval anomaly=if(Total > 'upper95(predicted_spend)', "Anomaly", "Normal")
| where anomaly="Anomaly"
```
- **Implementation:** Build 30-day baseline of daily spending per account and service. Use Splunk `predict` command with LLP5 algorithm for anomaly detection. Alert when actual spend exceeds upper 95% confidence interval. Investigate anomalies by drilling into specific services and resources. Integrate with incident management for cost-related incidents.
- **Visualization:** Timechart (actual vs predicted spend), Table (anomaly details), Single value (current anomaly count), Alert indicator (anomaly detected).
- **CIM Models:** N/A

### UC-20.1.3 · Reserved Instance Utilization

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Reserved Instances and Savings Plans represent upfront commitments. Monitoring utilization ensures you're getting value from these purchases. Low utilization means wasted money; gaps in coverage mean missed savings opportunities.
- **App/TA:** `Splunk Add-on for AWS`, billing TAs
- **Data Sources:** AWS CUR (reservation fields), Azure reservation utilization
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| search reservation_ReservationARN!=""
| stats sum(reservation_UnusedAmortizedUpfrontFeeForBillingPeriod) as unused_upfront, sum(reservation_EffectiveCost) as effective_cost, sum(reservation_UnusedRecurringFee) as unused_recurring by reservation_ReservationARN, lineItem_ProductCode
| eval utilization_pct=round((1-(unused_upfront+unused_recurring)/effective_cost)*100, 1)
| sort utilization_pct
| table reservation_ReservationARN, lineItem_ProductCode, effective_cost, unused_upfront, unused_recurring, utilization_pct
```
- **Implementation:** Parse RI/Savings Plan utilization from CUR data. Track utilization percentage per reservation. Alert when any RI falls below 80% utilization for 7+ consecutive days. Report on coverage gaps where on-demand spend could be covered by reservations. Review expiring reservations 30 days before expiry.
- **Visualization:** Gauge (overall RI utilization), Bar chart (utilization by reservation), Table (underutilized RIs), Timechart (utilization trending).
- **CIM Models:** N/A

### UC-20.1.4 · Idle Resource Identification

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Idle resources (running but unused instances, unattached volumes, unused load balancers) are pure waste. Identifying and eliminating them is the quickest path to cloud cost savings, often yielding 20-30% reduction.
- **App/TA:** `Splunk Add-on for AWS`, cloud monitoring TAs
- **Data Sources:** CloudWatch/Azure Monitor metrics + billing data
- **SPL:**
```spl
index=cloud_metrics sourcetype="aws:cloudwatch"
| search metric_name="CPUUtilization"
| stats avg(Average) as avg_cpu, max(Maximum) as peak_cpu by dimensions.InstanceId
| where avg_cpu < 5 AND peak_cpu < 10
| lookup aws_instance_details InstanceId as dimensions.InstanceId OUTPUT instance_type, monthly_cost, tags
| eval waste_monthly=monthly_cost
| sort -waste_monthly
| table dimensions.InstanceId, instance_type, avg_cpu, peak_cpu, monthly_cost, tags
```
- **Implementation:** Correlate CloudWatch CPU/network metrics with billing data. Define idle thresholds: CPU avg <5%, network <1MB/day for 7+ days. Include unattached EBS volumes, idle ELBs, unused Elastic IPs. Generate weekly idle resource reports with estimated savings. Route to resource owners for action.
- **Visualization:** Table (idle resources with cost), Bar chart (waste by service), Single value (total monthly waste), Pie chart (waste by team/tag).
- **CIM Models:** N/A

### UC-20.1.5 · Budget Threshold Alerting

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Budget alerts prevent overspend by notifying stakeholders at defined thresholds (50%, 75%, 90%, 100%). Combined with forecast-based alerts, teams can take corrective action before exceeding approved budgets.
- **App/TA:** `Splunk Add-on for AWS`, cloud billing TAs
- **Data Sources:** Billing data, budget definitions (lookup)
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| stats sum(cost) as mtd_spend by lineItem_UsageAccountId
| lookup cloud_budgets account_id as lineItem_UsageAccountId OUTPUT budget_amount, owner_email
| eval budget_pct=round((mtd_spend/budget_amount)*100, 1)
| eval status=case(budget_pct>=100, "Exceeded", budget_pct>=90, "Critical", budget_pct>=75, "Warning", budget_pct>=50, "On Track", 1==1, "Under Budget")
| sort -budget_pct
| table lineItem_UsageAccountId, owner_email, budget_amount, mtd_spend, budget_pct, status
```
- **Implementation:** Define budgets per account/team in a Splunk lookup table. Calculate MTD spend against budgets daily. Alert at 50%, 75%, 90%, and 100% thresholds. Include forecast-based alerts (projected to exceed budget). Escalate to management when budgets are exceeded.
- **Visualization:** Gauge (budget consumption), Table (budget status by account), Timechart (MTD spend vs budget line), Single value (accounts over budget).
- **CIM Models:** N/A

### UC-20.1.6 · Cost Allocation by Team

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Breaking down cloud costs by team/department via tagging creates accountability and enables chargeback/showback. Teams that see their own costs make better optimization decisions, driving organization-wide cost efficiency.
- **App/TA:** `Splunk Add-on for AWS`, cloud billing TAs
- **Data Sources:** CUR with tag data, organizational mapping
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| eval cost=tonumber(lineItem_UnblendedCost)
| eval team=coalesce('resourceTags_user_Team', 'resourceTags_user_team', "Untagged")
| stats sum(cost) as total_cost by team
| eventstats sum(total_cost) as grand_total
| eval cost_pct=round((total_cost/grand_total)*100, 1)
| sort -total_cost
| table team, total_cost, cost_pct
```
- **Implementation:** Enforce tagging policy requiring Team/Department/Environment tags. Parse resource tags from billing data. Calculate cost allocation by team, department, and environment. Report on untagged resources (assign to "Unknown" for follow-up). Generate monthly chargeback reports.
- **Visualization:** Pie chart (cost by team), Bar chart (team costs with trending), Table (detailed allocation), Single value (untagged cost percentage).
- **CIM Models:** N/A

### UC-20.1.7 · Spot/Preemptible Instance Tracking

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Spot instances offer significant savings (60-90%) but can be interrupted. Tracking interruptions, savings achieved, and workload placement ensures teams maximize savings while maintaining application resilience.
- **App/TA:** `Splunk Add-on for AWS`, EC2 event logs
- **Data Sources:** EC2 spot instance events, billing data
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail"
| search eventName="BidEvictedEvent" OR eventName="SpotInstanceInterruption"
| stats count as interruptions by requestParameters.instanceId, requestParameters.instanceType, userIdentity.arn
| lookup spot_savings instance_id as requestParameters.instanceId OUTPUT on_demand_cost, spot_cost
| eval savings=on_demand_cost-spot_cost
| eval savings_pct=round((savings/on_demand_cost)*100, 1)
| table requestParameters.instanceId, requestParameters.instanceType, interruptions, on_demand_cost, spot_cost, savings_pct
```
- **Implementation:** Track spot instance lifecycle events via CloudTrail. Monitor interruption frequency by instance type and AZ. Calculate savings vs on-demand pricing. Alert on interruption rate spikes affecting critical workloads. Report monthly spot savings to justify continued spot adoption.
- **Visualization:** Bar chart (interruptions by type), Timechart (interruption frequency), Single value (monthly spot savings), Table (instance interruption details).
- **CIM Models:** N/A

### UC-20.1.8 · Data Transfer Cost Analysis

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Data transfer costs are often the most surprising cloud bill item. Inter-region, cross-AZ, and internet egress charges add up quickly. Identifying the biggest transfer flows enables architectural optimization to reduce costs significantly.
- **App/TA:** `Splunk Add-on for AWS`, cloud billing TAs
- **Data Sources:** CUR data transfer line items, VPC flow logs
- **SPL:**
```spl
index=cloud_billing sourcetype="aws:billing:cur"
| search lineItem_UsageType="*DataTransfer*" OR lineItem_UsageType="*Bytes*"
| eval cost=tonumber(lineItem_UnblendedCost)
| eval transfer_type=case(
    lineItem_UsageType LIKE "%InterRegion%", "Inter-Region",
    lineItem_UsageType LIKE "%Out-Bytes%", "Internet Egress",
    lineItem_UsageType LIKE "%In-Bytes%", "Internet Ingress",
    lineItem_UsageType LIKE "%Regional%", "Cross-AZ",
    1==1, "Other")
| stats sum(cost) as transfer_cost, sum(lineItem_UsageAmount) as gb_transferred by transfer_type, lineItem_ProductCode
| sort -transfer_cost
```
- **Implementation:** Parse data transfer line items from CUR. Categorize by transfer type (egress, inter-region, cross-AZ). Identify top services and resources by transfer cost. Correlate with VPC flow logs for detailed flow analysis. Recommend architecture changes (CDN, VPC endpoints, same-AZ placement) for top cost drivers.
- **Visualization:** Pie chart (cost by transfer type), Bar chart (top services by transfer cost), Timechart (transfer cost trending), Table (detailed transfer breakdown).
- **CIM Models:** N/A

### 20.2 Capacity Planning

**Splunk Add-on:** Cross-referencing infrastructure metrics with trending/forecasting

### UC-20.2.1 · Compute Capacity Forecasting

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Running out of compute capacity causes provisioning failures and performance degradation. Forecasting when CPU and memory will be exhausted enables proactive procurement or scaling, avoiding emergency purchases at premium cost.
- **App/TA:** Infrastructure monitoring TAs (various), Splunk `predict` command
- **Data Sources:** Host performance metrics (CPU, memory utilization)
- **SPL:**
```spl
index=infrastructure sourcetype="Perfmon:Processor" OR sourcetype="cpu"
| timechart span=1d avg(cpu_load_percent) as avg_cpu by host
| predict avg_cpu as predicted_cpu algorithm=LLP5 future_timespan=30
| eval days_to_threshold=if('upper95(predicted_cpu)'>90, "Within 30 days", "OK")
```
- **Implementation:** Collect CPU and memory metrics from all hosts. Aggregate to daily averages for trending. Use Splunk `predict` with LLP5 for 30/60/90-day forecasting. Set alerts when forecast predicts >90% utilization within 30 days. Report quarterly on capacity headroom across infrastructure tiers.
- **Visualization:** Timechart (utilization with forecast overlay), Table (hosts approaching capacity), Gauge (current vs capacity), Single value (days to threshold).
- **CIM Models:** N/A

### UC-20.2.2 · Storage Growth Forecasting

- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Storage procurement has lead times. Forecasting growth trends enables timely ordering of additional capacity, preventing the emergency of running out of storage space that causes application outages and data loss.
- **App/TA:** Storage TAs (various), Splunk `predict` command
- **Data Sources:** Storage capacity metrics from SAN/NAS/HCI/cloud
- **SPL:**
```spl
index=storage sourcetype="storage:capacity"
| timechart span=1d latest(used_pct) as used_pct by storage_system
| predict used_pct as predicted_pct algorithm=LLP5 future_timespan=90
| eval forecast_90d='predicted_pct+90d'
| where forecast_90d > 85
```
- **Implementation:** Collect storage capacity metrics daily from all storage platforms. Build growth rate trends per volume/pool. Use Splunk predict for 90-day forecasting. Alert when projected usage exceeds 85% within 90 days. Initiate procurement workflow based on projected needs.
- **Visualization:** Timechart (usage with forecast), Table (systems approaching capacity), Gauge (current utilization), Single value (days to threshold).
- **CIM Models:** N/A

### UC-20.2.3 · Network Bandwidth Trending

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Network bandwidth constraints cause application latency and packet loss. Trending WAN/LAN utilization enables planned upgrades during maintenance windows rather than emergency bandwidth additions during business-impacting congestion.
- **App/TA:** Network monitoring TAs, SNMP
- **Data Sources:** Interface utilization metrics (SNMP, streaming telemetry)
- **SPL:**
```spl
index=network sourcetype="snmp:interface"
| eval util_pct=round((ifHCInOctets_rate*8/ifHighSpeed/1000000)*100, 2)
| timechart span=1h avg(util_pct) as avg_util, max(util_pct) as peak_util by interface_name
| predict avg_util as predicted_util algorithm=LLP5 future_timespan=30
```
- **Implementation:** Collect interface utilization via SNMP every 5 minutes. Aggregate to hourly peaks and daily averages. Trend key WAN links and data center interconnects. Alert when trending projects >80% utilization within 30 days. Plan circuit upgrades based on business growth forecasts.
- **Visualization:** Timechart (bandwidth trending with forecast), Table (high-utilization links), Gauge (current peak utilization), Bar chart (top links by utilization).
- **CIM Models:** N/A

### UC-20.2.4 · License Utilization Tracking

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Software licenses represent significant IT spend. Tracking usage vs entitlements identifies under-licensed risks (compliance violations) and over-licensed waste (unnecessary spend). Right-sizing licenses can save 15-30% of software costs.
- **App/TA:** Custom scripted inputs, vendor license APIs
- **Data Sources:** License server logs, vendor API data, entitlement records
- **SPL:**
```spl
index=licenses sourcetype="license:usage"
| stats latest(used_licenses) as used, latest(total_licenses) as total by product, vendor, license_type
| eval utilization_pct=round((used/total)*100, 1)
| eval status=case(utilization_pct>=95, "At Risk", utilization_pct>=80, "High Use", utilization_pct<50, "Underutilized", 1==1, "Healthy")
| sort -utilization_pct
| table product, vendor, license_type, used, total, utilization_pct, status
```
- **Implementation:** Collect license usage data from license servers (FlexLM, RLM) and vendor APIs. Maintain entitlement records in a lookup table. Track daily peak concurrent usage. Alert at 90% consumption (buy more) and flag <50% utilization (optimize). Generate quarterly true-up reports.
- **Visualization:** Gauge (license utilization), Table (license inventory with status), Bar chart (utilization by product), Timechart (usage trending).
- **CIM Models:** N/A

### UC-20.2.5 · Right-Sizing Recommendations

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Over-provisioned VMs and instances waste compute and money. Right-sizing analysis compares actual resource usage against allocated resources, identifying instances that can be downsized without impacting performance — typically saving 20-40%.
- **App/TA:** Cloud and virtualization TAs, performance metrics
- **Data Sources:** Performance metrics vs resource allocation data
- **SPL:**
```spl
index=infrastructure (sourcetype="vmware:perf:cpu" OR sourcetype="vmware:perf:mem")
| stats avg(cpu_usage_pct) as avg_cpu, p95(cpu_usage_pct) as p95_cpu, avg(mem_usage_pct) as avg_mem, p95(mem_usage_pct) as p95_mem by vm_name
| lookup vm_allocation vm_name OUTPUT allocated_vcpu, allocated_mem_gb, instance_type
| eval cpu_rightsized=case(p95_cpu<25, "Downsize", p95_cpu>90, "Upsize", 1==1, "Right-sized")
| eval mem_rightsized=case(p95_mem<25, "Downsize", p95_mem>90, "Upsize", 1==1, "Right-sized")
| where cpu_rightsized="Downsize" OR mem_rightsized="Downsize"
| table vm_name, instance_type, allocated_vcpu, avg_cpu, p95_cpu, cpu_rightsized, allocated_mem_gb, avg_mem, p95_mem, mem_rightsized
```
- **Implementation:** Collect 30+ days of CPU and memory utilization per VM/instance. Compare P95 utilization against allocated resources. Generate right-sizing recommendations based on workload patterns. Exclude burst workloads from analysis. Calculate estimated savings per recommendation.
- **Visualization:** Table (right-sizing recommendations with savings), Bar chart (waste by team), Scatter plot (allocated vs used), Single value (total potential savings).
- **CIM Models:** N/A

### UC-20.2.6 · Database Growth Projection

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Databases that run out of space cause application outages. Forecasting database growth enables proactive storage expansion, archive planning, and helps DBAs plan maintenance windows for data lifecycle operations.
- **App/TA:** Database monitoring TAs, `Splunk DB Connect`
- **Data Sources:** Database size metrics, tablespace utilization
- **SPL:**
```spl
index=database sourcetype="db:capacity"
| timechart span=1d latest(db_size_gb) as current_size by db_name
| predict current_size as predicted_size algorithm=LLP5 future_timespan=90
| eval growth_rate_gb_per_day=round(('predicted_size+30d'-current_size)/30, 2)
| where 'predicted_size+90d' > max_size*0.85
```
- **Implementation:** Collect database size metrics daily from all platforms. Track per-database and per-tablespace growth. Use Splunk predict for 90-day growth forecasting. Alert when projected size exceeds 85% of allocated space within 90 days. Plan archival or expansion based on projections.
- **Visualization:** Timechart (database size with forecast), Table (databases approaching limits), Gauge (current utilization), Bar chart (growth rate by database).
- **CIM Models:** N/A

### UC-20.2.7 · Seasonal Capacity Modeling

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Capacity
- **Value:** Many businesses have predictable seasonal patterns (retail holidays, fiscal year-end, enrollment periods). Building seasonal capacity models ensures infrastructure scales proactively for peak periods rather than reactively during customer-impacting events.
- **App/TA:** Infrastructure TAs, Splunk MLTK (Machine Learning Toolkit)
- **Data Sources:** Historical performance data (12+ months)
- **SPL:**
```spl
index=infrastructure sourcetype="perf:summary"
| eval day_of_year=strftime(_time, "%j")
| eval week_of_year=strftime(_time, "%V")
| stats avg(cpu_pct) as avg_cpu, avg(mem_pct) as avg_mem, avg(req_per_sec) as avg_rps by week_of_year
| append [| inputlookup previous_year_seasonal_data]
| stats avg(avg_cpu) as seasonal_cpu, avg(avg_mem) as seasonal_mem, avg(avg_rps) as seasonal_rps by week_of_year
| eval next_year_projected=seasonal_rps*1.15
```
- **Implementation:** Collect 12+ months of performance data for seasonal analysis. Identify recurring patterns (daily, weekly, monthly, seasonal). Build seasonal baseline models using Splunk MLTK or predict. Apply growth factor to historical peaks for next-year projections. Plan capacity expansions 2-3 months ahead of predicted peaks.
- **Visualization:** Timechart (year-over-year seasonal overlay), Area chart (seasonal patterns), Table (peak week projections), Line chart (actual vs seasonal model).
- **CIM Models:** N/A

### UC-20.2.8 · IP Address Space Utilization

- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** IP address exhaustion causes provisioning failures for new VMs, containers, and services. Monitoring IP pool utilization across subnets and VLANs enables proactive network planning and avoids emergency re-addressing projects.
- **App/TA:** IPAM/DHCP TAs, custom scripted inputs
- **Data Sources:** DHCP/IPAM data, subnet allocation records
- **SPL:**
```spl
index=network sourcetype="ipam:pool"
| stats latest(total_ips) as total, latest(allocated_ips) as allocated, latest(available_ips) as available by subnet, vlan, location
| eval used_pct=round((allocated/total)*100, 1)
| eval status=case(used_pct>=90, "Critical", used_pct>=75, "Warning", used_pct>=50, "Normal", 1==1, "Low Use")
| sort -used_pct
| table subnet, vlan, location, total, allocated, available, used_pct, status
```
- **Implementation:** Ingest IPAM/DHCP pool data daily. Track allocation rates per subnet, VLAN, and location. Alert at 75% warning and 90% critical utilization. Plan subnet expansions or new VLAN creation based on utilization trends. Report on unused allocations that could be reclaimed.
- **Visualization:** Table (subnet utilization), Bar chart (utilization by location), Heatmap (subnet usage map), Gauge (overall IP utilization).
- **CIM Models:** N/A

---

### UC-20.2.9 · Cloud Commitment and Savings Plan Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Underutilized commitments or savings plans leave money on the table. Monitoring utilization and coverage supports optimization and renewal decisions.
- **App/TA:** AWS Cost Explorer, Azure Cost Management, CUDRI/savings plan data
- **Data Sources:** Commitment usage, savings plan coverage, hourly coverage %
- **SPL:**
```spl
index=cloud_cost sourcetype="aws:savings_plan"
| stats latest(utilization_pct) as util_pct, latest(coverage_pct) as coverage by plan_id, commitment_type
| where util_pct < 80 OR coverage < 70
| table plan_id, commitment_type, util_pct, coverage
```
- **Implementation:** Ingest commitment and savings plan usage from cloud cost APIs. Alert when utilization or coverage drops below target. Report on commitment ROI and recommend size changes at renewal.
- **Visualization:** Gauge (utilization %), Table (plans below target), Line chart (coverage trend).
- **CIM Models:** N/A

---

### UC-20.2.10 · Anomalous Cost Spike by Service or Account
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Sudden cost spikes may indicate runaway resources, misconfiguration, or abuse. Early detection limits bill shock and supports incident response.
- **App/TA:** Cloud cost TAs, billing exports
- **Data Sources:** Daily cost by service, account, region
- **SPL:**
```spl
index=cloud_cost sourcetype="cost:daily"
| stats sum(cost) as daily_cost by service, account_id, _time span=1d
| eventstats avg(daily_cost) as avg_cost, stdev(daily_cost) as std_cost by service, account_id
| where daily_cost > (avg_cost + (3*std_cost))
| table service, account_id, daily_cost, avg_cost, std_cost
```
- **Implementation:** Ingest daily cost by dimensions. Compute baseline and standard deviation. Alert when cost exceeds 3× std dev. Report on top anomalies and trend. Correlate with resource and usage data.
- **Visualization:** Table (anomalous services/accounts), Line chart (cost vs baseline), Bar chart (spike magnitude).
- **CIM Models:** N/A

---

### UC-20.2.11 · Unused and Orphaned Resource Cost Attribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Unused disks, idle instances, and orphaned snapshots drive waste. Attributing cost to these resources supports cleanup and chargeback.
- **App/TA:** Cloud resource inventory, cost allocation tags
- **Data Sources:** Resource list with last used, cost, tags
- **SPL:**
```spl
index=cloud_cost sourcetype="resource:inventory"
| where (last_used_days > 30 OR state="stopped") AND cost > 0
| stats sum(cost) as waste_cost, count by resource_type, account_id
| sort -waste_cost
| table resource_type, account_id, count, waste_cost
```
- **Implementation:** Combine resource inventory (with last-used or state) and cost data. Flag idle or stopped resources older than threshold. Report on waste by type and account. Drive cleanup campaigns.
- **Visualization:** Table (waste by type and account), Bar chart (waste cost by resource type), Single value (total waste).
- **CIM Models:** N/A

---

### UC-20.2.12 · License and Subscription Consumption vs Entitlement
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Over-consumption causes true-up or compliance issues; under-consumption wastes spend. Monitoring usage vs entitlement supports optimization and renewal.
- **App/TA:** License management, SaaS usage APIs
- **Data Sources:** Entitlement count, consumed count, by product and pool
- **SPL:**
```spl
index=licenses sourcetype="license:usage"
| stats latest(entitled) as entitled, latest(consumed) as consumed by product, pool
| eval usage_pct=round((consumed/entitled)*100, 1)
| where usage_pct > 100 OR usage_pct < 50
| table product, pool, entitled, consumed, usage_pct
```
- **Implementation:** Ingest entitlement and consumption from license or SaaS tools. Alert when consumption exceeds entitlement or falls below target. Report on utilization by product and pool. Use for right-sizing at renewal.
- **Visualization:** Table (over/under utilized), Gauge (usage %), Bar chart (consumed vs entitled).
- **CIM Models:** N/A

---

### UC-20.2.13 · Cost Forecast vs Budget and Variance Alert
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Forecast over budget risks overspend; large variance indicates model or usage change. Monitoring forecast vs budget supports proactive control and reforecasting.
- **App/TA:** Cost forecasting tool, budget data
- **Data Sources:** Monthly forecast, budget, actuals to date
- **SPL:**
```spl
index=cloud_cost sourcetype="cost:forecast"
| stats latest(forecast_total) as forecast, latest(budget) as budget, latest(actual_ytd) as actual by account_id, month
| eval variance_pct=round((forecast-budget)/budget*100, 1)
| where variance_pct > 10 OR variance_pct < -20
| table account_id, month, forecast, budget, actual, variance_pct
```
- **Implementation:** Ingest forecast and budget. Compute variance. Alert when forecast exceeds budget by threshold or variance is large. Report on forecast accuracy and budget burn rate. Integrate with finance.
- **Visualization:** Table (accounts over budget), Gauge (variance %), Line chart (forecast vs budget trend).
- **CIM Models:** N/A

---

## Summary Statistics

| Category | Subcategories | Use Cases |
|----------|:------------:|:---------:|
| 1. Server & Compute | 4 | 262 |
| 2. Virtualization | 3 | 23 |
| 3. Containers & Orchestration | 4 | 30 |
| 4. Cloud Infrastructure | 4 | 44 |
| 5. Network Infrastructure | 9 | 203 |
| 6. Storage & Backup | 4 | 28 |
| 7. Database & Data Platforms | 4 | 40 |
| 8. Application Infrastructure | 5 | 45 |
| 9. Identity & Access Management | 4 | 29 |
| 10. Security Infrastructure | 8 | 47 |
| 11. Email & Collaboration | 3 | 24 |
| 12. DevOps & CI/CD | 4 | 23 |
| 13. Observability & Monitoring | 3 | 28 |
| 14. IoT & OT | 4 | 74 |
| 15. DC Physical Infrastructure | 3 | 16 |
| 16. Service Management & ITSM | 2 | 15 |
| 17. Network Security & Zero Trust | 3 | 22 |
| 18. Data Center Fabric & SDN | 3 | 15 |
| 19. Compute Infrastructure (HCI) | 2 | 13 |
| 20. Cost & Capacity Management | 2 | 16 |
| **TOTAL** | **72** | **1001** |

---

*Generated: March 2026*
*Primary tools: Splunk Enterprise / Cloud with free Splunkbase add-ons. Premium exceptions noted (ITSI, ES).*
*Each use case includes: criticality rating, value description, recommended App/TA, data sources, SPL query, implementation guidance, and visualization recommendations.*
