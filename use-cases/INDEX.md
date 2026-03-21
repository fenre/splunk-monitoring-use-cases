# Use Case Repository — Category Index

This file provides metadata for each category: icons, descriptions, and quick-start picks.
build.py reads this file to generate CAT_META, CAT_STARTERS, and CAT_GROUPS in data.js.

---

## 1. Server & Compute
- **Icon:** monitor
- **Description:** Linux, Windows, macOS endpoint and server monitoring — CPU, memory, disk, processes, security events, and compliance.
- **Quick Tip:** Deploy Splunk_TA_nix or Splunk_TA_windows on forwarders to start collecting OS metrics immediately.
- **Quick Start:**
  - UC-1.1.23 · Kernel Core Dump Generation (critical, Linux Servers)
  - UC-1.1.36 · Multipath I/O Failover Events (critical, Linux Servers)
  - UC-1.1.58 · Network Bond Failover Events (critical, Linux Servers)
  - UC-1.1.69 · SUID/SGID Binary Changes (critical, Linux Servers)
  - UC-1.1.70 · /etc/passwd Modifications (critical, Linux Servers)

## 2. Virtualization
- **Icon:** cloudNodes
- **Description:** VMware vSphere, Hyper-V, and KVM virtual infrastructure — host contention, VM sprawl, and capacity planning.
- **Quick Tip:** Install Splunk Add-on for VMware and connect to vCenter to pull ESXi host and VM performance data.
- **Quick Start:**
  - UC-2.1.7 · HA Failover Events (critical, VMware vSphere)
  - UC-2.2.3 · Cluster Shared Volume Health (critical, Microsoft Hyper-V)
  - UC-2.1.3 · Datastore Capacity Trending (critical, VMware vSphere)
  - UC-2.1.10 · vSAN Health Monitoring (high, VMware vSphere)
  - UC-2.1.11 · ESXi Host Hardware Alerts (high, VMware vSphere)

## 3. Containers & Orchestration
- **Icon:** container
- **Description:** Docker, Kubernetes, OpenShift container platforms — crash loops, OOM kills, resource limits, and orchestration health.
- **Quick Tip:** Deploy Splunk Connect for Kubernetes (SCK) to ingest container logs and cluster events.
- **Quick Start:**
  - UC-3.2.7 · Control Plane Health (critical, Kubernetes)
  - UC-3.2.8 · etcd Cluster Health (critical, Kubernetes)
  - UC-3.1.1 · Container Crash Loops (critical, Docker)
  - UC-3.1.2 · Container OOM Kills (critical, Docker)
  - UC-3.2.1 · Pod Restart Rate (critical, Kubernetes)

## 4. Cloud Infrastructure
- **Icon:** globe
- **Description:** AWS, Azure, GCP cloud infrastructure — API auditing, cost anomalies, resource drift, and security posture.
- **Quick Tip:** Enable CloudTrail/Activity Log and use the respective Splunk TA to start collecting API audit events.
- **Quick Start:**
  - UC-4.1.2 · Root Account Usage (critical, Amazon Web Services (AWS))
  - UC-4.1.7 · S3 Bucket Policy Changes (critical, Amazon Web Services (AWS))
  - UC-4.1.8 · GuardDuty Finding Ingestion (critical, Amazon Web Services (AWS))
  - UC-4.2.9 · Defender for Cloud Alerts (critical, Microsoft Azure)
  - UC-4.3.2 · IAM Policy Changes (critical, Google Cloud Platform (GCP))

## 5. Network Infrastructure
- **Icon:** networkDevices
- **Description:** Routers, switches, firewalls, load balancers, wireless, SD-WAN, and Meraki — interface health, routing, and traffic.
- **Quick Tip:** Configure syslog from network devices to Splunk. Install Splunk Add-on for Cisco or vendor-specific TA.
- **Quick Start:**
  - UC-5.1.1 · Interface Up/Down Events (critical, Routers & Switches)
  - UC-5.1.4 · BGP Peer State Changes (critical, Routers & Switches)
  - UC-5.1.5 · OSPF Neighbor Adjacency (critical, Routers & Switches)
  - UC-5.1.11 · Power Supply / Fan Failures (critical, Routers & Switches)
  - UC-5.2.2 · Policy Change Audit (critical, Firewalls)

## 6. Storage & Backup
- **Icon:** layersTriple
- **Description:** SAN, NAS, object storage, and backup systems — capacity trends, latency, IOPS, and backup job monitoring.
- **Quick Tip:** Install vendor TAs (NetApp, Pure Storage, etc.) and configure REST API or syslog collection.
- **Quick Start:**
  - UC-6.1.2 · Storage Latency Monitoring (critical, SAN / NAS Storage)
  - UC-6.1.4 · Disk Failure Alerts (critical, SAN / NAS Storage)
  - UC-6.1.6 · Controller Failover Events (critical, SAN / NAS Storage)
  - UC-6.2.3 · Public Bucket Detection (critical, Object Storage)
  - UC-6.1.1 · Volume Capacity Trending (critical, SAN / NAS Storage)

## 7. Database & Data Platforms
- **Icon:** table
- **Description:** SQL Server, Oracle, PostgreSQL, MongoDB, and data platforms — slow queries, deadlocks, replication, and connection pools.
- **Quick Tip:** Install Splunk DB Connect or vendor TA to collect database logs and performance metrics.
- **Quick Start:**
  - UC-7.1.2 · Deadlock Monitoring (critical, Relational Databases)
  - UC-7.1.3 · Connection Pool Exhaustion (critical, Relational Databases)
  - UC-7.1.12 · Database Availability Group Health (critical, Relational Databases)
  - UC-7.1.15 · Privilege Escalation Audit (critical, Relational Databases)
  - UC-7.2.1 · Cluster Membership Changes (critical, NoSQL Databases)

## 8. Application Infrastructure
- **Icon:** cog
- **Description:** Web servers, application servers, message queues, CDNs, and DNS — HTTP errors, response times, and SSL certificates.
- **Quick Tip:** Forward web server access/error logs and install the appropriate TA for structured field extraction.
- **Quick Start:**
  - UC-8.1.1 · HTTP Error Rate Monitoring (critical, Web Servers & Reverse Proxies)
  - UC-8.2.1 · JVM Heap Utilization (critical, Application Servers & Runtimes)
  - UC-8.3.1 · Consumer Lag Monitoring (critical, Message Queues & Event Streaming)
  - UC-8.3.3 · Broker Health Monitoring (critical, Message Queues & Event Streaming)
  - UC-8.1.5 · SSL Certificate Monitoring (critical, Web Servers & Reverse Proxies)

## 9. Identity & Access Management
- **Icon:** key
- **Description:** Active Directory, Entra ID, LDAP, MFA, and PAM — authentication failures, privilege escalation, and identity governance.
- **Quick Tip:** Enable Windows Security Event Log collection from DCs with Splunk_TA_windows for immediate AD visibility.
- **Quick Start:**
  - UC-9.1.3 · Privileged Group Membership Changes (critical, Active Directory / Entra ID)
  - UC-9.1.5 · Kerberos Ticket Anomalies (critical, Active Directory / Entra ID)
  - UC-9.1.7 · GPO Modification Detection (critical, Active Directory / Entra ID)
  - UC-9.2.3 · Schema Modification Audit (critical, LDAP Directories)
  - UC-9.3.5 · IdP Availability Monitoring (critical, Identity Providers (IdP) & SSO)

## 10. Security Infrastructure
- **Icon:** shield
- **Description:** Next-gen firewalls, IDS/IPS, endpoint protection, email security, web security, vulnerability management, SIEM & SOAR, and certificate/PKI — threat detection and SecOps. ESCU detections are distributed across subcategories 10.1–10.8.
- **Quick Tip:** Forward firewall logs (syslog) and install the vendor TA (Palo Alto, Fortinet, etc.). Use `import_sse_detections.py` to import ESCU detections, then `redistribute_sse_ucs.py` to place them in the right subcategories.
- **Quick Start:**
  - UC-10.1.2 · Wildfire / Sandbox Verdicts (critical, Next-Gen Firewalls (Security-Focused))
  - UC-10.1.4 · DNS Sinkhole Hits (critical, Next-Gen Firewalls (Security-Focused))
  - UC-10.3.5 · Endpoint Isolation Events (critical, Endpoint Detection & Response (EDR))
  - UC-10.4.2 · Malicious Attachment Tracking (critical, Email Security)
  - UC-10.4.3 · URL Click Tracking (critical, Email Security)
  - UC-10.7.1 · Alert Volume Trending (high, SIEM & SOAR)

## 11. Email & Collaboration
- **Icon:** envelope
- **Description:** Microsoft 365, Exchange, Teams, and collaboration platforms — mail flow, audit logging, and DLP events.
- **Quick Tip:** Configure Splunk Add-on for Microsoft 365 with Management Activity API for audit events.
- **Quick Start:**
  - UC-11.1.8 · Inbox Rule Monitoring (critical, Microsoft 365 / Exchange)
  - UC-11.1.1 · Mail Flow Health Monitoring (critical, Microsoft 365 / Exchange)
  - UC-11.2.4 · Login Anomaly Detection (critical, Google Workspace)
  - UC-11.3.6 · Toll Fraud Detection (critical, Unified Communications)
  - UC-11.1.2 · Mailbox Audit Logging (high, Microsoft 365 / Exchange)

## 12. DevOps & CI/CD
- **Icon:** nodeBranch
- **Description:** Source control, CI/CD pipelines, artifact management, and IaC — build failures, deployment frequency, and secret exposure.
- **Quick Tip:** Forward CI/CD logs (Jenkins, GitHub Actions) via webhook or log file monitoring to Splunk.
- **Quick Start:**
  - UC-12.1.4 · Secret Exposure Detection (critical, Source Control)
  - UC-12.2.5 · Failed Deployment Tracking (critical, CI/CD Pipelines)
  - UC-12.3.2 · Dependency Vulnerability Alerts (critical, Artifact & Package Management)
  - UC-12.1.2 · Branch Protection Bypasses (critical, Source Control)
  - UC-12.2.8 · Security Scan Results in Pipeline (critical, CI/CD Pipelines)

## 13. Observability & Monitoring Stack
- **Icon:** monitorChart
- **Description:** Splunk platform health, APM, synthetic monitoring, and log aggregation — indexer queues, search performance, and forwarder health.
- **Quick Tip:** Use the Monitoring Console (MC) built into Splunk and supplement with _internal index searches.
- **Quick Start:**
  - UC-13.1.1 · Indexer Queue Fill Ratio (critical, Splunk Platform Health)
  - UC-13.2.1 · Service Health Score Trending (critical, Splunk ITSI (Premium))
  - UC-13.2.6 · Rules Engine Health (critical, Splunk ITSI (Premium))
  - UC-13.1.3 · Forwarder Connectivity (critical, Splunk Platform Health)
  - UC-13.1.10 · Search Head Cluster Status (critical, Splunk Platform Health)

## 14. IoT & Operational Technology (OT)
- **Icon:** factory
- **Description:** Building management, industrial control, Splunk Edge Hub, and IoT platforms — sensor data, anomaly detection, and OT security.
- **Quick Tip:** Deploy Splunk Edge Hub with built-in sensors or configure MQTT/OPC-UA/Modbus protocol collection.
- **Quick Start:**
  - UC-14.1.2 · UPS Battery Monitoring (critical, Building Management Systems (BMS))
  - UC-14.1.6 · Environmental Compliance (critical, Building Management Systems (BMS))
  - UC-14.2.1 · PLC/RTU Health Monitoring (critical, Industrial Control Systems (ICS/SCADA))
  - UC-14.2.3 · Safety System Activation (critical, Industrial Control Systems (ICS/SCADA))
  - UC-14.2.2 · Process Variable Anomalies (critical, Industrial Control Systems (ICS/SCADA))

## 15. Data Center Physical Infrastructure
- **Icon:** buildings
- **Description:** Power/UPS, cooling/CRAC, and environmental monitoring — battery health, thermal management, and physical security.
- **Quick Tip:** Integrate DCIM or BMS platforms via SNMP or API to collect environmental and power data.
- **Quick Start:**
  - UC-15.1.1 · UPS Battery Health (critical, Power & UPS)
  - UC-15.1.6 · Circuit Breaker Trips (critical, Power & UPS)
  - UC-15.2.1 · Temperature Monitoring per Zone (critical, Cooling & Environmental)
  - UC-15.2.3 · CRAC/CRAH Unit Health (critical, Cooling & Environmental)
  - UC-15.1.3 · Power Redundancy Status (critical, Power & UPS)

## 16. Service Management & ITSM
- **Icon:** clipboard
- **Description:** Ticketing systems and CMDB — incident trends, SLA compliance, MTTR, and change management correlation.
- **Quick Tip:** Use Splunk Add-on for ServiceNow or REST API integration to pull ticket and CMDB data.
- **Quick Start:**
  - UC-16.1.2 · SLA Compliance Monitoring (critical, Ticketing Systems)
  - UC-16.1.9 · Change-Incident Correlation (critical, Ticketing Systems)
  - UC-16.1.3 · MTTR by Category (high, Ticketing Systems)
  - UC-16.1.4 · Change Success Rate (high, Ticketing Systems)
  - UC-16.2.1 · CMDB Data Quality Score (high, Configuration Management (CMDB))

## 17. Network Security & Zero Trust
- **Icon:** lock
- **Description:** NAC (802.1X), micro-segmentation, and SASE — network access control, posture assessment, and zero trust enforcement.
- **Quick Tip:** Collect ISE/NAC RADIUS accounting logs and install Splunk_TA_cisco-ise for structured data.
- **Quick Start:**
  - UC-17.2.3 · Geo-Location Anomalies (critical, VPN & Remote Access)
  - UC-17.2.8 · Simultaneous Session Detection (critical, VPN & Remote Access)
  - UC-17.1.2 · Endpoint Posture Failures (high, Network Access Control (NAC))
  - UC-17.1.8 · NAC Policy Change Audit (high, Network Access Control (NAC))
  - UC-17.2.1 · VPN Concurrent Sessions (high, VPN & Remote Access)

## 18. Data Center Fabric & SDN
- **Icon:** nodeNetwork
- **Description:** Cisco ACI, NSX-T, and software-defined networking — fabric health, policy compliance, and endpoint tracking.
- **Quick Tip:** Install Splunk Add-on for Cisco ACI and connect to APIC for fault, event, and audit data.
- **Quick Start:**
  - UC-18.2.5 · Transport Node Connectivity (critical, VMware NSX)
  - UC-18.2.1 · Distributed Firewall Rule Hits (high, VMware NSX)
  - UC-18.1.2 · Fault Trending by Severity (high, Cisco ACI)
  - UC-18.1.3 · Endpoint Mobility Tracking (high, Cisco ACI)
  - UC-18.1.4 · Contract/Filter Hit Analysis (high, Cisco ACI)

## 19. Compute Infrastructure (HCI & Converged)
- **Icon:** servers
- **Description:** Cisco UCS, Nutanix, and hyper-converged infrastructure — blade health, service profiles, and hardware faults.
- **Quick Tip:** Install vendor TA (UCS Manager, Nutanix Prism) and configure XML API or REST collection.
- **Quick Start:**
  - UC-19.1.1 · Blade/Rack Server Health (critical, Cisco UCS)
  - UC-19.1.5 · FI Port Channel Health (critical, Cisco UCS)
  - UC-19.2.1 · Cluster Health Monitoring (critical, Hyper-Converged Infrastructure (HCI))
  - UC-19.2.3 · Storage I/O Latency (critical, Hyper-Converged Infrastructure (HCI))
  - UC-19.2.5 · Disk Failure Tracking (critical, Hyper-Converged Infrastructure (HCI))

## 20. Cost & Capacity Management
- **Icon:** dollarMark
- **Description:** Cloud cost monitoring and capacity planning — spend trends, idle resources, rightsizing, and budget alerts.
- **Quick Tip:** Ingest cloud billing data (AWS CUR, Azure Cost Management) and use Splunk for trend analysis.
- **Quick Start:**
  - UC-20.1.1 · Daily Spend Trending (high, Cloud Cost Monitoring)
  - UC-20.1.4 · Idle Resource Identification (high, Cloud Cost Monitoring)
  - UC-20.1.5 · Budget Threshold Alerting (high, Cloud Cost Monitoring)
  - UC-20.2.1 · Compute Capacity Forecasting (high, Capacity Planning)
  - UC-20.2.2 · Storage Growth Forecasting (high, Capacity Planning)

## 21. Industry Verticals
- **Icon:** globe
- **Description:** Industry-specific operational monitoring and compliance — energy, manufacturing, healthcare, transportation, oil & gas, retail, aviation, telecom, water utilities, insurance, and regulatory frameworks (GDPR, NIS2, DORA, CCPA, MiFID II, ISO 27001, NIST CSF, SOC 2).
- **Quick Tip:** Combine standard infrastructure TAs with industry-specific data sources (SCADA historians, HL7 feeds, fleet telematics, POS systems) for vertical-specific observability.
- **Quick Start:**
  - UC-21.1.1 · SCADA RTU Communication Health (critical, Energy and Utilities)
  - UC-21.2.1 · PLC Program Change Detection (critical, Manufacturing and Process Industry)
  - UC-21.3.1 · HL7 ADT Message Processing Latency (critical, Healthcare and Life Sciences)
  - UC-21.11.1 · GDPR PII Detection in Application Log Data (high, Regulatory and Compliance Frameworks)
  - UC-21.11.12 · DORA ICT Risk Management Dashboard (high, Regulatory and Compliance Frameworks)

