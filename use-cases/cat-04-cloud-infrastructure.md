# 4. Cloud Infrastructure

## 4.1 Amazon Web Services (AWS)

**Primary App/TA:** Splunk Add-on for AWS (`Splunk_TA_aws`) — Free on Splunkbase; Splunk App for AWS (optional dashboards)

---

### UC-4.1.1 · Unauthorized API Calls
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** AccessDenied errors reveal reconnaissance activity, compromised credentials with insufficient permissions, or misconfigurations. Early indicator of attack or drift.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`, CloudTrail logs
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" errorCode="AccessDenied" OR errorCode="UnauthorizedAccess" OR errorCode="Client.UnauthorizedAccess"
| stats count by userIdentity.arn, eventName, sourceIPAddress, errorCode
| where count > 5
| sort -count
```
- **Implementation:** Configure CloudTrail to send logs to an S3 bucket. Set up the Splunk_TA_aws with an SQS-based S3 input for CloudTrail. Alert when a single principal gets >5 access denied errors in 10 minutes.
- **Visualization:** Table (principal, API call, source IP, count), Bar chart by principal, Map (source IP GeoIP).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.1.2 · Root Account Usage
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** The AWS root account has unrestricted access and should never be used for daily operations. Any root activity is a critical security event.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" userIdentity.type="Root"
| table _time eventName sourceIPAddress userAgent errorCode
| sort -_time
```
- **Implementation:** CloudTrail must be enabled in all regions. Create a critical real-time alert on any event where `userIdentity.type=Root`. Exclude expected events (e.g., automated billing).
- **Visualization:** Events list (critical alert), Single value (root events last 30d), Timeline.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.1.3 · Security Group Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Security group changes can expose services to the internet. Unauthorized modifications are a primary attack vector and compliance violation.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventName="AuthorizeSecurityGroupIngress" OR eventName="AuthorizeSecurityGroupEgress" OR eventName="RevokeSecurityGroup*"
| spath output=rules path=requestParameters.ipPermissions.items{}
| table _time userIdentity.arn eventName requestParameters.groupId rules sourceIPAddress
| sort -_time
```
- **Implementation:** Alert on any security group modification. Extra-critical alert when `0.0.0.0/0` is added as a source (exposes to internet). Correlate with change tickets.
- **Visualization:** Table (who, what, when), Timeline, Single value (changes last 24h).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.1.4 · IAM Policy Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** IAM policy changes affect who can do what across the entire AWS account. Unauthorized policy attachments can grant admin access.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" (eventName="CreatePolicy" OR eventName="AttachUserPolicy" OR eventName="AttachRolePolicy" OR eventName="PutUserPolicy" OR eventName="PutRolePolicy" OR eventName="CreateRole")
| table _time userIdentity.arn eventName requestParameters.policyArn requestParameters.roleName
| sort -_time
```
- **Implementation:** Alert on all IAM policy modifications. Critical alert when AdministratorAccess or PowerUserAccess policies are attached. Track with change management.
- **Visualization:** Table, Timeline, Bar chart by event type.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.1.5 · Console Login Without MFA
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Console access without MFA is a security risk — compromised passwords alone can grant full account access. Most compliance frameworks require MFA.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventName="ConsoleLogin" responseElements.ConsoleLogin="Success"
| eval mfa_used = if(additionalEventData.MFAUsed="Yes", "Yes", "No")
| where mfa_used="No"
| table _time userIdentity.arn sourceIPAddress mfa_used
| sort -_time
```
- **Implementation:** Monitor ConsoleLogin events. Alert on successful console logins where MFA is not used. Exclude service accounts that authenticate via SSO (which has its own MFA).
- **Visualization:** Table (user, source IP, MFA status), Pie chart (MFA vs. no-MFA), Single value.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.1.6 · EC2 Instance State Changes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Tracks instance lifecycle for audit and change management. Unexpected terminations indicate accidents, auto-scaling issues, or attacks.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" (eventName="RunInstances" OR eventName="TerminateInstances" OR eventName="StopInstances" OR eventName="StartInstances")
| table _time userIdentity.arn eventName requestParameters.instancesSet.items{}.instanceId responseElements.instancesSet.items{}.currentState.name
| sort -_time
```
- **Implementation:** Forward CloudTrail events. Create daily audit report of EC2 lifecycle events. Alert on terminations of tagged production instances.
- **Visualization:** Table (timeline), Bar chart (events by type per day), Line chart (instance count trending).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.1.7 · S3 Bucket Policy Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** S3 bucket policy changes can expose sensitive data to the public internet. One of the most common cloud security incidents.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" (eventName="PutBucketPolicy" OR eventName="PutBucketAcl" OR eventName="PutBucketPublicAccessBlock" OR eventName="DeleteBucketPolicy")
| table _time userIdentity.arn eventName requestParameters.bucketName
| sort -_time
```
- **Implementation:** Critical alert on any bucket policy change. Extra-critical when `PutBucketPublicAccessBlock` is disabled or when ACLs grant public access. Integrate with AWS Config for continuous compliance.
- **Visualization:** Events list (critical), Table, Single value (policy changes last 7d).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.1.8 · GuardDuty Finding Ingestion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** GuardDuty provides ML-powered threat detection for AWS accounts. Centralizing findings in Splunk enables correlation with other security data.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch:guardduty`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:guardduty"
| spath output=severity path=detail.severity
| spath output=finding_type path=detail.type
| where severity >= 7
| table _time finding_type severity detail.title detail.description
| sort -severity
```
- **Implementation:** Enable GuardDuty in all regions. Configure CloudWatch Events rule to forward findings to an SNS topic or S3. Ingest via Splunk_TA_aws. Alert on High/Critical findings (severity ≥7).
- **Visualization:** Table by severity, Bar chart (finding types), Trend line (findings over time), Single value.
- **CIM Models:** N/A

---

### UC-4.1.9 · VPC Flow Log Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** VPC Flow Logs provide network-level visibility into all traffic. Detects rejected traffic, data exfiltration, lateral movement, and network anomalies.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatchlogs:vpcflow`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatchlogs:vpcflow" action="REJECT"
| stats count by src_ip, dest_ip, dest_port, protocol
| sort -count
| head 20
```
- **Implementation:** Enable VPC Flow Logs on all VPCs (send to S3 or CloudWatch Logs). Ingest via Splunk_TA_aws. Create dashboards for rejected traffic, top talkers, and unusual port activity.
- **Visualization:** Table (top rejected flows), Sankey diagram (source to destination), Timechart, Map.
- **CIM Models:** N/A

---

### UC-4.1.10 · EC2 Performance Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** CloudWatch metrics provide host-level performance data without agents. Baseline trending for capacity planning and anomaly detection.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (EC2 namespace)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" metric_name="CPUUtilization" namespace="AWS/EC2"
| timechart span=1h avg(Average) as avg_cpu by metric_dimensions
| where avg_cpu > 80
```
- **Implementation:** Configure CloudWatch metric collection in Splunk_TA_aws for EC2 namespace. Collect CPUUtilization, NetworkIn/Out, DiskReadOps, DiskWriteOps. Set polling interval (300s minimum).
- **Visualization:** Line chart per instance, Heatmap across fleet, Gauge.
- **CIM Models:** N/A

---

### UC-4.1.11 · RDS Performance Insights
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Database performance issues directly impact application experience. Monitoring connections, CPU, IOPS, and replica lag catches problems before users notice.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (RDS namespace), RDS logs
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" (metric_name="CPUUtilization" OR metric_name="DatabaseConnections" OR metric_name="ReadLatency" OR metric_name="ReplicaLag")
| timechart span=5m avg(Average) by metric_name, DBInstanceIdentifier
```
- **Implementation:** Enable CloudWatch metric collection for RDS namespace. Also forward RDS logs (slow query, error, general) to Splunk via CloudWatch Logs. Alert on ReplicaLag >30s, CPU >80%, or connection count nearing max.
- **Visualization:** Multi-metric line chart, Gauge (connections vs. max), Table.
- **CIM Models:** N/A

---

### UC-4.1.12 · Lambda Error Rate Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Lambda errors affect serverless application reliability. Timeouts indicate functions need more memory/time. Throttling means concurrency limits are hit.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (Lambda namespace), Lambda logs
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" (metric_name="Errors" OR metric_name="Throttles" OR metric_name="Duration")
| timechart span=5m sum(Sum) by metric_name, FunctionName
```
- **Implementation:** Collect CloudWatch metrics for Lambda namespace. Forward Lambda function logs via CloudWatch Logs. Alert on error rate >5% or any throttling events.
- **Visualization:** Line chart (errors/invocations over time), Bar chart (top error functions), Single value (error rate %).
- **CIM Models:** N/A

---

### UC-4.1.13 · EKS/ECS Cluster Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Managed container orchestration health ensures application workloads are running correctly across the AWS compute fabric.
- **App/TA:** `Splunk_TA_aws`, Splunk OTel Collector
- **Data Sources:** CloudWatch EKS/ECS metrics, container insights
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ECS" metric_name="CPUUtilization"
| timechart span=5m avg(Average) by ClusterName, ServiceName
```
- **Implementation:** Enable Container Insights for EKS/ECS. Collect metrics via CloudWatch. For deeper Kubernetes visibility in EKS, deploy Splunk OTel Collector as described in Category 3.2.
- **Visualization:** Line chart per service, Cluster status panel, Table.
- **CIM Models:** N/A

---

### UC-4.1.14 · Cost Anomaly Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Anomaly
- **Value:** Unexpected spend spikes indicate runaway resources, cryptomining attacks, or misconfigured services. Catching anomalies early saves money.
- **App/TA:** `Splunk_TA_aws`, AWS Cost and Usage Report (CUR)
- **Data Sources:** `sourcetype=aws:billing` or CUR data
- **SPL:**
```spl
index=aws sourcetype="aws:billing"
| timechart span=1d sum(BlendedCost) as daily_cost by ProductName
| eventstats avg(daily_cost) as avg_cost, stdev(daily_cost) as stdev_cost by ProductName
| eval threshold = avg_cost + (2 * stdev_cost)
| where daily_cost > threshold
```
- **Implementation:** Enable CUR reports to S3. Ingest via Splunk_TA_aws (billing input). Calculate daily baselines per service. Alert when daily spend exceeds 2 standard deviations from the 30-day average.
- **Visualization:** Line chart (daily spend with threshold), Table (anomalous services), Stacked area (spend by service).
- **CIM Models:** N/A

---

### UC-4.1.15 · Config Compliance Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** AWS Config rules continuously evaluate resource compliance against security best practices. Non-compliant resources are attack surface.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:config:notification`
- **SPL:**
```spl
index=aws sourcetype="aws:config:notification" configRuleList{}.complianceType="NON_COMPLIANT"
| stats count by resourceType, resourceId, configRuleList{}.configRuleName
| sort -count
```
- **Implementation:** Enable AWS Config with rules (e.g., CIS Benchmark). Forward Config notifications to SNS/S3 and ingest in Splunk. Dashboard showing compliance score per rule. Alert on newly non-compliant critical resources.
- **Visualization:** Table (resource, rule, status), Pie chart (compliant %), Bar chart by rule.
- **CIM Models:** N/A

---

### UC-4.1.16 · KMS Key Usage Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Encryption key usage audit ensures data protection compliance. Unusual key access patterns may indicate unauthorized data decryption.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" (eventName="Decrypt" OR eventName="Encrypt" OR eventName="GenerateDataKey") eventSource="kms.amazonaws.com"
| stats count by userIdentity.arn, requestParameters.keyId, eventName
| sort -count
```
- **Implementation:** CloudTrail captures all KMS API calls. Monitor for unusual Decrypt call volumes or access from unexpected principals. Track key rotation compliance.
- **Visualization:** Table (principal, key, action, count), Trend line, Bar chart.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.1.17 · Elastic IP Association
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Unassociated Elastic IPs cost money. Tracking associations supports inventory accuracy and cost management.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" (eventName="AllocateAddress" OR eventName="AssociateAddress" OR eventName="DisassociateAddress" OR eventName="ReleaseAddress")
| table _time userIdentity.arn eventName requestParameters.publicIp
| sort -_time
```
- **Implementation:** Forward CloudTrail. Create weekly report of EIP allocations vs. associations. Flag unassociated EIPs for cleanup.
- **Visualization:** Table, Single value (unassociated EIPs), Bar chart.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.1.18 · CloudFormation Stack Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **Value:** Drift means infrastructure no longer matches its declared template — manual changes have been made. This breaks IaC and causes inconsistencies.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail` (DetectStackDrift events)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventName="DetectStackDrift" OR eventName="DetectStackResourceDrift"
| spath output=drift_status path=responseElements.stackDriftStatus
| where drift_status="DRIFTED"
| table _time requestParameters.stackName drift_status
```
- **Implementation:** Schedule periodic drift detection via CloudFormation API or AWS Config rule. Forward detection results to Splunk. Alert on stacks in DRIFTED state.
- **Visualization:** Table (stack, drift status), Pie chart (drifted vs. in-sync), Status indicator.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.1.19 · WAF Blocked Request Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** WAF blocks reveal attack patterns targeting your applications. Analysis helps tune rules and understand the threat landscape.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:waf` (WAF logs via S3 or Kinesis)
- **SPL:**
```spl
index=aws sourcetype="aws:waf" action="BLOCK"
| stats count by terminatingRuleId, httpRequest.clientIp, httpRequest.uri
| sort -count
| head 20
```
- **Implementation:** Enable WAF logging to S3 or Kinesis Firehose. Ingest via Splunk_TA_aws. Analyze blocked requests by rule, source IP, URI, and user agent to identify attack patterns and false positives.
- **Visualization:** Table (rule, source, URI, count), Bar chart by rule, Map (source IPs), Timeline.
- **CIM Models:** N/A

---

### UC-4.1.20 · Reserved Instance Utilization
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Underutilized RIs waste money. Tracking RI coverage and utilization helps optimize commit spending vs. on-demand costs.
- **App/TA:** `Splunk_TA_aws`, CUR data
- **Data Sources:** `sourcetype=aws:billing` (CUR)
- **SPL:**
```spl
index=aws sourcetype="aws:billing" lineItem_LineItemType="DiscountedUsage" OR lineItem_LineItemType="RIFee"
| stats sum(lineItem_UsageAmount) as ri_hours, sum(lineItem_UnblendedCost) as ri_cost by reservation_ReservationARN, product_instanceType
| eval utilization_pct = round(ri_hours / expected_hours * 100, 1)
```
- **Implementation:** Ingest CUR data. Calculate RI utilization by comparing reserved hours against actual usage. Dashboard showing RI coverage percentage and waste. Review monthly.
- **Visualization:** Table (RI, type, utilization %), Gauge (overall utilization), Bar chart by instance type.
- **CIM Models:** N/A

---

## 4.2 Microsoft Azure

**Primary App/TA:** Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`) — Free on Splunkbase

---

### UC-4.2.1 · Azure Activity Log Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Activity Log captures all control plane operations across Azure subscriptions. Essential audit trail for resource management and compliance.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:audit`, Azure Activity Log via Event Hub
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:audit" operationName.value="*delete*" OR operationName.value="*write*"
| stats count by caller, operationName.value, resourceGroupName, status.value
| sort -count
```
- **Implementation:** Configure Azure Event Hub to receive Activity Log events. Set up Splunk_TA_microsoft-cloudservices with Event Hub input (connection string, consumer group). Alert on critical operations (resource deletions, policy changes).
- **Visualization:** Table (caller, operation, resource, status), Timeline, Bar chart by operation.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.2.2 · Entra ID Sign-In Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Risky sign-ins include impossible travel, unfamiliar locations, and anonymous IP usage. Primary detection layer for account compromise.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:signinlog`, Entra ID sign-in logs
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:signinlog" riskLevelDuringSignIn!="none"
| table _time userPrincipalName riskLevelDuringSignIn riskState ipAddress location.city location.countryOrRegion
| sort -_time
```
- **Implementation:** Forward Entra ID sign-in logs via Event Hub or direct API. Alert on riskLevelDuringSignIn = high or medium. Correlate with conditional access policy results.
- **Visualization:** Table (user, risk level, location, IP), Map (sign-in locations), Timeline, Bar chart by risk type.
- **CIM Models:** N/A

---

### UC-4.2.3 · Entra ID Privilege Escalation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Privileged role assignments (Global Admin, Privileged Role Admin) grant extreme power. Unauthorized assignments mean full tenant compromise.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:auditlog`, Entra ID audit logs
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:auditlog" activityDisplayName="Add member to role"
| spath output=role path=targetResources{}.modifiedProperties{}.newValue
| table _time initiatedBy.user.userPrincipalName targetResources{}.userPrincipalName role
| sort -_time
```
- **Implementation:** Forward Entra ID audit logs. Create critical alerts on role assignments for Global Administrator, Privileged Role Administrator, and Exchange Administrator. Correlate with PIM activation events.
- **Visualization:** Events list (critical), Table (who assigned what to whom), Timeline.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.2.4 · NSG Flow Log Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** NSG Flow Logs provide Azure network-level visibility. Detects blocked traffic, anomalous patterns, and lateral movement within VNets.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:nsgflowlog`
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:nsgflowlog" flowState="D"
| stats count by src_ip, dest_ip, dest_port, protocol
| sort -count | head 20
```
- **Implementation:** Enable NSG Flow Logs (Version 2) on all NSGs. Send to a storage account. Ingest via Splunk_TA_microsoft-cloudservices. Create dashboards for denied traffic and top talkers.
- **Visualization:** Table (top denied flows), Sankey diagram, Timechart, Map.
- **CIM Models:** N/A

---

### UC-4.2.5 · Azure VM Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Azure Monitor metrics provide VM performance data without agents. Essential for capacity planning and correlating with application issues.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:metrics`
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" metricName="Percentage CPU"
| timechart span=1h avg(average) as avg_cpu by resourceId
| where avg_cpu > 80
```
- **Implementation:** Configure Azure Monitor metrics collection in the Splunk TA. Collect CPU, memory, disk, and network metrics. Alert on sustained high utilization.
- **Visualization:** Line chart per VM, Heatmap, Gauge.
- **CIM Models:** N/A

---

### UC-4.2.6 · Azure SQL Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** DTU/vCore exhaustion causes query throttling. Deadlocks and long-running queries impact application performance directly.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:diagnostics` (SQL diagnostics)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="SQLInsights" OR Category="Deadlocks"
| stats count by database_name, Category
| sort -count
```
- **Implementation:** Enable Azure SQL diagnostic logging to Event Hub. Collect SQL Insights, Deadlocks, and QueryStoreRuntimeStatistics categories. Alert on DTU >90%, deadlock events, and query duration outliers.
- **Visualization:** Line chart (DTU usage), Table (deadlocks), Bar chart (top slow queries).
- **CIM Models:** N/A

---

### UC-4.2.7 · AKS Cluster Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** AKS cluster health monitoring ensures Kubernetes workloads are running reliably on Azure's managed platform.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`, Splunk OTel Collector
- **Data Sources:** AKS diagnostics, kube-state-metrics
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="kube-apiserver" level="Error"
| stats count by host, message
| sort -count
```
- **Implementation:** Enable AKS diagnostic logging to Event Hub (kube-apiserver, kube-controller-manager, kube-scheduler, kube-audit). Deploy OTel Collector in the AKS cluster for deeper K8s-level monitoring (see Category 3.2).
- **Visualization:** Status panel, Error timeline, Table.
- **CIM Models:** N/A

---

### UC-4.2.8 · Azure Key Vault Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Key Vault stores secrets, keys, and certificates. Unauthorized or anomalous access could indicate credential theft or data breach preparation.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:diagnostics` (Key Vault diagnostics)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="AuditEvent" ResourceType="VAULTS"
| stats count by identity.claim.upn, operationName, ResultType
| where ResultType!="Success"
| sort -count
```
- **Implementation:** Enable Key Vault diagnostic logging. Monitor all access operations. Alert on failed access attempts and unusual access patterns (new principals accessing secrets).
- **Visualization:** Table (user, operation, result), Timeline, Bar chart by operation.
- **CIM Models:** N/A

---

### UC-4.2.9 · Defender for Cloud Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Microsoft Defender provides threat detection across Azure resources. Centralizing in Splunk enables cross-platform security correlation.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Defender alerts via Event Hub
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:defender" severity="High" OR severity="Critical"
| table _time alertDisplayName severity resourceIdentifiers{} description
| sort -_time
```
- **Implementation:** Configure Defender for Cloud to export alerts to Event Hub. Ingest via Splunk TA. Alert on High and Critical severity findings.
- **Visualization:** Table by severity, Bar chart (alert types), Timeline, Single value (critical count).
- **CIM Models:** N/A

---

### UC-4.2.10 · Storage Account Access Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Unusual storage access patterns may indicate data exfiltration or compromised service principals accessing sensitive data.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Storage analytics logs via Event Hub
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="StorageRead" OR Category="StorageWrite"
| stats count by callerIpAddress, accountName, operationName
| eventstats avg(count) as avg_ops, stdev(count) as stdev_ops
| where count > avg_ops + (2 * stdev_ops)
```
- **Implementation:** Enable storage diagnostic logging. Baseline normal access patterns. Alert on volumetric anomalies (unusual number of reads/writes) or new source IPs.
- **Visualization:** Table (IP, account, operations), Line chart (access over time), Map.
- **CIM Models:** N/A

---

### UC-4.2.11 · Resource Health Events
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Azure service health impacts your resources directly. Knowing when Azure itself is having problems prevents wasted troubleshooting time.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Azure Resource Health via Activity Log
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:audit" category.value="ResourceHealth"
| table _time resourceGroupName resourceType status.value properties.cause properties.currentHealthStatus
| sort -_time
```
- **Implementation:** Resource Health events flow through the Activity Log. Monitor for Unavailable and Degraded statuses. Correlate with your application health metrics to distinguish Azure platform issues from your own problems.
- **Visualization:** Status panel per resource type, Table, Timeline.
- **CIM Models:** N/A

---

### UC-4.2.12 · Cost Management Alerts
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Azure cost monitoring prevents budget overruns. Tracking spend by resource group/team enables chargeback and anomaly detection.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`, Azure Cost Management export
- **Data Sources:** Azure Cost Management data (exported to storage)
- **SPL:**
```spl
index=azure sourcetype="azure:costmanagement"
| timechart span=1d sum(CostInBillingCurrency) as daily_cost by ResourceGroup
| eventstats avg(daily_cost) as avg_cost by ResourceGroup
| where daily_cost > avg_cost * 1.5
```
- **Implementation:** Configure Azure Cost Management to export daily usage data to a storage account. Ingest in Splunk. Create budget alerts when spending approaches thresholds.
- **Visualization:** Stacked area chart (spend by RG), Line chart with budget overlay, Table.
- **CIM Models:** N/A

---

## 4.3 Google Cloud Platform (GCP)

**Primary App/TA:** Splunk Add-on for Google Cloud Platform (`Splunk_TA_google-cloudplatform`) — Free on Splunkbase

---

### UC-4.3.1 · Audit Log Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** GCP audit logs capture all admin activity and data access. Foundational for security monitoring and compliance in GCP environments.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:pubsub:message` (via Pub/Sub)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*activity"
| spath output=method path=protoPayload.methodName
| spath output=principal path=protoPayload.authenticationInfo.principalEmail
| stats count by principal, method
| sort -count
```
- **Implementation:** Create a Pub/Sub topic and subscription. Configure a log sink to route audit logs to Pub/Sub. Set up Splunk_TA_google-cloudplatform with a Pub/Sub input. Alert on destructive operations (delete, setIamPolicy).
- **Visualization:** Table (principal, method, count), Bar chart, Timeline.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.3.2 · IAM Policy Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** IAM binding changes control who can access what in GCP. Unauthorized changes to bindings on projects, folders, or organizations are critical security events.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:pubsub:message`
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.methodName="SetIamPolicy"
| spath output=resource path=resource.labels
| spath output=principal path=protoPayload.authenticationInfo.principalEmail
| table _time principal resource protoPayload.serviceData.policyDelta.bindingDeltas{}
| sort -_time
```
- **Implementation:** Forward admin activity logs via Pub/Sub. Alert on `SetIamPolicy` events, especially those granting `roles/owner` or `roles/editor`. Track with change management.
- **Visualization:** Events list (critical), Table (who changed what), Timeline.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

---

### UC-4.3.3 · VPC Flow Log Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** GCP VPC Flow Logs provide network traffic visibility. Same use case as AWS/Azure — detect rejected traffic, anomalies, exfiltration.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** VPC Flow Logs via Pub/Sub
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*vpc_flows"
| spath
| stats sum(bytes_sent) as total_bytes by connection.src_ip, connection.dest_ip, connection.dest_port
| sort -total_bytes | head 20
```
- **Implementation:** Enable VPC Flow Logs on subnets. Sink to Pub/Sub and ingest in Splunk. Analyze for top talkers, rejected flows, and anomalous destinations.
- **Visualization:** Table, Sankey diagram, Timechart, Map.
- **CIM Models:** N/A

---

### UC-4.3.4 · GKE Cluster Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** GKE cluster health monitoring for managed Kubernetes in GCP. Node pools, upgrade status, and workload health.
- **App/TA:** `Splunk_TA_google-cloudplatform`, Splunk OTel Collector
- **Data Sources:** GKE logs via Pub/Sub, Cloud Monitoring metrics
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="k8s_cluster"
| spath output=severity path=severity
| where severity="ERROR"
| stats count by resource.labels.cluster_name, textPayload
| sort -count
```
- **Implementation:** GKE logs flow through Cloud Logging. Sink to Pub/Sub for Splunk ingestion. Deploy OTel Collector in GKE for K8s-native monitoring (see Category 3.2).
- **Visualization:** Status panel, Error table, Timeline.
- **CIM Models:** N/A

---

### UC-4.3.5 · Security Command Center
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** SCC provides vulnerability findings and threat detections across GCP. Centralizing in Splunk enables multi-cloud security correlation.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** SCC findings via Pub/Sub notification
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="scc_finding"
| spath output=severity path=finding.severity
| spath output=category path=finding.category
| where severity="CRITICAL" OR severity="HIGH"
| table _time category severity finding.resourceName finding.description
| sort -_time
```
- **Implementation:** Configure SCC to publish findings to Pub/Sub. Ingest via Splunk TA. Alert on CRITICAL and HIGH severity findings.
- **Visualization:** Table by severity, Bar chart (finding categories), Trend line.
- **CIM Models:** N/A

---

### UC-4.3.6 · GCE Instance Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Cloud Monitoring metrics via API
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="compute.googleapis.com/instance/cpu/utilization"
| timechart span=1h avg(value) by resource.labels.instance_id
```
- **Implementation:** Configure Cloud Monitoring metric collection in the Splunk TA. Collect CPU utilization, disk I/O, and network metrics. Alert on sustained high utilization.
- **Visualization:** Line chart, Heatmap, Gauge.
- **CIM Models:** N/A

---

### UC-4.3.7 · BigQuery Audit and Cost
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** BigQuery can generate massive costs from poorly optimized queries. Audit and cost tracking prevents bill shock and identifies optimization opportunities.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** BigQuery audit logs via Pub/Sub
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="bigquery.googleapis.com" protoPayload.methodName="jobservice.jobcompleted"
| spath output=bytes_billed path=protoPayload.serviceData.jobCompletedEvent.job.jobStatistics.totalBilledBytes
| spath output=user path=protoPayload.authenticationInfo.principalEmail
| eval cost_usd = round(bytes_billed / 1099511627776 * 5, 4)
| stats sum(cost_usd) as total_cost, count as queries by user
| sort -total_cost
```
- **Implementation:** Forward BigQuery audit logs via Pub/Sub. Calculate cost from billed bytes ($5/TB). Create dashboard showing cost per user, top expensive queries, and slot utilization.
- **Visualization:** Table (user, queries, cost), Bar chart (top costly queries), Trend line (daily cost).
- **CIM Models:** N/A

---

### UC-4.3.8 · Cloud Run/Functions Errors
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Serverless function errors and cold starts impact application reliability and user experience.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Cloud Run/Functions logs via Cloud Logging
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="cloud_function" severity="ERROR"
| spath output=function path=resource.labels.function_name
| stats count by function, textPayload
| sort -count
```
- **Implementation:** Forward Cloud Run/Functions logs via Pub/Sub. Monitor error rates, execution duration, and cold start frequency. Alert on error rate >5%.
- **Visualization:** Line chart (errors over time), Bar chart (top error functions), Single value.
- **CIM Models:** N/A

---

## 4.4 Multi-Cloud & Cloud Management

---

### UC-4.4.1 · Terraform Drift Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Infrastructure drift from declared IaC state means manual changes broke the single source of truth. Causes unpredictable behavior and deployment failures.
- **App/TA:** Custom input (Terraform CLI output, CI/CD integration)
- **Data Sources:** `terraform plan` output, CI/CD pipeline logs
- **SPL:**
```spl
index=devops sourcetype="terraform:plan"
| where changes_detected="true"
| stats count as drifted_resources by workspace, resource_type
| sort -drifted_resources
```
- **Implementation:** Run `terraform plan -detailed-exitcode` on schedule in CI/CD. Forward plan output to Splunk via HEC. Exit code 2 = changes detected (drift). Alert on any drift in production workspaces.
- **Visualization:** Table (workspace, resource, drift), Single value (drifted resources), Bar chart.
- **CIM Models:** N/A

---

### UC-4.4.2 · Cross-Cloud Identity Correlation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Users often have identities across AWS/Azure/GCP. Correlating activity provides unified view for security investigation and insider threat detection.
- **App/TA:** Combined cloud TAs + lookup tables
- **Data Sources:** All cloud audit logs
- **SPL:**
```spl
index=aws OR index=azure OR index=gcp
| eval cloud=case(index="aws","AWS", index="azure","Azure", index="gcp","GCP")
| eval user=coalesce(userIdentity.arn, userPrincipalName, protoPayload.authenticationInfo.principalEmail)
| lookup cloud_identity_map user OUTPUT normalized_user
| stats count, dc(cloud) as clouds_active, values(cloud) as clouds by normalized_user
| where clouds_active > 1
| sort -count
```
- **Implementation:** Create a lookup table mapping cloud identities to a normalized user (e.g., email). Combine audit logs from all three providers. Dashboard showing cross-cloud activity per user.
- **Visualization:** Table (user, clouds, activity count), Sankey diagram (user to cloud to action).
- **CIM Models:** N/A

---

### UC-4.4.3 · Multi-Cloud Cost Dashboard
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Unified cost visibility across cloud providers enables budgeting, chargeback, and optimization decisions from a single pane of glass.
- **App/TA:** Combined cloud TAs, billing data
- **Data Sources:** AWS CUR, Azure Cost Management, GCP Billing export
- **SPL:**
```spl
index=aws sourcetype="aws:billing" OR index=azure sourcetype="azure:costmanagement" OR index=gcp sourcetype="gcp:billing"
| eval cloud=case(index="aws","AWS", index="azure","Azure", index="gcp","GCP")
| eval cost=coalesce(BlendedCost, CostInBillingCurrency, cost)
| timechart span=1d sum(cost) by cloud
```
- **Implementation:** Ingest billing data from each provider. Normalize cost fields. Create a unified dashboard with consistent time-grain (daily). Break down by team using tagging from each provider.
- **Visualization:** Stacked area chart (daily cost by cloud), Table (cost by service), Pie chart (cost distribution).
- **CIM Models:** N/A

---

### UC-4.4.4 · Cloud Resource Tagging Compliance
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Untagged resources can't be tracked for cost allocation, compliance, or ownership. Tagging compliance is foundational for cloud governance.
- **App/TA:** Cloud provider TAs, Config rules
- **Data Sources:** Cloud resource inventories, Config/Policy compliance
- **SPL:**
```spl
index=aws sourcetype="aws:config:notification" resourceType="AWS::EC2::Instance"
| spath output=tags path=configuration.tags{}
| eval has_owner = if(match(tags, "Owner"), "Yes", "No")
| eval has_env = if(match(tags, "Environment"), "Yes", "No")
| where has_owner="No" OR has_env="No"
| table resourceId has_owner has_env
```
- **Implementation:** Use AWS Config rules (required-tags), Azure Policy, or GCP org policies to evaluate tagging. Ingest compliance results. Dashboard showing tagging compliance by tag and resource type.
- **Visualization:** Table (resource, missing tags), Pie chart (compliant %), Bar chart by tag.
- **CIM Models:** N/A

---

