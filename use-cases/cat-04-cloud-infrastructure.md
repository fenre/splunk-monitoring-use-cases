## 4. Cloud Infrastructure

### 4.1 Amazon Web Services (AWS)

**Primary App/TA:** Splunk Add-on for AWS (`Splunk_TA_aws`) — Free on Splunkbase; Splunk App for AWS (optional dashboards)

---

### UC-4.1.1 · Unauthorized API Calls
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1078.004, T1526
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
- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876), [AWS CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/)
- **Known false positives:** Legitimate access denied for least-privilege testing or new IAM policies; verify with change management.
- **Detection type:** TTP
- **Security domain:** cloud

- **Implementation:** Configure CloudTrail to send logs to an S3 bucket. Set up the Splunk_TA_aws with an SQS-based S3 input for CloudTrail. Alert when a single principal gets >5 access denied errors in 10 minutes.
- **Visualization:** Table (principal, API call, source IP, count), Bar chart by principal, Map (source IP GeoIP).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="failure"
  by Authentication.user Authentication.src Authentication.app span=1h
| sort -count
```

---

### UC-4.1.2 · Root Account Usage
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1078.004
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.user="root" OR Authentication.user="Root"
  by Authentication.src Authentication.action Authentication.app span=1h
| sort -count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)

---

### UC-4.1.3 · Security Group Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1562.007, T1578
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
  where All_Changes.object_category="security_group" OR match(All_Changes.object, "(?i)SecurityGroup")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.1.4 · IAM Policy Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1098.001, T1098.003
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
  where All_Changes.object_category="policy" OR match(All_Changes.object, "(?i)IAMPolicy|iam:policy")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.1.5 · Console Login Without MFA
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1078.004
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
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="success" AND (match(Authentication.signature, "(?i)ConsoleLogin|AwsConsoleSignIn") OR match(Authentication.app, "(?i)signin\\.amazonaws"))
  AND NOT (Authentication.mfa="true" OR lower(Authentication.authentication_method)="mfa")
  by Authentication.user Authentication.src Authentication.app span=1h
| sort -count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)

---

### UC-4.1.6 · EC2 Instance State Changes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **MITRE ATT&CK:** T1578.002, T1578.003
- **Value:** Tracks instance lifecycle for audit and change management. Unexpected terminations indicate accidents, auto-scaling issues, or attacks.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" (eventName="RunInstances" OR eventName="TerminateInstances" OR eventName="StopInstances" OR eventName="StartInstances")
| table _time userIdentity.arn eventName requestParameters.instancesSet.items{}.instanceId responseElements.instancesSet.items{}.currentState.name
| sort -_time
```
- **Implementation:** Ingest CloudTrail via the Splunk Add-on for AWS (`Splunk_TA_aws`) using the S3/SQS input from the organization trail. Alert on `TerminateInstances` where `requestParameters.instancesSet.items{}.instanceId` matches production-tagged instances from a `prod_instances` lookup. Suppress alerts during Auto Scaling scale-in events by checking `userIdentity.invokedBy=autoscaling.amazonaws.com`.
- **Visualization:** Table (timeline), Bar chart (events by type per day), Line chart (instance count trending).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where All_Changes.object_category="instance" OR match(All_Changes.object, "(?i)ec2:|i-[0-9a-f]{8,17}")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.1.7 · S3 Bucket Policy Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1530, T1619
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
  where All_Changes.object_category="bucket" OR match(All_Changes.object, "(?i)s3:|arn:aws:s3:::")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.1.8 · GuardDuty Finding Ingestion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580, T1526
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

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.9 · VPC Flow Log Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **MITRE ATT&CK:** T1580, T1526
- **Value:** VPC Flow Logs provide network-level visibility into all traffic. Detects rejected traffic, data exfiltration, lateral movement, and network anomalies.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatchlogs:vpcflow`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatchlogs:vpcflow" action="REJECT"
| stats count by src, dest, dest_port, protocol
| sort 20 -count
```
- **Implementation:** Enable VPC Flow Logs on all VPCs (send to S3 or CloudWatch Logs). Ingest via Splunk_TA_aws. Create dashboards for rejected traffic, top talkers, and unusual port activity.
- **Visualization:** Table (top rejected flows), Sankey diagram (source to destination), Timechart, Map.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

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

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

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

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

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
- **Implementation:** Ingest CloudWatch metrics (namespace `AWS/Lambda`, metrics `Errors`, `Invocations`, `Throttles`) via the Splunk Add-on for AWS. Compute error rate as `Errors/Invocations` over a 5-minute window; alert when rate exceeds 5% AND invocations exceed 50 (to avoid low-traffic false positives). For throttles, alert on any non-zero value. Forward Lambda CloudWatch Logs for stack trace correlation.
- **Visualization:** Line chart (errors/invocations over time), Bar chart (top error functions), Single value (error rate %).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.13 · EKS/ECS Cluster Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Unhealthy ECS/EKS control planes strand deployments and skew desired-vs-running task counts, causing user-visible errors before infrastructure metrics breach thresholds. Route platform-level failures (API server, scheduler) to the platform team and workload-level failures (CrashLoopBackOff, OOM) to the application owner.
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

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

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

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.15 · Config Compliance Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1578
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

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.16 · KMS Key Usage Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1078.004, T1530
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
  where match(All_Changes.app, "(?i)kms\\.amazonaws") OR match(All_Changes.object, "(?i)kms:|key/")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

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
  where match(All_Changes.action, "(?i)AllocateAddress|AssociateAddress|DisassociateAddress|ReleaseAddress") OR match(All_Changes.object, "(?i)eipalloc|elastic.?ip")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.1.18 · CloudFormation Stack Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration
- **MITRE ATT&CK:** T1578
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
  where match(All_Changes.action, "(?i)DetectStackDrift|DetectStackResourceDrift|CreateStack|UpdateStack|DeleteStack") OR match(All_Changes.object, "(?i)cloudformation|stack:")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.1.19 · WAF Blocked Request Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580
- **Value:** WAF blocks reveal attack patterns targeting your applications. Analysis helps tune rules and understand the threat landscape.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:waf` (WAF logs via S3 or Kinesis)
- **SPL:**
```spl
index=aws sourcetype="aws:waf" action="BLOCK"
| stats count by terminatingRuleId, httpRequest.clientIp, httpRequest.uri
| sort 20 -count
```
- **Implementation:** Enable WAF logging to S3 or Kinesis Firehose. Ingest via Splunk_TA_aws. Analyze blocked requests by rule, source IP, URI, and user agent to identify attack patterns and false positives.
- **Visualization:** Table (rule, source, URI, count), Bar chart by rule, Map (source IPs), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

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

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.21 · ALB/NLB Access Logs and 5xx Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Load balancer 5xx and target failures indicate backend or LB misconfiguration. Access logs enable traffic analysis and security forensics.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** S3 bucket with ALB/NLB access logs, CloudWatch LB metrics
- **SPL:**
```spl
index=aws sourcetype="aws:elb:accesslogs" elb_status_code>=500
| stats count by target_port, elb_status_code, request_url
| sort -count
```
- **Implementation:** Enable access logging for ALB/NLB to S3. Ingest via Splunk_TA_aws S3 input. Collect CloudWatch metrics (RequestCount, TargetResponseTime, HTTPCode_Target_5XX_Count). Alert on 5xx rate >1%.
- **Visualization:** Table (status, target, count), Line chart (5xx over time), Bar chart by target.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.22 · ELB Target Health and Unhealthy Hosts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Unhealthy targets cause traffic to fail or shift to remaining nodes. Early detection prevents user-facing outages.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (AWS/ApplicationELB, AWS/NetworkELB)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ApplicationELB" metric_name="UnHealthyHostCount"
| where Average > 0
| timechart span=5m max(Average) by LoadBalancer
```
- **Implementation:** Collect UnHealthyHostCount and HealthyHostCount from CloudWatch. Alert when UnHealthyHostCount > 0 for more than 2 minutes. Correlate with target group and instance health checks.
- **Visualization:** Single value (unhealthy count), Table (LB, target group, unhealthy), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.23 · CloudFront Cache Hit Ratio and Origin Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Low cache hit ratio increases origin load and latency. Origin errors indicate backend or CDN misconfiguration.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch CloudFront metrics, CloudFront access logs (optional, to S3)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/CloudFront" (metric_name="4xxErrorRate" OR metric_name="5xxErrorRate" OR metric_name="BytesDownloaded")
| timechart span=1h avg(Average) by metric_name, DistributionId
```
- **Implementation:** Enable CloudFront metrics in CloudWatch. Optionally enable standard logging to S3 for request-level analysis. Calculate cache hit ratio from requests (Hit vs Miss). Alert on 5xxErrorRate > 1%.
- **Visualization:** Line chart (4xx/5xx rate, bytes), Gauge (cache hit %), Table by distribution.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.24 · SQS Queue Depth and Age of Oldest Message
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Growing queue depth or old messages indicate consumers are falling behind or failing. Prevents backlog and SLA breaches.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch SQS metrics (ApproximateNumberOfMessagesVisible, ApproximateAgeOfOldestMessage)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SQS" (metric_name="ApproximateNumberOfMessagesVisible" OR metric_name="ApproximateAgeOfOldestMessage")
| timechart span=5m avg(Average) by metric_name, QueueName
| where ApproximateNumberOfMessagesVisible > 1000 OR ApproximateAgeOfOldestMessage > 300
```
- **Implementation:** Collect SQS metrics. Alert when queue depth exceeds threshold (e.g. 1000) or age of oldest message > 5 minutes. Monitor dead-letter queue (ApproximateNumberOfMessagesDelayed) separately.
- **Visualization:** Line chart (depth, age by queue), Single value (oldest message age), Table (queue, depth).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.25 · SQS Dead-Letter Queue Message Count
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Messages in DLQ indicate processing failures. Immediate alerting ensures failed messages are investigated and reprocessed.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch SQS metrics for DLQ (ApproximateNumberOfMessagesVisible)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SQS" metric_name="ApproximateNumberOfMessagesVisible"
| search QueueName="*dlq*" OR QueueName="*dead*"
| where Average > 0
| table _time QueueName Average
```
- **Implementation:** Tag or identify DLQ queues (naming convention or tags). Alert when ApproximateNumberOfMessagesVisible > 0 for any DLQ. Create runbook for DLQ investigation and replay.
- **Visualization:** Single value (DLQ messages), Table (queue, count), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.26 · DynamoDB Throttled Requests and Consumed Capacity
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Throttling causes request failures and degraded application performance. Capacity monitoring supports right-sizing and auto-scaling.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch DynamoDB metrics (ThrottledRequests, ConsumedReadCapacityUnits, ConsumedWriteCapacityUnits)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/DynamoDB" metric_name="ThrottledRequests"
| where Sum > 0
| timechart span=5m sum(Sum) by TableName, Operation
```
- **Implementation:** Collect DynamoDB metrics per table. Alert on any ThrottledRequests. Dashboard consumed vs. provisioned capacity to tune throughput. Consider on-demand capacity if spikes are unpredictable.
- **Visualization:** Line chart (throttled, consumed by table), Table (top throttled tables), Gauge (utilization %).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.27 · API Gateway 4xx/5xx and Throttling
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** High 4xx/5xx or throttling indicates misconfigured APIs, backend failures, or abuse. Essential for API reliability and quota management.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch API Gateway metrics (Count, 4XXError, 5XXError, IntegrationLatency)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ApiGateway" (metric_name="5XXError" OR metric_name="Count")
| timechart span=5m sum(Sum) by metric_name, ApiName, Stage
| eval error_rate = 5XXError / Count * 100
| where error_rate > 1
```
- **Implementation:** Enable detailed metrics for API Gateway (per-stage). Ingest CloudWatch. Alert on 5XXError rate >1% or ThrottleCount > 0. Optionally enable access logging to S3 for request-level analysis.
- **Visualization:** Line chart (errors, count, latency), Table (API, stage, error rate), Single value.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.28 · EBS Volume Status and Burst Balance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** EBS status checks and burst balance (gp2/gp3) indicate volume health and risk of I/O throttling when credits are exhausted.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch EBS metrics (VolumeStatusCheckFailed, BurstBalancePercentage)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/EBS" (metric_name="VolumeStatusCheckFailed" OR metric_name="BurstBalancePercentage")
| where VolumeStatusCheckFailed > 0 OR BurstBalancePercentage < 20
| table _time VolumeId metric_name Average
```
- **Implementation:** Collect EBS metrics. Alert on VolumeStatusCheckFailed. For gp2/gp3, alert when BurstBalancePercentage < 20%. Consider io1/io2 or gp3 with higher baseline IOPS for steady high I/O.
- **Visualization:** Table (volume, status, burst %), Single value (volumes with low burst), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.29 · EC2 Spot Instance Interruption Notices
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Spot interruptions cause instance termination with short notice. Tracking enables graceful shutdown, workload migration, and capacity planning.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch Events (EC2 Spot Instance Interruption Warning), EventBridge
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="EC2 Spot Instance Interruption Warning"
| table _time detail.instance-id detail.instance-action detail.spot-instance-request-id
| sort -_time
```
- **Implementation:** Create EventBridge rule for EC2 Spot Instance Interruption Warning. Forward to SNS or Lambda for Splunk ingestion. Alert on every interruption; use for fleet metrics and hybrid/on-demand fallback decisions.
- **Visualization:** Table (instance, action, time), Timeline (interruptions by AZ), Bar chart (interruptions by instance type).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.30 · CloudTrail Log File Delivery Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1562.008
- **Value:** Failed CloudTrail delivery means audit gaps. Attackers may target trail deletion or S3 permissions to hide activity.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudTrail insight events, S3 bucket event notifications, or CloudWatch Logs for trail validation
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventName="DeleteTrail" OR eventName="PutBucketPolicy" requestParameters.name=*
| table _time userIdentity.arn eventName requestParameters.bucketName
| sort -_time
```
- **Implementation:** Enable CloudTrail log file validation. Monitor for DeleteTrail, PutBucketPolicy on the trail bucket, or S3 access denied to trail bucket. Use AWS Config or custom Lambda to validate delivery and alert on gaps.
- **Visualization:** Events list (critical), Table (trail, bucket, event), Timeline.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.action, "(?i)DeleteTrail|StopLogging|UpdateTrail|PutBucketPolicy|PutEventSelectors") OR match(All_Changes.object, "(?i)cloudtrail|trail")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.1.31 · CloudWatch Alarm State Changes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Alarm state transitions (OK → ALARM, INSUFFICIENT_DATA) provide a consolidated view of metric-based issues. Centralizing in Splunk enables correlation with other data.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch Events (Alarm state change), SNS subscription
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="CloudWatch Alarm State Change" detail.state.value="ALARM"
| table _time detail.alarmName detail.state.value detail.newStateReason
| sort -_time
```
- **Implementation:** Create EventBridge rule for CloudWatch Alarm State Change. Send to SNS topic; ingest via Splunk_TA_aws or HEC. Filter for state=ALARM. Correlate alarm name with resource tags for ownership.
- **Visualization:** Table (alarm, state, reason), Timeline (alarms over time), Single value (active alarms).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.32 · NAT Gateway Bytes Processed and Connection Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** NAT Gateway is a single point of egress for private subnets. Monitoring bytes and connection count supports capacity and cost (data processed) planning.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch NAT Gateway metrics (BytesOutToDestination, ActiveConnectionCount)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/NATGateway"
| timechart span=1h sum(Sum) as bytes, avg(Average) as connections by NatGatewayId
```
- **Implementation:** Collect NAT Gateway metrics. Alert on sudden drop in BytesOutToDestination (possible outage) or spike in ActiveConnectionCount (possible connection exhaustion). Track data processed for cost.
- **Visualization:** Line chart (bytes, connections by NAT GW), Table (NAT GW, bytes today), Single value.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.33 · VPN Connection State and Tunnel Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** VPN down breaks hybrid connectivity. Tunnel state monitoring ensures quick detection and failover to secondary tunnel or connection.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch VPN metrics (TunnelState, TunnelDataIn, TunnelDataOut)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/VPN" metric_name="TunnelState"
| where Average != 1
| table _time VpnId TunnelIpAddress Average
```
- **Implementation:** TunnelState 1 = UP, 0 = DOWN. Alert when either tunnel is down. Monitor TunnelDataIn/Out for traffic; zero traffic may indicate routing or peer issue even if state is UP.
- **Visualization:** Status panel (tunnel up/down), Table (VPN, tunnel, state), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.34 · AWS Organizations SCP and OU Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1098.003
- **Value:** SCP (Service Control Policy) and OU structure changes affect permissions across many accounts. Unauthorized changes can weaken security boundaries.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail` (management account or delegated admin)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" (eventName="AttachPolicy" OR eventName="DetachPolicy" OR eventName="CreateOrganizationalUnit" OR eventName="MoveAccount") requestParameters.targetId=*
| table _time userIdentity.arn eventName requestParameters.policyId requestParameters.organizationalUnitId
| sort -_time
```
- **Implementation:** Ensure CloudTrail in management account logs Organizations API calls. Alert on AttachPolicy/DetachPolicy (SCP) and MoveAccount. Restrict who can modify SCPs via IAM and MFA.
- **Visualization:** Table (who, what, when), Timeline, Bar chart by event type.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.action, "(?i)AttachPolicy|DetachPolicy|CreateOrganizationalUnit|MoveAccount|CreateAccount|CloseAccount") OR match(All_Changes.object, "(?i)organizations|scp|ou-")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.1.35 · S3 Replication Lag and Failed Replication
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Replication lag or failures break DR and compliance. Detecting failures ensures data is replicated within RPO.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** S3 Replication metrics (ReplicationLatency, BytesPendingReplication), S3 event notifications for replication failures
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/S3" metric_name="ReplicationLatency"
| where Average > 900
| timechart span=15m avg(Average) by SourceBucket, DestinationBucket
```
- **Implementation:** Enable S3 Replication metrics in CloudWatch. Configure event notifications for replication failures (s3:Replication:OperationFailedReplication). Alert on ReplicationLatency > 15 min or any failure event.
- **Visualization:** Line chart (latency by bucket pair), Table (failed replications), Single value (bytes pending).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.36 · ElastiCache/Redis CPU and Evictions
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** High CPU or evictions indicate undersized cache or hot keys. Impacts application latency and cache hit ratio.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch ElastiCache metrics (CPUUtilization, CacheEvictions, CacheHitRate)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ElastiCache" (metric_name="CPUUtilization" OR metric_name="CacheEvictions")
| timechart span=5m avg(Average) by metric_name, CacheClusterId
| where CPUUtilization > 80 OR CacheEvictions > 100
```
- **Implementation:** Collect ElastiCache metrics per node/cluster. Alert on CPUUtilization > 80% sustained. Monitor CacheHitRate; low hit rate and high evictions suggest need for more memory or key design review.
- **Visualization:** Line chart (CPU, evictions, hit rate), Table (cluster, metrics), Gauge (hit rate).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.37 · SNS Delivery Failures and Bounce/Complaint
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** SNS delivery failures mean subscribers are not receiving notifications. Bounce/complaint (for email) affects sender reputation and deliverability.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch SNS metrics (NumberOfNotificationsFailed, NumberOfMessagesFailed)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SNS" metric_name="NumberOfNotificationsFailed"
| where Sum > 0
| timechart span=5m sum(Sum) by TopicName
```
- **Implementation:** Collect SNS metrics. Alert when NumberOfNotificationsFailed > 0. For email subscriptions, enable bounce/complaint feedback and ingest via SNS or EventBridge. Track delivery success rate.
- **Visualization:** Line chart (failures by topic), Table (topic, failure count), Single value (failed notifications).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.38 · EventBridge Rule Invocation and Failed Invocations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Failed invocations mean downstream targets (Lambda, SQS, etc.) are not receiving events. Critical for event-driven architecture reliability.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch EventBridge metrics (Invocations, FailedInvocations, TriggeredRules)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Events" metric_name="FailedInvocations"
| where Sum > 0
| timechart span=5m sum(Sum) by RuleName
```
- **Implementation:** Collect EventBridge metrics per rule. Alert on FailedInvocations > 0. Correlate with target service (e.g. Lambda errors, SQS rejections) for root cause.
- **Visualization:** Table (rule, failures), Line chart (invocations vs failures), Single value.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.39 · AWS Backup Restore Job Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Restore job failures prevent recovery during DR. Monitoring ensures backup and restore pipeline is healthy.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch Events (Backup job state change), Backup job history via API
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="Backup Job State Change" (detail.state="FAILED" OR detail.state="ABORTED")
| table _time detail.backupJobId detail.resourceType detail.state detail.message
| sort -_time
```
- **Implementation:** Create EventBridge rule for Backup Job State Change. Filter for FAILED/ABORTED. Optionally ingest backup job list from AWS Backup API for compliance dashboard. Run periodic restore tests and log results.
- **Visualization:** Table (job, resource, state, message), Timeline (failed restores), Single value (failed jobs last 24h).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.40 · Route 53 Health Check Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Health check failures indicate endpoint or path unreachable. Used for failover and monitoring of external/internal resources.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch Route 53 health check metrics (HealthCheckStatus)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Route53" metric_name="HealthCheckStatus"
| where Average != 1
| table _time HealthCheckId Average
```
- **Implementation:** HealthCheckStatus 1 = Healthy, 0 = Unhealthy. Alert when status = 0. Create dashboard of all health checks with status. Use for failover routing and status page.
- **Visualization:** Status panel (healthy/unhealthy), Table (health check, status), Map (endpoint locations).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.41 · Redshift Cluster Health and Connection Count
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Redshift cluster health and connection exhaustion impact analytics workloads. Monitoring supports capacity and connection limit management.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch Redshift metrics (DatabaseConnections, CPUUtilization, PercentageDiskSpaceUsed)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Redshift" metric_name="DatabaseConnections"
| timechart span=5m avg(Average) by ClusterIdentifier
| where DatabaseConnections > 80
```
- **Implementation:** Collect Redshift metrics. Alert when DatabaseConnections approaches max (e.g. 90% of limit) or CPUUtilization/PercentageDiskSpaceUsed is high. Correlate with query queue length.
- **Visualization:** Line chart (connections, CPU, disk by cluster), Table (cluster, metrics), Gauge (connection %).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.42 · Step Functions Execution Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Failed or aborted executions break workflows. Tracking failure rate and failed execution IDs enables debugging and retry.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch Step Functions metrics (ExecutionsFailed, ExecutionsAborted), or EventBridge for state machine events
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/States" (metric_name="ExecutionsFailed" OR metric_name="ExecutionsAborted")
| where Sum > 0
| timechart span=5m sum(Sum) by StateMachineArn
```
- **Implementation:** Collect Step Functions metrics. Alert when ExecutionsFailed or ExecutionsAborted > 0. Use X-Ray or CloudWatch Logs for failed execution details. Create runbook for common failure causes.
- **Visualization:** Line chart (failed, aborted by workflow), Table (state machine, count), Single value.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.43 · EFS Burst Credit Balance and Throughput
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** EFS burst credits deplete under sustained high throughput; performance then drops to baseline. Monitoring prevents unexpected slowdowns.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch EFS metrics (BurstCreditBalance, DataReadIOBytes, DataWriteIOBytes)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/EFS" metric_name="BurstCreditBalance"
| where Average < 500000000
| timechart span=1h avg(Average) by FileSystemId
```
- **Implementation:** Collect EFS metrics. Alert when BurstCreditBalance falls below threshold (e.g. 500M). Consider provisioned throughput for consistent high I/O. Dashboard read/write IOPS and throughput.
- **Visualization:** Line chart (burst balance, IOPS by filesystem), Table (filesystem, balance), Gauge (balance %).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.44 · Inspector Vulnerability and Finding Trends
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1526, T1613
- **Value:** Inspector findings (EC2, ECR, Lambda) identify vulnerabilities. Tracking trends and new critical findings supports patch and image hygiene.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** Inspector findings via EventBridge or SNS, or Security Hub (which aggregates Inspector)
- **SPL:**
```spl
index=aws sourcetype="aws:inspector" severity="CRITICAL" OR severity="HIGH"
| stats count by severity, findingType, resourceType
| sort -count
```
- **Implementation:** Configure Inspector to send findings to EventBridge or SNS; ingest in Splunk. Alert on new CRITICAL findings. Dashboard open findings by severity and age. Correlate with patch compliance (SSM).
- **Visualization:** Table (severity, type, count), Bar chart by severity, Trend line (findings over time).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.45 · Systems Manager (SSM) Patch Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Low patch compliance increases vulnerability. SSM Patch Manager compliance status enables prioritization and remediation tracking.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** SSM compliance data via Config, or custom Lambda polling SSM DescribeInstancePatchStates
- **SPL:**
```spl
index=aws sourcetype="aws:ssm:compliance" ComplianceType="Patch" status!="Compliant"
| stats count by status, InstanceId
| sort -count
```
- **Implementation:** Use AWS Config rule for patch-compliance or custom automation to export Patch Manager compliance to S3/CloudWatch. Ingest in Splunk. Dashboard compliance % by OU/account. Alert when compliance drops below threshold.
- **Visualization:** Table (instance, status), Pie chart (compliant vs non-compliant), Bar chart by patch group.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.46 · Direct Connect Virtual Interface BGP State
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** BGP down on Direct Connect breaks hybrid connectivity. Monitoring BGP session state ensures quick detection and carrier escalation.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch Direct Connect metrics (ConnectionState, VirtualInterfaceState), or custom script polling DescribeVirtualInterfaces
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/DX" metric_name="ConnectionState"
| where Average != 1
| table _time VirtualInterfaceId ConnectionState
```
- **Implementation:** ConnectionState 1 = available. Alert when state changes to down or unknown. For BGP specifically, use Direct Connect LAG/connection health or partner/carrier APIs if AWS metrics are insufficient.
- **Visualization:** Status panel (connection state), Table (VIF, state), Timeline (state changes).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.47 · Glue Job Run Failures and Duration
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Glue job failures break ETL pipelines. Duration trends support capacity and cost optimization.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch Glue metrics (JobRunFailureCount, JobRunDuration), Glue job run history
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Glue" metric_name="JobRunFailureCount"
| where Sum > 0
| timechart span=1h sum(Sum) by JobName
```
- **Implementation:** Collect Glue metrics. Alert when JobRunFailureCount > 0. Track JobRunDuration for SLA and DPU tuning. Ingest job run events from EventBridge for run-level detail.
- **Visualization:** Line chart (failures, duration by job), Table (job, failure count), Single value.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.48 · Athena Query Execution Failures and Bytes Scanned
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Failed queries and high bytes scanned impact user experience and cost. Monitoring supports optimization and error triage.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** Athena query history via API or CloudWatch (DataScannedInBytes), CloudTrail (StartQueryExecution, GetQueryResults)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventName="StartQueryExecution" errorCode!=""
| table _time userIdentity.arn requestParameters.queryExecutionId errorCode
| sort -_time
```
- **Implementation:** Use CloudTrail for Athena API calls (success/failure). Optionally export query execution IDs and join with GetQueryExecution for bytes scanned and state. Alert on high failure rate or queries scanning >1TB.
- **Visualization:** Table (query, user, bytes, state), Line chart (bytes scanned over time), Bar chart (top users by bytes).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.49 · FSx for Lustre/Windows Capacity and Throughput
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** FSx capacity and throughput metrics support HPC and Windows file share capacity planning and performance troubleshooting.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch FSx metrics (DataReadBytes, DataWriteBytes, FreeDataStorageCapacity)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/FSx" metric_name="FreeDataStorageCapacity"
| timechart span=1d avg(Average) by FileSystemId
| eval free_gb = FreeDataStorageCapacity / 1024 / 1024 / 1024
| where free_gb < 100
```
- **Implementation:** Collect FSx metrics. Alert when free capacity is low. Monitor read/write throughput for Lustre; for Windows, track client connections and IOPS. Correlate with backup completion.
- **Visualization:** Line chart (capacity, throughput by filesystem), Table (filesystem, free GB), Gauge (used %).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.50 · Trusted Advisor Check Results and Cost Optimization
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Trusted Advisor identifies cost optimization, performance, and security improvements. Tracking check results supports governance and savings.
- **App/TA:** `Splunk_TA_aws` (Trusted Advisor API or Support API)
- **Data Sources:** Trusted Advisor API (describe-trusted-advisor-checks, describe-trusted-advisor-check-result)
- **SPL:**
```spl
index=aws sourcetype="aws:trustedadvisor" status="warning" OR status="error"
| stats count by category name status
| sort -count
```
- **Implementation:** Schedule Lambda or script to call Trusted Advisor API (requires Business/Enterprise Support). Export check results to S3 or send to Splunk via HEC. Dashboard by category (cost, performance, security). Alert on new critical security checks failing.
- **Visualization:** Table (check, category, status), Pie chart (ok vs warning vs error), Bar chart by category.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.51 · Lambda Concurrent Executions and Throttling
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Throttling occurs when concurrent executions hit account or function limits. Monitoring prevents dropped invocations and supports quota increase requests.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch Lambda metrics (ConcurrentExecutions, Throttles)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="Throttles"
| where Sum > 0
| timechart span=5m sum(Sum) by FunctionName
```
- **Implementation:** Collect Lambda metrics. Alert on Throttles > 0. Monitor ConcurrentExecutions vs account limit (1000 default). Consider reserved concurrency for critical functions. Dashboard invocations, duration, errors, throttles together.
- **Visualization:** Line chart (concurrent, throttles by function), Table (function, throttles), Single value (account concurrent %).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.52 · ECR Image Scan Findings
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1610, T1613
- **Value:** ECR image scan finds CVEs in container images. Critical/high findings in production images require immediate remediation or rollback.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** ECR scan findings via EventBridge (ECR Image Scan), or Security Hub
- **SPL:**
```spl
index=aws sourcetype="aws:ecr:scan" severity="CRITICAL" OR severity="HIGH"
| table _time repositoryName imageTag severity findingName
| sort -_time
```
- **Implementation:** Enable ECR image scanning (enhanced or basic). Send scan completion events to EventBridge; forward to Splunk. Alert on CRITICAL/HIGH in repos tagged as production. Block deployment in pipeline when findings exceed threshold.
- **Visualization:** Table (repo, tag, severity, CVE), Bar chart (findings by repo), Trend line (findings over time).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.53 · CloudWatch Logs Subscription Filter Errors
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Subscription filter delivery failures mean logs are not reaching Lambda, Kinesis, or Firehose. Indicates quota, permission, or downstream failures.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch Logs metric filters (IncomingLogEvents, DeliveryErrors), or destination-specific metrics
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Logs" metric_name="DeliveryErrors"
| where Sum > 0
| timechart span=5m sum(Sum) by LogGroupName, FilterName
```
- **Implementation:** Create CloudWatch metric filter for subscription delivery errors if available, or monitor Kinesis/Firehose delivery errors. Alert when delivery errors spike. Check Lambda/Kinesis throttling and IAM permissions.
- **Visualization:** Table (log group, filter, errors), Line chart (delivery errors over time), Single value.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.54 · Kinesis Data Stream Iterator Age and Throttling
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** High iterator age means consumers are falling behind. Throttling indicates producers exceed shard capacity. Both cause lag and potential data loss.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch Kinesis metrics (GetRecords.IteratorAgeMilliseconds, WriteProvisionedThroughputExceeded)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Kinesis" metric_name="GetRecords.IteratorAgeMilliseconds"
| where Average > 60000
| timechart span=1m avg(Average) by StreamName
```
- **Implementation:** Collect Kinesis metrics. Alert when iterator age > 60 seconds (consumer lag). Alert on WriteProvisionedThroughputExceeded (add shards or reduce write rate). Monitor IncomingRecords/OutgoingRecords for throughput.
- **Visualization:** Line chart (iterator age, throttles by stream), Table (stream, age ms), Single value (max lag).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.55 · Secrets Manager Secret Rotation and Access
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1098.001, T1078.004
- **Value:** Failed rotation leaves stale credentials. Unusual access patterns may indicate credential abuse. Audit supports compliance and incident response.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudTrail (RotateSecret, GetSecretValue, DescribeSecret)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventSource="secretsmanager.amazonaws.com" (eventName="RotateSecret" OR eventName="GetSecretValue")
| stats count by userIdentity.arn eventName requestParameters.secretId
| sort -count
```
- **Implementation:** CloudTrail logs Secrets Manager API. Alert on RotateSecret failures. Baseline GetSecretValue by principal and secret; alert on anomalous access (new principal, spike in access). Track rotation schedule compliance.
- **Visualization:** Table (principal, secret, action, count), Timeline (rotation events), Bar chart by secret.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  where match(All_Changes.app, "(?i)secretsmanager\\.amazonaws") OR match(All_Changes.object, "(?i)secret:")
  by All_Changes.user All_Changes.object All_Changes.action span=1h
| sort -count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.1.56 · AWS Lambda Cold Start Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Cold start frequency and duration impact user experience. High cold start rates or long init times cause request latency spikes and timeouts.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudWatch Logs (Lambda platform logs: REPORT, INIT), X-Ray traces
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatchlogs" ("REPORT RequestId" OR "INIT_START")
| eval function_name=case(isnotnull(log_group), replace(log_group, "/aws/lambda/", ""), 1=1, "unknown")
| rex "Init Duration:\s+(?<init_ms>\d+\.?\d*)\s*ms"
| rex "Duration:\s+(?<duration_ms>\d+\.?\d*)\s*ms"
| eval cold_start=if(match(_raw, "INIT_START"), 1, 0)
| stats count as invocations, sum(cold_start) as cold_starts, avg(init_ms) as avg_init_ms, avg(duration_ms) as avg_duration_ms by function_name, bin(_time, 1h)
| eval cold_start_pct=round(cold_starts/invocations*100, 1)
| where cold_start_pct > 10 OR avg_init_ms > 1000
| table _time function_name invocations cold_starts cold_start_pct avg_init_ms avg_duration_ms
| sort -cold_start_pct
```
- **Implementation:** Enable CloudWatch Logs for Lambda (platform logs include REPORT and INIT). Optionally ingest X-Ray traces for end-to-end cold start visibility. Parse REPORT/INIT_START lines to extract init duration and invocation type. Alert when cold start rate exceeds 10% or init duration > 1s for critical functions. Consider provisioned concurrency for latency-sensitive workloads.
- **Visualization:** Line chart (cold start % and init duration by function over time), Table (function, cold starts, avg init ms), Single value (cold start rate).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.57 · AWS ECS Task Placement Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Tasks failing to place due to resource constraints (CPU, memory, ports, attributes) cause service scaling failures and deployment blockages.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** CloudTrail (RunTask, CreateService with placement failures), ECS container instance state change events
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventSource="ecs.amazonaws.com" (eventName="RunTask" OR eventName="CreateService")
| spath path=responseElements.failures{}
| mvexpand responseElements.failures{} limit=500
| spath input=responseElements.failures{} path=reason
| spath input=responseElements.failures{} path=arn
| search reason=*
| stats count by reason, requestParameters.cluster
| sort -count
```
- **Implementation:** CloudTrail logs ECS API calls; RunTask and CreateService responses include a `failures` array when placement fails. Ingest ECS events from EventBridge for container instance state changes. Parse failure reasons (RESOURCE:MEMORY, RESOURCE:CPU, RESOURCE:PORT, attribute constraints). Alert on any placement failure. Dashboard by cluster, reason, and task definition. Remediate by adding capacity, relaxing constraints, or adjusting task definitions.
- **Visualization:** Table (reason, cluster, count), Bar chart (failures by reason), Timeline (placement failure events).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.58 · AWS Transit Gateway Attachment Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Fault
- **Value:** TGW route propagation and attachment state affect cross-VPC and hybrid connectivity. Failed attachments or stale routes cause network outages.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** AWS Config (TGW attachment compliance), TGW flow logs, CloudWatch TGW metrics (BytesIn, BytesOut, PacketsIn, PacketsOut)
- **SPL:**
```spl
index=aws (sourcetype="aws:config:notification" resourceType="AWS::EC2::TransitGatewayAttachment" OR (sourcetype="aws:cloudwatch" namespace="AWS/TransitGateway" metric_name="BytesIn"))
| eval attachment_state=case(
  configurationItemStatus="ResourceDeleted", "deleted",
  configurationItemStatus="ResourceNotRecorded", "unknown",
  configurationItemStatus="OK", "ok",
  isnotnull(configurationItemStatus), configurationItemStatus,
  1=1, null())
| eval resourceId=coalesce(resourceId, resource_id)
| stats latest(attachment_state) as state, latest(Sum) as bytes_in by resourceId, bin(_time, 1h)
| where (isnotnull(state) AND state!="ok") OR (isnotnull(bytes_in) AND bytes_in=0)
| table _time resourceId state bytes_in
| sort -_time
```
- **Implementation:** Enable AWS Config for TGW attachments to track state changes. Ingest TGW flow logs to S3 and forward to Splunk for traffic analysis. Collect CloudWatch TGW metrics (BytesIn, BytesOut) per attachment. Alert when attachment state is not available or traffic drops to zero unexpectedly. Correlate with route table propagation events. Use for hybrid connectivity and SD-WAN monitoring.
- **Visualization:** Table (attachment, state, traffic), Status grid (attachment health), Line chart (bytes in/out by attachment).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.59 · S3 Suspicious Access Patterns
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1530, T1619
- **Value:** Unusual ListBucket volume, access from new regions, or anonymous reads often precede data exfiltration; pattern detection reduces dwell time.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail` (s3.amazonaws.com), optional S3 server access logs `sourcetype=aws:s3:accesslogs`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventSource="s3.amazonaws.com" eventName="GetObject"
| eval geo=if(isnull(sourceIPAddress),"unknown",sourceIPAddress)
| stats dc(eventName) as ops, dc(awsRegion) as regions, count by userIdentity.arn, requestParameters.bucketName
| where regions > 3 OR count > 10000
| sort -count
```
- **Implementation:** Baseline normal GetObject/ListBucket rates per bucket and principal. Enrich with GeoIP on `sourceIPAddress`. Alert on first-seen ASN, burst downloads, or ListBucket without matching application inventory. Correlate with GuardDuty S3 findings.
- **Visualization:** Table (bucket, principal, count), Map (source IP), Timeline (access spikes).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port | sort - count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-4.1.60 · Security Hub Alert Aggregation
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580, T1526
- **Value:** Security Hub rolls up Config, GuardDuty, Inspector, and partner findings; aggregating by account and severity prioritizes remediation queues.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:firehose` or `sourcetype=aws:cloudwatch:events` (Security Hub findings), EventBridge to Splunk
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="Security Hub Findings - Imported"
| spath path=detail.findings{}
| mvexpand detail.findings{} limit=500
| spath input=detail.findings{} output=sev path=Severity.Label
| spath input=detail.findings{} output=title path=Title
| stats count by sev, title, account
| sort -count
```
- **Implementation:** Send Security Hub custom actions or EventBridge rules to Firehose/HEC. Normalize `Severity` and `ComplianceStatus`. Auto-ticket CRITICAL/HIGH. Deduplicate by finding ID across updates. Feed executive dashboards with counts by standard (CIS, PCI).
- **Visualization:** Bar chart (findings by severity), Table (title, account, count), Single value (open critical).
- **CIM Models:** Intrusion_Detection
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.action, IDS_Attacks.signature, IDS_Attacks.src, IDS_Attacks.dest | sort - count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)

---

### UC-4.1.61 · Network ACL Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1562.007
- **Value:** NACL changes can open subnets to the internet or break least-privilege segmentation; they are less common than security groups and warrant explicit audit.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail` (ec2.amazonaws.com CreateNetworkAclEntry, ReplaceNetworkAclEntry, DeleteNetworkAclEntry)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventSource="ec2.amazonaws.com" (eventName="CreateNetworkAclEntry" OR eventName="ReplaceNetworkAclEntry" OR eventName="DeleteNetworkAclEntry")
| stats count by userIdentity.arn, requestParameters.networkAclId, eventName, awsRegion
| sort -_time
```
- **Implementation:** Require change tickets in deployment pipeline metadata where possible. Alert on any prod NACL change. Visualize before/after rule numbers and CIDR blocks from `requestParameters`. Weekly review with network team.
- **Visualization:** Table (NACL, user, action), Timeline (changes), Single value (changes 24h).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user | sort - count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.1.62 · RDS Performance Insights Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Performance Insights exposes DB load by wait state; trending top SQL and waits guides index and instance right-sizing beyond raw CPU.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** Performance Insights API export, `sourcetype=aws:cloudwatch` (PI metrics), RDS log exports
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="DBLoad" statistic="Average"
| timechart span=1h avg(Average) as dbload by DBInstanceIdentifier
| streamstats window=168 global=f avg(dbload) as baseline by DBInstanceIdentifier
| where dbload > baseline * 1.5
```
- **Implementation:** Enable Performance Insights (7–30 day retention). Export `DBLoad`, `DBLoadCPU`, `DBLoadNonCPU` via API or CloudWatch where available. Alert on sustained elevation vs weekly baseline. Join with application release times.
- **Visualization:** Line chart (DB load vs baseline), Table (instance, wait class if ingested), Area chart (CPU vs non-CPU load).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host span=1h | sort - agg_value
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### UC-4.1.63 · ECS Service Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Service-level running count versus desired indicates deployment failures, capacity shortfall, or health check flapping.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (AWS/ECS — CPUUtilization, MemoryUtilization), `sourcetype=aws:cloudwatch:events` (service events)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ECS" (metric_name="CPUUtilization" OR metric_name="MemoryUtilization")
| stats latest(Average) as util by ClusterName, ServiceName, metric_name
| where util > 85
```
- **Implementation:** Ingest ECS service events from EventBridge for steady-state issues. Dashboard desired vs running from `DescribeServices` snapshots if scripted. Alert on failed deployments or service unable to reach steady state.
- **Visualization:** Status grid (service health), Line chart (CPU/memory by service), Table (cluster, service, failures).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.64 · EKS Control Plane Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1613, T1609
- **Value:** Kubernetes audit logs capture who changed roles, secrets, and workloads; essential for forensics and SOC2 evidence on EKS.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** EKS control plane logs in `sourcetype=aws:cloudwatchlogs` (cluster audit), CloudTrail `eks.amazonaws.com` API
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatchlogs" log_group="/aws/eks/*/cluster"
| search "audit.k8s.io" verb="create" objectRef.resource="clusterroles" OR objectRef.resource="secrets"
| stats count by user.username, objectRef.namespace, objectRef.name
| sort -count
```
- **Implementation:** Enable EKS audit logging to CloudWatch Logs and subscribe to Splunk. Optionally include CloudTrail for `CreateCluster`, `AssociateIdentityProviderConfig`. Alert on cluster-admin bindings, anonymous access, or secret reads from unexpected service accounts.
- **Visualization:** Table (user, resource, count), Timeline (privileged API calls), Sankey (user→namespace).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user | sort - count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.1.65 · GuardDuty Severity Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580, T1526
- **Value:** Prioritizing GuardDuty findings by severity and type reduces noise and speeds triage versus raw event volume.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch:guardduty`, GuardDuty S3 export
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:guardduty"
| stats count by severity, type, accountId
| sort -count
```
- **Implementation:** Normalize severity (8–10 = high). Auto-suppress known pen-test ranges via lookup. Weekly trend of finding types. SOAR integration for HIGH and above with runbooks per `type`.
- **Visualization:** Bar chart (findings by type), Pie chart (severity), Table (account, type, count).
- **CIM Models:** Intrusion_Detection
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.severity | sort - count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)

---

### UC-4.1.66 · AWS Config Rule Compliance Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1578
- **Value:** Resources oscillating between COMPLIANT and NON_COMPLIANT indicate automation fights or manual changes—drift trends surface systemic issues.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:config:notification`, Config history snapshots
- **SPL:**
```spl
index=aws sourcetype="aws:config:notification" configRuleList{}.complianceType=*
| mvexpand configRuleList{} limit=500
| spath input=configRuleList{} path=complianceType
| spath input=configRuleList{} path=configRuleName
| stats dc(complianceType) as state_changes by resourceId, configRuleName
| where state_changes > 1
| sort -state_changes
```
- **Implementation:** Ingest configuration item change streams. Track flapping rules weekly. Alert when critical rules (encryption, public access) change state more than N times per day. Root-cause with CloudTrail correlation.
- **Visualization:** Table (resource, rule, changes), Line chart (compliant % over time), Single value (flapping resources).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.67 · SNS Delivery Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Failed SMS, email, or HTTP subscriptions break alerting and fan-out; monitoring delivery failures prevents silent notification loss.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (AWS/SNS — NumberOfNotificationsFailed), delivery status logs
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SNS" metric_name="NumberOfNotificationsFailed"
| timechart span=15m sum(Sum) as failed by TopicName
| where failed > 0
```
- **Implementation:** Enable delivery status logging for HTTP/S endpoints. Ingest CloudWatch metrics per topic. Alert on any failed count sustained 15 minutes. Validate endpoint URLs and DLQ for failed deliveries if configured.
- **Visualization:** Line chart (failures by topic), Table (topic, failed count), Single value (total failures).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.68 · SQS Dead Letter Queue Growth
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** DLQ depth growth means poison messages or downstream outages; rate-of-change highlights incidents faster than static thresholds.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (AWS/SQS — ApproximateNumberOfMessagesVisible on DLQ ARNs)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SQS" metric_name="ApproximateNumberOfMessagesVisible" QueueName="*dlq*"
| sort 0 _time
| streamstats window=12 global=f first(Average) as prev by QueueName
| eval growth=Average-prev
| where growth > 10
| table _time QueueName Average growth
```
- **Implementation:** Tag DLQs consistently for `*dlq*` matching or use explicit dimension. Alert on positive growth over 1h or depth exceeding SLO. Replay with caution after root-cause.
- **Visualization:** Line chart (DLQ depth), Single value (growth rate), Table (queue, depth).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.69 · CloudFront Error Rates by Distribution
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Origin or edge errors vary by distribution; breaking out 4xx/5xx by `DistributionId` isolates bad releases and misconfigured behaviors.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (AWS/CloudFront — 4xxErrorRate, 5xxErrorRate), real-time logs
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/CloudFront" (metric_name="4xxErrorRate" OR metric_name="5xxErrorRate")
| stats latest(Average) as err_rate by DistributionId, metric_name, bin(_time, 5m)
| where err_rate > 1
| sort - err_rate
```
- **Implementation:** Ingest metrics per distribution ID. Correlate spikes with deployments and origin health. Use real-time logs for URI-level detail. Alert when 5xx error rate exceeds SLO for 10 minutes.
- **Visualization:** Line chart (error rate by distribution), Table (distribution, metric), Map (viewer country if from logs).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.70 · Route 53 Health Check Failover Validation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Failed health checks drive DNS failover; sustained failures mean user-facing outages or flapping routing policies.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (AWS/Route53 — HealthCheckStatus, ChildHealthCheckHealthyCount)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Route53" metric_name="HealthCheckStatus"
| stats latest(Minimum) as healthy by HealthCheckId, bin(_time, 5m)
| where healthy < 1
| sort HealthCheckId -_time
```
- **Implementation:** Map `HealthCheckId` to application names via lookup. Alert on unhealthy state for two consecutive periods. Correlate with target (ALB, IP) metrics. Include calculator health checks for complex routing.
- **Visualization:** Status grid (health check × time), Table (check id, target), Timeline (failures).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.71 · Systems Manager Patch Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Patch baselines reduce exploit exposure; instance-level compliance gaps show outdated AMIs or broken agents.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:ssm:compliance`, SSM Inventory association
- **SPL:**
```spl
index=aws sourcetype="aws:ssm:compliance" ComplianceType="Patch"
| stats latest(status) as patch_status by resourceId, PatchSeverity
| where patch_status!="Compliant"
| stats count by resourceId
| sort -count
```
- **Implementation:** Schedule `AWS-RunPatchBaseline` and ingest compliance association results. Dashboard by OU and environment tag. Alert when CRITICAL severity patches are non-compliant past SLA window.
- **Visualization:** Table (instance, missing count), Pie chart (compliant %), Bar chart (severity).
- **CIM Models:** Updates
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Updates.Updates by Updates.status, Updates.dest | sort - count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Updates](https://docs.splunk.com/Documentation/CIM/latest/User/Updates)

---

### UC-4.1.72 · Transit Gateway Route Table Attachment Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Beyond attachment state, route propagation to TGW route tables determines reachability; blackholes show as dropped traffic or failed tests.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail` (ec2:ReplaceTransitGatewayRoute, CreateRoute), TGW route table notifications
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventSource="ec2.amazonaws.com" (eventName="CreateTransitGatewayRoute" OR eventName="DeleteTransitGatewayRoute" OR eventName="ReplaceTransitGatewayRoute")
| stats count by userIdentity.arn, requestParameters.transitGatewayRouteTableId, eventName
| sort -_time
```
- **Implementation:** Alert on route changes in production TGW tables. Correlate with change windows. Combine with UC-4.1.58 metrics for end-to-end path validation. Use Network Manager events if enabled.
- **Visualization:** Timeline (route changes), Table (route table, CIDR, action), Line chart (cross-VPC bytes with UC-4.1.58).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user | sort - count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.1.73 · ELB Target Health Check Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Unhealthy targets are removed from rotation; rising unhealthy counts precede customer-facing errors.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (AWS/ApplicationELB, AWS/NetworkELB — UnHealthyHostCount, HealthyHostCount)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" (namespace="AWS/ApplicationELB" OR namespace="AWS/NetworkELB") metric_name="UnHealthyHostCount"
| stats latest(Maximum) as unhealthy by LoadBalancer, TargetGroup, bin(_time, 5m)
| where unhealthy > 0
| sort - unhealthy
```
- **Implementation:** Join with target group tags for app name. Alert when unhealthy > 0 for 5 minutes or half of targets unhealthy. Correlate with ASG events and backend application logs.
- **Visualization:** Line chart (unhealthy hosts), Table (TG, AZ, count), Status grid (target).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.74 · IAM Access Analyzer Findings
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1087.004, T1580
- **Value:** Access Analyzer identifies unintended external access to S3, IAM roles, KMS keys, and other resources—reducing public exposure risk.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** Access Analyzer findings export (EventBridge, Security Hub), `sourcetype=aws:cloudwatch:events`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="Access Analyzer Finding" detail.status="ACTIVE"
| stats count by detail.resourceType, detail.principal.awsAccountId, detail.isPublic
| sort -count
```
- **Implementation:** Enable organization-wide analyzer. Send findings to EventBridge and Splunk. Auto-remediate public S3 where policy allows or ticket owners. Weekly review of new external access paths.
- **Visualization:** Table (resource type, account, public), Bar chart (findings by type), Single value (active findings).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.75 · AWS Backup Job Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Centralized backup vault jobs must complete on schedule; failed jobs leave RPO gaps across EC2, EFS, and databases.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch:events` (Backup Job State Change), Backup notifications
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:events" detail-type="Backup Job State Change"
| eval ok=if(detail.state="COMPLETED",1,0)
| stats count(eval(ok=0)) as failed, count as total by detail.backupVaultArn, detail.resourceArn
| where failed>0
```
- **Implementation:** Parse job states COMPLETED, FAILED, EXPIRED. Alert on FAILED. Track partial completion for large resources. Cross-check with UC-4.4.29 restore drills for end-to-end assurance.
- **Visualization:** Table (vault, resource, status), Timeline (job outcomes), Single value (failed jobs 24h).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.1.76 · Lambda Layer Version Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Outdated layers carry vulnerable dependencies; enforcing approved layer ARNs avoids shadow IT libraries in functions.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudtrail` (lambda:GetFunction, PublishLayerVersion), Config custom rule output
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" eventSource="lambda.amazonaws.com" eventName="UpdateFunctionConfiguration"
| spath path=requestParameters.layers{}
| mvexpand requestParameters.layers{} limit=200
| eval layer_arn=requestParameters.layers{}
| lookup approved_lambda_layers layer_arn OUTPUT approved
| where isnull(approved)
| stats count by userIdentity.arn, requestParameters.functionName, layer_arn
```
- **Implementation:** Maintain CSV lookup of approved layer version ARNs. Alert on attach of unapproved layer or version drift weekly scan via `ListFunctions`. Integrate with CI/CD to block deploys pre-merge.
- **Visualization:** Table (function, layer, user), Bar chart (non-compliant functions), Timeline (changes).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---


### UC-4.1.77 · AWS Fargate Task Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Fargate tasks are the unit of scale; tracking stopped tasks and resource limits surfaces platform issues before services miss SLAs.
- **App/TA:** `Splunk_TA_aws` (CloudWatch Logs/Metrics)
- **Data Sources:** `sourcetype=aws:cloudwatch:metric` or `sourcetype=aws:cloudwatchlogs`
- **SPL:**
```spl
index=cloud sourcetype="aws:cloudwatch:metric" Namespace="AWS/ECS" MetricName="CPUUtilization"
| stats avg(Average) as cpu_avg, max(Maximum) as cpu_max by ServiceName, ClusterName
| where cpu_max>90
| sort -cpu_max
```
- **Implementation:** Enable CloudWatch Container Insights for ECS on Fargate and pull metrics via `Splunk_TA_aws` CloudWatch metric input. Ship task and service logs to Splunk (FireLens, Lambda, or direct subscription) and run a companion search on `sourcetype=aws:cloudwatchlogs` for `Task stopped` / error patterns. Map dimensions `ClusterName`, `ServiceName`, `TaskId`. Alert on sustained high CPU/memory, task stop reasons, and log error bursts.
- **Visualization:** Time chart (CPU/memory by service), Table (stopped tasks with reason), Single value (running task count).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110)

---

### 4.2 Microsoft Azure

**Primary App/TA:** Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`) — Free on Splunkbase

---

### UC-4.2.1 · Azure Activity Log Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1580, T1526
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

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.2.2 · Entra ID Sign-In Anomalies
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1078.004, T1110
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

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.3 · Entra ID Privilege Escalation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1098.003, T1078.004
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

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.2.4 · NSG Flow Log Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **MITRE ATT&CK:** T1580, T1526
- **Value:** NSG Flow Logs provide Azure network-level visibility. Detects blocked traffic, anomalous patterns, and lateral movement within VNets.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:nsgflowlog`
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:nsgflowlog" flowState="D"
| stats count by src, dest, dest_port, protocol
| sort -count | head 20
```
- **Implementation:** Enable NSG Flow Logs (Version 2) on all NSGs. Send to a storage account. Ingest via Splunk_TA_microsoft-cloudservices. Create dashboards for denied traffic and top talkers.
- **Visualization:** Table (top denied flows), Sankey diagram, Timechart, Map.
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

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

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

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

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

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

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.8 · Azure Key Vault Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1078.004, T1530
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

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.9 · Defender for Cloud Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1530, T1619
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

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.10 · Storage Account Access Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **MITRE ATT&CK:** T1530, T1619
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

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

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

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

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

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.13 · App Service (Web App) HTTP 5xx and Slot Swap
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** App Service 5xx and failed slot swaps impact user experience and deployment safety. Monitoring supports reliability and blue-green deployment.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Azure Monitor metrics (Http5xx, ResponseTime), Activity Log (Slot swap)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" metricName="Http5xx" namespace="Microsoft.Web/sites"
| where average > 0
| timechart span=5m sum(total) by resourceId
```
- **Implementation:** Collect App Service metrics. Alert on Http5xx rate >1%. Monitor slot swap operations in Activity Log; alert on swap failure. Track response time and memory usage for capacity.
- **Visualization:** Line chart (5xx, response time by app), Table (app, 5xx count), Timeline (slot swaps).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.14 · Azure Load Balancer Health Probe Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Probe failures mean backends are unhealthy; traffic stops flowing to those instances. Critical for load balancer and application availability.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Azure Monitor metrics (ProbeHealthStatus, SnatConnectionCount)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" metricName="ProbeHealthStatus" namespace="Microsoft.Network/loadBalancers"
| where average == 0
| table _time resourceId backendPoolName average
```
- **Implementation:** ProbeHealthStatus 1 = healthy, 0 = unhealthy. Alert when any backend pool shows unhealthy. Correlate with VM availability and application logs. Monitor SNAT exhaustion (SnatConnectionCount) for outbound issues.
- **Visualization:** Status panel (probe health), Table (LB, backend, status), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.15 · Azure Backup Job Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Backup job failures break recovery guarantees. Detecting failures ensures backups are fixed before they are needed for restore.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Azure Monitor Activity Log (Backup job events), or Backup vault diagnostic logs
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:audit" operationName.value="*Backup*" status.value="Failed"
| table _time caller operationName.value resourceGroupName properties
| sort -_time
```
- **Implementation:** Enable Activity Log or diagnostic settings for Recovery Services vault. Ingest backup job completion events. Alert on status=Failed. Dashboard job success rate by vault and policy.
- **Visualization:** Table (job, vault, status, time), Timeline (failed jobs), Single value (failed last 24h).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.16 · Logic Apps Run Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Logic App run failures break automation and integrations. Tracking failures and retries supports debugging and SLA.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Logic Apps workflow run history via diagnostic logs or Azure Monitor
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" ResourceType="MICROSOFT.LOGIC/WORKFLOWS" status="Failed"
| stats count by resourceId runId
| sort -count
```
- **Implementation:** Enable diagnostic logging for Logic Apps to Event Hub or Log Analytics. Ingest in Splunk. Alert when run status=Failed. Track retry patterns and correlate with connector/API errors.
- **Visualization:** Line chart (runs, failures by workflow), Table (workflow, run, status), Single value (failure rate).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.17 · Service Bus Queue Message Count and Dead Letter
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Growing queue or dead-letter count indicates consumers falling behind or message processing failures. Prevents backlog and lost messages.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Azure Monitor metrics (ActiveMessageCount, DeadletterMessageCount)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" namespace="Microsoft.ServiceBus/namespaces" metricName="ActiveMessageCount"
| timechart span=5m avg(average) by EntityName
| where ActiveMessageCount > 1000
```
- **Implementation:** Collect Service Bus metrics per queue/topic. Alert when ActiveMessageCount exceeds threshold or DeadletterMessageCount > 0. Monitor message age via custom metric or run history if available.
- **Visualization:** Line chart (message count, dead letter by queue), Table (queue, active, dead letter), Single value.
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.18 · Cosmos DB RU Consumption and Throttling
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Throttling (429) occurs when RU consumption exceeds provisioned throughput. Monitoring supports right-sizing and autoscale tuning.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Azure Monitor Cosmos DB metrics (TotalRequestUnits, TotalRequests, Http429)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" namespace="Microsoft.DocumentDB/databaseAccounts" metricName="TotalRequestUnits"
| timechart span=5m sum(total) by CollectionName
| eval ru_utilization_pct = TotalRequestUnits / provisioned_ru * 100
```
- **Implementation:** Collect Cosmos DB metrics. Alert when Http429 > 0 or RU consumption consistently near provisioned. Dashboard RU by operation type and partition. Consider autoscale for variable workload.
- **Visualization:** Line chart (RU, 429 by collection), Table (collection, RU, 429), Gauge (RU utilization %).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.19 · Azure Front Door / CDN Origin Errors and Cache Hit
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Origin errors and low cache hit ratio impact latency and origin load. Essential for CDN and global app performance.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Azure Monitor Front Door metrics (BackendHealthPercentage, RequestCount, BackendRequestCount)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" namespace="Microsoft.Cdn/profiles" metricName="BackendHealthPercentage"
| where average < 100
| table _time resourceId endpoint average
```
- **Implementation:** Collect Front Door/CDN metrics. Alert when BackendHealthPercentage < 100%. Track RequestCount vs BackendRequestCount for cache hit ratio. Enable diagnostic logs for request-level analysis.
- **Visualization:** Line chart (origin health, request count), Table (endpoint, health %, cache hit), Gauge (cache hit %).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.20 · Event Grid Delivery Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Delivery failures mean subscribers did not receive events. Critical for event-driven architecture and integration reliability.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Event Grid diagnostic logs (DeliveryFailure, DeliverySuccess)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="DeliveryFailure"
| stats count by topic eventSubscriptionName errorCode
| sort -count
```
- **Implementation:** Enable Event Grid diagnostic logging to Event Hub or storage. Ingest in Splunk. Alert when DeliveryFailure count > 0. Correlate with dead-letter and subscriber endpoint health.
- **Visualization:** Table (topic, subscription, failures), Line chart (deliveries vs failures), Single value (failed deliveries).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.21 · Azure Container Registry Pull/Push and Vulnerability Scan
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1610, T1613
- **Value:** ACR stores container images. Unusual pull/push or image scan findings indicate abuse or vulnerable images in use.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** ACR diagnostic logs (Pull, Push), Defender for Containers / ACR vulnerability scan
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" ResourceType="MICROSOFT.CONTAINERREGISTRY/REGISTRIES" OperationName="Pull"
| stats count by identity_claim_upn repository
| eventstats avg(count) as avg_pull, stdev(count) as stdev_pull
| where count > avg_pull + 2*stdev_pull
```
- **Implementation:** Enable ACR diagnostic logs. Baseline pull/push by identity and repo; alert on anomalies. Ingest vulnerability scan results from Defender or ACR task; alert on critical/high in production repos.
- **Visualization:** Table (user, repo, pulls), Bar chart (top pullers), Table (image, CVE, severity).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.22 · Azure Firewall Rule Hit and Threat Intel
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580, T1562.007
- **Value:** Firewall logs show allowed/denied traffic and threat intelligence hits. Essential for network security and incident response.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Azure Firewall diagnostic logs (AzureFirewallApplicationRule, AzureFirewallNetworkRule, AzureFirewallThreatIntelLog)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="AzureFirewallThreatIntelLog"
| rename msg_src_ip as src, msg_dest_ip as dest
| table _time src dest action threat_id
| sort -_time
```
- **Implementation:** Enable Azure Firewall diagnostic logs to Event Hub or storage. Ingest in Splunk. Alert on any threat intel hit. Dashboard rule hits, denied flows, and top sources/destinations.
- **Visualization:** Table (source, dest, action, rule), Map (threat IPs), Timeline (threat intel hits).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.23 · Azure Database for MySQL/PostgreSQL Metrics
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Managed MySQL/PostgreSQL CPU, storage, and connection metrics support capacity and performance management beyond Azure SQL.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Azure Monitor metrics (percentage_cpu, storage_percent, active_connections)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" namespace="Microsoft.DBforMySQL/servers" metricName="percentage_cpu"
| timechart span=5m avg(average) by resourceId
| where percentage_cpu > 80
```
- **Implementation:** Collect Azure DB for MySQL/PostgreSQL metrics. Alert on CPU >80%, storage_percent >85%, or active_connections nearing max. Enable slow query log and ingest for query-level analysis.
- **Visualization:** Line chart (CPU, storage, connections by server), Table (server, metrics), Gauge (storage %).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.24 · Azure Monitor Alert State Changes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Alert state changes (fired, resolved) provide consolidated view of metric/log conditions. Centralizing in Splunk enables correlation.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Activity Log (Microsoft.Insights/activityLogAlerts), or Action Group webhook to Splunk
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:audit" operationName.value="Microsoft.Insights/activityLogAlerts/Activated/Action"
| table _time caller properties.condition properties.alertRule
| sort -_time
```
- **Implementation:** Configure Action Group to send alert payload to Splunk (Logic App or webhook). Ingest fired and resolved events. Dashboard active alerts by severity and resource group.
- **Visualization:** Table (alert, state, time), Timeline (alert history), Single value (active alerts).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.25 · Entra ID Conditional Access Blocked Sign-Ins
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1078.004
- **Value:** Blocked sign-ins by Conditional Access indicate policy enforcement. Tracking blocks helps tune policies and detect bypass attempts.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Entra ID sign-in logs (resultType=0 for success; filter for blocks)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:signinlog" status.errorCode!="0"
| stats count by userPrincipalName appDisplayName status.errorCode location
| sort -count
```
- **Implementation:** Forward sign-in logs. Filter for resultType or status indicating block (e.g. conditional access block). Alert on spike in blocks or blocks for sensitive apps. Correlate with risk and device compliance.
- **Visualization:** Table (user, app, error, location), Bar chart (blocks by reason), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.26 · Azure Service Health and Planned Maintenance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Service Health and planned maintenance notifications prevent wasted troubleshooting and enable change planning.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Service Health alerts via Activity Log (ServiceHealth)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:audit" category.value="ServiceHealth"
| table _time properties.incidentType properties.title properties.description properties.status
| sort -_time
```
- **Implementation:** Service Health events flow to Activity Log. Ingest and filter for category=ServiceHealth. Alert on incidentType=Incident or Security. Dashboard active incidents and upcoming maintenance.
- **Visualization:** Table (incident, service, status), Timeline (incidents), Single value (active incidents).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.27 · Azure Policy Compliance and Non-Compliant Resources
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1578
- **Value:** Azure Policy enforces governance. Non-compliant resources increase risk and compliance gaps. Tracking compliance supports remediation.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Policy state change events, Azure Monitor (policy compliance API or diagnostic)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:audit" resourceId=*Microsoft.Authorization/policyAssignments*
| search complianceState="NonCompliant"
| stats count by policyDefinitionId resourceType
| sort -count
```
- **Implementation:** Use Azure Policy compliance API or export policy states to storage/Event Hub. Ingest in Splunk. Dashboard compliance % by policy and resource group. Alert when critical policy becomes non-compliant.
- **Visualization:** Table (policy, resource, state), Pie chart (compliant %), Bar chart (non-compliant by type).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.28 · Azure App Service Plan CPU and Memory
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Platform-level resource pressure on App Service plan (not app-level) causes throttling, slow responses, and out-of-memory errors across all apps in the plan.
- **App/TA:** Splunk Add-on for Microsoft Cloud Services
- **Data Sources:** Azure Monitor metrics (CpuPercentage, MemoryPercentage for App Service Plan)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" resourceType="Microsoft.Web/serverfarms" (metric_name="CpuPercentage" OR metric_name="MemoryPercentage")
| stats avg(average) as avg_pct by resourceId, metric_name, bin(_time, 5m)
| where avg_pct > 80
| eval avg_pct=round(avg_pct, 1)
| table _time resourceId metric_name avg_pct
| sort -avg_pct
```
- **Implementation:** Configure Azure Monitor diagnostic settings or metrics API to export App Service Plan metrics (CpuPercentage, MemoryPercentage) to Event Hub or storage. Ingest via Splunk_TA_microsoft-cloudservices. Alert when CPU or memory exceeds 80% for 5+ minutes. Scale up plan or optimize app code. Distinguish plan-level metrics from app-level (requests, response time).
- **Visualization:** Line chart (CPU and memory % by plan over time), Table (plan, metric, avg %), Gauge (current utilization).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.29 · Azure Front Door Origin Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Origin probe failures cause automatic failover. Repeated failures indicate backend issues or misconfigured health probes; critical for global load balancing and CDN reliability.
- **App/TA:** Splunk Add-on for Microsoft Cloud Services
- **Data Sources:** Azure Front Door health probe logs, FrontDoorHealthProbeLog
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" resourceType="Microsoft.Cdn/profiles" log_s="FrontDoorHealthProbeLog"
| spath path=properties
| search properties.httpStatusCode!=200 OR properties.healthProbeSentResult="Unhealthy"
| stats count by resourceId, properties.backendPoolName, properties.healthProbeSentResult
| sort -count
```
- **Implementation:** Enable Front Door diagnostic logs (FrontDoorHealthProbeLog) and route to Log Analytics or Event Hub. Ingest in Splunk. Alert on any Unhealthy probe result or non-200 status. Correlate with origin availability and probe configuration (path, interval). Dashboard by backend pool and origin.
- **Visualization:** Table (backend pool, result, count), Status grid (origin health), Timeline (probe failures).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.30 · NSG Flow Log Threat Hunting
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580, T1526
- **Value:** NSG flow logs reveal lateral movement, denied probes, and unexpected east-west volume; baselining flows speeds incident triage beyond simple allow/deny counts.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:nsgflow` or Event Hub JSON (flow records)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:nsgflow" flowDirection="In" macAddress=*
| stats sum(bytes) as total_bytes, dc(src) as unique_sources by dest, dest_port_s, rule
| where unique_sources > 50 OR total_bytes > 1000000000
| sort -total_bytes
```
- **Implementation:** Ingest NSG Flow Logs to Event Hub and Splunk. Enrich IPs with threat intel and CMDB. Alert on denied burst to sensitive subnets or new rare port pairs. Retention per compliance.
- **Visualization:** Sankey or chord (src→dest), Table (top talkers), Map (geo of external IPs).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t dc(All_Traffic.src) as agg_value from datamodel=Network_Traffic.All_Traffic by All_Traffic.dest | sort - agg_value
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-4.2.31 · Azure Policy Compliance Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Point-in-time compliance misses drift; trending non-compliant resource counts shows whether governance keeps pace with deployments.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Policy compliance export, `sourcetype=mscs:azure:audit` (policy events)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:audit" complianceState="NonCompliant"
| timechart span=1d count by policyDefinitionId
```
- **Implementation:** Schedule daily export of compliance snapshot per subscription. Ingest as JSON with timestamp. Alert when rolling 7-day average of non-compliant % increases week over week. Tie to deployment pipelines.
- **Visualization:** Line chart (non-compliant % over time), Table (policy, delta), Bar chart (top resource types).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.32 · Key Vault Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1078.004, T1530
- **Value:** Secret and key unwrap operations must be traceable for insider and breach investigations; unusual callers warrant immediate review.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:audit` (Microsoft.KeyVault vaults), diagnostic logs
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:audit" resourceId="*vaults*" (operationName.value="SecretGet" OR operationName.value="Decrypt" OR operationName.value="UnwrapKey")
| stats count by identity.claims.name, callerIpAddress, resourceId
| sort -count
```
- **Implementation:** Enable Key Vault diagnostic logs to Log Analytics or Event Hub. Alert on first-time principal, after-hours bulk access, or access from non-corporate IP ranges using lookups.
- **Visualization:** Table (identity, vault, count), Timeline (access spikes), Map (caller IP).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)

---

### UC-4.2.33 · App Service Health Metrics
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** HTTP queue length, response time, and instance health explain user-visible slowness before 5xx rates spike.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:metrics` (Microsoft.Web/sites — HttpQueueLength, AverageResponseTime, HealthCheckStatus)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" resourceType="Microsoft.Web/sites" (metric_name="HttpQueueLength" OR metric_name="AverageResponseTime" OR metric_name="HealthCheckStatus")
| stats avg(average) as v by resourceId, metric_name, bin(_time, 5m)
| where (metric_name="HttpQueueLength" AND v>100) OR (metric_name="AverageResponseTime" AND v>2000) OR (metric_name="HealthCheckStatus" AND v>0)
```
- **Implementation:** Stream App Service metrics via diagnostic settings. Correlate with App Service Plan saturation (UC-4.2.28). Alert on sustained queue depth or failed health probes. Scale out or warm up instances.
- **Visualization:** Line chart (queue, response time, health), Table (app, metric, value), Status grid (probe per slot).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.CPU by Performance.host | sort - agg_value
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### UC-4.2.34 · AKS Diagnostics and Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fault
- **MITRE ATT&CK:** T1613, T1609
- **Value:** Control plane and node problems surface as API errors, failed mounts, and ImagePullBackOff; centralized errors shorten MTTR.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:diagnostics` (kube-audit, container logs), Azure Monitor for containers
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" category="kube-audit" "responseStatus.code">=400
| stats count by objectRef.resource, verb, responseStatus.code
| sort -count
```
- **Implementation:** Enable AKS diagnostic categories for audit and container logs. Ingest to Splunk. Alert on elevated 5xx from API server or repeated ImagePullBackOff patterns. Dashboard by namespace and deployment.
- **Visualization:** Table (resource, code, count), Timeline (audit errors), Bar chart (namespace).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.35 · Cost Management Anomaly Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Cost
- **Value:** Built-in Cost Management alerts help, but statistical baselines on daily spend catch unusual service charges early.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`, Cost Management export
- **Data Sources:** `sourcetype=mscs:azure:cost` or amortized cost CSV to blob/Event Hub
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:cost"
| timechart span=1d sum(pretax_cost) as daily by ServiceName
| eventstats avg(daily) as mu, stdev(daily) as sigma by ServiceName
| eval z=if(sigma>0, (daily-mu)/sigma, 0)
| where z > 3
```
- **Implementation:** Ingest daily actual cost by service and resource group. Use `predict` or manual z-score as shown. Alert finance and owners on anomalies. Exclude known one-time purchases via lookup.
- **Visualization:** Line chart (daily cost by service), Table (service, z-score), Single value (anomaly count).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.36 · Azure Firewall Threat Intelligence Hits
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580, T1562.007
- **Value:** Threat intel–based denies block known-bad IPs and domains at the edge; volume and target trends indicate active campaigns or misclassified traffic.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Azure Firewall diagnostic logs (`AzureFirewallApplicationRule`, `AzureFirewallNetworkRule`), threat intel action
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="AzureFirewallApplicationRule" msg_s="*ThreatIntel*"
| stats count by msg_s, FQDN, SourceAddress
| sort -count
```
- **Implementation:** Enable Threat Intel mode on Firewall and full diagnostic logging. Parse rule collection and threat category. Alert on new destination countries or sudden hit rate increase. Tune false positives with application owners.
- **Visualization:** Map (source IP), Table (FQDN, count), Timeline (hits).
- **CIM Models:** Intrusion_Detection
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.src | sort - count
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)

---

### UC-4.2.37 · Front Door WAF Blocks
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580
- **Value:** Managed rule blocks protect origins; tracking rule IDs separates scanning noise from targeted application abuse.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Front Door diagnostic logs (WebApplicationFirewallLog)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" log_s="WebApplicationFirewallLog" action_s="Block"
| stats count by ruleName_s, clientIP_s, hostName_s
| sort -count
```
- **Implementation:** Enable WAF logs on Front Door profile. Ingest to Splunk. Dashboard OWASP rule groups. Create exceptions carefully with SecOps. Correlate with origin 5xx to avoid blocking good clients.
- **Visualization:** Bar chart (ruleName), Table (client IP, URI), Timeline (block rate).
- **CIM Models:** Intrusion_Detection
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.action, IDS_Attacks.signature, IDS_Attacks.src, IDS_Attacks.dest | sort - count
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)

---

### UC-4.2.38 · Logic App Run Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Integration workflows power automation; failed runs leave tickets, data, and approvals stuck.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:diagnostics` (WorkflowRuntime), Logic App run history export
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" resourceType="Microsoft.Logic/workflows" status_s="Failed"
| stats count by resource_name_s, code_s, error_s
| sort -count
```
- **Implementation:** Enable Logic App workflow diagnostics. Ingest run status and error codes. Alert on any failed production workflow or retry exhaustion. Replay failed runs from operations team process.
- **Visualization:** Table (workflow, error), Timeline (failures), Single value (failed runs / hour).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.39 · Event Hub Capture Lag
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Capture to ADLS/Blob enables batch analytics; lag between enqueue and file availability delays downstream pipelines.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Event Hub metrics (`CaptureLag`, incoming messages), storage write diagnostics
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" resourceType="Microsoft.EventHub/namespaces" metric_name="CaptureLag"
| stats latest(average) as lag_ms by resourceId, bin(_time, 5m)
| where lag_ms > 600000
| eval lag_min=round(lag_ms/60000,1)
```
- **Implementation:** Ingest CaptureLag from Azure Monitor. Alert when lag exceeds SLA (for example 10 minutes). Check storage throttling and capture file naming collisions. Scale throughput units if needed.
- **Visualization:** Line chart (capture lag), Table (namespace, lag minutes), Single value (worst lag).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.40 · Azure Backup Job Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Failed or missed backup jobs leave restore gaps; operational health must be tracked per protected item.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:diagnostics` Category="AzureBackupReport" or Recovery Services job events
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="AzureBackupReport" OperationName="Backup"
| eval ok=if(match(JobStatus,"(?i)completed"),1,0)
| stats count(eval(ok=0)) as failed, count as total by BackupItemName
| where failed>0
| sort -failed
```
- **Implementation:** Parse backup job JSON from diagnostic stream. Alert on Failed, CompletedWithWarnings patterns, or missing job in expected window (lookup per item). Test restores quarterly (see UC-4.4.29).
- **Visualization:** Table (item, status), Timeline (job outcomes), Single value (failed jobs 24h).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.41 · Private Link DNS Resolution
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Private Endpoint FQDNs resolve via private DNS zones; NXDOMAIN or public resolution leaks traffic or breaks apps.
- **App/TA:** Custom (DNS query logs), `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** Azure DNS private zone query logs (if enabled), VM DNS client logs, `sourcetype=dns:query`
- **SPL:**
```spl
index=network sourcetype="dns:query" zone_type="private"
| stats count(eval(rcode!="NOERROR")) as failures, count as total by fqdn, src
| eval fail_pct=round(100*failures/total,2)
| where fail_pct > 5 AND total > 20
```
- **Implementation:** Forward DNS resolver logs from VNet-linked zones or Azure Firewall DNS proxy. Alert on high NXDOMAIN for PE FQDNs. Validate zone links and auto-registration on new NICs.
- **Visualization:** Table (fqdn, fail %), Timeline (DNS errors), Map (source subnet).
- **CIM Models:** Network_Resolution
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Network_Resolution.DNS by DNS.src | sort - count
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)

---

### UC-4.2.42 · Azure Monitor Alert Rule Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Disabled or misconfigured alert rules create silent monitoring gaps; tracking rule state protects on-call coverage.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:audit` (scheduledQueryRules, metricAlerts), Activity Log for alert changes
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:audit" (operationName.value="*scheduledQueryRules*" OR operationName.value="*metricAlerts*")
| search disable OR Disabled OR delete OR Delete
| stats count by caller, operationName.value, resourceId
| sort -_time
```
- **Implementation:** Ingest Activity Log for alert create/update/delete. Nightly compare inventory of enabled rules vs golden baseline lookup. Alert when production-critical rules are disabled > 15 minutes.
- **Visualization:** Table (rule, action, caller), Timeline (changes), Single value (disabled rules count).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.43 · Defender for Cloud Recommendations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1538
- **Value:** Secure score and recommendations drive hardening backlog; trending open recommendations shows risk posture over time.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`, Defender export API
- **Data Sources:** Defender for Cloud recommendations JSON, continuous export to Log Analytics/Event Hub
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:defender" recommendationState="Active"
| stats count by recommendationName, severity
| sort -count
```
- **Implementation:** Export recommendations on schedule via Logic App or Microsoft Graph security API to Splunk. Track mean time to remediate by severity. Executive dashboard of secure score trend if ingested.
- **Visualization:** Bar chart (recommendations by type), Table (severity, count), Line chart (open recommendations over time).
- **CIM Models:** Vulnerabilities
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Vulnerabilities.Vulnerabilities by Vulnerabilities.severity | sort - count
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Vulnerabilities](https://docs.splunk.com/Documentation/CIM/latest/User/Vulnerabilities)

---

### UC-4.2.44 · Azure Resource Lock Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1098.003
- **Value:** Locks prevent accidental deletes; removing a lock before maintenance is high risk and must be audited.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:audit` (Microsoft.Authorization/locks)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:audit" resourceId="*providers/Microsoft.Authorization/locks*"
| stats count by operationName.value, identity.claims.name, resourceGroupName
| sort -count
```
- **Implementation:** Alert on Delete or write operations against lock resources. Require change ticket in comments where possible. Correlate with subsequent delete operations on parent resources.
- **Visualization:** Table (operation, user, resource group), Timeline (lock changes).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---


### UC-4.2.45 · Azure Container Instances Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** ACI containers are short-lived and opaque without platform metrics; monitoring restarts and resource exhaustion preserves burst workloads and integrations.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics)
- **Data Sources:** `sourcetype=azure:monitor:metric` or `sourcetype=azure:diagnostics`
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.containerinstance/containergroups"
| stats avg(average) as cpu_avg, max(maximum) as cpu_peak by resource_name, resource_group
| join type=left max=1 resource_name [
    search index=cloud sourcetype="azure:diagnostics" Category="ContainerInstanceLog"
    | where match(_raw, "(?i)error|fail|OOM")
    | stats count as log_errors by resource_name
]
| where cpu_peak>85 OR log_errors>0
| sort -cpu_peak
```
- **Implementation:** Route Azure Monitor metrics for Container Instances to Splunk using the Azure Add-on (Event Hub or metrics export). Enable diagnostic logs for container groups. Normalize `resource_name` to container group. Alert on CPU/memory threshold breaches, exit code non-zero patterns in logs, and restart counts from platform events.
- **Visualization:** Line chart (CPU/memory over time), Table (container group, region, state), Bar chart (events by group).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.46 · Azure Application Gateway and WAF Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Fault
- **MITRE ATT&CK:** T1580, T1562.007
- **Value:** Application Gateway is the primary L7 load balancer for most Azure web workloads. Backend health probe failures cause 502 errors for users; WAF blocks need tuning to avoid false positives.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics)
- **Data Sources:** `sourcetype=azure:monitor:metric`, `sourcetype=azure:diagnostics` (ApplicationGatewayAccessLog, ApplicationGatewayFirewallLog)
- **SPL:**
```spl
index=cloud sourcetype="azure:diagnostics" Category="ApplicationGatewayAccessLog"
| eval is_error=if(httpStatusCode>=500,1,0)
| timechart span=5m count as total_requests, sum(is_error) as server_errors by host
| eval error_pct=round(100*server_errors/total_requests,2)
| where error_pct > 5
```
- **Implementation:** Enable diagnostics on Application Gateway to send access logs and WAF logs via Event Hub or Storage Account to Splunk. Monitor backend pool health probe status from metrics (`UnhealthyHostCount`). Alert on rising 502/504 rates, unhealthy backends, and WAF blocks that correlate with user-reported issues. Track WAF rule hit distribution to tune rule exclusions.
- **Visualization:** Line chart (request rate and error rate), Table (unhealthy backends), Bar chart (WAF blocks by rule ID).
- **CIM Models:** Network Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t sum(All_Traffic.bytes_in) as agg_value from datamodel=Network_Traffic.All_Traffic by All_Traffic.dest span=5m | sort - agg_value
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-4.2.47 · Azure VPN Gateway Tunnel Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** VPN gateway tunnel drops break hybrid connectivity between Azure and on-premises networks. Nearly every enterprise Azure customer relies on site-to-site VPN; tunnel status is a fundamental availability signal.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics)
- **Data Sources:** `sourcetype=azure:monitor:metric` (Microsoft.Network/vpnGateways)
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.network/vpngateways" metric_name="TunnelAverageBandwidth" OR metric_name="TunnelEgressBytes"
| timechart span=5m avg(average) as avg_bandwidth by resource_name
| where avg_bandwidth < 1
```
- **Implementation:** Collect Azure Monitor metrics for VPN Gateway resources. Monitor `TunnelAverageBandwidth` (drops to zero when tunnel is down), `TunnelEgressBytes`, `TunnelIngressBytes`, and `BGPPeerStatus`. Alert when tunnel bandwidth drops to zero or BGP peer status changes. Correlate with Azure Service Health events for planned maintenance.
- **Visualization:** Line chart (tunnel bandwidth over time), Single value (tunnel status up/down), Table (tunnels with status).
- **CIM Models:** Network Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t avg(All_Traffic.bytes_in) as agg_value from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port span=5m | sort - agg_value
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-4.2.48 · Azure ExpressRoute Circuit Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** ExpressRoute provides dedicated private connectivity to Azure for large enterprises. Circuit degradation or BGP peer loss causes failover to backup paths or complete connectivity loss to Azure services.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics)
- **Data Sources:** `sourcetype=azure:monitor:metric` (Microsoft.Network/expressRouteCircuits)
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.network/expressroutecircuits"
| eval metric=metric_name
| where metric IN ("BgpAvailability","ArpAvailability","BitsInPerSecond","BitsOutPerSecond")
| timechart span=5m avg(average) as value by metric, resource_name
```
- **Implementation:** Collect metrics for ExpressRoute circuits: `BgpAvailability` and `ArpAvailability` (should be 100%), `BitsInPerSecond`/`BitsOutPerSecond` for throughput trending. Alert when BGP availability drops below 100% or throughput drops to zero. Track circuit utilization against provisioned bandwidth to plan capacity upgrades.
- **Visualization:** Line chart (BGP/ARP availability %), Line chart (throughput), Single value (circuit status).
- **CIM Models:** Network Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t avg(All_Traffic.bytes_in) as agg_value from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port span=5m | sort - agg_value
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-4.2.49 · Azure Redis Cache Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** Redis Cache is a common caching and session store layer in Azure architectures. High server load, memory pressure, or cache misses directly impact application response times.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics)
- **Data Sources:** `sourcetype=azure:monitor:metric` (Microsoft.Cache/Redis)
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.cache/redis"
| where metric_name IN ("serverLoad","usedmemorypercentage","cacheHits","cacheMisses","connectedclients","evictedkeys")
| timechart span=5m avg(average) as value by metric_name, resource_name
```
- **Implementation:** Collect Azure Monitor metrics for Redis Cache resources. Key metrics: `serverLoad` (alert >80%), `usedmemorypercentage` (alert >90%), `evictedkeys` (any eviction signals memory pressure), and cache hit ratio (`cacheHits/(cacheHits+cacheMisses)`). Track `connectedclients` against tier limits. For Premium tier, monitor replication lag between primary and replica.
- **Visualization:** Gauge (server load), Line chart (memory % and hit ratio), Single value (evicted keys).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.Memory by Performance.host span=5m | sort - agg_value
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### UC-4.2.50 · Azure Data Factory Pipeline Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Data Factory orchestrates ETL/ELT pipelines that feed data warehouses, analytics, and operational systems. Pipeline failures cause stale data, broken dashboards, and missed SLAs.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics)
- **Data Sources:** `sourcetype=azure:diagnostics` (PipelineRuns, ActivityRuns, TriggerRuns)
- **SPL:**
```spl
index=cloud sourcetype="azure:diagnostics" Category="PipelineRuns"
| where status="Failed"
| stats count as failures, latest(start) as last_failure by pipelineName, resource_name
| sort -failures
```
- **Implementation:** Enable diagnostics on Data Factory to route `PipelineRuns`, `ActivityRuns`, and `TriggerRuns` to Splunk via Event Hub. Alert on failed pipeline runs. Track activity-level errors for root cause (copy failures, data flow errors, linked service timeouts). Monitor pipeline duration trending to detect degradation before SLA breach.
- **Visualization:** Table (failed pipelines with error), Bar chart (failures by pipeline), Line chart (pipeline duration trend).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.51 · Azure API Management (APIM) Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** APIM is the gateway for API-first architectures. Backend errors, high latency, and rate limit breaches directly impact API consumers and downstream applications.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics)
- **Data Sources:** `sourcetype=azure:monitor:metric` (Microsoft.ApiManagement/service), `sourcetype=azure:diagnostics` (GatewayLogs)
- **SPL:**
```spl
index=cloud sourcetype="azure:diagnostics" Category="GatewayLogs"
| eval is_error=if(responseCode>=500,1,0)
| timechart span=5m count as requests, sum(is_error) as errors, avg(totalTime) as avg_latency_ms by apiId
| eval error_pct=round(100*errors/requests,2)
| where error_pct > 5 OR avg_latency_ms > 2000
```
- **Implementation:** Enable diagnostics on APIM to send GatewayLogs via Event Hub to Splunk. Collect metrics for `Requests`, `BackendDuration`, `OverallDuration`, `FailedRequests`, and `UnauthorizedRequests`. Alert on backend error rate spikes, latency exceeding SLA thresholds, and capacity exhaustion (approaching unit limits). Track API-level usage patterns for capacity planning.
- **Visualization:** Line chart (request rate and error rate by API), Gauge (latency vs. SLA), Table (top errors by API and operation).
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest span=5m | sort - count
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)

---

### UC-4.2.52 · Azure Virtual Desktop Session Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** Azure Virtual Desktop provides remote desktop infrastructure. Connection failures, high round-trip latency, and session drops directly impact end-user productivity.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics)
- **Data Sources:** `sourcetype=azure:diagnostics` (WVDConnections, WVDErrors, WVDCheckpoints)
- **SPL:**
```spl
index=cloud sourcetype="azure:diagnostics" Category="WVDConnections"
| eval duration_min=round(SessionDuration/60000,1)
| stats count as connections, avg(duration_min) as avg_session_min, dc(UserName) as unique_users by HostPoolName, SessionHostName
| join type=left max=1 SessionHostName [
    search index=cloud sourcetype="azure:diagnostics" Category="WVDErrors"
    | stats count as errors by SessionHostName
]
| where errors > 0
| sort -errors
```
- **Implementation:** Enable diagnostics on AVD host pools to route `WVDConnections`, `WVDErrors`, and `WVDCheckpoints` to Splunk. Monitor connection success rate, average session duration, and round-trip time. Alert on connection failure spikes, session host unavailability, and high input delay (>200ms). Track session host resource utilization (CPU, memory, disk) from Azure Monitor metrics.
- **Visualization:** Table (session hosts with errors), Line chart (connections and failures over time), Single value (active sessions).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.53 · Azure Traffic Manager Endpoint Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Traffic Manager provides DNS-based global load balancing. Degraded endpoints cause traffic to shift, but undetected health changes can leave users routed to unhealthy regions.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics)
- **Data Sources:** `sourcetype=azure:monitor:metric` (Microsoft.Network/trafficManagerProfiles)
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.network/trafficmanagerprofiles" metric_name="ProbeAgentCurrentEndpointStateByProfileResourceId"
| timechart span=5m latest(average) as health_pct by resource_name
| where health_pct < 100
```
- **Implementation:** Collect Azure Monitor metrics for Traffic Manager profiles. Monitor `ProbeAgentCurrentEndpointStateByProfileResourceId` for endpoint health percentage and `QpsByEndpoint` for query distribution. Alert when any endpoint degrades or goes offline. Track DNS query patterns to verify failover behavior is correct after endpoint changes.
- **Visualization:** Status grid (endpoint × health), Line chart (health % per endpoint), Single value (degraded endpoint count).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.54 · Azure Bastion Session Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1078.004, T1580
- **Value:** Bastion provides secure, auditable VM access without public IPs. Monitoring session activity ensures compliance with access policies and detects unauthorized connection attempts.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics)
- **Data Sources:** `sourcetype=azure:diagnostics` (BastionAuditLogs)
- **SPL:**
```spl
index=cloud sourcetype="azure:diagnostics" Category="BastionAuditLogs"
| stats count as sessions, dc(targetVMIPAddress) as unique_targets by userName, clientIpAddress
| sort -sessions
```
- **Implementation:** Enable diagnostic logging on Azure Bastion to send audit logs via Event Hub. Track user sessions by `userName`, `targetVMIPAddress`, `protocol` (SSH/RDP), and `duration`. Alert on connections to unexpected VMs, connections from unusual IP addresses, and failed authentication attempts. Correlate with Entra ID sign-in logs for identity context.
- **Visualization:** Table (sessions by user and target), Bar chart (sessions by protocol), Line chart (session count over time).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user | sort - count
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)

---

### UC-4.2.55 · Azure Network Watcher Connection Troubleshooting
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Network Watcher captures flow logs, connection monitors, and packet captures for Azure networks. Proactive monitoring of connectivity test results detects network issues before they impact applications.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics)
- **Data Sources:** `sourcetype=azure:diagnostics` (NetworkSecurityGroupFlowEvent), `sourcetype=azure:monitor:metric` (Connection Monitor)
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.network/networkwatchers/connectionmonitors"
| where metric_name="ChecksFailedPercent"
| timechart span=5m avg(average) as failed_pct by resource_name
| where failed_pct > 10
```
- **Implementation:** Configure Connection Monitor tests for critical network paths (VM-to-VM, VM-to-PaaS, on-prem-to-Azure). Collect `ChecksFailedPercent`, `RoundTripTimeMs`, and `TestResult` metrics. Alert when failed check percentage exceeds threshold or round-trip time degrades significantly. Use NSG flow logs enriched with Traffic Analytics for deeper investigation.
- **Visualization:** Line chart (check failure % by monitor), Table (failing paths), Single value (overall connectivity health).
- **CIM Models:** Network Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t avg(All_Traffic.bytes_in) as agg_value from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port span=5m | sort - agg_value
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-4.2.56 · Azure Storage Queue Depth and Poison Messages
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Fault
- **Value:** Storage Queues decouple application components. Growing queue depth indicates consumers cannot keep up; poison messages in the poison queue represent permanently failed processing that needs attention.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics)
- **Data Sources:** `sourcetype=azure:monitor:metric` (Microsoft.Storage/storageAccounts/queueServices)
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.storage/storageaccounts" metric_name="QueueMessageCount"
| timechart span=5m avg(average) as queue_depth by resource_name
| where queue_depth > 1000
```
- **Implementation:** Collect Azure Monitor metrics for Storage Account queue services. Monitor `QueueMessageCount` for growing backlogs and `QueueCapacity` for storage limits. Set up a separate alert for poison queues (queues ending in `-poison`) with any messages. Alert when main queue depth exceeds baseline by 3x or poison queue is non-empty.
- **Visualization:** Line chart (queue depth over time), Single value (current depth), Table (queues with poison messages).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.2.57 · Azure Managed Disk Performance Throttling
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Azure managed disks have IOPS and throughput caps based on tier and size. When VMs hit these limits, disk I/O is throttled, causing application slowdowns that are hard to diagnose without platform metrics.
- **App/TA:** `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics)
- **Data Sources:** `sourcetype=azure:monitor:metric` (Microsoft.Compute/disks)
- **SPL:**
```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.compute/disks"
| where metric_name IN ("DiskIOPSReadWrite","DiskMBpsReadWrite","BurstIOCreditsConsumedPercentage")
| timechart span=5m avg(average) as value by metric_name, resource_name
```
- **Implementation:** Collect Azure Monitor metrics for managed disks. Monitor `Composite Disk Read/Write IOPS` against the disk SKU IOPS limit and `Composite Disk Read/Write Bytes/sec` against the throughput limit. For burstable disks, track `BurstIOCreditsConsumedPercentage` — when credits exhaust, performance drops to baseline. Alert when consumption exceeds 90% of provisioned capacity sustained over 15 minutes.
- **Visualization:** Gauge (IOPS vs. limit), Line chart (throughput and burst credits), Table (disks hitting limits).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.Storage by Performance.host span=5m | sort - agg_value
```

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [Splunk Add-on for Google Cloud Platform](https://splunkbase.splunk.com/app/3088), [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)

---

### 4.3 Google Cloud Platform (GCP)

**Primary App/TA:** Splunk Add-on for Google Cloud Platform (`Splunk_TA_google-cloudplatform`) — Free on Splunkbase

---

### UC-4.3.1 · Audit Log Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1580, T1526
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

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.3.2 · IAM Policy Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1098.001, T1098.003
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

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.3.3 · VPC Flow Log Analysis
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **MITRE ATT&CK:** T1580, T1526
- **Value:** GCP VPC Flow Logs provide network traffic visibility. Same use case as AWS/Azure — detect rejected traffic, anomalies, exfiltration.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** VPC Flow Logs via Pub/Sub
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*vpc_flows"
| spath
| eval src=coalesce(src,'connection.src_ip'), dest=coalesce(dest,'connection.dest_ip'), dest_port=coalesce(dest_port,'connection.dest_port')
| stats sum(bytes_sent) as total_bytes by src, dest, dest_port
| sort -total_bytes | head 20
```
- **Implementation:** Enable VPC Flow Logs on subnets. Sink to Pub/Sub and ingest in Splunk. Analyze for top talkers, rejected flows, and anomalous destinations.
- **Visualization:** Table, Sankey diagram, Timechart, Map.
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

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

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.5 · Security Command Center
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580, T1526
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

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.6 · GCE Instance Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **MITRE ATT&CK:** T1578.002
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

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.7 · BigQuery Audit and Cost
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **MITRE ATT&CK:** T1530, T1619
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

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

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

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.9 · Cloud Load Balancing Backend Health and Request Count
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Unhealthy backends receive no traffic; request count and latency indicate load and performance. Essential for global and regional LB reliability.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Cloud Monitoring (loadbalancing.googleapis.com/https/request_count, backend_utilization)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="loadbalancing.googleapis.com/https/backend_utilization"
| where value > 0.9
| timechart span=5m avg(value) by resource.labels.backend_name
```
- **Implementation:** Collect Load Balancing metrics. Alert when backend health is unhealthy or backend_utilization >90%. Monitor request_count and latency by backend and URL map.
- **Visualization:** Status panel (backend health), Line chart (requests, latency by backend), Table (backend, utilization).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.10 · Cloud Pub/Sub Subscription Backlog and Dead Letter
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Backlog (unacked messages) and dead-letter count indicate consumers falling behind or failing. Prevents message loss and SLA breach.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Cloud Monitoring (pubsub.googleapis.com/subscription/num_undelivered_messages, dead_letter_message_count)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages"
| where value > 1000
| timechart span=5m avg(value) by resource.labels.subscription_id
```
- **Implementation:** Collect Pub/Sub subscription metrics. Alert when num_undelivered_messages exceeds threshold or dead_letter_message_count > 0. Monitor old_unacked_message_age for consumer lag.
- **Visualization:** Line chart (backlog, dead letter by subscription), Table (subscription, backlog), Single value (max backlog).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.11 · Cloud Storage (GCS) Request Metrics and Cost
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **MITRE ATT&CK:** T1619, T1530
- **Value:** GCS request count and latency support performance tuning. Cost tracking by bucket/class prevents bill shock.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Cloud Monitoring (storage.googleapis.com/request_count), Billing export
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="storage.googleapis.com"
| spath output=method path=protoPayload.methodName
| stats count by method resource.labels.bucket_name
| sort -count
```
- **Implementation:** Enable GCS request logging to Cloud Logging; sink to Pub/Sub for Splunk. Collect storage metrics. Ingest billing export for cost by bucket. Alert on anomalous request volume or cost spike.
- **Visualization:** Line chart (requests, cost by bucket), Table (bucket, method, count), Bar chart (cost by bucket).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.12 · Cloud SQL Instance Metrics and Replication Lag
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Cloud SQL CPU, storage, and replication lag impact application performance and DR. Monitoring supports capacity and replica health.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Cloud Monitoring (cloudsql.googleapis.com/database/cpu/utilization, replication/replica_lag)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="cloudsql.googleapis.com/database/replication/replica_lag"
| where value > 10
| timechart span=5m avg(value) by resource.labels.database_id
```
- **Implementation:** Collect Cloud SQL metrics. Alert when replica_lag > 10 seconds or CPU utilization > 80%. Monitor disk utilization and connection count. Enable slow query log for query-level analysis.
- **Visualization:** Line chart (CPU, lag, connections by instance), Table (instance, lag), Gauge (replica lag).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.13 · Cloud Build Build Failures and Duration
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Build failures block deployments. Duration trends support pipeline optimization and quota management.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Cloud Build logs via Pub/Sub (build completion events)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="build" status="FAILURE"
| table _time buildId triggerId status message
| sort -_time
```
- **Implementation:** Sink Cloud Build logs to Pub/Sub; ingest in Splunk. Alert when status=FAILURE or TIMEOUT. Track build duration and success rate by trigger. Correlate with source repo and branch.
- **Visualization:** Line chart (builds, failures by trigger), Table (build, trigger, status, duration), Single value (failure rate).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.14 · GKE Node Pool Autoscaling and Upgrade Events
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Node pool scale-up/down and upgrade events affect workload placement and availability. Monitoring supports capacity and upgrade windows.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** GKE cluster logs, Cloud Monitoring (container metrics)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="k8s_cluster" textPayload=*"upgrade"*
| table _time resource.labels.cluster_name textPayload
| sort -_time
```
- **Implementation:** Ingest GKE logs (cluster operations, node pool events). Monitor node count and autoscaler events. Track upgrade and maintenance window events. Alert on node pool scaling failures.
- **Visualization:** Timeline (node pool events), Table (cluster, pool, node count), Line chart (node count over time).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.15 · Cloud CDN Cache Hit Ratio and Egress
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Cache hit ratio and egress volume impact latency and cost. Low hit ratio increases origin load and egress charges.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Cloud Monitoring (cdn.googleapis.com/cache/hit_ratio, egress)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="cdn.googleapis.com/cache/hit_ratio"
| timechart span=1h avg(value) by resource.labels.origin_name
| where hit_ratio < 0.7
```
- **Implementation:** Collect CDN metrics. Calculate hit ratio from cache hits and misses. Alert when hit ratio < 70% or egress spike. Optimize cache TTL and key design based on metrics.
- **Visualization:** Line chart (hit ratio, egress by origin), Table (origin, hit ratio), Gauge (overall hit ratio).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.16 · Artifact Registry Push/Pull and Vulnerability Scan
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1610, T1613
- **Value:** Unusual push/pull may indicate abuse. Vulnerability scan findings in images require remediation before deployment.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Audit logs (Artifact Registry API), Container Analysis (vulnerability occurrences)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="artifactregistry.googleapis.com"
| spath output=method path=protoPayload.methodName
| stats count by method resource.labels.repository
| sort -count
```
- **Implementation:** Forward Artifact Registry audit logs via Pub/Sub. Ingest Container Analysis for CVE findings. Alert on critical/high in production repos. Baseline push/pull by principal; alert on anomalies.
- **Visualization:** Table (repo, method, count), Bar chart (top push/pull), Table (image, CVE, severity).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.17 · Cloud Logging Export Sink and Exclusion Filter
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **MITRE ATT&CK:** T1562.008
- **Value:** Log sink and exclusion changes affect what is exported to Splunk or other destinations. Unauthorized changes create visibility gaps.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Audit logs (logging.googleapis.com)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="logging.googleapis.com" (protoPayload.methodName="CreateSink" OR protoPayload.methodName="UpdateSink" OR protoPayload.methodName="DeleteSink")
| table _time protoPayload.authenticationInfo.principalEmail protoPayload.methodName resource.labels.sink_id
| sort -_time
```
- **Implementation:** Forward audit logs. Alert on CreateSink, UpdateSink, DeleteSink. Track sink destinations and filters. Ensure critical sinks (e.g. to Pub/Sub for Splunk) are not modified without change control.
- **Visualization:** Table (who, what, sink), Timeline (sink changes), Single value (sink count).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.3.18 · Cloud IAM Policy and Binding Changes (Beyond SetIamPolicy)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1098.001, T1098.003
- **Value:** IAM policy and custom role changes affect who can access resources. Broader than SetIamPolicy — includes role create/delete and org policy.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Audit logs (iam.googleapis.com, admin.googleapis.com)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="iam.googleapis.com" (protoPayload.methodName=*Create* OR protoPayload.methodName=*Delete* OR protoPayload.methodName=*Update*)
| table _time protoPayload.authenticationInfo.principalEmail protoPayload.methodName resource.labels
| sort -_time
```
- **Implementation:** Forward IAM and Admin API audit logs. Alert on CreateRole, DeleteRole, SetIamPolicy on project/folder/org. Track custom role changes. Correlate with security review process.
- **Visualization:** Table (principal, method, resource), Timeline (IAM changes), Bar chart by method.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.3.19 · Cloud Billing Budget Alerts and Anomaly
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Budget alerts and spend anomalies prevent cost overruns. Early detection enables corrective action before invoice.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Billing export to BigQuery or Pub/Sub, Budget alert notifications
- **SPL:**
```spl
index=gcp sourcetype="gcp:billing"
| timechart span=1d sum(cost) by service
| eventstats avg(cost) as avg_cost stdev(cost) as stdev_cost by service
| where cost > avg_cost + 2*stdev_cost
```
- **Implementation:** Enable billing export. Ingest daily/monthly cost data. Create budget alerts and forward to Splunk. Calculate baseline and alert on 2-sigma anomaly by service or project.
- **Visualization:** Line chart (cost with threshold), Table (service, cost, anomaly), Stacked area (cost by service).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.20 · Cloud Armor Security Policy and DDoS Metrics
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1562.007, T1580
- **Value:** Cloud Armor blocks and DDoS metrics indicate attack traffic and policy effectiveness. Essential for WAF and DDoS visibility.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Cloud Logging (loadbalancing.googleapis.com/http_requests with security policy), Cloud Monitoring (DDoS metrics)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" jsonPayload.enforcedSecurityPolicy.name=*
| stats count by jsonPayload.enforcedSecurityPolicy.outcome jsonPayload.enforcedSecurityPolicy.name
| sort -count
```
- **Implementation:** Enable HTTP(S) LB logging with security policy info. Ingest in Splunk. Alert on high block rate or DDoS mitigation events. Dashboard allowed vs denied by rule and source.
- **Visualization:** Table (policy, outcome, count), Bar chart (blocks by rule), Timeline (block rate).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.21 · Cloud Run Revision Traffic and Error Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Cloud Run revision traffic and errors indicate service health. Supports canary and blue-green deployment monitoring.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Cloud Run metrics (request_count, container_instance_count, container_cpu_utilizations)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="run.googleapis.com/request_count"
| timechart span=5m sum(value) by resource.labels.revision_name
| eval error_rate = request_count_5xx / request_count * 100
| where error_rate > 1
```
- **Implementation:** Collect Cloud Run metrics. Alert on 5xx rate >1% or container instance count spike. Monitor cold start and latency. Track traffic split across revisions for canary analysis.
- **Visualization:** Line chart (requests, errors by revision), Table (revision, error rate), Gauge (traffic % by revision).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.22 · Dataproc Cluster and Job Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Dataproc cluster and job failures break data pipelines. Monitoring supports reliability and cost (preemptible) optimization.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Dataproc logs (cluster and job state), Cloud Monitoring (dataproc cluster metrics)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="dataproc_cluster" severity="ERROR"
| table _time resource.labels.cluster_name textPayload
| sort -_time
```
- **Implementation:** Sink Dataproc logs to Pub/Sub. Ingest cluster state and job completion. Alert on cluster ERROR or job FAILED. Monitor preemptible node loss for cost vs. reliability trade-off.
- **Visualization:** Table (cluster, job, state), Timeline (job failures), Bar chart (failures by job type).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.23 · VPC Service Controls Perimeter Violations
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1562.007
- **Value:** VPC Service Controls enforce network perimeter. Violations indicate data exfiltration attempts or misconfigured access. Critical for data perimeter security.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Access Context Manager / VPC SC audit logs (perimeter violation events)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="accesscontextmanager.googleapis.com"
| search "violation" OR "perimeter"
| table _time protoPayload.authenticationInfo.principalEmail protoPayload.requestMetadata.callerIp resource
| sort -_time
```
- **Implementation:** Enable VPC SC violation logging. Forward to Pub/Sub and Splunk. Alert on every violation. Correlate with principal, source IP, and resource. Use for perimeter tuning and incident response.
- **Visualization:** Table (principal, resource, violation), Timeline (violations), Map (source IPs).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.24 · GCP Cloud Run Cold Start Rate
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Serverless cold start impact on request latency. High cold start rates cause P99 latency spikes and timeouts for scale-to-zero services.
- **App/TA:** Custom (GCP Monitoring API)
- **Data Sources:** Cloud Run metrics (request_latencies, instance_count, container/startup_latencies)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="run.googleapis.com/request_count" OR metric.type="run.googleapis.com/container/instance_count"
| eval metric_type=coalesce(metric.type, 'run.googleapis.com/request_count')
| stats sum(value) as requests, latest(value) as instances by resource.labels.service_name, metric_type, bin(_time, 5m)
| eval cold_start_indicator=if(instances=0 AND requests>0, 1, 0)
| stats sum(requests) as total_requests, sum(cold_start_indicator) as cold_start_events by resource.labels.service_name
| eval cold_start_pct=round(cold_start_events/total_requests*100, 1)
| where cold_start_pct > 5
| table resource.labels.service_name total_requests cold_start_events cold_start_pct
| sort -cold_start_pct
```
- **Implementation:** Use GCP Monitoring API (or Cloud Monitoring export) to ingest Cloud Run metrics. Request count and instance count indicate scale-to-zero; zero instances with requests implies cold starts. For detailed latency, ingest `run.googleapis.com/request_latencies` and `run.googleapis.com/container/startup_latencies`. Alert when cold start rate exceeds 5% or startup latency > 3s. Consider min instances for latency-critical services.
- **Visualization:** Line chart (cold start % and startup latency by service over time), Table (service, cold starts, %), Single value (cold start rate).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.3.25 · BigQuery Slot Usage Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** Slot contention slows queries and raises cost; tracking slot usage versus reservation prevents interactive BI outages and runaway batch jobs.
- **App/TA:** `Splunk_TA_google-cloudplatform`, BigQuery INFORMATION_SCHEMA export
- **Data Sources:** `sourcetype=google:gcp:monitoring` (`bigquery.googleapis.com/slot/usage`), audit exports to Pub/Sub
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="bigquery.googleapis.com/slot/usage"
| stats latest(value) as slot_seconds by resource.labels.project_id, bin(_time, 5m)
| eventstats avg(slot_seconds) as baseline by resource.labels.project_id
| where slot_seconds > baseline * 1.5
| table _time resource.labels.project_id slot_seconds baseline
```
- **Implementation:** Ingest Cloud Monitoring metrics for slot usage and optional `JOBS_BY_PROJECT` exports. Alert when usage exceeds reservation plus burst buffer or sustained elevation vs 7-day baseline. Dashboard by reservation assignment and job type.
- **Visualization:** Area chart (slot usage vs cap), Table (project, peak slots), Single value (utilization %).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.26 · GKE Autopilot Pod Scaling
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Autopilot scales node pools automatically; failed scale-outs leave pods pending and degrade SLOs.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:pubsub:message` (GKE cluster logs), `sourcetype=google:gcp:monitoring` (scheduler, pending pods)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="k8s_cluster" ("FailedScheduling" OR "Insufficient cpu" OR "Insufficient memory")
| stats count by resource.labels.cluster_name, jsonPayload.reason
| sort -count
```
- **Implementation:** Enable GKE logging and filter for scheduling events. Correlate with pending pod metrics if exported. Alert on rising pending pod count or repeated scale failures.
- **Visualization:** Timeline (scheduling failures), Table (cluster, reason, count), Line chart (pending pods).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.27 · Cloud Armor WAF Events
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580, T1562.007
- **Value:** WAF blocks indicate attack traffic or misrules; separating noise from targeted campaigns protects edge apps behind HTTPS load balancers.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** HTTP(S) LB request logs with Cloud Armor, `sourcetype=google:gcp:pubsub:message` (loadbalancing.googleapis.com/requests)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*requests" httpRequest.status=403
| search enforcedSecurityPolicy OR CLOUD_ARMOR
| stats count by jsonPayload.enforcedSecurityPolicy.name, httpRequest.remoteIp, httpRequest.requestUrl
| sort -count
```
- **Implementation:** Enable logging on security policies and sink to Pub/Sub. Parse rule ID and preview vs enforce. Alert on spike vs baseline or new country/ASN concentration. Tune rules to reduce false positives.
- **Visualization:** Bar chart (rule hits), Map (client IP geo), Timeline (block rate).
- **CIM Models:** Intrusion_Detection
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.action, IDS_Attacks.signature, IDS_Attacks.src, IDS_Attacks.dest | sort - count
```

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088), [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)

---

### UC-4.3.28 · VPC Service Controls Violations
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1562.007
- **Value:** Real-time violation tracking complements perimeter design reviews and catches data exfiltration paths early.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Access Context Manager audit via `sourcetype=google:gcp:pubsub:message`
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="accesscontextmanager.googleapis.com"
| search violation OR denied OR blocked
| stats count by protoPayload.authenticationInfo.principalEmail, resource.labels.project_id
| sort -count
```
- **Implementation:** Ensure VPC SC dry-run and enforce modes both log. Route to SIEM with severity by service (BigQuery, GCS). Weekly review of top principals for false positives.
- **Visualization:** Table (principal, project, count), Timeline (violations), Pie chart (service).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.29 · Pub/Sub Subscription Backlog
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Growing backlog signals consumer lag or under-provisioned workers; oldest-unacked age breaches processing SLAs.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:monitoring` (`pubsub.googleapis.com/subscription/num_undelivered_messages`, `oldest_unacked_message_age`)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages"
| stats latest(value) as backlog by resource.labels.subscription_id, bin(_time, 5m)
| where backlog > 10000
| sort - backlog
```
- **Implementation:** Set per-subscription SLOs for max backlog and oldest age. Scale push subscribers or fix poison messages. Use dead-letter topics for bad payloads.
- **Visualization:** Line chart (backlog over time), Single value (oldest message age), Table (subscription, backlog).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.30 · Security Command Center Findings
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580, T1526
- **Value:** SCC aggregates misconfigurations and threats; operationalizing findings closes gaps faster than periodic console reviews.
- **App/TA:** `Splunk_TA_google-cloudplatform` (Pub/Sub export)
- **Data Sources:** `sourcetype=google:gcp:pubsub:message` (SCC findings JSON), SCC Pub/Sub notifications
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" sourceProperties.ResourceName=*
| spath path=finding
| search finding.state="ACTIVE" (finding.severity="HIGH" OR finding.severity="CRITICAL")
| stats latest(finding.createTime) as seen by finding.category, resource
| sort -seen
```
- **Implementation:** Enable continuous export or finding notifications to Pub/Sub. Map categories to owners. Auto-ticket CRITICAL; weekly review HIGH. Deduplicate by finding ID across updates.
- **Visualization:** Table (category, resource, severity), Bar chart (findings by category), Timeline (new findings).
- **CIM Models:** Vulnerabilities
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Vulnerabilities.Vulnerabilities by Vulnerabilities.category | sort - count
```

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088), [CIM: Vulnerabilities](https://docs.splunk.com/Documentation/CIM/latest/User/Vulnerabilities)

---

### UC-4.3.31 · Cloud KMS Key Rotation Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1098.001
- **Value:** Crypto policy often mandates rotation; tracking next rotation time avoids audit findings and forced emergency rotations.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:pubsub:message` (cloudkms.googleapis.com audit), Asset Inventory key metadata
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="cloudkms.googleapis.com" protoPayload.methodName="*CryptoKey*"
| stats latest(protoPayload.request.nextRotationTime) as next_rot by resource.labels.key_ring_id, resource.labels.crypto_key_id
| eval days=round((strptime(next_rot,"%Y-%m-%dT%H:%M:%SZ")-now())/86400,0)
| where days < 30 OR isnull(days)
```
- **Implementation:** Nightly sync key metadata including rotation period and next rotation. Alert when rotation overdue or manual rotation gaps detected. Include CMEK keys for BigQuery and GCS.
- **Visualization:** Table (key, days to rotation), Timeline (rotation events), Single value (keys out of compliance).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.32 · Cloud Logging Sink Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **MITRE ATT&CK:** T1562.008
- **Value:** Broken sinks drop audit and security logs silently; monitoring export errors preserves compliance and detection coverage.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:pubsub:message` (logging sink errors), Admin Activity for sink changes
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*logging*" (severity="ERROR" OR "SinkDisappeared" OR "WriteError")
| stats count by resource.labels.project_id, textPayload
| sort -count
```
- **Implementation:** Enable log metrics on sink write errors to Pub/Sub destinations. Alert on any error count > 0 in 15 minutes. Verify Pub/Sub IAM and destination bucket permissions after changes.
- **Visualization:** Single value (sink errors), Table (project, error text), Timeline.
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.33 · GKE Node Auto-Repair Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Auto-repair replaces unhealthy nodes; frequent repairs indicate image, disk, or hardware issues affecting workload stability.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** GKE node pool operations in `sourcetype=google:gcp:pubsub:message`, cluster operations log
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.methodName="repairNodePool" OR textPayload="*auto-repair*"
| stats count by resource.labels.cluster_name, resource.labels.node_pool
| sort -count
```
- **Implementation:** Correlate repairs with container restarts and kernel OOM. Alert when repairs per day exceed baseline for a pool. Review node image version skew.
- **Visualization:** Bar chart (repairs by pool), Timeline (repair events), Table (cluster, pool, count).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.34 · Dataflow Pipeline Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Batch and streaming pipelines power analytics; failed jobs or high system lag delay downstream consumers.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:monitoring` (`dataflow.googleapis.com/job/*`), Dataflow worker logs
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="dataflow.googleapis.com/job/system_lag"
| stats latest(value) as lag_sec by resource.labels.job_name, bin(_time, 5m)
| where lag_sec > 300
| sort - lag_sec
```
- **Implementation:** Ingest job state changes (FAILED, UPDATED) from logging. Alert on sustained system lag for streaming jobs or failed batch completion. Dashboard worker CPU and shuffle errors.
- **Visualization:** Line chart (system lag), Table (job, state), Timeline (job failures).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.35 · Cloud SQL Connection Limits
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Hitting max connections causes application errors; trending connections versus tier limits guides pool sizing and read replicas.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:monitoring` (`cloudsql.googleapis.com/database/network/connections`, `postgresql.googleapis.com/connection_count`)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="cloudsql.googleapis.com/database/network/connections"
| stats latest(value) as conns by resource.labels.database_id, bin(_time, 5m)
| lookup cloudsql_tier_limits database_id OUTPUT max_connections
| where conns > max_connections * 0.85
```
- **Implementation:** Maintain lookup of instance tier to max connections. Alert at 85% sustained. Correlate with connection pool metrics from apps. Plan vertical scale or read replicas before hard failures.
- **Visualization:** Line chart (connections vs limit), Gauge (utilization %), Table (instance, conns).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.36 · Memorystore (Redis) Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Redis backs sessions and caches; memory pressure and replication lag cause timeouts and stale reads.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:monitoring` (`redis.googleapis.com/stats/memory/usage_ratio`, `replication/role`, `cpu/utilization`)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="redis.googleapis.com/stats/memory/usage_ratio"
| stats latest(value) as mem_ratio by resource.labels.instance_id, bin(_time, 5m)
| where mem_ratio > 0.9
| sort - mem_ratio
```
- **Implementation:** Alert on memory usage above 90%, high CPU, or replica lag metrics. Plan tier upgrades or key eviction policies. Monitor persistence (RDB/AOF) failures if enabled.
- **Visualization:** Line chart (memory ratio, CPU), Table (instance, tier), Single value (evictions if exported).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.37 · Cloud CDN Cache Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Low hit ratio raises origin load and latency; optimizing cache keys and TTL improves cost and user experience.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** HTTP(S) LB logs with cache fill/lookup fields, `sourcetype=google:gcp:monitoring` (cdn metrics)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" httpRequest.latency!=""
| eval cache_hit=if(match(_raw,"cacheHit|CACHE_HIT"),1,0)
| stats sum(cache_hit) as hits, count as total by resource.labels.url_map_name
| eval hit_ratio=round(100*hits/total,2)
| where hit_ratio < 60 AND total > 1000
| sort hit_ratio
```
- **Implementation:** Parse cache hit/miss from load balancer logs. Segment by content type and geography. Alert when hit ratio drops vs 14-day baseline. Review cache mode and Vary headers.
- **Visualization:** Line chart (hit ratio by URL map), Bar chart (origin egress), Table (backend, hit %).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.3.38 · GCS Bucket Policy Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1530, T1619
- **Value:** Public buckets and IAM relaxations are common breach paths; real-time detection limits exposure window.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** Admin Activity `sourcetype=google:gcp:pubsub:message` (storage.setIamPermissions, bucket updates)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="storage.googleapis.com" protoPayload.methodName="storage.buckets.setIamPermissions"
| spath path=protoPayload.serviceData.policy.bindings{}
| mvexpand protoPayload.serviceData.policy.bindings{} limit=500
| search bindings.members="allUsers" OR bindings.members="allAuthenticatedUsers"
| table _time protoPayload.authenticationInfo.principalEmail resource.labels.bucket_name bindings.role
```
- **Implementation:** Alert on any allUsers/allAuthenticatedUsers binding or removal of org constraints. Weekly review of bucket-level IAM diffs. Integrate with SCC public bucket findings.
- **Visualization:** Table (bucket, principal, role), Timeline (IAM changes), Single value (public buckets).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### UC-4.3.39 · Anthos Service Mesh Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Istio-based meshes add control-plane and sidecar failure modes; monitoring error budgets and latency protects microservices SLOs.
- **App/TA:** `Splunk_TA_google-cloudplatform`, Anthos Service Mesh telemetry
- **Data Sources:** `sourcetype=google:gcp:monitoring` (Istio canonical metrics)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring"
| where match(metric.type, "(istio|kubernetes\.io/istio)")
| stats avg(value) as err_rate by metric.labels.destination_service_name
| where err_rate > 0.01
| sort - err_rate
```
- **Implementation:** Export Istio canonical metrics (4xx/5xx, request duration) to Cloud Monitoring and Splunk. Dashboard golden signals per service. Alert on error rate > 1% or p99 latency vs SLO. Include control plane (istiod) pod health.
- **Visualization:** Service mesh graph (external tool) plus Table (service, error rate), Line chart (p50/p99 latency).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---


### UC-4.3.40 · GCP Cloud Run Task Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Cloud Run scales to zero and on demand; tracking request latency, instance count, and error ratio catches cold-start and quota issues before customers notice.
- **App/TA:** `Splunk_TA_google-cloudplatform` (Pub/Sub logging/metrics) or OTel export from Cloud Ops
- **Data Sources:** `sourcetype=google:gcp:pubsub:message` or `sourcetype=gcp:monitoring:timeseries`
- **SPL:**
```spl
index=cloud sourcetype="gcp:monitoring:timeseries"
| where like(metric.type, "run.googleapis.com%")
| stats avg(value) as val_avg, max(value) as val_max by metric.type
| where match(metric.type, "(?i)request|latency|instance|container")
| sort -val_max
```
- **Implementation:** Export Cloud Run request, latency, and instance metrics via GCP monitoring sink to Pub/Sub and ingest with `Splunk_TA_google-cloudplatform`, or forward OpenTelemetry from a sidecar/collector if you run hybrid instrumentation. Ensure `service_name` and `revision_name` are extracted. Alert on elevated `server_request_latencies` and `5xx` ratio versus SLO.
- **Visualization:** Time chart (p95 latency, request rate), Table (service, revision, error rate), Single value (active instances).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### 4.4 Multi-Cloud & Cloud Management

---

### UC-4.4.1 · Terraform Drift Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **MITRE ATT&CK:** T1578
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.2 · Cross-Cloud Identity Correlation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1078.004, T1580
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.4 · Cloud Resource Tagging Compliance
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1578
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

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.5 · Cloud Resource Inventory and Drift Summary
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **MITRE ATT&CK:** T1580, T1526
- **Value:** Unified inventory of resources across AWS/Azure/GCP supports compliance, cost, and drift detection. Drift summary highlights resources changed outside IaC.
- **App/TA:** Combined cloud TAs, Config/Policy exports, or third-party CSPM
- **Data Sources:** AWS Config, Azure Resource Graph, GCP Asset Inventory (or provider APIs)
- **SPL:**
```spl
index=aws OR index=azure OR index=gcp
| eval cloud=case(index="aws","AWS", index="azure","Azure", index="gcp","GCP")
| eval resource_type=coalesce(resourceType, type, resource.type)
| stats dc(resourceId) as resource_count values(cloud) as clouds by resource_type
| sort -resource_count
```
- **Implementation:** Export resource inventory from each provider (Config snapshot, Resource Graph query, Asset Inventory API) to S3/storage or stream to Splunk. Normalize resource type and tags. Dashboard resource count by type and cloud. Compare with IaC state for drift.
- **Visualization:** Table (type, cloud, count), Stacked bar (resources by cloud), Pie chart (resource distribution).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.6 · Multi-Cloud Security Posture (CSPM) Findings
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580, T1526
- **Value:** CSPM tools (or native Security Hub, Defender, SCC) produce findings across clouds. Centralizing in Splunk enables unified prioritization and remediation tracking.
- **App/TA:** Splunk TAs for each cloud, or CSPM product integration (e.g. Prisma Cloud, Wiz)
- **Data Sources:** AWS Security Hub, Azure Defender/Security Center, GCP Security Command Center, or third-party CSPM API
- **SPL:**
```spl
index=security (sourcetype=aws:securityhub OR sourcetype=azure:defender OR sourcetype=gcp:scc)
| eval cloud=case(sourcetype="aws*","AWS", sourcetype="azure*","Azure", sourcetype="gcp*","GCP")
| eval severity=coalesce(severity, Severity, finding.severity)
| where severity="CRITICAL" OR severity="HIGH"
| stats count by cloud severity finding_type
| sort -count
```
- **Implementation:** Ingest Security Hub, Defender for Cloud, and SCC findings into a common index. Normalize severity and finding type. Alert on new critical/high. Dashboard open findings by cloud, severity, and category (e.g. encryption, networking).
- **Visualization:** Table (cloud, severity, type, count), Bar chart (findings by cloud), Trend line (findings over time).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.7 · Cross-Cloud Log Ingestion Pipeline Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **MITRE ATT&CK:** T1562.008
- **Value:** Log pipelines (CloudTrail → S3 → Splunk, Event Hub → Splunk, Pub/Sub → Splunk) can break. Monitoring pipeline health ensures no audit or observability gaps.
- **App/TA:** Splunk _internal, ingest metrics, or custom heartbeat
- **Data Sources:** Splunk ingest metrics (by source/sourcetype), heartbeat searches, or pipeline-specific metrics (e.g. S3 object count, Event Hub lag)
- **SPL:**
```spl
index=_internal source=*metrics* group=per_sourcetype_thruput
| eval delay_minutes = (now() - _time) / 60
| where delay_minutes > 15 AND (sourcetype=*aws* OR sourcetype=*azure* OR sourcetype=*gcp*)
| table sourcetype last_time delay_minutes
```
- **Implementation:** Track last event time per cloud sourcetype (e.g. aws:cloudtrail, mscs:azure:audit, google:gcp:pubsub). Alert when no events received for >15–30 minutes. Monitor Event Hub consumer lag and Pub/Sub subscription backlog as pipeline indicators.
- **Visualization:** Table (sourcetype, last event, delay), Single value (stale pipelines), Timeline (ingest volume by source).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.8 · Cloud Spend by Tag or Project (Chargeback)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Allocating cost by tag (AWS/Azure) or project/label (GCP) enables chargeback and showback. Supports budget accountability and optimization by team.
- **App/TA:** Combined cloud TAs, CUR, Azure Cost Management export, GCP Billing export
- **Data Sources:** AWS CUR (with tag allocation), Azure Cost Management (by tag/resource group), GCP Billing (by project/labels)
- **SPL:**
```spl
index=aws sourcetype="aws:billing"
| spath path=resourceTags output=tags
| mvexpand tags limit=500
| rex field=tags "^(?<tag_key>[^:]+):(?<tag_value>.+)$"
| stats sum(BlendedCost) as cost by tag_key tag_value
| where tag_key="Owner" OR tag_key="Team"
| sort -cost
```
- **Implementation:** Ingest billing data with tag/project dimensions. Normalize tag keys (e.g. Owner, Team, Environment). Dashboard cost by tag/project and trend. Set budget alerts per tag/project. Reconcile with actual invoices.
- **Visualization:** Stacked bar (cost by tag value), Table (tag, cost, % of total), Line chart (cost trend by team).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.9 · Reserved Capacity and Savings Plan Utilization (Multi-Cloud)
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** AWS RIs/SPs, Azure Reservations, and GCP Committed Use discounts reduce cost when utilized. Low utilization wastes commitment spend.
- **App/TA:** Combined cloud TAs, billing and usage exports
- **Data Sources:** AWS CUR (RI/SP usage), Azure Cost Management (reservation utilization), GCP Committed Use reports
- **SPL:**
```spl
index=aws sourcetype="aws:billing" lineItem_LineItemType=*Reserved* OR lineItem_LineItemType=*Savings*
| stats sum(lineItem_UnblendedCost) as cost sum(lineItem_UsageAmount) as usage by product_instanceType reservation_ReservationARN
| eval utilization_pct = usage / reserved_units * 100
| where utilization_pct < 70
```
- **Implementation:** Ingest reservation and usage data from each provider. Calculate utilization (used vs. committed). Dashboard utilization by type and account/project. Alert when utilization < 70% to trigger right-sizing or exchange.
- **Visualization:** Table (reservation, type, utilization %), Gauge (overall utilization), Bar chart (waste by type).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.10 · Cloud API Rate Limit and Throttling (429) Trends
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **MITRE ATT&CK:** T1526, T1580
- **Value:** 429 (Too Many Requests) from cloud APIs indicate client or provider throttling. Tracking trends supports quota increase and architecture changes.
- **App/TA:** Splunk TAs for each cloud (CloudTrail, Activity Log, GCP audit)
- **Data Sources:** CloudTrail (errorCode=ThrottlingException), Azure Activity Log (status=Throttled), GCP audit (status 429)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudtrail" errorCode="ThrottlingException"
| stats count by eventName userIdentity.principalId
| sort -count
```
- **Implementation:** Search audit logs for throttling errors (AWS ThrottlingException, Azure 429, GCP RESOURCE_EXHAUSTED). Dashboard by API and principal. Request quota increase when sustained. Consider exponential backoff and request batching in applications.
- **Visualization:** Table (API, principal, 429 count), Line chart (429 over time), Bar chart (top throttled APIs).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.11 · Cloud Encryption and Key Rotation Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1098.001, T1530
- **Value:** Unencrypted resources or keys past rotation date violate compliance. Central view across clouds supports audit and remediation.
- **App/TA:** Config/Security Hub, Defender, SCC, or CSPM
- **Data Sources:** AWS Config (encryption rules), Azure Policy (encryption compliance), GCP SCC (crypto key rotation)
- **SPL:**
```spl
index=aws sourcetype="aws:config:notification" configRuleList{}.configRuleName=*encryption*
| search complianceType="NON_COMPLIANT"
| table _time resourceType resourceId configRuleList{}.configRuleName
```
- **Implementation:** Use native compliance (Config rules, Azure Policy, SCC) or CSPM to evaluate encryption and key rotation. Ingest findings. Dashboard non-compliant resources by rule and cloud. Alert on new non-compliant critical resources.
- **Visualization:** Table (resource, rule, cloud, status), Pie chart (compliant %), Bar chart (non-compliant by rule).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.12 · Multi-Cloud Identity and Access Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1078.004, T1087.004
- **Value:** Correlating identity activity across AWS IAM, Entra ID, and GCP IAM detects cross-cloud abuse and compromised identities.
- **App/TA:** Combined cloud TAs, identity lookup tables
- **Data Sources:** CloudTrail (IAM), Entra ID sign-in/audit, GCP audit (IAM)
- **SPL:**
```spl
index=aws OR index=azure OR index=gcp
| eval user=coalesce(userIdentity.principalId, userPrincipalName, protoPayload.authenticationInfo.principalEmail)
| lookup identity_normalized user OUTPUT normalized_id
| stats count dc(index) as clouds values(index) as indices by normalized_id
| where clouds >= 2
| sort -count
```
- **Implementation:** Normalize principal IDs to a common identity (e.g. email). Ingest IAM and sign-in events from all clouds. Baseline activity per identity; alert on first-time cross-cloud activity or impossible travel across cloud regions. Use for insider threat and compromise detection.
- **Visualization:** Table (identity, clouds, activity count), Sankey (identity to cloud to action), Timeline (cross-cloud events).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.13 · Cloud Provider Status and Incident Correlation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** When AWS/Azure/GCP have outages, correlating provider status with your alerts prevents wasted troubleshooting and supports customer communication.
- **App/TA:** Custom input (status page API or RSS), or status page integration
- **Data Sources:** AWS Service Health Dashboard, Azure Status, GCP Status (APIs or scraped)
- **SPL:**
```spl
index=cloud_status provider=* status=*impact*
| table _time provider service status description
| sort -_time
```
- **Implementation:** Poll provider status APIs (e.g. status.aws.amazon.com, status.azure.com) or ingest RSS. Normalize to common schema. When your alerts spike, search status index for same time window and provider. Dashboard active incidents by provider.
- **Visualization:** Table (provider, service, status), Timeline (incidents), Single value (active incidents).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.14 · Cloud Trail and Diagnostic Logging Gaps
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1562.008
- **Value:** Missing or disabled CloudTrail, Activity Log export, or GCP audit log sink creates blind spots. Detecting gaps ensures full audit coverage.
- **App/TA:** Config, Azure Policy, GCP Asset Inventory, or custom API checks
- **Data Sources:** AWS Config (cloudtrail-enabled), Azure Policy (diagnostic setting compliance), GCP log sink audit
- **SPL:**
```spl
index=aws sourcetype="aws:config:notification" resourceType="AWS::CloudTrail::Trail"
| search configuration.isMultiRegionTrail=false OR configuration.logFileValidationEnabled=false
| table resourceId configuration.isMultiRegionTrail configuration.logFileValidationEnabled
```
- **Implementation:** Use Config rules (e.g. cloudtrail-enabled, multi-region), Azure Policy (diagnostic logs to Event Hub), or GCP org policy for log sinks. Ingest compliance state. Alert when any account/region has trail disabled or logging gap. Dashboard coverage by account and log type.
- **Visualization:** Table (account, region, trail, multi-region, validation), Status (coverage %), Bar chart (gaps by account).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.15 · Cloud Resource Tag Compliance and Drift
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1578
- **Value:** Missing or inconsistent tags (Owner, CostCenter, Environment) block cost allocation, automation, and governance. Detecting untagged or non-compliant resources supports tag policy enforcement.
- **App/TA:** `Splunk_TA_aws`, Azure Resource Graph, GCP Asset Inventory
- **Data Sources:** AWS Config (resource compliance), Azure Policy compliance, GCP labels API
- **SPL:**
```spl
index=aws sourcetype="aws:config:resource" tag_compliance="non_compliant"
| stats count by resourceType, account_id, region
| where count > 0
| sort -count
```
- **Implementation:** Use AWS Config rules (required-tags), Azure Policy (e.g. RequireTagAndValue), or GCP org policy for label requirements. Ingest compliance results. Alert when net new untagged resources appear or compliance score drops below threshold. Dashboard by OU/account and resource type.
- **Visualization:** Table (account, resource type, non-compliant count), Gauge (tag compliance %), Bar chart by tag key missing.
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.4.16 · Cross-Region Replication and Backup Verification
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **MITRE ATT&CK:** T1578.001, T1537
- **Value:** Replication lag or failed backup copies leave RPO/RTO at risk. Monitoring ensures DR readiness and supports audit of backup and replication jobs.
- **App/TA:** `Splunk_TA_aws`, Azure Monitor, GCP operations
- **Data Sources:** S3 replication metrics, RDS cross-region replica lag, Azure Backup job status, GCP snapshot schedule
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch:metric" metric_name=ReplicationLatency namespace=AWS/S3
| stats latest(value) as lag_seconds by dimension.BucketName, dimension.DestinationBucket
| where lag_seconds > 900
| table dimension.BucketName dimension.DestinationBucket lag_seconds
```
- **Implementation:** Collect S3 ReplicationTime and ReplicationLatency from CloudWatch. For RDS, use ReplicaLag. For Azure, ingest Backup job state from Monitor or automation runbooks. Alert when replication lag exceeds RPO (e.g. 15 min) or backup job fails.
- **Visualization:** Line chart (replication lag by bucket/replica), Table (failed backup jobs), Single value (max lag).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.4.17 · Cloud Quota and Service Limit Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Hitting account or region quotas (e.g. EC2 instance limit, VPCs, EBS volumes) blocks provisioning and causes runtime failures. Proactive tracking supports limit increase requests.
- **App/TA:** `Splunk_TA_aws`, Service Quotas API, Azure quotas, GCP quotas
- **Data Sources:** AWS Service Quotas API, Trusted Advisor (limits), Azure usage and quotas, GCP quota API
- **SPL:**
```spl
index=aws sourcetype="aws:service_quotas"
| eval usage_pct=round(usage/value*100, 1)
| where usage_pct > 80
| table quota_name region usage value usage_pct
| sort -usage_pct
```
- **Implementation:** Poll Service Quotas (or equivalent) for key limits (EC2, EBS, VPC, Lambda concurrency). Ingest current usage and quota value. Alert when utilization exceeds 80%. Dashboard all quotas with trend.
- **Visualization:** Table (quota, usage %, limit), Gauge per critical quota, Bar chart (top near-limit quotas).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.4.18 · Cloud Endpoint and DNS Resolution Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **MITRE ATT&CK:** T1580
- **Value:** PrivateLink, VPC endpoints, and private DNS zones enable secure access to AWS/Azure/GCP services. Endpoint or DNS failures cause application outages that are hard to diagnose.
- **App/TA:** Custom scripted input (nslookup, curl to endpoint), CloudWatch Route53 health
- **Data Sources:** Route53 Resolver query logs, VPC endpoint connection acceptance, Azure Private Endpoint status
- **SPL:**
```spl
index=cloud sourcetype="endpoint:health"
| stats latest(connect_ok) as ok, latest(rtt_ms) as rtt by endpoint_id, vpc_id
| where ok != 1 OR rtt > 500
| table endpoint_id vpc_id ok rtt _time
```
- **Implementation:** Run periodic probes (DNS lookup for private hosted zone, HTTPS to VPC endpoint) from a central host or Lambda. Ingest success/failure and latency. Alert when endpoint is unreachable or RTT exceeds threshold.
- **Visualization:** Status grid (endpoint, OK/fail), Table (endpoint, RTT), Line chart (RTT over time).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.19 · Multi-Cloud Cost Anomaly and Spike Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Cost
- **MITRE ATT&CK:** T1580
- **Value:** Sudden cost spikes across AWS, Azure, or GCP indicate misconfiguration, abuse, or runaway resources. Early detection limits financial impact and supports FinOps review.
- **App/TA:** `Splunk_TA_aws`, Azure Cost Management export, GCP Billing export
- **Data Sources:** AWS CUR, Azure Cost Management, GCP Billing export (BigQuery or file)
- **SPL:**
```spl
index=cloud sourcetype="billing:daily" (provider=aws OR provider=azure OR provider=gcp)
| timechart span=1d sum(unblended_cost) as cost by provider
| eventstats avg(cost) as avg_cost, stdev(cost) as std_cost by provider
| eval z_score=if(std_cost>0, (cost-avg_cost)/std_cost, 0)
| where z_score > 2
| table _time provider cost avg_cost z_score
```
- **Implementation:** Ingest daily (or hourly) cost by provider and service. Compute rolling mean and standard deviation per provider. Alert when daily cost exceeds 2 standard deviations. Correlate with resource inventory for top contributors.
- **Visualization:** Line chart (cost by provider over time), Table (anomalous days), Single value (current day vs baseline).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.4.20 · Multi-Cloud DNS Resolution Latency
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Cross-provider DNS query performance comparison. Slow or failed resolution causes application timeouts and user experience degradation.
- **App/TA:** Custom scripted input (dig, nslookup)
- **Data Sources:** DNS query timing from multiple vantage points (AWS, Azure, GCP, on-prem)
- **SPL:**
```spl
index=cloud sourcetype="dns:resolution" 
| stats avg(resolution_ms) as avg_ms, max(resolution_ms) as max_ms, count as queries by provider, vantage_point, domain
| where avg_ms > 200 OR max_ms > 1000
| eval avg_ms=round(avg_ms, 1), max_ms=round(max_ms, 1)
| table provider vantage_point domain queries avg_ms max_ms
| sort -avg_ms
```
- **Implementation:** Run periodic DNS probes (dig, nslookup, or custom script) from Lambda, Azure Functions, Cloud Functions, or on-prem agents. Measure resolution time per domain. Ingest results via HEC with fields: provider, vantage_point, domain, resolution_ms, success. Alert when avg latency exceeds 200ms or failure rate > 5%. Compare providers for DNS migration decisions.
- **Visualization:** Line chart (resolution latency by provider and domain over time), Table (provider, domain, avg ms), Heat map (provider vs domain).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.21 · Cloud Resource Tag Coverage Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1578
- **Value:** Untagged or improperly tagged resources impact cost allocation, governance, and security. Compliance gaps block chargeback and policy enforcement.
- **App/TA:** `Splunk_TA_aws`, Azure inputs, GCP inputs
- **Data Sources:** AWS Config rules (required-tags), Azure Policy (tag compliance), GCP Asset Inventory (resource metadata)
- **SPL:**
```spl
index=aws sourcetype="aws:config:notification" configRuleName="*required-tags*" complianceType="NON_COMPLIANT"
| eval provider="aws", resource_type=coalesce(resourceType, configuration.resourceType)
| stats count by provider, resource_type
| sort -count
```
- **Implementation:** Enable AWS Config rule `required-tags` (or custom rule). Use Azure Policy for tag compliance. Export GCP Asset Inventory to BigQuery or Pub/Sub. Ingest compliance results in Splunk with normalized fields (provider, resource_type, compliance_status). For multi-cloud, use `index=cloud` and union searches per provider. Dashboard untagged resources by provider, resource type, and owner. Alert when critical resources (e.g. production EC2, storage) lack required tags (Environment, Owner, CostCenter).
- **Visualization:** Table (provider, resource type, compliance count), Pie chart (compliant vs non-compliant), Bar chart (non-compliant by tag key).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.4.22 · Cross-Cloud Identity Federation Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1078.004, T1580
- **Value:** Federation misconfiguration or token abuse spans IdPs and cloud consoles; unified visibility reduces blind spots for lateral movement across AWS, Azure, and GCP.
- **App/TA:** `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=aws:cloudtrail` (AssumeRoleWithSAML, federation), `sourcetype=mscs:azure:audit` (federated sign-ins), `sourcetype=google:gcp:pubsub:message` (SAML/OIDC audit)
- **SPL:**
```spl
(index=aws sourcetype="aws:cloudtrail" eventName="AssumeRoleWithSAML")
 OR (index=azure sourcetype="mscs:azure:audit" identity.claims.http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier=)
 OR (index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.methodName="google.iam.admin.v1.IAM.SignBlob")
| eval cloud=case(isnotnull(index) AND index="aws","aws", index="azure","azure", index="gcp","gcp",1=1,"unknown")
| stats count by cloud, user, _time span=1h
| sort -count
```
- **Implementation:** Normalize federated principal fields into a common `user` or `subject` via `eval`/`lookup`. Ingest IdP logs (Okta, Entra ID) via HEC if available and join on session ID. Alert on unusual federation volume, new IdP thumbprint, or cross-cloud sessions within minutes for the same user.
- **Visualization:** Table (cloud, user, count), Timeline (federation events), Sankey or chord (IdP to cloud role).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user | sort - count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088), [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)

---

### UC-4.4.23 · Multi-Cloud DNS Resolution Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **MITRE ATT&CK:** T1580
- **Value:** DNS failures in one cloud or resolver path strand hybrid apps; proactive health checks catch resolver outages and split-horizon misconfiguration before user impact.
- **App/TA:** Custom (synthetic probes, Route 53 Resolver / Azure DNS / Cloud DNS logs)
- **Data Sources:** `sourcetype=dns:health`, `sourcetype=aws:route53resolverquerylog`, `sourcetype=mscs:azure:diagnostics` (DNS if enabled)
- **SPL:**
```spl
index=cloud (sourcetype="dns:health" OR sourcetype="synthetic:dns")
| stats latest(success) as ok, avg(latency_ms) as avg_ms by provider, resolver_vantage, tested_fqdn
| where ok=0 OR avg_ms>500
| eval avg_ms=round(avg_ms,1)
| sort provider tested_fqdn
```
- **Implementation:** Emit probe results from each cloud (success, latency_ms, NXDOMAIN rate) via HEC. Optionally join Route 53 Resolver query logs for SERVFAIL spikes. Page when any critical FQDN fails from two vantage points or latency doubles vs baseline.
- **Visualization:** Status grid (FQDN × provider), Line chart (success rate over time), Single value (failed probes).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.24 · Hybrid Connectivity Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** ExpressRoute, Direct Connect, VPN, and Interconnect carry production traffic; tunnel or BGP drops partition workloads between on-prem and cloud.
- **App/TA:** `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=aws:cloudwatch` (DX, VPN, TGW), Azure Monitor VPN/ExpressRoute metrics, `sourcetype=google:gcp:monitoring` (VPN/interconnect)
- **SPL:**
```spl
(index=aws sourcetype="aws:cloudwatch" (namespace="AWS/DX" OR namespace="AWS/VPN") (metric_name="ConnectionState" OR metric_name="TunnelState"))
 OR (index=azure sourcetype="mscs:azure:metrics" resourceType="Microsoft.Network/expressRouteCircuits" metric_name="BgpPeerStatus")
 OR (index=gcp sourcetype="google:gcp:monitoring" metric.type="vpn.googleapis.com/tunnel_established")
| eval link_up=case(metric_name="ConnectionState" AND maximum=1,1, metric_name="TunnelState" AND maximum=1,1, metric_name="BgpPeerStatus" AND average>0,1, metric.type="vpn.googleapis.com/tunnel_established" AND value>0,1,1=1,0)
| stats min(link_up) as healthy by resourceId, resource.labels.*, bin(_time, 5m)
| where healthy=0
```
- **Implementation:** Align metric semantics per provider in lookups; alert on sustained unhealthy state. Correlate with provider status pages ingested as `sourcetype=cloud:status`. Dashboard RTO/RPO targets for hybrid links.
- **Visualization:** Timeline (link state), Table (circuit, tunnel, status), Map (peering location if geo fields exist).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.4.25 · Multi-Cloud Secret Management Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1098.001, T1552.005
- **Value:** Secrets touched across AWS Secrets Manager, Azure Key Vault, and GCP Secret Manager must be auditable for least-privilege reviews and breach investigations.
- **App/TA:** `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=aws:cloudtrail` (secretsmanager, kms), `sourcetype=mscs:azure:audit` (Key Vault), `sourcetype=google:gcp:pubsub:message` (secretmanager.googleapis.com)
- **SPL:**
```spl
(index=aws sourcetype="aws:cloudtrail" eventSource="secretsmanager.amazonaws.com" eventName="GetSecretValue")
 OR (index=azure sourcetype="mscs:azure:audit" resourceId="*vaults*")
 OR (index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="secretmanager.googleapis.com")
| eval principal=coalesce(userIdentity.arn, identity.claims.appid, protoPayload.authenticationInfo.principalEmail)
| stats count by principal, index
| sort -count
```
- **Implementation:** Enrich with HR or CMDB owner for service principals. Alert on first-time accessor, after-hours bulk reads, or secrets read from unexpected regions. Retention aligned to compliance policy.
- **Visualization:** Table (principal, cloud, access count), Bar chart (top accessors), Timeline (spikes).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088), [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)

---

### UC-4.4.26 · Cross-Cloud Resource Tagging Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1578
- **Value:** A single tagging schema across clouds enables chargeback and policy automation; drift in one provider breaks consolidated FinOps views.
- **App/TA:** `Splunk_TA_aws`, Azure Policy exports, GCP Asset Inventory
- **Data Sources:** `sourcetype=aws:config:notification`, Azure Policy compliance events, `sourcetype=google:gcp:pubsub:message` (asset exports)
- **SPL:**
```spl
(index=aws sourcetype="aws:config:notification" configRuleName="*tag*" complianceType="NON_COMPLIANT")
 OR (index=azure sourcetype="mscs:azure:audit" complianceState="NonCompliant" operationName.value="*policy*")
 OR (index=gcp sourcetype="google:gcp:pubsub:message" "missingLabelKeys")
| eval provider=case(index="aws","aws", index="azure","azure", index="gcp","gcp",1=1,"other")
| stats count by provider, resourceType, resourceGroup
| sort -count
```
- **Implementation:** Normalize required tag keys (for example Environment, Owner, CostCenter) in a lookup. Weekly trend of non-compliant count per provider. Alert when any provider’s gap exceeds SLA threshold.
- **Visualization:** Stacked bar (non-compliant by provider over time), Table (resource, missing tags), Single value (compliance %).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.4.27 · Multi-Cloud Egress Cost Comparison
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Cost
- **Value:** Egress drives surprise bills; comparing outbound spend by provider and region guides data locality and CDN decisions.
- **App/TA:** Billing exports (CUR, Cost Management export, BigQuery billing)
- **Data Sources:** `sourcetype=aws:billing`, `sourcetype=azure:cost`, `sourcetype=gcp:billing`
- **SPL:**
```spl
index=cloud (sourcetype="aws:billing" OR sourcetype="azure:cost" OR sourcetype="gcp:billing")
| eval ut=lower(coalesce(lineItem_UsageType, usage_type, usageType, productSku))
| eval is_egress=if(match(ut,"egress|transfer|internet|download|outbound|data_transfer"),1,0)
| where is_egress=1
| eval provider=case(sourcetype="aws:billing","aws", sourcetype="azure:cost","azure", sourcetype="gcp:billing","gcp",1=1,"unknown")
| eval region=coalesce(lineItem_AvailabilityZone, resourceLocation, region)
| stats sum(cost) as egress_usd by provider, region, bin(_time, 1d)
| sort -egress_usd
```
- **Implementation:** Map each provider’s line items to normalized `usage_type` and `cost` fields during ingestion. Join with application tags where available. Alert on week-over-week egress growth above threshold per provider.
- **Visualization:** Line chart (egress USD by provider), Bar chart (region), Table (top services driving egress).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.28 · Hybrid Identity Synchronization Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **MITRE ATT&CK:** T1078.004, T1098
- **Value:** AD Connect, Cloud Identity, and similar sync failures leave cloud groups stale, breaking access and compliance.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`, Windows/Entra diagnostics, GCP Identity logs
- **Data Sources:** `sourcetype=mscs:azure:audit` / AD Connect health, `sourcetype=WinEventLog:Security` (on-prem), `sourcetype=google:gcp:pubsub:message` (identity sync)
- **SPL:**
```spl
(index=azure sourcetype="mscs:azure:audit" (operationName.value="*AADConnect*" OR activityDisplayName="*sync*") activityStatus!="Success")
 OR (index=identity sourcetype="adconnect:health" status!="success")
| eval connector_name=coalesce(connector_name, resourceGroupName, "aadconnect")
| stats count by sourcetype, connector_name, bin(_time, 1h)
```
- **Implementation:** Ingest connector health JSON or Event Hub stream. Correlate with password hash sync errors and object export failures. Alert on any failed sync window or rising error count.
- **Visualization:** Timeline (sync status), Table (connector, error), Single value (last successful sync age in minutes).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.4.29 · Multi-Cloud Backup Recovery Testing
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1578.001, T1578.004
- **Value:** Untested restores fail when needed; tracking drill outcomes across AWS Backup, Azure Backup, and GCP proves RPO/RTO.
- **App/TA:** `Splunk_TA_aws`, Azure Backup logs, GCP Backup for GKE / Database exports
- **Data Sources:** `sourcetype=aws:cloudwatch:events` (Backup), `sourcetype=mscs:azure:diagnostics` (Backup), `sourcetype=google:gcp:pubsub:message` (gkebackup, sqladmin)
- **SPL:**
```spl
(index=aws sourcetype="aws:cloudwatch:events" detail-type="Restore Job State Change")
 OR (index=azure sourcetype="mscs:azure:diagnostics" Category="AzureBackupReport" OperationName="Restore")
 OR (index=gcp sourcetype="google:gcp:pubsub:message" "Restore" OR "restoreBackup")
| eval ok=if(match(_raw,"(?i)(FAILED|ERROR|PARTIAL)"),0,1)
| eval provider=case(index="aws","aws", index="azure","azure", index="gcp","gcp",1=1,"unknown")
| eval app_name=coalesce(detail.resourceArn, BackupItemName, resource.labels.project_id, "unknown")
| stats count(eval(ok=1)) as success, count(eval(ok=0)) as failed by app_name, provider
| where failed>0
```
- **Implementation:** Tag restore jobs with `drill=true` in application metadata. Quarterly dashboard of success rate and restore duration percentiles. Alert on any failed table-top restore.
- **Visualization:** Table (app, provider, success/fail), Bar chart (drill outcomes by quarter), Line chart (restore duration trend).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.4.30 · Cloud Provider API Rate Limit Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **MITRE ATT&CK:** T1526, T1580
- **Value:** Automation hitting AWS throttling, Azure 429s, or GCP RESOURCE_EXHAUSTED breaks pipelines; trending limits prevents silent job loss.
- **App/TA:** Cloud TAs + application logs with HTTP status
- **Data Sources:** `sourcetype=aws:cloudtrail` (ThrottlingException), `sourcetype=mscs:azure:audit` / app logs (429), `sourcetype=google:gcp:pubsub:message` (status 429, RESOURCE_EXHAUSTED)
- **SPL:**
```spl
(index=aws sourcetype="aws:cloudtrail" errorCode="Throttling")
 OR (index=azure sourcetype="mscs:azure:audit" status.value="429")
 OR (index=gcp sourcetype="google:gcp:pubsub:message" "RESOURCE_EXHAUSTED" OR status="429")
| eval provider=case(index="aws","aws", index="azure","azure", index="gcp","gcp",1=1,"unknown")
| timechart span=15m count by provider
```
- **Implementation:** Back off and jitter in automation based on Splunk alerts. Separate control-plane vs data-plane APIs. Dashboard top callers (principal or workload) causing throttles.
- **Visualization:** Line chart (throttle count by provider), Table (API operation, caller, count), Single value (15m throttle burst).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.4.31 · Multi-Cloud Certificate Expiry Tracking
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **MITRE ATT&CK:** T1580
- **Value:** Expired certs break TLS for APIs and VPNs across regions; a unified expiry calendar prevents outages.
- **App/TA:** ACM/Key Vault/Certificate Manager exports, optional certstream
- **Data Sources:** `sourcetype=aws:acm:inventory`, `sourcetype=mscs:azure:metrics` / cert inventory, `sourcetype=google:gcp:pubsub:message` (certificatemanager)
- **SPL:**
```spl
index=cloud (sourcetype="aws:acm:inventory" OR sourcetype="azure:keyvault:certs" OR sourcetype="google:gcp:pubsub:message")
| eval not_after_epoch=coalesce(strptime(expiry, "%Y-%m-%dT%H:%M:%SZ"), strptime(expiry, "%Y-%m-%dT%H:%M:%S%z"), strptime(notAfter, "%Y-%m-%dT%H:%M:%S"))
| eval days_left=round((not_after_epoch-now())/86400,0)
| eval provider=case(sourcetype="aws:acm:inventory","aws", sourcetype="azure:keyvault:certs","azure", sourcetype="google:gcp:pubsub:message","gcp",1=1,"unknown")
| where days_left < 30 AND days_left >= 0
| table cert_name, provider, expiry, days_left
| sort days_left
```
- **Implementation:** Nightly inventory jobs push cert metadata via HEC. Escalate at 30, 14, and 7 days. Include private CAs and cloud-managed certs for load balancers and API gateways.
- **Visualization:** Table (cert, provider, days left), Timeline (expiry dates), Single value (next expiry).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### 4.5 Serverless & FaaS

---

### UC-4.5.1 · Lambda Invocation Errors and Failed Invocations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Failed Lambda invocations surface runtime bugs, dependency outages, and misconfiguration before they silently drop user traffic or break downstream workflows.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (namespace `AWS/Lambda`)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="Errors"
| timechart span=5m sum(Sum) as errors by FunctionName
| join max=1 FunctionName type=left
    [ search index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="Invocations"
    | timechart span=5m sum(Sum) as invocations by FunctionName ]
| eval error_rate=if(invocations>0, round(100*errors/invocations, 2), 0)
| where error_rate > 1
```
- **Implementation:** Enable CloudWatch metric collection for the Lambda namespace (Errors, Invocations). Ingest via Splunk_TA_aws. Optionally correlate with Lambda application logs from CloudWatch Logs subscription. Alert when error rate exceeds policy (for example 1–5% sustained over 15 minutes).
- **Visualization:** Line chart (errors and invocations over time by function), Single value (error rate %), Table (FunctionName, errors, invocations, error_rate).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.5.2 · Lambda Cold Start and Init Duration Latency
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Cold starts add tail latency to user-facing APIs and batch jobs; tracking Init Duration guides memory tuning, provisioned concurrency, and VPC design.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (`InitDuration`), optional `sourcetype=aws:cloudwatchlogs` (Lambda REPORT lines)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="InitDuration"
| timechart span=5m avg(Average) as avg_init_ms, max(Maximum) as max_init_ms by FunctionName
| where avg_init_ms > 500
```
- **Implementation:** Collect the `InitDuration` CloudWatch metric for each function. For log-based validation, subscribe Lambda log groups to Splunk and parse `REPORT` lines for `Init Duration`. Baseline p95/p99 init time per function and alert when cold-start latency breaches SLO after deploys or scaling events.
- **Visualization:** Line chart (avg/max Init Duration by function), Box plot or percentile overlay (if precomputed), Table (FunctionName, p95 init ms).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.5.3 · Lambda Concurrent Execution Limits and Throttling
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Account- and function-level concurrency caps cause synchronous throttles and async retries; monitoring utilization prevents dropped work during traffic spikes.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (namespace `AWS/Lambda`)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" (metric_name="ConcurrentExecutions" OR metric_name="Throttles")
| stats sum(Sum) as volume by FunctionName, metric_name
| xyseries FunctionName metric_name volume
| fillnull value=0
| where Throttles>0
```
- **Implementation:** Ingest `ConcurrentExecutions`, `Throttles`, and reserved concurrency settings (from tags or a nightly inventory lookup). Compare concurrent usage to reserved and account limits. Alert on any non-zero throttles or when concurrent executions approach the configured cap for bursty functions.
- **Visualization:** Line chart (ConcurrentExecutions vs limit by function), Single value (throttle count), Area chart (stacked concurrency by function).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.5.4 · Azure Functions Host and Worker Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Host startup failures, platform updates, and worker crashes take entire function apps offline; early detection reduces MTTR for serverless workloads on Azure.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:diagnostics` (Function App logs), `sourcetype=mscs:azure:metrics`
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="FunctionAppLogs" (level="Error" OR level="Critical")
| bin span=5m _time
| stats count as errors by resourceName, operationName, _time
| where errors > 0
```
- **Implementation:** Stream Function App diagnostics (FunctionAppLogs) to Event Hub and ingest with the Microsoft Cloud Services add-on. Normalize `resourceName` (app name) and severity. Optionally join with `mscs:azure:metrics` for `Http5xx` or `FunctionExecutionCount` drops. Alert on sustained host-level errors or absence of successful executions.
- **Visualization:** Timeline (errors by app), Table (resourceName, message pattern, count), Status indicator (healthy/degraded per Function App).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.5.5 · Azure Functions Execution Duration
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Long-running functions tie up scale-out units and can hit timeout limits; duration trending guides right-sizing, connection pooling, and async patterns.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:metrics` (Function metrics)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" metricName="FunctionExecutionDuration"
| timechart span=5m avg(average) as avg_ms, max(maximum) as max_ms by resourceName
| where max_ms > 10000
```
- **Implementation:** Enable Azure Monitor metrics for Function Apps and ingest via the TA (dimensions: function name where available). Establish baselines per function. Alert when p95 duration approaches the function timeout or degrades after releases.
- **Visualization:** Line chart (avg/max duration by app or function), Heatmap (duration by hour), Table (resourceName, avg_ms, max_ms).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.5.6 · Azure Functions Queue Trigger Backlog and Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Queue-triggered functions depend on storage or Service Bus depth; growing backlogs mean consumers cannot keep pace or messages are poisoned.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:metrics` (Storage Queue / Service Bus), `sourcetype=mscs:azure:diagnostics`
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:metrics" (metricName="QueueMessageCount" OR metricName="ActiveMessages")
| timechart span=5m avg(average) as depth by resourceName, metricName
| join type=left max=1 resourceName
    [ search index=azure sourcetype="mscs:azure:diagnostics" Category="FunctionAppLogs" "QueueTrigger"
    | stats count as trigger_errors by resourceName ]
| where depth > 1000 OR trigger_errors > 0
```
- **Implementation:** Ingest queue depth metrics for the storage account or Service Bus namespace backing the trigger. Correlate with FunctionAppLogs for dequeue/processing errors. Alert when depth exceeds threshold or poison-message handling spikes. Map queue resource to Function App via tags or a lookup.
- **Visualization:** Dual-axis line chart (queue depth vs successful executions), Table (queue, depth, errors), Single value (oldest message age if exported).
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.5.7 · GCP Cloud Functions Memory Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Memory pressure causes OOM terminations and retries; tracking user memory against allocation prevents instability and guides memory settings per function.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:monitoring` (Cloud Functions metrics)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="cloudfunctions.googleapis.com/function/user_memory_bytes"
| timechart span=5m avg(value) as avg_bytes, max(value) as max_bytes by metric.labels.function_name
| eval max_mb=round(max_bytes/1048576, 2)
| where max_mb > 0
```
- **Implementation:** Export Cloud Monitoring metrics for Cloud Functions to Splunk via the GCP add-on. Join max memory usage with deployed memory configuration from labels or an asset lookup. Alert when utilization consistently approaches the configured limit (for example >85% of allocated memory).
- **Visualization:** Line chart (avg/max memory by function), Gauge (peak vs allocation), Table (function_name, max_mb, allocation_mb).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.5.8 · GCP Cloud Functions Timeout Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Timeouts indicate hung dependencies or insufficient deadline; they drive retries, duplicate side effects, and user-visible failures in synchronous invocations.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:pubsub:message` (Cloud Logging for `cloud_function`), `sourcetype=google:gcp:monitoring`
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="cloud_function"
| where match(_raw, "(?i)timeout|deadline exceeded|function execution took too long")
| stats count as timeout_events by resource.labels.function_name, resource.labels.region
| sort -timeout_events
```
- **Implementation:** Forward Cloud Functions logs to Pub/Sub and ingest with `resource.type="cloud_function"`. Optionally add monitoring metrics for execution times and error result codes. Alert on timeout string patterns or rising timeout counts after dependency or region incidents.
- **Visualization:** Column chart (timeouts by function), Line chart (timeouts over time), Table (function_name, region, count).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.5.9 · Serverless Cost Tracking by Function
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Cost
- **Value:** Function-level spend exposes expensive handlers, mis-scaled concurrency, and test sandboxes left running—essential for FinOps and chargeback.
- **App/TA:** `Splunk_TA_aws`, `Splunk_TA_microsoft-cloudservices`, `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=aws:billing`, `sourcetype=azure:costmanagement`, `sourcetype=gcp:billing`
- **SPL:**
```spl
index=aws sourcetype="aws:billing" OR index=azure sourcetype="azure:costmanagement" OR index=gcp sourcetype="gcp:billing"
| eval cloud=case(index=="aws","AWS", index=="azure","Azure", index=="gcp","GCP")
| eval line_cost=coalesce(BlendedCost, UnblendedCost, cost, CostInBillingCurrency)
| eval fn=coalesce(resourceId, ResourceId, labels.value)
| where match(lower(ProductName).lower(service).lower(resource_type), "(lambda|function|cloudfunctions|functions)")
| stats sum(line_cost) as spend by cloud, fn
| sort -spend
```
- **Implementation:** Ingest CUR or cost exports with resource-level granularity and tags (`aws:createdBy`, Azure resource name, GCP labels). Normalize into a common schema. Filter to serverless SKUs (Lambda, Azure Functions, Cloud Functions). Schedule weekly reports and alerts for top-N spenders or day-over-day spikes per function.
- **Visualization:** Bar chart (spend by function), Treemap (cost by cloud and service), Table (cloud, function, spend, % of total).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876), [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110), [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.5.10 · Lambda Dead Letter Queue Depth and Message Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **MITRE ATT&CK:** T1610
- **Value:** Messages landing in DLQs mean unprocessed events—often billing, inventory, or security actions—until replayed or dropped.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (namespace `AWS/SQS`), optional `sourcetype=aws:cloudwatch:events`
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/SQS" metric_name="ApproximateNumberOfMessagesVisible"
| where match(QueueName, "(?i)dlq|dead")
| timechart span=5m max(Maximum) as visible by QueueName
| where visible > 0
```
- **Implementation:** Tag or name DLQ queues consistently (`*dlq*`). Ingest SQS CloudWatch metrics per queue. Correlate queue to owning Lambda via Event Source Mapping inventory (lookup table). Alert on any sustained visible message count or sudden spikes after bad deployments.
- **Visualization:** Single value (DLQ depth), Line chart (visible messages by queue), Table (QueueName, linked function, visible).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.5.11 · AWS Step Functions Execution Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Failed state machine runs break orchestrated business processes; tracking failed executions enables rapid rollback and pinpointing of failing states or Lambda tasks.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (namespace `AWS/States`)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/States" metric_name="ExecutionsFailed"
| timechart span=5m sum(Sum) as failed by StateMachineArn
| where failed > 0
```
- **Implementation:** Enable CloudWatch metrics for Step Functions (`ExecutionsFailed`, `ExecutionsTimedOut`, `ExecutionsAborted`). Ingest via Splunk_TA_aws. Optionally join with execution history forwarded to S3 or CloudWatch Logs for failure context. Alert on any failed executions in production state machines or rate-based thresholds.
- **Visualization:** Line chart (failed executions by state machine), Single value (failures in last hour), Table (StateMachineArn, failed, timed out).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.5.12 · Azure Durable Functions Orchestration Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Durable orchestrations span many activities; failed or stuck instances block business workflows until replayed or purged from storage.
- **App/TA:** `Splunk_TA_microsoft-cloudservices`
- **Data Sources:** `sourcetype=mscs:azure:diagnostics` (FunctionAppLogs, traces)
- **SPL:**
```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="FunctionAppLogs"
| where match(_raw, "(?i)orchestration.*(failed|faulted)|TaskFailed|SubOrchestrationFailed")
| stats count as orch_failures by resourceName, coalesce(functionName, name)
| sort -orch_failures
```
- **Implementation:** Enable verbose logging for Durable Functions and ingest FunctionAppLogs. Extract orchestration instance IDs where present. Correlate with Storage Account metrics (queue/table used by the task hub) for backlog. Alert on failure patterns or rising pending instances versus completions.
- **Visualization:** Table (app, orchestration name, failures), Line chart (failures over time), Link to Application Insights-style trace IDs if forwarded.
- **CIM Models:** N/A

- **References:** [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)

---

### UC-4.5.13 · Lambda Provisioned Concurrency Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Provisioned concurrency is a fixed cost; low utilization wastes spend while high utilization risks cold starts on overflow—balance requires continuous measurement.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (namespace `AWS/Lambda`)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Lambda" metric_name="ProvisionedConcurrencyUtilization"
| timechart span=5m avg(Average) as util by FunctionName, Resource
| where util < 0.2 OR util > 0.9
```
- **Implementation:** Collect `ProvisionedConcurrencyUtilization` for each alias or version with provisioned settings. Compare against provisioned units from tags or CloudFormation export. Alert when utilization is chronically low (cost optimization) or high (risk of throttling on burst beyond provisioned pool).
- **Visualization:** Line chart (utilization by function/alias), Area chart (consumed vs provisioned concurrency), Table (FunctionName, util %, recommended units).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.5.14 · API Gateway Integration Latency for Serverless Backends
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Integration latency isolates backend (Lambda, HTTP proxy) time from client-facing latency; spikes often precede Lambda timeouts or VPC connectivity issues.
- **App/TA:** `Splunk_TA_aws`
- **Data Sources:** `sourcetype=aws:cloudwatch` (namespace `AWS/ApiGateway`)
- **SPL:**
```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/ApiGateway" metric_name="IntegrationLatency"
| timechart span=5m avg(Average) as integ_ms by ApiName, Stage
| where integ_ms > 2000
```
- **Implementation:** Enable detailed CloudWatch metrics for REST or HTTP APIs. Ingest `IntegrationLatency` alongside `Latency` and `4XXError`/`5XXError`. Split dashboards by stage (prod vs dev). Alert when integration latency exceeds backend SLA or diverges from total API latency (pointing to edge vs origin issues).
- **Visualization:** Line chart (IntegrationLatency vs Latency by API), Heatmap (route/method if dimensions available), Table (ApiName, Stage, p95 integ_ms).
- **CIM Models:** N/A

- **References:** [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)

---

### UC-4.5.15 · GCP Cloud Functions Retry and Error Rate Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Rising retries and error rates signal unstable dependencies or quota issues before quotas hard-stop traffic; trending supports SLO review and incident prevention.
- **App/TA:** `Splunk_TA_google-cloudplatform`
- **Data Sources:** `sourcetype=google:gcp:pubsub:message` (Cloud Logging), optional `sourcetype=google:gcp:monitoring` (execution metrics)
- **SPL:**
```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="cloud_function"
| eval fn=resource.labels.function_name
| eval is_err=if(severity="ERROR", 1, 0)
| timechart span=1h sum(is_err) as errors, count as invocations by fn
| eval err_rate=if(invocations>0, round(100*errors/invocations, 2), 0)
| where err_rate > 5
```
- **Implementation:** Ingest execution count metrics with result/status labels from Cloud Monitoring. Supplement with log-based counts from Cloud Logging for detailed error classes. Baseline hourly error and retry rates per function. Alert when error share exceeds threshold or retries spike versus invocations.
- **Visualization:** Stacked area chart (executions by outcome), Line chart (error rate % over time), Table (function_name, invocations, errors, retry estimate).
- **CIM Models:** N/A

- **References:** [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)

---

### UC-4.4.32 · Cloud Control Plane API Call Volume Anomaly (MLTK)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security, Performance
- **MITRE ATT&CK:** T1078.004, T1526, T1580, T1098.001
- **Value:** Cloud control plane API calls (EC2 RunInstances, IAM CreateUser, S3 PutBucketPolicy) follow predictable patterns tied to deployment schedules and automation cadence. Anomalous spikes in API call volume may indicate compromised credentials, runaway automation, or an attacker enumerating resources — all of which are invisible to static rate limits but detectable through ML-based baselining.
- **App/TA:** Splunk Machine Learning Toolkit (MLTK), Splunk Add-on for AWS / Azure / GCP
- **Data Sources:** `index=cloud sourcetype=aws:cloudtrail` or `sourcetype=azure:monitor:activity` or `sourcetype=google:gcp:pubsub:message`
- **SPL:**
```spl
index=cloud sourcetype IN ("aws:cloudtrail","azure:monitor:activity","google:gcp:pubsub:message")
| bin _time span=1h
| stats count by _time, eventName, userIdentity.arn, sourceIPAddress
| eventstats avg(count) as baseline_avg, stdev(count) as baseline_std by eventName
| eval z_score=round((count - baseline_avg) / nullif(baseline_std, 0), 2)
| where z_score > 3 AND count > 50
| fit DensityFunction count by eventName into cloud_api_anomaly_model
| rename "IsOutlier(count)" as isOutlier
| where isOutlier > 0
| table _time, eventName, userIdentity.arn, sourceIPAddress, count, baseline_avg, z_score
| sort -z_score
```
- **Implementation:** Aggregate CloudTrail / Activity Log / Admin Activity events hourly by API action and principal. Train DensityFunction models per API action on 30 days of data to capture automation schedules and deployment patterns. Flag calls that exceed 3 standard deviations from the learned baseline. Prioritize high-risk APIs: IAM mutations, security group changes, KMS key operations, and resource creation. Enrich with source IP geolocation and threat intelligence. Correlate with CI/CD deployment events (cat-12) to suppress planned automation bursts. Generate risk events for Splunk ES with MITRE T1078/T1580 annotations. Retrain models weekly.
- **Visualization:** Line chart (API call volume vs baseline), Table (anomalous API calls with z-scores), Bar chart (top anomalous APIs by principal).
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user span=1h | sort - count
```

- **Known false positives:** Infrastructure-as-code deployments (Terraform apply), DR drills, and cloud migration events. Maintain a deployment calendar lookup to suppress known automation windows.
- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)

---

### 4.6 Cloud Infrastructure Trending

### UC-4.6.1 · Cloud Resource Count Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** EC2/VM instance count over 90 days reveals organic growth, failed automation leaving orphan instances, or shrinkage after optimization campaigns. Supports FinOps conversations and capacity forecasts.
- **App/TA:** Splunk Add-on for AWS, Splunk Add-on for Microsoft Cloud Services, Google Cloud add-ons
- **Data Sources:** `index=cloud sourcetype=aws:config:notification` or `sourcetype=aws:description` (inventory); Azure Resource Graph exports; GCP Asset Inventory
- **SPL:**
```spl
index=cloud sourcetype="aws:config:notification" resourceType="AWS::EC2::Instance"
| bin _time span=1d
| stats dc(resourceId) as instance_count by _time, awsAccountId
| timechart span=1d sum(instance_count) as total_instances
| trendline sma7(total_instances) as instance_trend
| predict total_instances as predicted algorithm=LLP future_timespan=30
```
- **Implementation:** Ingest periodic inventory snapshots (AWS Config, DescribeInstances exports, or Azure Resource Graph) into index=cloud with one event per instance per snapshot. If only change streams exist, maintain state with a nightly summary search. Chart instance_count over 90 days; optionally split by accountId or region. For multi-cloud, normalize resourceType across providers.
- **Visualization:** Line chart (instance count over 90 days with trend and 30-day forecast), area chart stacked by account.
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876), [Splunk Add-on for Microsoft Cloud Services](https://splunkbase.splunk.com/app/3110)

---

### UC-4.6.2 · Lambda/Function Invocation Volume Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Daily invocation counts show traffic growth, seasonal patterns, and the impact of new features or batch jobs. Sharp changes often precede cost spikes or throttling if concurrency limits are fixed.
- **App/TA:** Splunk Add-on for AWS (CloudWatch metrics), Azure Monitor
- **Data Sources:** `index=cloud sourcetype=aws:cloudwatch` (Lambda Invocations metric); Azure Functions metrics
- **SPL:**
```spl
index=cloud sourcetype="aws:cloudwatch" Namespace="AWS/Lambda" MetricName="Invocations"
| bin _time span=1d
| stats sum(Sum) as invocations by _time, FunctionName
| timechart span=1d sum(invocations) as total_invocations
| trendline sma7(total_invocations) as invocation_trend
```
- **Implementation:** Enable CloudWatch metric ingestion for AWS/Lambda Invocations with FunctionName dimension. For Azure, use Microsoft.Web/sites/functions equivalent metrics. Normalize time to UTC for daily buckets. Use top-N functions by volume to keep the chart readable. Correlate step changes with deployments from CI/CD timestamps.
- **Visualization:** Line chart (daily invocations with 7-day SMA, 30 days), column chart (top functions by volume).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)

---

### UC-4.6.3 · Cloud Security Finding Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **MITRE ATT&CK:** T1580, T1526
- **Value:** Tracking new versus resolved security findings over time shows whether your cloud security posture is improving and whether scanners or policies are flagging more issues than teams can remediate. Supports executive reporting and backlog triage.
- **App/TA:** AWS Security Hub, Azure Defender, GCP Security Command Center — forwarded via HEC or add-on
- **Data Sources:** `index=cloud sourcetype=aws:securityhub:finding` OR `sourcetype=azure:defender:alert` OR `sourcetype=gcp:scc:finding`
- **SPL:**
```spl
index=cloud sourcetype IN ("aws:securityhub:finding", "azure:defender:alert", "gcp:scc:finding")
| eval status=case(match(WorkflowStatus,"(?i)resolved|archived|suppressed"),"resolved",1=1,"new")
| timechart span=1d count by status
| trendline sma7(new) as new_trend sma7(resolved) as resolved_trend
```
- **Implementation:** Map your findings feed so each event represents a finding state change or daily snapshot with Severity and status. For snapshot models, compare consecutive days to derive new and resolved counts via summary search. Align severities (Critical/High/Medium) across clouds for a combined view or use separate panels per provider. Refresh suppression lookups so trends reflect true risk.
- **Visualization:** Stacked column chart (new vs resolved per day), line chart (open critical count trend), area chart (cumulative open findings).
- **CIM Models:** N/A

- **References:** [Splunk Lantern — use case library](https://lantern.splunk.com/)

---

### UC-4.6.4 · S3/Blob Storage Growth Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Total object storage bytes month over month highlights data hoarding, log retention growth, or unexpected replication. Supports budgeting and lifecycle policy decisions before bills spike.
- **App/TA:** Splunk Add-on for AWS (S3 storage metrics), Azure Monitor metrics
- **Data Sources:** `index=cloud sourcetype=aws:cloudwatch` (BucketSizeBytes metric); `sourcetype=azure:monitor:metrics` for storage accounts
- **SPL:**
```spl
index=cloud sourcetype="aws:cloudwatch" Namespace="AWS/S3" MetricName="BucketSizeBytes"
| bin _time span=1mon
| stats latest(Average) as bytes by _time, BucketName
| eval tb=round(bytes/1099511627776, 2)
| timechart span=1mon sum(tb) as total_tb
| predict total_tb as predicted algorithm=LLP future_timespan=3
```
- **Implementation:** Ingest daily CloudWatch BucketSizeBytes per bucket or storage account metrics for Azure/Blob. Use span=1mon aligned to calendar months for FinOps reporting. Convert bytes to TB for readability. Optionally exclude archive buckets matched to a lookup. Alert on month-over-month growth above a percentage threshold. Use predict to forecast 3 months ahead for capacity planning.
- **Visualization:** Line chart (total TB monthly with 3-month forecast), bar chart (top buckets by size), table (month-over-month growth %).
- **CIM Models:** N/A

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876)

---

### UC-4.6.5 · Cloud Network Traffic Volume Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Weekly VPC flow log volume indicates shifting traffic patterns, DDoS aftermath, or misconfigured mirroring. Complements per-flow analysis with a coarse health signal and correlates with network-related cost changes.
- **App/TA:** Splunk Add-on for AWS (VPC Flow Logs), Azure NSG flow logs
- **Data Sources:** `index=cloud sourcetype=aws:cloudwatch:vpcflow` OR `sourcetype=azure:nsg:flow`
- **SPL:**
```spl
index=cloud sourcetype="aws:cloudwatch:vpcflow"
| eval bytes=tonumber(bytes)
| timechart span=1w sum(bytes) as total_bytes
| eval total_gb=round(total_bytes/1073741824, 2)
| trendline sma4(total_gb) as traffic_trend
```
- **Implementation:** Parse VPC Flow or NSG flow fields so bytes is numeric. Filter internal-only noise if needed via RFC1918 CIDR lists. Use weekly buckets for medium-term trending; index volume growth also correlates with ingest cost. For Azure, map to the appropriate custom sourcetype for raw flows. Alert on sudden jumps exceeding 2x the 4-week moving average.
- **Visualization:** Column chart (weekly total GB), line overlay (4-week SMA), dual axis with flow record count.
- **CIM Models:** Network Traffic
- **CIM SPL:**
```spl
| tstats summariesonly=t sum(All_Traffic.bytes_in) as agg_value from datamodel=Network_Traffic.All_Traffic by All_Traffic.action, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port span=1w | sort - agg_value
```

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876), [CIM: Network Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)

---

### UC-4.6.6 · CloudTrail/Activity Log Event Volume Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Management event volume over 90 days highlights automation changes, new integrations, or possible abuse such as enumeration or bulk API use. Baselines help spot anomalies without reading every event.
- **App/TA:** Splunk Add-on for AWS, Azure Activity Log add-on
- **Data Sources:** `index=cloud sourcetype=aws:cloudtrail`; `sourcetype=azure:monitor:activity`
- **SPL:**
```spl
index=cloud sourcetype="aws:cloudtrail" readOnly=false
| timechart span=1d count as mgmt_events
| trendline sma7(mgmt_events) as event_trend
| predict mgmt_events as predicted algorithm=LLP future_timespan=14
```
- **Implementation:** Filter to non-read-only events for management actions. For multi-cloud, use union or a combined index with sourcetype in the by clause. Chart 90 days with daily span. Alert on statistical outliers exceeding 3x baseline. Ensure CloudTrail is multi-region and organization trails where applicable so the trend is complete. For Azure, include Activity Log management category events.
- **Visualization:** Line chart (daily management events with 7-day SMA, 90 days), anomaly overlay, 14-day forecast.
- **CIM Models:** Change
- **CIM SPL:**
```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user span=1d | sort - count
```

- **References:** [Splunk Add-on for AWS](https://splunkbase.splunk.com/app/1876), [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
