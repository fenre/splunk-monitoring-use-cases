# IT Infrastructure Monitoring Categories
## Splunk Core Infrastructure Monitoring Use Case Repository

---

## 1. Server & Compute

### 1.1 Linux Servers
- RHEL, Ubuntu, SUSE, CentOS, Debian, Amazon Linux
- System metrics (CPU, memory, disk, swap, load)
- Syslog, auth logs, cron, kernel messages
- Package management and patching
- Process monitoring and resource consumption

### 1.2 Windows Servers
- Windows Server (2016, 2019, 2022, 2025)
- Event logs (System, Application, Security, PowerShell)
- Performance counters (CPU, memory, disk, network)
- Windows services and scheduled tasks
- Active Directory domain controller health
- IIS web server logs and performance
- Windows Update and patch compliance

### 1.3 macOS Endpoints
- System logs (Unified Logging)
- Hardware and software inventory
- Security and compliance (FileVault, Gatekeeper)

### 1.4 Bare-Metal / Hardware
- BIOS/UEFI and firmware alerts
- Hardware health (IPMI/iLO/iDRAC/IMM)
- Disk controller and RAID status
- Power supply and fan health
- Temperature and thermal events

---

## 2. Virtualization

### 2.1 VMware vSphere
- ESXi host performance (CPU, memory, storage, network)
- vCenter events and alarms
- VM lifecycle (provisioning, migration, snapshots)
- Datastore capacity and latency
- DRS, HA, and vMotion events
- vSAN health and performance

### 2.2 Microsoft Hyper-V
- VM performance and resource allocation
- Hyper-V event logs and replication status
- Cluster Shared Volumes (CSV) health

### 2.3 KVM / Proxmox / oVirt
- Libvirt events and guest monitoring
- Host resource utilization

---

## 3. Containers & Orchestration

### 3.1 Docker
- Container lifecycle events (start, stop, crash, OOM)
- Container resource usage (CPU, memory, network, I/O)
- Image pull and build events
- Docker daemon logs

### 3.2 Kubernetes
- Cluster health (nodes, pods, deployments, replicasets)
- Control plane components (API server, etcd, scheduler, controller-manager)
- Pod scheduling, eviction, and restart events
- Resource requests vs. limits vs. actual usage
- Namespace and RBAC audit
- Ingress and service mesh telemetry
- Helm release tracking

### 3.3 OpenShift
- Operator lifecycle and cluster version updates
- Build and deployment pipelines
- OpenShift-specific security context constraints

### 3.4 Container Registries
- Image vulnerability scan results
- Push/pull activity and access audit

---

## 4. Cloud Infrastructure

### 4.1 Amazon Web Services (AWS)
- CloudTrail (API activity and audit)
- CloudWatch (metrics and logs)
- VPC Flow Logs (network traffic)
- GuardDuty (threat detection)
- Config (resource configuration compliance)
- S3 access logs
- EC2, RDS, Lambda, EKS, ECS resource monitoring
- Cost and billing data (Cost Explorer)
- IAM activity and credential reports

### 4.2 Microsoft Azure
- Azure Activity Log and diagnostic logs
- Azure Monitor metrics
- NSG Flow Logs
- Azure AD / Entra ID sign-in and audit logs
- Azure Security Center / Defender for Cloud alerts
- Azure VMs, SQL, AKS, App Service monitoring
- Cost management data

### 4.3 Google Cloud Platform (GCP)
- Cloud Audit Logs
- Cloud Monitoring metrics
- VPC Flow Logs
- Security Command Center findings
- GKE, Cloud Run, BigQuery monitoring

### 4.4 Multi-Cloud & Cloud Management
- Terraform state and plan drift detection
- Cloud cost optimization across providers
- Cross-cloud identity and access correlation

---

## 5. Network Infrastructure

### 5.1 Routers & Switches
- Syslog events (interface up/down, errors, warnings)
- SNMP polling (interface utilization, CPU, memory, uptime)
- Configuration change detection
- Routing protocol events (OSPF, BGP, EIGRP)
- Spanning Tree topology changes
- Vendors: Cisco IOS/IOS-XE/NX-OS, Arista, Juniper, HPE/Aruba

### 5.2 Firewalls
- Traffic logs (allow/deny)
- Threat detection and IPS/IDS events
- NAT translation events
- VPN tunnel status and usage
- Policy change auditing
- Vendors: Palo Alto, Cisco Firepower/ASA, Fortinet, Check Point, Sophos

### 5.3 Load Balancers & ADCs
- Virtual server health and availability
- Connection metrics and throughput
- SSL offload and certificate management
- Pool member health status
- Vendors: F5 BIG-IP, Citrix NetScaler/ADC, HAProxy, NGINX Plus, AWS ELB/ALB

### 5.4 Wireless Infrastructure
- AP health and client associations
- SSID performance and channel utilization
- Roaming and authentication events
- RF interference detection
- Vendors: Cisco (WLC, Catalyst, Meraki), Aruba, Juniper Mist

### 5.5 SD-WAN
- Tunnel health (loss, latency, jitter)
- Application performance per transport
- Path selection and policy routing events
- Site health and failover events
- Vendors: Cisco SD-WAN (Viptela), VMware VeloCloud, Fortinet, Palo Alto Prisma SD-WAN

### 5.6 DNS & DHCP
- Query logs and response times
- NXDOMAIN and SERVFAIL rates
- DHCP lease activity and pool utilization
- DNS security (DNSSEC, RPZ, sinkhole events)
- Platforms: Windows DNS/DHCP, BIND, Infoblox, Pi-hole, Cloudflare

### 5.7 Network Flow Data (NetFlow / sFlow / IPFIX)
- Traffic volume and patterns by source/destination
- Top talkers and application identification
- Anomalous traffic detection
- Bandwidth utilization trending

### 5.8 Network Management Platforms
- Cisco DNA Center / Catalyst Center
- Cisco Meraki Dashboard
- SolarWinds, PRTG, LibreNMS traps and alerts

---

## 6. Storage & Backup

### 6.1 SAN / NAS Storage
- Array health and controller status
- Volume capacity, IOPS, latency, throughput
- Disk failures and rebuild events
- Replication status
- Vendors: NetApp, Dell EMC (PowerStore, Unity, PowerScale/Isilon), Pure Storage, HPE (Nimble, 3PAR, Alletra)

### 6.2 Object Storage
- Bucket/container access patterns
- Storage capacity trending
- Replication and lifecycle policy events
- Platforms: AWS S3, Azure Blob, MinIO, Ceph

### 6.3 Backup & Recovery
- Backup job success/failure rates
- Backup duration and data volume trending
- Restore test results
- Retention policy compliance
- Platforms: Veeam, Commvault, Veritas NetBackup, Rubrik, Cohesity, AWS Backup

### 6.4 File Services
- SMB/NFS share access patterns and audit logs
- DFS replication health
- File access anomaly detection (ransomware indicators)

---

## 7. Database & Data Platforms

### 7.1 Relational Databases
- Query performance (slow queries, deadlocks, blocking)
- Connection pool utilization
- Replication lag and cluster health
- Tablespace/storage growth
- Backup and recovery status
- Platforms: Microsoft SQL Server, Oracle, PostgreSQL, MySQL/MariaDB

### 7.2 NoSQL Databases
- Cluster health and node membership
- Read/write latency and throughput
- Replication and sharding status
- Compaction and garbage collection events
- Platforms: MongoDB, Cassandra, Elasticsearch, Redis, CouchDB

### 7.3 Cloud-Managed Databases
- AWS RDS/Aurora, Azure SQL, Google Cloud SQL
- Performance insights and advisory recommendations
- Automated failover events
- Read replica lag

### 7.4 Data Warehouses & Analytics Platforms
- Query performance and resource consumption
- Cluster scaling events
- Data ingestion rates and pipeline health
- Platforms: Snowflake, Databricks, AWS Redshift, Google BigQuery, Azure Synapse

---

## 8. Application Infrastructure

### 8.1 Web Servers & Reverse Proxies
- Access logs (status codes, response times, request rates)
- Error logs
- SSL/TLS certificate monitoring
- Connection and thread pool metrics
- Platforms: Apache HTTP, NGINX, Caddy, Microsoft IIS, Traefik

### 8.2 Application Servers & Runtimes
- JVM performance (heap, GC, threads) for Java apps
- .NET CLR metrics
- Node.js event loop and memory
- Python application metrics
- Platforms: Apache Tomcat, JBoss/WildFly, WebLogic, WebSphere, Gunicorn, uWSGI

### 8.3 Message Queues & Event Streaming
- Queue depth and consumer lag
- Message throughput and latency
- Broker health and partition status
- Dead letter queues
- Platforms: Apache Kafka, RabbitMQ, ActiveMQ, AWS SQS/SNS, Azure Service Bus

### 8.4 API Gateways & Service Mesh
- Request rate, latency, and error rate per endpoint
- Rate limiting and throttling events
- Authentication and authorization failures
- Platforms: Kong, Apigee, AWS API Gateway, Istio, Linkerd, Envoy

### 8.5 Caching Layers
- Hit/miss ratio
- Memory utilization and eviction rates
- Replication and cluster health
- Platforms: Redis, Memcached, Varnish, CDN caches

---

## 9. Identity & Access Management

### 9.1 Active Directory / Entra ID
- Authentication events (success/failure/lockout)
- Group membership changes
- Privileged account activity
- Replication health
- GPO change detection

### 9.2 LDAP Directories
- Bind success/failure
- Search performance
- Schema and configuration changes
- Platforms: OpenLDAP, 389 Directory, Oracle Directory

### 9.3 Identity Providers (IdP) & SSO
- SAML/OIDC token issuance and validation
- MFA challenge and completion rates
- Anomalous authentication patterns
- Platforms: Okta, Ping Identity, Azure AD/Entra, Duo, OneLogin, Keycloak

### 9.4 Privileged Access Management (PAM)
- Session recordings and activity logs
- Password checkout and rotation events
- Emergency access / break-glass events
- Platforms: CyberArk, BeyondTrust, Delinea (Thycotic)

---

## 10. Security Infrastructure

### 10.1 Firewalls & Next-Gen Firewalls
- (Covered in 5.2 — cross-reference for security-focused use cases)
- Threat prevention events, URL filtering, sandboxing results

### 10.2 Intrusion Detection/Prevention (IDS/IPS)
- Alert correlation and trending
- Signature match vs. anomaly-based detections
- Platforms: Cisco Firepower, Snort, Suricata, Palo Alto Threat Prevention

### 10.3 Endpoint Detection & Response (EDR)
- Malware detection and quarantine events
- Process and file activity monitoring
- Threat hunting telemetry
- Platforms: CrowdStrike Falcon, Microsoft Defender for Endpoint, Cisco Secure Endpoint, SentinelOne, Carbon Black

### 10.4 Email Security
- Spam and phishing detection rates
- Quarantine and release activity
- DLP policy violations
- Platforms: Microsoft Defender for Office 365, Proofpoint, Mimecast, Cisco Email Security

### 10.5 Web Security / Secure Web Gateway
- URL category and reputation blocks
- DLP events over web traffic
- Cloud app usage (Shadow IT)
- Platforms: Cisco Umbrella, Zscaler, Netskope, Palo Alto Prisma Access

### 10.6 Vulnerability Management
- Scan results and vulnerability counts by severity
- Remediation tracking and SLA compliance
- Asset coverage and scan completeness
- Platforms: Tenable (Nessus), Qualys, Rapid7, Microsoft Defender Vulnerability Management

### 10.7 SIEM & SOAR
- Alert volume and disposition trending
- Playbook execution metrics
- Analyst workload and MTTR
- (Splunk ES and SOAR are the primary platforms here)

### 10.8 Certificate & PKI Management
- Certificate expiration monitoring
- CA health and issuance logs
- Certificate transparency log monitoring
- Platforms: Venafi, DigiCert, Let's Encrypt, internal PKIs

---

## 11. Email & Collaboration

### 11.1 Microsoft 365 / Exchange
- Mail flow logs and delivery status
- Mailbox audit logs
- Exchange Online Protection events
- Teams usage and quality metrics
- SharePoint and OneDrive activity

### 11.2 Google Workspace
- Admin audit logs
- Gmail message flow and DLP
- Drive sharing and access events
- Meet usage and quality

### 11.3 Unified Communications
- Call quality (jitter, latency, packet loss, MOS scores)
- Call Detail Records (CDR)
- System health and capacity
- Platforms: Cisco UCM/Webex, Microsoft Teams, Zoom

---

## 12. DevOps & CI/CD

### 12.1 Source Control
- Commit and merge activity
- Branch protection and access events
- Pull/merge request metrics
- Platforms: GitHub, GitLab, Bitbucket, Azure DevOps

### 12.2 CI/CD Pipelines
- Build success/failure rates and durations
- Deployment frequency and lead time
- Rollback events
- Platforms: Jenkins, GitHub Actions, GitLab CI, Azure Pipelines, ArgoCD

### 12.3 Artifact & Package Management
- Repository health and storage
- Dependency vulnerability scanning
- Download and access patterns
- Platforms: Artifactory, Nexus, GitHub Packages, npm, PyPI

### 12.4 Infrastructure as Code
- Terraform plan/apply results and drift detection
- Ansible/Puppet/Chef run outcomes
- Configuration compliance

---

## 13. Observability & Monitoring Stack

### 13.1 Splunk Platform Health
- Indexer performance (queue sizes, pipeline throughput)
- Search performance and concurrency
- Forwarder connectivity and data flow
- License usage trending
- KV store and deployment server health

### 13.2 Splunk ITSI (Premium)
- Service health scores and KPI trending
- Episode management and MTTD/MTTR
- Adaptive threshold effectiveness
- Correlation search performance

### 13.3 Third-Party Monitoring Integration
- Forwarding alerts from Nagios, Zabbix, Datadog, Prometheus/Grafana, PRTG
- Normalizing and correlating cross-tool alerts
- Monitoring tool health and gap detection

---

## 14. IoT & Operational Technology (OT)

### 14.1 Building Management Systems (BMS)
- HVAC performance and environmental conditions
- Power distribution and UPS monitoring
- Access control and physical security systems
- Protocols: BACnet, Modbus, SNMP

### 14.2 Industrial Control Systems (ICS/SCADA)
- PLC and RTU health
- Process variable monitoring
- Safety system events
- Protocols: OPC-UA, Modbus TCP, DNP3

### 14.3 Splunk Edge Hub
- Built-in sensor data (temperature, humidity, vibration, sound, air quality)
- External sensor integration (I²C probes)
- MQTT broker topics
- On-device anomaly detection (kNN)
- SNMP device polling from edge

### 14.4 IoT Platforms & Sensors
- Smart building sensors
- Environmental monitoring
- Asset tracking
- Platforms: Homey, Home Assistant, AWS IoT, Azure IoT Hub

---

## 15. Data Center Physical Infrastructure

### 15.1 Power & UPS
- UPS battery health and runtime
- PDU power consumption per rack/circuit
- Power redundancy status
- Generator test and activation events

### 15.2 Cooling & Environmental
- Temperature and humidity sensors per zone
- CRAC/CRAH unit performance
- Hot/cold aisle containment effectiveness
- Water leak detection

### 15.3 Physical Security
- Badge access logs
- Camera system health (NVR/DVR)
- Cabinet door open/close events

---

## 16. Service Management & ITSM

### 16.1 Ticketing Systems
- Incident volume and SLA compliance
- Change request approval and implementation tracking
- Problem management trending
- Platforms: ServiceNow, BMC Remedy, Jira Service Management, Zendesk

### 16.2 Configuration Management (CMDB)
- CI discovery and reconciliation
- Relationship mapping validation
- CMDB data quality metrics
- Platforms: ServiceNow CMDB, BMC Atrium, Device42

---

## 17. Network Security & Zero Trust

### 17.1 Network Access Control (NAC)
- Endpoint posture assessment
- VLAN assignment and segmentation enforcement
- Guest and BYOD onboarding
- Platforms: Cisco ISE, Aruba ClearPass, Forescout

### 17.2 VPN & Remote Access
- VPN tunnel establishment and teardown
- Concurrent session counts and capacity
- Split-tunnel vs. full-tunnel usage
- Geo-location anomaly detection
- Platforms: Cisco AnyConnect, GlobalProtect, Pulse Secure, OpenVPN, WireGuard

### 17.3 Zero Trust / SASE
- Conditional access policy enforcement
- Device trust score evaluation
- Micro-segmentation policy events
- Platforms: Zscaler, Netskope, Palo Alto Prisma, Cisco Secure Access

---

## 18. Data Center Fabric & SDN

### 18.1 Cisco ACI
- Fabric health and fault monitoring
- Tenant and EPG policy audit
- Endpoint mobility tracking
- Contract and filter rule analysis

### 18.2 VMware NSX
- Distributed firewall rule events
- Micro-segmentation enforcement
- Logical switch and router health

### 18.3 Other SDN
- OpenStack Neutron events
- Cloud-native networking (Cilium, Calico)

---

## 19. Compute Infrastructure (HCI & Converged)

### 19.1 Cisco UCS
- Blade and rack server health
- Service profile compliance
- Firmware and BIOS events
- Power and thermal monitoring

### 19.2 Hyper-Converged Infrastructure (HCI)
- Cluster health and node performance
- Storage pool capacity and I/O
- VM placement and rebalancing
- Platforms: Nutanix, VMware vSAN, Azure Stack HCI, Dell VxRail

---

## 20. Cost & Capacity Management

### 20.1 Cloud Cost Monitoring
- Spend by service, team, and tag
- Reserved instance and savings plan utilization
- Anomalous spend detection
- Budget threshold alerts

### 20.2 Capacity Planning
- Infrastructure utilization trending
- Growth forecasting (CPU, storage, network)
- License utilization tracking
- Right-sizing recommendations

---

*Total: 20 top-level categories, 60+ subcategories*

*Primary tools: Splunk Enterprise / Splunk Cloud with free Splunkbase add-ons (TAs). Premium exceptions noted where applicable (ITSI, ES).*
