# Splunk Core Infrastructure Monitoring — Use Case Repository

> A comprehensive collection of IT infrastructure monitoring use cases for Splunk.
> Primary focus: Splunk Enterprise / Cloud with free Splunkbase add-ons.
> Premium apps (ITSI, ES) noted where applicable.

---

## 1. Server & Compute

### 1.1 Linux Servers

**Splunk Add-on:** Splunk Add-on for Unix and Linux (TA-unix), Splunk Add-on for Syslog

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 1.1.1 | CPU utilization trending | Track per-host CPU usage over time, alert on sustained high utilization (>90% for 15+ min) | `cpu` (vmstat), `top` |
| 1.1.2 | Memory pressure detection | Monitor free/available memory and swap usage; alert when swap usage crosses threshold | `vmstat`, `free` |
| 1.1.3 | Disk capacity forecasting | Track filesystem usage trending and predict when disks will reach capacity | `df` |
| 1.1.4 | Disk I/O saturation | Detect high disk wait times (iowait) and throughput bottlenecks | `iostat` |
| 1.1.5 | System load anomalies | Alert when load average exceeds CPU core count for extended periods | `uptime`, `top` |
| 1.1.6 | Process crash detection | Detect unexpected process terminations via syslog (segfault, OOM killer, killed) | `/var/log/messages`, `/var/log/syslog` |
| 1.1.7 | OOM killer events | Alert on Linux Out-of-Memory killer invocations identifying the killed process | `/var/log/messages`, `dmesg` |
| 1.1.8 | SSH brute-force detection | Detect repeated failed SSH login attempts from single or distributed sources | `/var/log/auth.log`, `/var/log/secure` |
| 1.1.9 | Unauthorized sudo usage | Monitor sudo command execution and alert on failures or unusual users | `/var/log/auth.log`, `/var/log/secure` |
| 1.1.10 | Cron job failure monitoring | Track cron job execution and alert on failures or missing expected runs | `/var/log/cron`, syslog |
| 1.1.11 | Kernel panic detection | Alert on kernel panics, oops, and critical kernel errors | `dmesg`, `/var/log/kern.log` |
| 1.1.12 | NTP time sync drift | Monitor NTP synchronization status and alert on clock drift exceeding thresholds | `ntpq`, `chronyc` |
| 1.1.13 | Zombie process accumulation | Detect accumulation of zombie processes indicating application issues | `ps`, `top` |
| 1.1.14 | File descriptor exhaustion | Monitor open file descriptor counts per process approaching system limits | `/proc/sys/fs/file-nr`, `lsof` |
| 1.1.15 | Network interface errors | Track interface TX/RX errors, drops, and CRC errors indicating hardware or cabling issues | `netstat`, `interfaces` |
| 1.1.16 | Package vulnerability tracking | Monitor installed packages against known CVEs after security scans | Custom scripted input |
| 1.1.17 | Service availability monitoring | Track systemd/init service status and alert on unexpected stops | `service`, scripted input |
| 1.1.18 | User account changes | Detect creation, deletion, or modification of user accounts | `/var/log/auth.log`, `audit.log` |
| 1.1.19 | Filesystem read-only detection | Alert when a filesystem remounts as read-only indicating disk or mount issues | `dmesg`, syslog |
| 1.1.20 | Reboot detection | Detect unexpected server reboots (vs. planned maintenance windows) | `last`, `wtmp`, syslog |

### 1.2 Windows Servers

**Splunk Add-on:** Splunk Add-on for Microsoft Windows (Splunk_TA_windows)

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 1.2.1 | CPU utilization trending | Track per-host CPU usage over time with alerting on sustained high utilization | WMI/Perfmon: `Processor` |
| 1.2.2 | Memory utilization & paging | Monitor committed bytes, available memory, and page file usage | Perfmon: `Memory` |
| 1.2.3 | Disk space monitoring | Track logical disk free space and alert before capacity issues | Perfmon: `LogicalDisk` |
| 1.2.4 | Windows Service failures | Alert when critical Windows services stop unexpectedly | Event Log: System (Event ID 7036, 7034) |
| 1.2.5 | Event log flood detection | Detect abnormal volumes of event log entries indicating a problem loop | All Windows Event Logs |
| 1.2.6 | Failed login monitoring | Track failed logon events (4625) with source IP correlation | Security Event Log |
| 1.2.7 | Account lockout tracking | Monitor account lockouts (4740) with source computer identification | Security Event Log |
| 1.2.8 | Privileged group changes | Detect additions/removals from Domain Admins, Enterprise Admins, etc. | Security Event Log (4728, 4732, 4756) |
| 1.2.9 | Windows Update compliance | Track patch installation status and missing critical updates | WSUS logs, Windows Update log |
| 1.2.10 | Scheduled task failures | Monitor scheduled task outcomes and alert on failures | Event Log: Task Scheduler (Event ID 201) |
| 1.2.11 | Blue Screen of Death (BSOD) | Detect system crashes via bugcheck events | Event Log: System (Event ID 1001) |
| 1.2.12 | RDP session monitoring | Track Remote Desktop connections — who connected, from where, duration | Security Event Log (4624 type 10), TerminalServices |
| 1.2.13 | PowerShell script execution | Monitor PowerShell script block logging for suspicious command execution | PowerShell/Operational log (4104) |
| 1.2.14 | IIS web server monitoring | Track HTTP status codes, response times, and request volumes for IIS | IIS W3C logs |
| 1.2.15 | DNS Server health | Monitor Windows DNS query rates, failures, and zone transfer events | DNS Debug/Analytical logs |
| 1.2.16 | DHCP scope exhaustion | Alert when DHCP scopes approach capacity limits | DHCP Server audit log |
| 1.2.17 | Certificate expiration | Monitor certificates in the local certificate store approaching expiry | Scripted input / CertUtil |
| 1.2.18 | Active Directory replication | Track AD replication health and alert on failures between DCs | Directory Service event log, `repadmin` |
| 1.2.19 | Group Policy processing failures | Detect GPO application failures on member servers and workstations | Event Log: GroupPolicy (Event ID 1085, 1096) |
| 1.2.20 | Print spooler issues | Monitor print spooler service crashes and queue backlogs | Event Log: PrintService |

### 1.3 macOS Endpoints

**Splunk Add-on:** Splunk Add-on for macOS (or Universal Forwarder with custom inputs)

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 1.3.1 | System resource monitoring | Track CPU, memory, and disk utilization on macOS endpoints | `top`, `vm_stat`, `df` |
| 1.3.2 | FileVault encryption status | Verify all endpoints have FileVault disk encryption enabled | `fdesetup status` scripted input |
| 1.3.3 | Gatekeeper and SIP status | Ensure security features are enabled across the fleet | `spctl`, `csrutil` scripted input |
| 1.3.4 | Software update compliance | Track macOS and application patch levels | `softwareupdate`, system_profiler |
| 1.3.5 | Application crash monitoring | Detect frequent application crashes via crash reporter logs | `/Library/Logs/DiagnosticReports` |

### 1.4 Bare-Metal / Hardware

**Splunk Add-on:** Splunk Add-on for IPMI, vendor-specific TAs, SNMP

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 1.4.1 | Hardware sensor monitoring | Track temperature, voltage, and fan speed via IPMI/BMC | IPMI sensor data |
| 1.4.2 | RAID degradation alerts | Detect degraded RAID arrays, failed disks, and rebuild status | MegaCLI/storcli, RAID controller logs |
| 1.4.3 | Power supply failure | Alert on PSU failures or redundancy loss | IPMI SEL, iLO/iDRAC events |
| 1.4.4 | Predictive disk failure | Monitor SMART attributes for early disk failure indicators | `smartctl` scripted input |
| 1.4.5 | Firmware version compliance | Track BIOS/BMC firmware versions and flag outdated systems | IPMI, iLO/iDRAC API |
| 1.4.6 | Memory ECC error trending | Track correctable ECC memory errors that indicate impending failure | IPMI SEL, `edac-util` |

---

## 2. Virtualization

### 2.1 VMware vSphere

**Splunk Add-on:** Splunk Add-on for VMware (TA-vmware), Splunk App for VMware (optional)

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 2.1.1 | ESXi host CPU contention | Detect CPU ready times indicating overcommitted hosts | vCenter performance metrics |
| 2.1.2 | ESXi host memory ballooning | Alert on excessive memory ballooning or swapping at the hypervisor | vCenter performance metrics |
| 2.1.3 | Datastore capacity trending | Track datastore utilization and forecast when space will run out | vCenter inventory/performance |
| 2.1.4 | Datastore latency spikes | Alert on high storage latency (>20ms) impacting VM performance | vCenter performance metrics |
| 2.1.5 | VM snapshot sprawl | Detect VMs with old or excessively large snapshots consuming storage | vCenter inventory |
| 2.1.6 | vMotion tracking | Log and correlate VM migrations with performance events | vCenter events |
| 2.1.7 | HA failover events | Alert when HA restarts VMs due to host failure | vCenter events/alarms |
| 2.1.8 | DRS imbalance detection | Monitor DRS recommendations and migrations for cluster balance | vCenter events |
| 2.1.9 | VM sprawl detection | Identify orphaned, powered-off, or idle VMs wasting resources | vCenter inventory |
| 2.1.10 | vSAN health monitoring | Track vSAN disk group health, resync status, and capacity | vSAN health service |
| 2.1.11 | ESXi host hardware alerts | Forward CIM-based hardware health alerts (sensors, fans, PSU) | vCenter alarms |
| 2.1.12 | VM resource over-allocation | Identify VMs consistently using far less than allocated resources | vCenter performance |
| 2.1.13 | vCenter alarm correlation | Ingest and correlate all vCenter alarms with infrastructure events | vCenter alarms |
| 2.1.14 | ESXi patch compliance | Track ESXi build versions and flag hosts behind on patches | vCenter inventory |
| 2.1.15 | VM creation/deletion audit | Log all VM lifecycle events for change management compliance | vCenter events |

### 2.2 Microsoft Hyper-V

**Splunk Add-on:** Splunk Add-on for Microsoft Hyper-V, Windows Event Logs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 2.2.1 | VM performance monitoring | Track CPU, memory, and disk metrics per Hyper-V VM | Perfmon: Hyper-V counters |
| 2.2.2 | Hyper-V replication health | Monitor replication status and lag between primary and replica | Hyper-V event logs |
| 2.2.3 | Cluster Shared Volume health | Track CSV ownership, redirected access, and disk health | Failover Cluster logs |
| 2.2.4 | Live migration tracking | Log and audit VM live migration events | Hyper-V-VMMS event logs |
| 2.2.5 | Integration services version | Detect VMs with outdated integration services components | Hyper-V inventory |

### 2.3 KVM / Proxmox / oVirt

**Splunk Add-on:** Custom inputs via libvirt API, syslog

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 2.3.1 | Guest VM resource monitoring | Track per-VM CPU, memory, and I/O via libvirt metrics | `virsh`, libvirt API |
| 2.3.2 | Host overcommit detection | Alert when aggregate VM allocation exceeds host capacity | libvirt, custom scripts |
| 2.3.3 | VM lifecycle events | Track VM start, stop, migrate, and crash events | libvirt/syslog |

---

## 3. Containers & Orchestration

### 3.1 Docker

**Splunk Add-on:** Splunk Connect for Docker, Docker stats scripted inputs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 3.1.1 | Container crash loops | Detect containers repeatedly restarting (exit code != 0) | Docker events |
| 3.1.2 | Container OOM kills | Alert when containers are killed by the OOM killer | Docker events, host dmesg |
| 3.1.3 | Container CPU throttling | Detect containers hitting CPU limits and being throttled | Docker stats, cgroups |
| 3.1.4 | Container memory utilization | Track memory usage per container relative to limits | Docker stats |
| 3.1.5 | Image vulnerability scanning | Correlate container images with vulnerability scan results | Trivy, Snyk, or Grype output |
| 3.1.6 | Privileged container detection | Alert on containers running in privileged mode | Docker inspect, audit |
| 3.1.7 | Container sprawl | Identify stopped containers accumulating and wasting disk | Docker ps |
| 3.1.8 | Docker daemon errors | Monitor Docker daemon logs for errors and warnings | Docker daemon logs |

### 3.2 Kubernetes

**Splunk Add-on:** Splunk OpenTelemetry Collector for Kubernetes, Splunk Connect for Kubernetes

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 3.2.1 | Pod restart rate | Alert on pods with high restart counts indicating application instability | kube-state-metrics, K8s events |
| 3.2.2 | Pod scheduling failures | Detect pods stuck in Pending state due to resource constraints or affinity rules | K8s events |
| 3.2.3 | Node NotReady detection | Alert when cluster nodes transition to NotReady status | K8s events, node conditions |
| 3.2.4 | Resource quota exhaustion | Monitor namespace resource quotas approaching limits | kube-state-metrics |
| 3.2.5 | Persistent Volume claims | Track PVC binding status and alert on failed claims | K8s events |
| 3.2.6 | Deployment rollout failures | Detect failed deployments that don't reach desired replica count | K8s events, deployment status |
| 3.2.7 | Control plane health | Monitor API server latency, etcd health, scheduler, controller-manager | Control plane component metrics |
| 3.2.8 | etcd cluster health | Track etcd leader elections, compaction, and latency | etcd metrics |
| 3.2.9 | Ingress error rates | Monitor HTTP error rates (4xx/5xx) through ingress controllers | Ingress controller logs |
| 3.2.10 | CrashLoopBackOff detection | Alert on pods in CrashLoopBackOff state | kube-state-metrics |
| 3.2.11 | HPA scaling events | Track Horizontal Pod Autoscaler scaling decisions and limits | K8s events |
| 3.2.12 | RBAC audit | Monitor RBAC permission changes and unauthorized access attempts | K8s audit log |
| 3.2.13 | Certificate expiration | Track Kubernetes TLS certificate expiry (API server, kubelet, etc.) | cert-manager, scripted input |
| 3.2.14 | Container image pull failures | Detect ImagePullBackOff errors indicating registry or image issues | K8s events |
| 3.2.15 | DaemonSet completeness | Ensure DaemonSets are running on all expected nodes | kube-state-metrics |

### 3.3 OpenShift

**Splunk Add-on:** OpenTelemetry Collector, OpenShift audit logs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 3.3.1 | Cluster version & upgrade status | Track OpenShift cluster upgrade progress and failures | ClusterVersion API |
| 3.3.2 | Operator degraded detection | Alert when cluster operators report degraded status | ClusterOperator API |
| 3.3.3 | Build failure monitoring | Track OpenShift build outcomes and failure patterns | Build events |
| 3.3.4 | SCC violation detection | Detect pods violating Security Context Constraints | OpenShift audit logs |

### 3.4 Container Registries

**Splunk Add-on:** Custom API inputs, webhook receivers

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 3.4.1 | Image push/pull audit | Track who pushed or pulled images, when, and from where | Registry audit logs |
| 3.4.2 | Vulnerability scan results | Ingest and trend vulnerability findings per image/tag | Harbor, ACR, ECR scan results |
| 3.4.3 | Storage quota monitoring | Track registry storage usage and alert on capacity | Registry metrics/API |

---

## 4. Cloud Infrastructure

### 4.1 Amazon Web Services (AWS)

**Splunk Add-on:** Splunk Add-on for AWS (Splunk_TA_aws), Splunk App for AWS

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 4.1.1 | Unauthorized API calls | Detect API calls that return AccessDenied or UnauthorizedAccess errors | CloudTrail |
| 4.1.2 | Root account usage | Alert on any AWS root account activity | CloudTrail |
| 4.1.3 | Security group changes | Track modifications to security groups (ingress/egress rule changes) | CloudTrail |
| 4.1.4 | IAM policy changes | Monitor IAM policy creation, modification, and attachment | CloudTrail |
| 4.1.5 | Console login without MFA | Detect console sign-ins that don't use multi-factor authentication | CloudTrail |
| 4.1.6 | EC2 instance state changes | Track instance launches, stops, terminations for audit | CloudTrail |
| 4.1.7 | S3 bucket policy changes | Alert on S3 bucket policy or ACL modifications (public exposure risk) | CloudTrail, S3 access logs |
| 4.1.8 | GuardDuty finding ingestion | Ingest and correlate GuardDuty threat findings | GuardDuty via CloudWatch |
| 4.1.9 | VPC flow log analysis | Detect rejected traffic, unusual traffic patterns, data exfiltration | VPC Flow Logs |
| 4.1.10 | EC2 performance monitoring | Track EC2 CPU, network, and EBS metrics; alert on anomalies | CloudWatch metrics |
| 4.1.11 | RDS performance insights | Monitor database connections, CPU, read/write IOPS, replica lag | CloudWatch, RDS logs |
| 4.1.12 | Lambda error rate monitoring | Track Lambda invocation errors, timeouts, and cold starts | CloudWatch, Lambda logs |
| 4.1.13 | EKS/ECS cluster health | Monitor container orchestration health in managed services | CloudWatch, EKS/ECS events |
| 4.1.14 | Cost anomaly detection | Alert on sudden spend increases vs. baseline by service or account | Cost Explorer data, CUR |
| 4.1.15 | Config compliance monitoring | Track AWS Config rule evaluations and non-compliant resources | AWS Config |
| 4.1.16 | KMS key usage audit | Monitor encryption key usage and rotation status | CloudTrail |
| 4.1.17 | Elastic IP association | Track EIP allocations and associations for inventory accuracy | CloudTrail |
| 4.1.18 | CloudFormation stack drift | Detect infrastructure drift from declared CloudFormation templates | CloudFormation events |
| 4.1.19 | WAF blocked request analysis | Analyze AWS WAF blocked requests by rule, source IP, and URI | AWS WAF logs |
| 4.1.20 | Reserved Instance utilization | Track RI/Savings Plan coverage and utilization rates | Cost Explorer, CUR |

### 4.2 Microsoft Azure

**Splunk Add-on:** Splunk Add-on for Microsoft Cloud Services (Splunk_TA_microsoft-cloudservices), Azure Event Hub integration

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 4.2.1 | Azure Activity Log monitoring | Track resource creation, modification, deletion across subscriptions | Activity Log |
| 4.2.2 | Entra ID sign-in anomalies | Detect risky sign-ins, impossible travel, and unusual locations | Entra ID sign-in logs |
| 4.2.3 | Entra ID privilege escalation | Monitor role assignments and privileged identity management events | Entra ID audit logs |
| 4.2.4 | NSG flow log analysis | Analyze network traffic patterns and blocked connections | NSG Flow Logs |
| 4.2.5 | Azure VM performance | Track VM CPU, memory, disk, and network metrics | Azure Monitor metrics |
| 4.2.6 | Azure SQL performance | Monitor DTU/vCore consumption, deadlocks, and long-running queries | Azure SQL diagnostics |
| 4.2.7 | AKS cluster health | Monitor Kubernetes cluster health, node pool status, and pod events | AKS diagnostics |
| 4.2.8 | Azure Key Vault access audit | Track secret, key, and certificate access patterns | Key Vault diagnostic logs |
| 4.2.9 | Defender for Cloud alerts | Ingest and correlate Microsoft Defender security alerts | Defender via Event Hub |
| 4.2.10 | Storage account access anomalies | Detect unusual access patterns to storage accounts | Storage diagnostic logs |
| 4.2.11 | Resource health events | Track Azure service health incidents affecting your resources | Azure Resource Health |
| 4.2.12 | Cost management alerts | Monitor spending by resource group and alert on budget thresholds | Cost Management data |

### 4.3 Google Cloud Platform (GCP)

**Splunk Add-on:** Splunk Add-on for Google Cloud Platform (Splunk_TA_google-cloudplatform)

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 4.3.1 | Audit log monitoring | Track admin activity and data access across GCP projects | Cloud Audit Logs |
| 4.3.2 | IAM policy changes | Detect changes to IAM bindings and service account key creation | Cloud Audit Logs |
| 4.3.3 | VPC Flow Log analysis | Analyze network traffic for anomalies and denied connections | VPC Flow Logs |
| 4.3.4 | GKE cluster health | Monitor GKE node status, pod failures, and scaling events | GKE logs and metrics |
| 4.3.5 | Security Command Center | Ingest vulnerability findings and threat detections | SCC findings |
| 4.3.6 | GCE instance monitoring | Track Compute Engine VM performance and lifecycle | Cloud Monitoring metrics |
| 4.3.7 | BigQuery audit and cost | Monitor query execution, slot utilization, and cost per query | BigQuery audit logs |
| 4.3.8 | Cloud Run/Functions errors | Track serverless function errors and cold start latency | Cloud Logging |

### 4.4 Multi-Cloud & Cloud Management

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 4.4.1 | Terraform drift detection | Compare deployed infrastructure against Terraform state | Terraform plan output |
| 4.4.2 | Cross-cloud identity correlation | Correlate user activity across AWS/Azure/GCP for unified audit | Combined cloud audit logs |
| 4.4.3 | Multi-cloud cost dashboard | Unified cost visibility across cloud providers | CUR, Azure Cost, GCP Billing |
| 4.4.4 | Cloud resource tagging compliance | Identify untagged or mis-tagged resources across clouds | Cloud provider APIs |

---

## 5. Network Infrastructure

### 5.1 Routers & Switches

**Splunk Add-on:** Splunk Add-on for Cisco (Splunk_TA_cisco), Splunk Add-on for Infrastructure (Syslog/SNMP)

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 5.1.1 | Interface up/down events | Alert on network interface state changes (link flapping) | Syslog (%LINEPROTO, %LINK) |
| 5.1.2 | Interface error rates | Track CRC errors, input/output errors, and discards by interface | SNMP IF-MIB |
| 5.1.3 | Interface utilization | Monitor bandwidth utilization per interface and alert on saturation | SNMP IF-MIB (ifInOctets/ifOutOctets) |
| 5.1.4 | BGP peer state changes | Alert on BGP neighbor state transitions (Established/Idle) | Syslog (%BGP) |
| 5.1.5 | OSPF neighbor adjacency | Detect OSPF neighbor state changes indicating routing instability | Syslog (%OSPF) |
| 5.1.6 | Spanning Tree topology change | Alert on STP topology change notifications and root bridge changes | Syslog (%SPANTREE) |
| 5.1.7 | Configuration change detection | Detect when device configurations are modified (who, when, what) | Syslog (%SYS-5-CONFIG_I), SNMP trap |
| 5.1.8 | Device CPU/memory utilization | Monitor network device CPU and memory to detect resource exhaustion | SNMP HOST-RESOURCES-MIB |
| 5.1.9 | Device uptime / reload tracking | Track device reboots and uptime across the network estate | SNMP sysUpTime, syslog |
| 5.1.10 | VLAN configuration changes | Detect VLAN additions, removals, and trunk modifications | Syslog, configuration audit |
| 5.1.11 | Power supply / fan failures | Alert on hardware component failures in network devices | SNMP ENTITY-MIB, syslog |
| 5.1.12 | ARP/MAC table anomalies | Detect MAC flapping, ARP storms, or gratuitous ARP flooding | Syslog (%SW_MATM, %ARP) |
| 5.1.13 | ACL deny logging | Track and trend ACL deny hits for security visibility | Syslog (ACL log entries) |
| 5.1.14 | SNMP authentication failures | Alert on failed SNMP community string or SNMPv3 authentication | Syslog (%SNMP) |
| 5.1.15 | Environmental monitoring | Track device temperature and alert on thermal thresholds | SNMP CISCO-ENVMON-MIB |

### 5.2 Firewalls

**Splunk Add-on:** Vendor-specific TAs (Palo Alto, Cisco, Fortinet, Check Point)

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 5.2.1 | Top denied traffic sources | Identify top sources of denied connections by IP, port, and zone | Firewall traffic logs |
| 5.2.2 | Policy change audit | Track firewall rule additions, modifications, and deletions | Firewall system/config logs |
| 5.2.3 | Threat detection events | Correlate IPS/IDS threat events with traffic context | Threat logs |
| 5.2.4 | VPN tunnel status | Monitor IPsec/SSL VPN tunnel state changes and throughput | VPN system logs |
| 5.2.5 | High-risk port exposure | Alert on traffic allowed to high-risk ports (RDP, SMB, etc.) from untrusted zones | Traffic logs |
| 5.2.6 | Geo-IP anomaly detection | Flag traffic to/from unexpected or sanctioned countries | Traffic logs + GeoIP lookup |
| 5.2.7 | Connection rate anomalies | Detect spikes in connection rates indicating DDoS or scanning | Traffic logs |
| 5.2.8 | Certificate inspection failures | Track SSL/TLS decryption failures and certificate errors | Decryption logs |
| 5.2.9 | URL filtering blocks | Monitor and trend web content filtering blocks by category | URL filtering logs |
| 5.2.10 | Admin access audit | Track who accessed the firewall management, from where, and what they changed | System/auth logs |
| 5.2.11 | Firewall resource utilization | Monitor session table usage, CPU, and memory on firewall appliances | System resource logs, SNMP |
| 5.2.12 | NAT pool exhaustion | Alert when NAT translation pools approach capacity limits | NAT logs |

### 5.3 Load Balancers & ADCs

**Splunk Add-on:** Splunk Add-on for F5 BIG-IP, Citrix ADC TA, custom syslog

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 5.3.1 | Pool member health status | Alert when backend pool members go offline or flap | Health monitor logs |
| 5.3.2 | Virtual server availability | Track VIP availability and alert on service-down events | LTM logs |
| 5.3.3 | Connection and throughput trending | Monitor connections per second and throughput per VIP | Performance metrics |
| 5.3.4 | SSL certificate expiry | Alert on upcoming SSL certificate expirations on load balancer | Certificate inventory |
| 5.3.5 | HTTP error rate by VIP | Track backend HTTP 5xx error rates per virtual server | Request logs |
| 5.3.6 | Response time degradation | Detect increasing response times for backend services | Performance metrics |
| 5.3.7 | Session persistence issues | Identify persistence failures causing session affinity problems | LTM logs |
| 5.3.8 | WAF policy violations | Monitor and trend web application firewall rule triggers | ASM/WAF logs (F5, Citrix) |

### 5.4 Wireless Infrastructure

**Splunk Add-on:** Splunk Add-on for Cisco Meraki, Cisco WLC syslog, Aruba syslog

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 5.4.1 | AP offline detection | Alert when access points become unreachable or go offline | WLC/Meraki events |
| 5.4.2 | Client association failures | Track failed client associations and authentication failures | WLC/AP syslog |
| 5.4.3 | Channel utilization | Monitor RF channel utilization and detect congestion | WLC/Meraki RF metrics |
| 5.4.4 | Rogue AP detection | Alert on rogue access points detected in the environment | WLC/Meraki security events |
| 5.4.5 | Client count trending | Track connected client counts per AP/SSID for capacity planning | WLC/Meraki client data |
| 5.4.6 | RF interference events | Detect radar events (DFS), interference, and channel changes | WLC/AP syslog |
| 5.4.7 | Wireless authentication trends | Monitor 802.1X authentication success/failure rates | RADIUS logs, WLC events |

### 5.5 SD-WAN

**Splunk Add-on:** Cisco SD-WAN TA, vendor-specific APIs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 5.5.1 | Tunnel health monitoring | Track tunnel loss, latency, and jitter per transport | vManage API / BFD metrics |
| 5.5.2 | Site availability | Alert when SD-WAN edge devices go offline | vManage device status |
| 5.5.3 | Application SLA violations | Detect when application traffic violates defined SLA thresholds | App-aware routing metrics |
| 5.5.4 | Path failover events | Track path switches and failover events between transports | vManage events |
| 5.5.5 | Control plane health | Monitor connections to vSmart controllers and vManage | Control connection logs |
| 5.5.6 | Certificate expiration | Track SD-WAN device certificate lifetimes | vManage API |
| 5.5.7 | Bandwidth utilization per site | Monitor WAN bandwidth consumption by site and transport | Interface metrics |

### 5.6 DNS & DHCP

**Splunk Add-on:** Splunk Add-on for Infoblox, Windows DNS/DHCP logs, BIND syslog

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 5.6.1 | DNS query volume trending | Track DNS queries per second for capacity planning | DNS query logs |
| 5.6.2 | NXDOMAIN spike detection | Alert on unusual NXDOMAIN rates indicating DGA malware or misconfiguration | DNS query logs |
| 5.6.3 | SERVFAIL rate monitoring | Detect increases in SERVFAIL responses indicating upstream issues | DNS query logs |
| 5.6.4 | DNS tunneling detection | Identify anomalously long DNS queries or high query volumes to single domains | DNS query logs |
| 5.6.5 | DHCP scope exhaustion | Alert when DHCP pools are running low on available addresses | DHCP lease logs |
| 5.6.6 | DHCP rogue server detection | Detect unauthorized DHCP servers on the network | DHCP conflict events |
| 5.6.7 | DNS record change audit | Track zone file changes (A, CNAME, MX, etc.) for change management | DNS update logs, Infoblox audit |
| 5.6.8 | DNS latency monitoring | Track DNS response times and alert on degradation | DNS recursive query metrics |

### 5.7 Network Flow Data

**Splunk Add-on:** Splunk App for Stream, Splunk Add-on for NetFlow, sFlow collectors

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 5.7.1 | Top talkers analysis | Identify top bandwidth consumers by source/destination pair | NetFlow/sFlow/IPFIX |
| 5.7.2 | Anomalous traffic patterns | Detect unusual traffic flows (new protocols, unexpected destinations) | NetFlow |
| 5.7.3 | Bandwidth utilization by application | Track bandwidth consumption by application/protocol | NetFlow with NBAR |
| 5.7.4 | East-west traffic monitoring | Monitor internal lateral traffic for anomaly detection | NetFlow from internal segments |
| 5.7.5 | Data exfiltration detection | Alert on unusually large outbound transfers to uncommon destinations | NetFlow |
| 5.7.6 | Port scan detection | Detect hosts connecting to many ports on single targets | NetFlow |

### 5.8 Network Management Platforms

**Splunk Add-on:** Cisco DNA Center TA, Meraki TA, syslog/SNMP trap receivers

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 5.8.1 | DNA Center assurance alerts | Ingest and correlate Cisco DNA Center issue alerts | DNA Center API |
| 5.8.2 | Meraki organization monitoring | Track Meraki device status, client counts, and connectivity across orgs | Meraki Dashboard API |
| 5.8.3 | SNMP trap consolidation | Centralize SNMP traps from all NMS platforms for correlation | SNMP trap receiver |
| 5.8.4 | Network device inventory | Maintain up-to-date inventory from NMS discovery results | NMS API exports |

---

## 6. Storage & Backup

### 6.1 SAN / NAS Storage

**Splunk Add-on:** Vendor-specific TAs (NetApp TA, Dell EMC TA, Pure Storage TA), SNMP

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 6.1.1 | Volume capacity trending | Track volume/LUN utilization and predict when space will run out | Storage array API/metrics |
| 6.1.2 | Storage latency monitoring | Alert on read/write latency exceeding SLA thresholds | Array performance metrics |
| 6.1.3 | IOPS trending per volume | Monitor IOPS patterns to detect workload changes and hotspots | Array performance metrics |
| 6.1.4 | Disk failure alerts | Alert on disk failures and spare disk consumption | Array event logs |
| 6.1.5 | Replication lag monitoring | Track async replication lag between primary and DR arrays | Array replication metrics |
| 6.1.6 | Controller failover events | Alert on storage controller failover events indicating hardware issues | Array event logs |
| 6.1.7 | Thin provisioning overcommit | Alert when thin-provisioned capacity exceeds physical capacity thresholds | Array capacity metrics |
| 6.1.8 | Snapshot space consumption | Track snapshot usage and alert on runaway growth | Array capacity reports |
| 6.1.9 | Fibre Channel port errors | Monitor FC port link failures, CRC errors, and signal loss | FC switch logs, SNMP |
| 6.1.10 | Storage array firmware compliance | Track firmware versions and flag arrays behind on patches | Array inventory API |

### 6.2 Object Storage

**Splunk Add-on:** Cloud provider TAs, MinIO webhook, custom API inputs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 6.2.1 | Bucket capacity trending | Track storage growth per bucket/container over time | S3/Blob/GCS metrics |
| 6.2.2 | Access pattern anomalies | Detect unusual access patterns (spikes in reads/writes, new sources) | Access logs |
| 6.2.3 | Public bucket detection | Alert on buckets with public read/write ACLs | Cloud Config rules, API |
| 6.2.4 | Lifecycle policy compliance | Verify objects are transitioning/expiring per policy | Cloud provider metrics |
| 6.2.5 | Cross-region replication lag | Monitor replication status for geo-redundant storage | Replication metrics |

### 6.3 Backup & Recovery

**Splunk Add-on:** Vendor-specific TAs (Veeam TA, Commvault TA), syslog, scripted inputs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 6.3.1 | Backup job success rate | Track backup job outcomes (success/warning/failure) per job and client | Backup server logs |
| 6.3.2 | Backup job duration trending | Identify jobs with increasing duration indicating growth or performance issues | Backup server logs |
| 6.3.3 | Missed backup detection | Alert when expected backup jobs don't run within their scheduled window | Backup scheduler logs |
| 6.3.4 | Backup storage capacity | Monitor backup repository/tape library capacity utilization | Backup infrastructure metrics |
| 6.3.5 | Restore test tracking | Track restore test results and flag systems with no recent successful restore | Backup logs, manual input |
| 6.3.6 | Backup SLA compliance | Dashboard showing backup coverage, RPO/RTO compliance per system | Backup logs, CMDB correlation |
| 6.3.7 | Backup data volume trending | Track daily backup data volumes for capacity planning | Backup job statistics |
| 6.3.8 | Tape library health | Monitor tape drive errors, media faults, and library hardware status | Tape library logs, SNMP |

### 6.4 File Services

**Splunk Add-on:** Windows Event Logs (file auditing), NFS syslogs, Varonis TA

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 6.4.1 | File access audit | Track who accessed what files, when, and from where | Windows Security (4663) |
| 6.4.2 | Ransomware indicator detection | Alert on mass file rename/encrypt patterns (high rate of file modifications) | File audit logs |
| 6.4.3 | DFS replication health | Monitor DFS-R backlog and conflict rates between servers | DFS-R event logs |
| 6.4.4 | Share permission changes | Detect modifications to share and NTFS permissions | Windows Security events |
| 6.4.5 | Large file transfer detection | Alert on unusually large file copies that may indicate data exfiltration | File audit logs |

---

## 7. Database & Data Platforms

### 7.1 Relational Databases

**Splunk Add-on:** Splunk DB Connect, Splunk Add-on for Microsoft SQL Server, MySQL/PostgreSQL TAs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 7.1.1 | Slow query detection | Identify queries exceeding duration thresholds and impacting performance | Slow query logs, DMVs |
| 7.1.2 | Deadlock monitoring | Alert on database deadlocks and identify the involved queries/tables | Error logs, trace flags |
| 7.1.3 | Connection pool exhaustion | Alert when active connections approach maximum limits | Performance counters, DMVs |
| 7.1.4 | Replication lag monitoring | Track master-slave or Always On replication lag | Replication status queries |
| 7.1.5 | Tablespace/data file growth | Monitor database file sizes and predict capacity needs | Scripted input, DB Connect |
| 7.1.6 | Backup success verification | Confirm database backups complete successfully within windows | Backup logs, msdb history |
| 7.1.7 | Login failure monitoring | Track failed database authentication attempts | Error logs, audit logs |
| 7.1.8 | Long-running transaction detection | Alert on transactions held open for extended periods causing blocking | DMVs, `pg_stat_activity` |
| 7.1.9 | Index fragmentation | Monitor index fragmentation levels and alert when above threshold | DMVs, scripted input |
| 7.1.10 | TempDB contention (SQL Server) | Detect TempDB allocation bottlenecks affecting query performance | SQL Server DMVs |
| 7.1.11 | Buffer cache hit ratio | Monitor database buffer cache effectiveness | Performance counters |
| 7.1.12 | Database availability group health | Track Always On AG/RAC cluster status and failover events | SQL Server AG DMVs, Oracle alert log |
| 7.1.13 | Schema change detection | Alert on DDL changes (CREATE/ALTER/DROP) to production databases | Audit logs, DDL triggers |
| 7.1.14 | Query plan regression | Detect when query execution plans change causing performance degradation | Query store, plan cache |
| 7.1.15 | Privilege escalation audit | Monitor GRANT/REVOKE operations and privileged role assignments | Audit logs |

### 7.2 NoSQL Databases

**Splunk Add-on:** Custom inputs, vendor APIs, JMX for Java-based systems

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 7.2.1 | Cluster membership changes | Alert on node additions, removals, or failures in the cluster | Cluster event logs |
| 7.2.2 | Replication lag/consistency | Monitor replication lag between primary and secondaries | Database metrics (rs.status, nodetool) |
| 7.2.3 | Read/write latency trending | Track operation latency percentiles over time | Database metrics |
| 7.2.4 | Shard imbalance detection | Detect uneven data distribution across shards | Shard statistics |
| 7.2.5 | Compaction monitoring | Track compaction operations and alert on pending compaction backlogs | Cassandra/MongoDB logs |
| 7.2.6 | GC pause detection | Alert on long garbage collection pauses in Java-based databases | JVM GC logs |
| 7.2.7 | Connection count monitoring | Track client connections approaching configured limits | Database metrics |
| 7.2.8 | Index build monitoring | Track index creation progress and impact on cluster performance | Database logs |
| 7.2.9 | Memory utilization | Monitor cache hit ratios, resident memory, and eviction rates | Database metrics |
| 7.2.10 | Elasticsearch cluster health | Track cluster status (green/yellow/red) and unassigned shards | Elasticsearch API |

### 7.3 Cloud-Managed Databases

**Splunk Add-on:** Cloud provider TAs (AWS, Azure, GCP)

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 7.3.1 | RDS/Aurora performance insights | Track top SQL, wait events, and resource bottlenecks | RDS Performance Insights |
| 7.3.2 | Automated failover events | Detect and alert on managed database failovers | CloudWatch events, Activity Log |
| 7.3.3 | Read replica lag | Monitor replica lag and alert when it exceeds thresholds | CloudWatch/Azure Monitor |
| 7.3.4 | Storage auto-scaling events | Track storage scaling events and remaining capacity | Cloud provider events |
| 7.3.5 | Maintenance window tracking | Alert on upcoming and completed maintenance events | Cloud provider notifications |

### 7.4 Data Warehouses & Analytics Platforms

**Splunk Add-on:** Custom API inputs, cloud provider integrations

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 7.4.1 | Query performance trending | Track warehouse query duration, queue time, and resource consumption | Query history/logs |
| 7.4.2 | Cluster scaling events | Monitor auto-scaling decisions and cluster resizing | Platform event logs |
| 7.4.3 | Data pipeline health | Track ETL/ELT job outcomes and data freshness | Pipeline orchestrator logs |
| 7.4.4 | Credit/cost per query | Monitor compute cost per query for optimization (Snowflake, BigQuery) | Usage/billing APIs |
| 7.4.5 | Warehouse utilization | Track warehouse concurrency and queuing to right-size resources | Usage metrics |

---

## 8. Application Infrastructure

### 8.1 Web Servers & Reverse Proxies

**Splunk Add-on:** Splunk Add-on for Apache, Splunk Add-on for NGINX, IIS logs via Windows TA

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 8.1.1 | HTTP error rate monitoring | Track 4xx and 5xx error rates and alert on spikes | Access logs |
| 8.1.2 | Response time trending | Monitor server response times and alert on degradation | Access logs (response time field) |
| 8.1.3 | Request rate trending | Track requests per second for capacity planning | Access logs |
| 8.1.4 | Top error URIs | Identify the most error-prone endpoints | Access logs |
| 8.1.5 | SSL certificate monitoring | Alert on certificate expiration dates approaching | Scripted input, certificate checks |
| 8.1.6 | Upstream backend health | Monitor NGINX/HAProxy backend server status and failover | Error logs, upstream health |
| 8.1.7 | Bot and crawler detection | Identify and quantify bot traffic vs. legitimate users | Access logs (user-agent analysis) |
| 8.1.8 | Connection pool saturation | Detect when worker threads/processes reach configured maximums | Server status metrics, error logs |
| 8.1.9 | Slow POST detection | Identify slow HTTP POST requests indicating application performance issues | Access logs |
| 8.1.10 | Configuration reload tracking | Log and audit web server configuration reloads and restarts | Error/event logs |

### 8.2 Application Servers & Runtimes

**Splunk Add-on:** Splunk Add-on for JMX, custom log inputs, OpenTelemetry Collector

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 8.2.1 | JVM heap utilization | Track Java heap memory usage and alert before OOM | JMX metrics |
| 8.2.2 | Garbage collection impact | Monitor GC pause duration and frequency | GC logs, JMX |
| 8.2.3 | Thread pool exhaustion | Detect when application thread pools are saturated | JMX, application metrics |
| 8.2.4 | Application error rate | Track application-level exceptions and error log entries | Application logs |
| 8.2.5 | Deployment tracking | Log application deployments for change correlation | Deployment tool webhooks |
| 8.2.6 | Connection pool monitoring | Track JDBC/database connection pool usage and wait times | JMX, application metrics |
| 8.2.7 | Session count trending | Monitor active user sessions for capacity planning | Application metrics |
| 8.2.8 | .NET CLR performance | Track .NET memory, exception rate, and thread count | Perfmon CLR counters |
| 8.2.9 | Node.js event loop lag | Monitor event loop latency and detect blocking operations | Node.js process metrics |
| 8.2.10 | Class loading issues | Detect ClassNotFoundException or NoClassDefFoundError patterns | Application error logs |

### 8.3 Message Queues & Event Streaming

**Splunk Add-on:** Splunk Add-on for Kafka, RabbitMQ management API, custom JMX inputs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 8.3.1 | Consumer lag monitoring | Alert when Kafka consumer group lag exceeds thresholds | Kafka metrics (JMX, Burrow) |
| 8.3.2 | Queue depth trending | Track message queue depths and alert on growing backlogs | RabbitMQ/ActiveMQ management API |
| 8.3.3 | Broker health monitoring | Track broker availability, disk usage, and resource utilization | Broker metrics, JMX |
| 8.3.4 | Under-replicated partitions | Alert on Kafka partitions that are under-replicated | Kafka JMX metrics |
| 8.3.5 | Dead letter queue monitoring | Alert when messages appear in dead letter queues | Queue management APIs |
| 8.3.6 | Message throughput trending | Track messages produced/consumed per second | Broker metrics |
| 8.3.7 | Topic/queue creation audit | Log creation and deletion of topics/queues | Broker audit logs |
| 8.3.8 | Consumer group rebalancing | Detect frequent consumer rebalances indicating instability | Kafka logs |
| 8.3.9 | Partition leader elections | Track leader elections indicating broker instability | Kafka controller logs |
| 8.3.10 | Message age monitoring | Alert when message age in queue exceeds SLA thresholds | Queue metrics |

### 8.4 API Gateways & Service Mesh

**Splunk Add-on:** Custom API inputs, Envoy access logs, Istio telemetry

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 8.4.1 | API error rate by endpoint | Track 4xx/5xx error rates per API endpoint | API gateway access logs |
| 8.4.2 | API latency percentiles | Monitor P50/P95/P99 latency per endpoint | Access logs, metrics |
| 8.4.3 | Rate limiting events | Track rate-limited requests by consumer and endpoint | Gateway logs |
| 8.4.4 | Authentication failures | Monitor OAuth/API key authentication failure rates | Gateway auth logs |
| 8.4.5 | Service-to-service call failures | Track inter-service communication failures in the mesh | Envoy/Istio access logs |
| 8.4.6 | Circuit breaker activations | Alert when circuit breakers trip indicating downstream failures | Service mesh metrics |
| 8.4.7 | API consumer usage tracking | Monitor API usage per consumer/key for billing and quotas | Gateway access logs |
| 8.4.8 | mTLS certificate expiration | Track service mesh mTLS certificate lifetimes | Istio/Linkerd metrics |

### 8.5 Caching Layers

**Splunk Add-on:** Custom inputs, Redis CLI scripted input, SNMP

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 8.5.1 | Cache hit/miss ratio | Track cache effectiveness and alert on degradation | Redis INFO, Memcached stats |
| 8.5.2 | Memory utilization | Monitor cache memory usage and eviction rates | Redis INFO, Memcached stats |
| 8.5.3 | Eviction rate trending | Alert on high eviction rates indicating undersized cache | Cache metrics |
| 8.5.4 | Connection count monitoring | Track client connections approaching limits | Cache metrics |
| 8.5.5 | Replication lag (Redis) | Monitor Redis replication offset lag between master and replicas | Redis INFO replication |
| 8.5.6 | Slow command detection | Identify slow Redis commands impacting performance | Redis SLOWLOG |
| 8.5.7 | Key expiration trending | Monitor key TTL patterns and expired key rates | Redis INFO keyspace |

---

## 9. Identity & Access Management

### 9.1 Active Directory / Entra ID

**Splunk Add-on:** Splunk Add-on for Microsoft Windows, Splunk Add-on for Microsoft Cloud Services

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 9.1.1 | Brute-force login detection | Detect repeated failed logon attempts against single accounts | Security Event Log (4625) |
| 9.1.2 | Account lockout monitoring | Track and alert on account lockouts with source identification | Security Event Log (4740) |
| 9.1.3 | Privileged group membership changes | Alert on additions/removals from Domain Admins, Schema Admins, etc. | Security Event Log (4728, 4732, 4756) |
| 9.1.4 | Service account anomalies | Detect service accounts used interactively or from unexpected hosts | Security Event Log (4624) |
| 9.1.5 | Kerberos ticket anomalies | Detect Kerberoasting (4769) or Golden Ticket attacks (4768/4769 anomalies) | Security Event Log |
| 9.1.6 | Password policy violations | Monitor password change attempts and policy enforcement failures | Security Event Log (4723, 4724) |
| 9.1.7 | GPO modification detection | Alert on Group Policy Object changes to prevent unauthorized changes | Security Event Log (5136) |
| 9.1.8 | AD replication monitoring | Track replication health between domain controllers | Directory Service event log |
| 9.1.9 | LDAP query performance | Monitor LDAP search durations and expensive queries | Directory Service diagnostics |
| 9.1.10 | Stale account detection | Identify accounts that haven't logged in within defined periods | AD attribute queries via scripted input |
| 9.1.11 | Entra ID risky sign-ins | Ingest and alert on Entra ID Identity Protection risk detections | Entra ID sign-in logs |
| 9.1.12 | Conditional Access policy failures | Track Conditional Access policy blocks and non-compliant devices | Entra ID sign-in logs |

### 9.2 LDAP Directories

**Splunk Add-on:** Syslog, custom inputs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 9.2.1 | Bind failure monitoring | Track LDAP bind failures and identify brute-force patterns | LDAP server logs |
| 9.2.2 | Search performance degradation | Alert on LDAP search queries exceeding time thresholds | LDAP access logs |
| 9.2.3 | Schema modification audit | Detect unauthorized schema changes to the directory | LDAP audit logs |
| 9.2.4 | Replication health monitoring | Track directory replication status between servers | Replication logs |

### 9.3 Identity Providers (IdP) & SSO

**Splunk Add-on:** Splunk Add-on for Okta, Duo TA, custom API inputs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 9.3.1 | MFA challenge failure rate | Track MFA challenge success/failure rates and identify struggling users | IdP logs |
| 9.3.2 | Impossible travel detection | Alert when a user authenticates from geographically distant locations in short timeframes | IdP sign-in logs |
| 9.3.3 | Token anomaly detection | Detect unusual SAML/OIDC token requests or token replay attempts | IdP audit logs |
| 9.3.4 | Application access patterns | Monitor which applications users access and detect anomalous patterns | IdP access logs |
| 9.3.5 | IdP availability monitoring | Track IdP service health and response times | IdP status API |
| 9.3.6 | Phishing-resistant MFA adoption | Track migration from SMS/phone MFA to FIDO2/WebAuthn | IdP MFA logs |
| 9.3.7 | Session hijacking detection | Detect sessions used from multiple IPs or locations simultaneously | IdP session logs |

### 9.4 Privileged Access Management (PAM)

**Splunk Add-on:** Vendor-specific TAs (CyberArk TA, BeyondTrust TA)

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 9.4.1 | Privileged session audit | Track all privileged sessions — who, when, what system, duration | PAM session logs |
| 9.4.2 | Password checkout tracking | Monitor password checkout/checkin activity and detect hoarding | PAM vault logs |
| 9.4.3 | Break-glass account usage | Alert immediately on emergency/break-glass account access | PAM vault events |
| 9.4.4 | Credential rotation compliance | Track password rotation schedules and flag overdue rotations | PAM policy logs |
| 9.4.5 | Suspicious session commands | Detect high-risk commands during privileged sessions (rm -rf, format, etc.) | PAM session recordings |
| 9.4.6 | Vault health monitoring | Monitor PAM vault availability, replication, and component health | PAM infrastructure logs |

---

## 10. Security Infrastructure

### 10.1 Next-Gen Firewalls (Security-Focused)

**Splunk Add-on:** Palo Alto TA, Cisco Firepower TA, Fortinet TA

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 10.1.1 | Threat prevention event trending | Track IPS/AV/Anti-spyware detections over time by severity | Threat logs |
| 10.1.2 | Wildfire/sandbox verdicts | Monitor file submissions and malicious verdict rates | Wildfire/sandbox logs |
| 10.1.3 | C2 communication detection | Alert on traffic matching command-and-control patterns | Threat/URL filtering logs |
| 10.1.4 | DNS sinkhole hits | Track queries to sinkholed domains indicating compromised hosts | DNS proxy/sinkhole logs |
| 10.1.5 | SSL decryption coverage | Monitor percentage of traffic being decrypted for inspection | Decryption statistics |

### 10.2 Intrusion Detection/Prevention (IDS/IPS)

**Splunk Add-on:** Vendor-specific TAs, Snort/Suricata syslog

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 10.2.1 | Alert severity trending | Track IDS/IPS alert volumes by severity over time | IDS/IPS alert logs |
| 10.2.2 | Top targeted hosts | Identify most-targeted internal hosts by alert count | IDS/IPS alert logs |
| 10.2.3 | Signature coverage gaps | Identify traffic or network segments not covered by IDS/IPS sensors | Sensor health/coverage reports |
| 10.2.4 | False positive tracking | Monitor and trend false positive rates per signature for tuning | Alert logs + analyst disposition |
| 10.2.5 | Lateral movement detection | Alert on IDS/IPS detections on internal segments indicating lateral movement | IDS/IPS alerts from internal sensors |

### 10.3 Endpoint Detection & Response (EDR)

**Splunk Add-on:** CrowdStrike TA, Microsoft Defender TA, Cisco Secure Endpoint TA, SentinelOne TA

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 10.3.1 | Malware detection trending | Track malware detection rates across the endpoint fleet | EDR detection events |
| 10.3.2 | Quarantine action monitoring | Monitor quarantine success/failure rates | EDR action logs |
| 10.3.3 | Agent health monitoring | Detect endpoints with offline, outdated, or unhealthy EDR agents | EDR agent status |
| 10.3.4 | Behavioral detection alerts | Track behavioral/heuristic detections that bypass signature-based detection | EDR behavioral alerts |
| 10.3.5 | Endpoint isolation events | Monitor when endpoints are network-isolated due to threats | EDR containment logs |
| 10.3.6 | Threat hunting indicators | Track suspicious process trees, LOLBin usage, and fileless malware indicators | EDR telemetry |
| 10.3.7 | EDR coverage gaps | Identify endpoints without EDR agent deployed | EDR inventory vs. CMDB |
| 10.3.8 | Ransomware canary detection | Alert on mass file encryption patterns detected by EDR | EDR behavioral detection |

### 10.4 Email Security

**Splunk Add-on:** Microsoft O365 TA, Proofpoint TA, vendor-specific TAs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 10.4.1 | Phishing detection rate | Track phishing emails caught vs. delivered over time | Email security gateway logs |
| 10.4.2 | Malicious attachment tracking | Monitor attachment-based threats by file type and detection method | Email security logs |
| 10.4.3 | URL click tracking | Monitor user clicks on malicious URLs in emails | URL protection/rewrite logs |
| 10.4.4 | DLP policy violations | Track data loss prevention triggers on outbound email | DLP logs |
| 10.4.5 | Spoofed email detection | Monitor DMARC/SPF/DKIM failures indicating spoofing attempts | Email authentication logs |
| 10.4.6 | Email volume anomalies | Detect unusual outbound email volumes (potential compromised account) | Mail flow logs |
| 10.4.7 | Quarantine management | Track quarantine rates and user release requests | Email gateway logs |

### 10.5 Web Security / Secure Web Gateway

**Splunk Add-on:** Cisco Umbrella TA, Zscaler TA, vendor-specific TAs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 10.5.1 | Blocked category trending | Track web content filtering blocks by URL category | SWG logs |
| 10.5.2 | Shadow IT detection | Identify unapproved SaaS application usage by users | SWG/CASB logs |
| 10.5.3 | Malware download blocks | Monitor blocked malware downloads from web traffic | SWG threat logs |
| 10.5.4 | DLP over web traffic | Track data loss prevention events on web uploads | SWG DLP logs |
| 10.5.5 | DNS security events | Monitor blocked DNS queries to malicious domains | Umbrella/DNS security logs |
| 10.5.6 | Bandwidth abuse detection | Identify users consuming excessive bandwidth on streaming/personal sites | SWG traffic logs |
| 10.5.7 | Unencrypted traffic detection | Flag sensitive transactions over HTTP instead of HTTPS | SWG logs |

### 10.6 Vulnerability Management

**Splunk Add-on:** Tenable TA, Qualys TA, Rapid7 TA

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 10.6.1 | Critical vulnerability trending | Track critical/high severity vulnerability counts over time | Scan results |
| 10.6.2 | Mean time to remediation | Measure average time between detection and fix by severity | Scan results (first/last seen) |
| 10.6.3 | Scan coverage monitoring | Identify assets not scanned within expected intervals | Scan schedules, asset inventory |
| 10.6.4 | Patch compliance by team/BU | Dashboard showing vulnerability remediation status per team | Scan results + CMDB |
| 10.6.5 | Exploitable vulnerability prioritization | Correlate vulnerabilities with known exploits (CISA KEV, EPSS) | Scan results + threat intel |
| 10.6.6 | Vulnerability SLA compliance | Track remediation against SLA targets (Critical=7d, High=30d, etc.) | Scan results with timestamps |
| 10.6.7 | New vulnerability detection | Alert on newly discovered critical vulnerabilities in the environment | Scan delta comparison |

### 10.7 SIEM & SOAR

**Splunk Add-on:** Splunk Enterprise Security (Premium), Splunk SOAR

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 10.7.1 | Alert volume trending | Track notable event volumes by source type over time | ES notable events |
| 10.7.2 | Analyst workload distribution | Monitor alert assignment and resolution rates per analyst | ES investigation logs |
| 10.7.3 | MTTD and MTTR tracking | Measure mean time to detect and respond to security incidents | ES notable events |
| 10.7.4 | Playbook execution monitoring | Track SOAR playbook success/failure rates and execution times | SOAR logs |
| 10.7.5 | Correlation search performance | Monitor ES correlation search run times and resource consumption | _internal scheduler logs |
| 10.7.6 | False positive rate tracking | Track true positive vs. false positive rates per detection rule | ES analyst dispositions |

### 10.8 Certificate & PKI Management

**Splunk Add-on:** Custom scripted inputs, certificate monitoring scripts

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 10.8.1 | Certificate expiry monitoring | Alert at 90/60/30/7 day thresholds before certificate expiration | Certificate inventory scans |
| 10.8.2 | Certificate issuance audit | Track new certificate issuance from internal and external CAs | CA audit logs |
| 10.8.3 | Weak cipher/key detection | Identify certificates using deprecated algorithms or short key lengths | Certificate scan results |
| 10.8.4 | Certificate revocation tracking | Monitor CRL and OCSP revocation activity | CA logs |
| 10.8.5 | CT log monitoring | Alert on certificates issued for your domains via Certificate Transparency | CT log API |

---

## 11. Email & Collaboration

### 11.1 Microsoft 365 / Exchange

**Splunk Add-on:** Splunk Add-on for Microsoft Office 365 (Splunk_TA_MS_O365), Splunk Add-on for Microsoft Exchange

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 11.1.1 | Mail flow health monitoring | Track message delivery rates, queuing, and NDR volumes | Exchange message tracking logs |
| 11.1.2 | Mailbox audit logging | Monitor mailbox access by delegates, admins, and owners | O365 unified audit log |
| 11.1.3 | Exchange Online Protection events | Track spam, phishing, and malware filtering effectiveness | EOP message trace |
| 11.1.4 | Teams usage analytics | Monitor Teams adoption, meeting quality, and usage patterns | Teams activity reports |
| 11.1.5 | SharePoint/OneDrive sharing audit | Track external sharing and detect overshared content | O365 audit log |
| 11.1.6 | DLP policy events | Monitor Data Loss Prevention policy matches across M365 services | O365 DLP logs |
| 11.1.7 | Admin activity audit | Track administrative actions in M365 admin center | O365 audit log |
| 11.1.8 | Inbox rule monitoring | Detect creation of suspicious inbox forwarding rules (data exfiltration) | O365 audit log |
| 11.1.9 | Service health monitoring | Track M365 service advisories and incidents | M365 Service Health API |
| 11.1.10 | License utilization | Monitor M365 license assignments and usage for cost optimization | M365 admin reports |

### 11.2 Google Workspace

**Splunk Add-on:** Splunk Add-on for Google Workspace (Splunk_TA_GoogleWorkspace)

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 11.2.1 | Admin console audit | Track admin actions, user management, and organizational changes | Admin audit log |
| 11.2.2 | Gmail message flow | Monitor email delivery, spam rates, and DLP triggers | Gmail logs |
| 11.2.3 | Drive sharing anomalies | Detect unusual file sharing patterns, especially external sharing | Drive audit log |
| 11.2.4 | Login anomaly detection | Identify suspicious login activity, location changes, device changes | Login audit log |
| 11.2.5 | Meet quality monitoring | Track meeting quality metrics and participant experience | Meet quality logs |
| 11.2.6 | Third-party app access | Monitor OAuth app grants and third-party integrations | Token audit log |

### 11.3 Unified Communications

**Splunk Add-on:** Cisco UCM/Webex TA, custom CDR inputs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 11.3.1 | Call quality monitoring (MOS) | Track Mean Opinion Score (MOS) across calls and flag poor quality | CDR/CMR records |
| 11.3.2 | Call volume trending | Monitor call volumes for capacity planning and anomaly detection | CDR records |
| 11.3.3 | VoIP jitter/latency/packet loss | Track real-time transport quality metrics | CMR records, RTP metrics |
| 11.3.4 | Trunk utilization | Monitor PRI/SIP trunk utilization and alert on capacity issues | Gateway/trunk CDRs |
| 11.3.5 | Conference bridge capacity | Track meeting/bridge resource usage | Webex/UCM reports |
| 11.3.6 | Toll fraud detection | Alert on unusual international or premium-rate call patterns | CDR records |
| 11.3.7 | Phone registration status | Monitor IP phone registration health and detect mass de-registration | UCM device status |
| 11.3.8 | Webex meeting analytics | Track Webex meeting quality, participant counts, and engagement | Webex API |

---

## 12. DevOps & CI/CD

### 12.1 Source Control

**Splunk Add-on:** GitHub TA, GitLab webhook inputs, custom API inputs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 12.1.1 | Commit activity trending | Track commit volumes by repository, team, and contributor | Git webhook events |
| 12.1.2 | Branch protection bypasses | Alert when commits are pushed directly to protected branches | GitHub/GitLab audit log |
| 12.1.3 | Pull request metrics | Track PR open-to-merge time, review cycles, and abandonment rates | PR events |
| 12.1.4 | Secret exposure detection | Alert when secrets (API keys, passwords) appear in commits | Pre-commit hook results, GitGuardian |
| 12.1.5 | Repository access audit | Monitor repository permission changes and access events | Audit logs |
| 12.1.6 | Force push detection | Alert on force pushes that could overwrite history | Git webhook events |

### 12.2 CI/CD Pipelines

**Splunk Add-on:** Jenkins TA, custom webhook receivers

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 12.2.1 | Build success rate trending | Track build pass/fail rates per pipeline and project | CI/CD event logs |
| 12.2.2 | Build duration monitoring | Detect builds with increasing duration indicating pipeline degradation | CI/CD metrics |
| 12.2.3 | Deployment frequency (DORA) | Track deployment frequency as a DORA metric | Deployment events |
| 12.2.4 | Lead time for changes (DORA) | Measure time from commit to production deployment | Git + deployment correlation |
| 12.2.5 | Failed deployment tracking | Alert on failed deployments and track rollback events | Deployment logs |
| 12.2.6 | Pipeline queue time | Monitor job queue wait times indicating runner/agent shortage | CI/CD system metrics |
| 12.2.7 | Test coverage trending | Track unit/integration test coverage per project over time | Test result reports |
| 12.2.8 | Security scan results in pipeline | Monitor SAST/DAST/SCA scan findings blocking deployments | Security tool outputs |

### 12.3 Artifact & Package Management

**Splunk Add-on:** Custom API inputs, webhook receivers

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 12.3.1 | Artifact repository health | Monitor storage utilization and cleanup policy effectiveness | Artifactory/Nexus metrics |
| 12.3.2 | Dependency vulnerability alerts | Track vulnerable dependencies across projects | SCA tool output (Snyk, Dependabot) |
| 12.3.3 | Package download anomalies | Detect unusual download patterns indicating supply chain attacks | Repository access logs |
| 12.3.4 | License compliance tracking | Monitor open-source license usage for compliance | SCA tool output |

### 12.4 Infrastructure as Code

**Splunk Add-on:** Custom log inputs, CI/CD integration

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 12.4.1 | Terraform plan/apply tracking | Log all Terraform operations with resource change summaries | Terraform CLI output |
| 12.4.2 | Configuration drift detection | Detect when infrastructure drifts from declared IaC state | Terraform plan, cloud config |
| 12.4.3 | Ansible playbook outcomes | Track Ansible run results (changed/failed/ok counts per play) | Ansible callback plugin output |
| 12.4.4 | Puppet/Chef compliance reports | Monitor configuration management compliance rates | Puppet/Chef reports |
| 12.4.5 | IaC policy violations | Track OPA/Sentinel policy check results blocking deployments | Policy engine output |

---

## 13. Observability & Monitoring Stack

### 13.1 Splunk Platform Health

**Splunk Add-on:** Splunk Monitoring Console (built-in), Splunk Add-on for Splunk

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 13.1.1 | Indexer queue fill ratio | Alert when indexing queues (parsing, merging, typing) back up | _internal (metrics.log) |
| 13.1.2 | Search concurrency monitoring | Track concurrent search counts and alert on license limits | _internal (scheduler) |
| 13.1.3 | Forwarder connectivity | Detect universal forwarders that stop sending data | _internal (metrics.log) |
| 13.1.4 | License usage trending | Track daily license consumption and predict overage | _internal (license_usage.log) |
| 13.1.5 | Skipped search detection | Identify scheduled searches that are being skipped due to concurrency | _internal (scheduler) |
| 13.1.6 | Index size trending | Monitor index sizes and predict when retention limits will be hit | _internal (indexes) |
| 13.1.7 | KV store health | Monitor KV store replication lag and connection issues | _internal (kvstore) |
| 13.1.8 | Deployment server status | Track app deployment status to forwarders | _internal (deployment server) |
| 13.1.9 | Data ingestion latency | Detect event indexing lag (difference between _time and _indextime) | Any index (sampling) |
| 13.1.10 | Search head cluster status | Monitor SHC captain, member health, and replication | _internal (SHC) |
| 13.1.11 | Indexer cluster bucket replication | Track bucket replication status and factor compliance | _internal (CM) |
| 13.1.12 | HEC endpoint health | Monitor HTTP Event Collector availability and error rates | _internal (http_event_collector) |
| 13.1.13 | Sourcetype breakdown trending | Track data volume per sourcetype for capacity planning | _internal (license_usage.log) |
| 13.1.14 | Long-running search detection | Alert on searches running longer than expected thresholds | _internal (scheduler, search audit) |
| 13.1.15 | Splunk certificate expiration | Monitor expiry of Splunk internal SSL certificates | _internal (splunkd) |

### 13.2 Splunk ITSI (Premium)

**Splunk Add-on:** Splunk IT Service Intelligence, Content Pack for Monitoring and Alerting

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 13.2.1 | Service health score trending | Track service health over time for SLA reporting | itsi_summary |
| 13.2.2 | KPI degradation alerting | Alert when KPIs breach adaptive or static thresholds | Correlation searches |
| 13.2.3 | Episode volume and MTTR | Track episode creation rates and time-to-resolution | itsi_grouped_alerts |
| 13.2.4 | Entity status monitoring | Track entity states (active, inactive, unstable) across entity types | Entity overview |
| 13.2.5 | Base search performance | Monitor KPI base search runtimes and skipped searches | _internal (scheduler) |
| 13.2.6 | Rules Engine health | Ensure the ITSI Rules Engine is running and processing events | _internal (itsi_internal_log) |
| 13.2.7 | Predictive service degradation | Use MLTK to predict service health degradation before it happens | itsi_summary + MLTK |
| 13.2.8 | Glass Table NOC display | Real-time service health visualization for operations centers | ITSI Glass Tables |

### 13.3 Third-Party Monitoring Integration

**Splunk Add-on:** Custom webhook/API inputs, Prometheus remote write, SNMP trap receiver

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 13.3.1 | Nagios/Zabbix alert ingestion | Forward alerts from legacy monitoring tools into Splunk for correlation | Nagios/Zabbix webhook/export |
| 13.3.2 | Prometheus metric ingestion | Ingest Prometheus metrics for long-term storage and correlation | Prometheus remote write |
| 13.3.3 | PagerDuty/Opsgenie integration | Track alert lifecycle and on-call response metrics | PagerDuty API |
| 13.3.4 | Monitoring coverage gap detection | Identify hosts in the CMDB not covered by any monitoring tool | Cross-tool asset correlation |
| 13.3.5 | Alert storm detection | Detect correlated alert storms across multiple monitoring tools | Multi-source alert correlation |

---

## 14. IoT & Operational Technology (OT)

### 14.1 Building Management Systems (BMS)

**Splunk Add-on:** MQTT inputs, Modbus TA, SNMP, custom API inputs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 14.1.1 | HVAC performance monitoring | Track temperature setpoints, actual values, and energy consumption | BACnet/Modbus sensors |
| 14.1.2 | UPS battery monitoring | Monitor UPS charge levels, runtime, and battery health | SNMP (UPS-MIB) |
| 14.1.3 | Power consumption trending | Track building/floor/rack power consumption over time | Smart PDU metrics |
| 14.1.4 | Access control event audit | Log badge access events for physical security correlation | Access control system logs |
| 14.1.5 | Elevator/equipment health | Monitor equipment fault codes and maintenance indicators | BMS event logs |
| 14.1.6 | Environmental compliance | Ensure temperature/humidity stay within compliance ranges (data center, labs) | Environmental sensors |

### 14.2 Industrial Control Systems (ICS/SCADA)

**Splunk Add-on:** Splunk Add-on for OPC, MQTT inputs, Modbus TA

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 14.2.1 | PLC/RTU health monitoring | Track controller health, CPU load, and memory utilization | OPC-UA metrics |
| 14.2.2 | Process variable anomalies | Alert on process variables deviating from normal operating ranges | OPC-UA/Modbus data |
| 14.2.3 | Safety system activation | Log and alert on safety interlock and emergency shutdown events | Safety PLC logs |
| 14.2.4 | Network segmentation monitoring | Verify IT/OT network boundary enforcement | Firewall logs, flow data |
| 14.2.5 | Firmware version tracking | Track PLC/RTU firmware versions for vulnerability management | Asset inventory scans |
| 14.2.6 | Unauthorized access detection | Alert on access to ICS systems from unauthorized sources | ICS network logs, firewalls |

### 14.3 Splunk Edge Hub

**Splunk Add-on:** Splunk Edge Hub (built-in), Splunk Add-on for Edge Hub

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 14.3.1 | Temperature anomaly detection | Use built-in kNN model to detect temperature anomalies | Edge Hub temperature sensor |
| 14.3.2 | Vibration monitoring | Track equipment vibration patterns and detect anomalies | Edge Hub vibration sensor |
| 14.3.3 | Air quality monitoring | Monitor CO2, VOC, and particulate levels | Edge Hub air quality sensor |
| 14.3.4 | Sound level anomalies | Detect unusual sound levels indicating equipment issues | Edge Hub sound sensor |
| 14.3.5 | MQTT device monitoring | Track MQTT-connected device health and message rates | Edge Hub MQTT broker |
| 14.3.6 | SNMP device polling from edge | Monitor remote/OT devices via SNMP through Edge Hub | Edge Hub SNMP integration |
| 14.3.7 | Edge-to-cloud data pipeline | Monitor Edge Hub data forwarding health to Splunk Cloud | Edge Hub system logs |

### 14.4 IoT Platforms & Sensors

**Splunk Add-on:** Custom API inputs, MQTT, webhook receivers

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 14.4.1 | Smart sensor fleet health | Track sensor battery levels, connectivity, and data freshness | IoT platform API |
| 14.4.2 | Environmental monitoring | Monitor temperature, humidity, water leak sensors across facilities | Sensor data (MQTT, API) |
| 14.4.3 | Asset tracking | Track asset locations and movement patterns | GPS/BLE beacon data |
| 14.4.4 | Home automation monitoring | Track smart home events, device status, and energy usage | Homey/Home Assistant API |
| 14.4.5 | IoT device firmware compliance | Identify IoT devices running outdated or vulnerable firmware | Device inventory scans |

---

## 15. Data Center Physical Infrastructure

### 15.1 Power & UPS

**Splunk Add-on:** SNMP (UPS-MIB, PDU-MIB), vendor APIs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 15.1.1 | UPS battery health | Monitor battery charge, runtime remaining, and replace indicators | SNMP UPS-MIB |
| 15.1.2 | PDU power per rack | Track per-rack and per-circuit power consumption | SNMP PDU metrics |
| 15.1.3 | Power redundancy status | Alert on loss of power feed redundancy (A/B feed) | PDU/UPS events |
| 15.1.4 | Generator test results | Log generator test runs and alert on failures | BMS/generator controller |
| 15.1.5 | PUE calculation | Calculate Power Usage Effectiveness from facility vs. IT load | Aggregate power metrics |
| 15.1.6 | Circuit breaker trips | Alert on breaker trips and overcurrent events | PDU/BMS events |

### 15.2 Cooling & Environmental

**Splunk Add-on:** SNMP, BMS integration, environmental sensor inputs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 15.2.1 | Temperature monitoring per zone | Track temperature across data center zones and alert on exceedances | Environmental sensors |
| 15.2.2 | Humidity monitoring | Alert on humidity outside acceptable range (40-60% RH) | Environmental sensors |
| 15.2.3 | CRAC/CRAH unit health | Monitor cooling unit operational status and performance | BMS/SNMP |
| 15.2.4 | Hot aisle temperature trending | Track hot aisle return air temperatures for cooling efficiency | Environmental sensors |
| 15.2.5 | Water leak detection | Alert immediately on water detection sensors | Leak detection system |
| 15.2.6 | Cooling capacity planning | Trend cooling load vs. capacity for future planning | BMS metrics |

### 15.3 Physical Security

**Splunk Add-on:** Access control system integration, custom syslog/API

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 15.3.1 | Badge access audit | Track all data center physical access events | Access control system |
| 15.3.2 | After-hours access alerts | Alert on data center access outside business hours | Access control with time rules |
| 15.3.3 | Tailgating detection | Detect multiple badge-ins without corresponding badge-outs | Access control events |
| 15.3.4 | Camera system health | Monitor NVR/DVR recording status and camera connectivity | Video management system |
| 15.3.5 | Cabinet door monitoring | Track server cabinet door open/close events | Cabinet lock sensors |

---

## 16. Service Management & ITSM

### 16.1 Ticketing Systems

**Splunk Add-on:** Splunk Add-on for ServiceNow, Splunk Add-on for Jira, custom API inputs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 16.1.1 | Incident volume trending | Track incident creation rates over time by category and priority | ITSM ticket data |
| 16.1.2 | SLA compliance monitoring | Measure response and resolution SLA adherence per priority level | Ticket timestamps |
| 16.1.3 | MTTR by category | Track mean time to resolve incidents by category and assignment group | Ticket lifecycle data |
| 16.1.4 | Change success rate | Monitor change request outcomes (successful, failed, backed out) | Change records |
| 16.1.5 | Change collision detection | Alert when multiple changes are scheduled for overlapping windows on related CIs | Change calendar data |
| 16.1.6 | Problem trending | Identify recurring incident patterns that should become problems | Incident categorization data |
| 16.1.7 | Ticket reassignment rate | Track tickets bounced between groups indicating routing or skills gaps | Ticket audit trail |
| 16.1.8 | Aging ticket alerts | Alert on tickets open beyond expected timeframes per priority | Ticket open duration |
| 16.1.9 | Change-incident correlation | Correlate incidents with recent changes to identify change-related outages | Change + Incident records |
| 16.1.10 | Service request fulfillment time | Track fulfillment times for service catalog requests | Service request data |

### 16.2 Configuration Management (CMDB)

**Splunk Add-on:** ServiceNow CMDB integration, Device42 TA, custom API inputs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 16.2.1 | CMDB data quality score | Track CMDB completeness, accuracy, and freshness metrics | CMDB CI data |
| 16.2.2 | CI discovery reconciliation | Compare auto-discovered assets with CMDB records to find gaps | Discovery + CMDB data |
| 16.2.3 | Orphaned CI detection | Identify CIs with no owner, support group, or service mapping | CMDB CI attributes |
| 16.2.4 | Relationship integrity check | Validate CI relationships are complete and bidirectional | CMDB relationship data |
| 16.2.5 | CMDB change audit | Track all CI attribute changes for compliance and audit | CMDB audit trail |

---

## 17. Network Security & Zero Trust

### 17.1 Network Access Control (NAC)

**Splunk Add-on:** Cisco ISE TA, Aruba ClearPass TA, Forescout TA

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 17.1.1 | NAC authentication trending | Track 802.1X authentication success/failure rates by location | RADIUS/ISE logs |
| 17.1.2 | Endpoint posture failures | Monitor posture assessment failures and non-compliant endpoints | NAC posture logs |
| 17.1.3 | VLAN assignment audit | Track dynamic VLAN assignments and detect anomalous placements | NAC authorization logs |
| 17.1.4 | Guest network usage | Monitor guest access volume, duration, and sponsor activity | NAC guest portal logs |
| 17.1.5 | BYOD onboarding tracking | Track personal device enrollment and certificate provisioning | NAC BYOD logs |
| 17.1.6 | MAC Authentication Bypass (MAB) | Monitor MAB devices and detect unauthorized MAC addresses | NAC authentication logs |
| 17.1.7 | Profiling accuracy | Track device profiling accuracy and re-profiling events | ISE profiler logs |
| 17.1.8 | NAC policy change audit | Monitor changes to authentication and authorization policies | NAC admin audit logs |

### 17.2 VPN & Remote Access

**Splunk Add-on:** Cisco ASA/AnyConnect TA, Palo Alto GlobalProtect TA, vendor syslog

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 17.2.1 | VPN concurrent sessions | Track concurrent VPN user sessions for capacity planning | VPN concentrator logs |
| 17.2.2 | VPN authentication failures | Alert on repeated VPN login failures indicating credential attacks | VPN auth logs |
| 17.2.3 | Geo-location anomalies | Flag VPN connections from unexpected or sanctioned countries | VPN logs + GeoIP lookup |
| 17.2.4 | Split-tunnel compliance | Monitor split-tunnel vs. full-tunnel usage for security policy compliance | VPN session attributes |
| 17.2.5 | VPN tunnel stability | Detect users with frequent connect/disconnect cycles | VPN session logs |
| 17.2.6 | Off-hours VPN access | Alert on VPN connections during unusual hours by user role | VPN session logs + HR data |
| 17.2.7 | VPN bandwidth consumption | Monitor per-user and aggregate VPN bandwidth usage | VPN throughput metrics |
| 17.2.8 | Simultaneous session detection | Alert when a single user has VPN sessions from multiple locations | VPN session logs |

### 17.3 Zero Trust / SASE

**Splunk Add-on:** Zscaler TA, Netskope TA, Palo Alto Prisma TA

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 17.3.1 | Conditional access enforcement | Track policy enforcement decisions (allow, block, step-up auth) | SASE/ZT policy logs |
| 17.3.2 | Device trust scoring | Monitor device trust/compliance scores and access decisions | ZT platform logs |
| 17.3.3 | Micro-segmentation audit | Track micro-segmentation policy hits and violations | SDN/ZT policy logs |
| 17.3.4 | ZTNA application access | Monitor per-application access patterns through Zero Trust Network Access | ZTNA access logs |
| 17.3.5 | Posture assessment trending | Track endpoint posture compliance rates over time | ZT posture data |
| 17.3.6 | Policy drift detection | Detect deviations from baseline Zero Trust policies | ZT policy audit logs |

---

## 18. Data Center Fabric & SDN

### 18.1 Cisco ACI

**Splunk Add-on:** Cisco ACI TA, APIC syslog

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 18.1.1 | Fabric health score monitoring | Track ACI fabric-wide and node-level health scores | APIC API |
| 18.1.2 | Fault trending by severity | Monitor fault counts by severity (critical, major, minor, warning) | APIC faults |
| 18.1.3 | Endpoint mobility tracking | Track endpoint moves between leaves and detect anomalous mobility | APIC endpoint tracker |
| 18.1.4 | Contract/filter hit analysis | Monitor EPG-to-EPG traffic allowed/denied by contracts | APIC flow logs |
| 18.1.5 | Tenant configuration audit | Track tenant, BD, EPG, and contract configuration changes | APIC audit log |
| 18.1.6 | Leaf/spine interface utilization | Monitor fabric link utilization and detect hotspots | APIC interface metrics |
| 18.1.7 | APIC cluster health | Track APIC controller cluster convergence and leader election | APIC system logs |

### 18.2 VMware NSX

**Splunk Add-on:** VMware NSX TA, syslog

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 18.2.1 | Distributed firewall rule hits | Track DFW rule matches for security visibility | NSX DFW logs |
| 18.2.2 | Micro-segmentation enforcement | Monitor allowed vs. denied traffic between micro-segments | NSX DFW logs |
| 18.2.3 | Logical switch health | Track logical switch and router operational status | NSX manager events |
| 18.2.4 | NSX Edge performance | Monitor NSX Edge node CPU, memory, and datapath performance | NSX Edge metrics |
| 18.2.5 | Transport node connectivity | Track transport node tunnel status and alert on failures | NSX transport node logs |

### 18.3 Other SDN

**Splunk Add-on:** Custom inputs, Kubernetes CNI logs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 18.3.1 | Cilium/Calico network policy | Monitor CNI network policy enforcement in Kubernetes | CNI policy logs |
| 18.3.2 | OpenStack Neutron events | Track virtual network creation, modification, and deletion | Neutron API logs |
| 18.3.3 | SDN controller health | Monitor SDN controller availability and cluster consensus | Controller system logs |

---

## 19. Compute Infrastructure (HCI & Converged)

### 19.1 Cisco UCS

**Splunk Add-on:** Cisco UCS TA, UCS Manager syslog

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 19.1.1 | Blade/rack server health | Monitor server component health (CPU, memory, PSU, fans) | UCS Manager faults |
| 19.1.2 | Service profile compliance | Track service profile association and compliance state | UCS Manager events |
| 19.1.3 | Firmware compliance | Monitor firmware versions and flag servers behind on updates | UCS Manager inventory |
| 19.1.4 | Fault trending by severity | Track UCS fault counts by type and severity | UCS Manager faults |
| 19.1.5 | FI port channel health | Monitor fabric interconnect port-channel status and utilization | UCS Manager stats |
| 19.1.6 | Power and thermal monitoring | Track power consumption and temperature across chassis | UCS Manager environmental |

### 19.2 Hyper-Converged Infrastructure (HCI)

**Splunk Add-on:** Nutanix TA, VMware vSAN (via vCenter TA), vendor APIs

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 19.2.1 | Cluster health monitoring | Track overall cluster health status and node availability | HCI management API |
| 19.2.2 | Storage pool capacity | Monitor storage pool utilization and predict capacity needs | HCI storage metrics |
| 19.2.3 | Storage I/O latency | Track read/write latency at the cluster and VM level | HCI performance metrics |
| 19.2.4 | Node performance balance | Detect workload imbalance across cluster nodes | HCI node metrics |
| 19.2.5 | Disk failure tracking | Alert on disk failures and rebuild progress | HCI disk events |
| 19.2.6 | Replication factor compliance | Verify data replication meets configured RF targets | HCI replication status |
| 19.2.7 | CVM (Controller VM) health | Monitor Nutanix CVM resource usage and service status | Nutanix CVM logs |

---

## 20. Cost & Capacity Management

### 20.1 Cloud Cost Monitoring

**Splunk Add-on:** Cloud provider TAs, CUR/billing export ingestion

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 20.1.1 | Daily spend trending | Track cloud spending by service, account, and tag | CUR, Azure Cost, GCP Billing |
| 20.1.2 | Cost anomaly detection | Alert on daily spend deviations exceeding baseline by X% | Billing data with trending |
| 20.1.3 | Reserved Instance utilization | Track RI/Savings Plan utilization and coverage | Billing/CUR data |
| 20.1.4 | Idle resource identification | Identify running resources with near-zero utilization | CloudWatch/Monitor + billing |
| 20.1.5 | Budget threshold alerting | Alert when spending approaches defined budget limits | Billing data vs. budgets |
| 20.1.6 | Cost allocation by team | Break down costs by team/department via tagging | CUR with tag data |
| 20.1.7 | Spot/preemptible instance tracking | Monitor spot instance interruptions and savings | EC2 spot events, billing |
| 20.1.8 | Data transfer cost analysis | Identify and optimize inter-region and egress data transfer costs | CUR data transfer line items |

### 20.2 Capacity Planning

**Splunk Add-on:** Cross-referencing infrastructure metrics with trending/forecasting

| # | Use Case | Description | Key Data Sources |
|---|----------|-------------|-----------------|
| 20.2.1 | Compute capacity forecasting | Predict when CPU/memory capacity will be exhausted based on growth trends | Host performance metrics |
| 20.2.2 | Storage growth forecasting | Project storage consumption trends and predict procurement needs | Storage capacity metrics |
| 20.2.3 | Network bandwidth trending | Track WAN/LAN bandwidth utilization trends for upgrade planning | Interface utilization metrics |
| 20.2.4 | License utilization tracking | Monitor software license usage vs. entitlements | License server logs, vendor APIs |
| 20.2.5 | Right-sizing recommendations | Identify over-provisioned VMs/instances that can be downsized | Performance metrics vs. allocation |
| 20.2.6 | Database growth projection | Forecast database size growth for storage and performance planning | Database size metrics |
| 20.2.7 | Seasonal capacity modeling | Build seasonal models for capacity that varies by business cycle | Historical performance data |
| 20.2.8 | IP address space utilization | Track IP address pool usage across subnets and VLANs | DHCP/IPAM data |

---

## Summary Statistics

| Category | Subcategories | Use Cases |
|----------|:------------:|:---------:|
| 1. Server & Compute | 4 | 51 |
| 2. Virtualization | 3 | 23 |
| 3. Containers & Orchestration | 4 | 30 |
| 4. Cloud Infrastructure | 4 | 44 |
| 5. Network Infrastructure | 8 | 62 |
| 6. Storage & Backup | 4 | 28 |
| 7. Database & Data Platforms | 4 | 40 |
| 8. Application Infrastructure | 5 | 45 |
| 9. Identity & Access Management | 4 | 29 |
| 10. Security Infrastructure | 8 | 47 |
| 11. Email & Collaboration | 3 | 24 |
| 12. DevOps & CI/CD | 4 | 23 |
| 13. Observability & Monitoring | 3 | 28 |
| 14. IoT & OT | 4 | 24 |
| 15. DC Physical Infrastructure | 3 | 16 |
| 16. Service Management & ITSM | 2 | 15 |
| 17. Network Security & Zero Trust | 3 | 22 |
| 18. Data Center Fabric & SDN | 3 | 15 |
| 19. Compute Infrastructure (HCI) | 2 | 13 |
| 20. Cost & Capacity Management | 2 | 16 |
| **TOTAL** | **71** | **~595** |

---

*Generated: March 2026*
*Primary tools: Splunk Enterprise / Cloud with free Splunkbase add-ons. Premium exceptions noted (ITSI, ES).*
