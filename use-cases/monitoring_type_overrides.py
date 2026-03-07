# Explicit Monitoring type overrides (uc_id -> type string).
# Used when inference from title/value would be wrong. Add entries here and re-run build then apply.
# Format: "X.Y.Z": "Type" or "Type1, Type2"

# Per-UC correct type when rules would assign wrong (reviewed per use case)
EXPLICIT_CORRECT = {
    # Cat 1.1 - Linux (rule corrections)
    "1.1.25": "Performance",   # NUMA Imbalance - performance degradation
    "1.1.30": "Performance",  # Scheduler Latency - application performance
    "1.1.34": "Fault",        # RAID Array Degradation - data loss risk
    "1.1.36": "Availability", # Multipath I/O Failover
    "1.1.37": "Fault",        # NFS Mount Stale Handle
    "1.1.42": "Fault",        # SSD Wear - predictive failure
    "1.1.54": "Security",     # Network Namespace - container escape
    "1.1.57": "Security",     # ARP Table Overflow - spoofing
    "1.1.80": "Availability", # Systemd Unit Failures
    "1.1.82": "Fault",        # D-State Process - hang/deadlock
    "1.1.86": "Fault",        # Fork Bomb
    "1.1.89": "Anomaly",      # Syslog Flood
    "1.1.97": "Performance",  # CPU C-State Residency
    "1.1.112": "Fault",       # Unowned File - corruption
    "1.1.114": "Capacity",    # Open File Handle per process
    "1.1.119": "Fault",       # Defunct Zombie accumulation
    "1.1.43": "Performance",  # Fstrim/TRIM - SSD performance
    "1.1.44": "Fault",        # Memory Leak - OOM eventual
    "1.1.81": "Fault",        # Systemd Timer Missed - scheduling failure
    "1.1.90": "Capacity",     # Journal Disk Usage - storage growth
    "1.1.91": "Fault",        # Log Rotation Failures
    "1.1.93": "Performance", # Rsyslog Queue Backlog - forwarding load
    "1.1.95": "Security",     # TCP Connection Rate - DDoS indicator
    # Cat 1.2 - Windows
    "1.2.1": "Performance, Capacity",  # CPU Utilization Trending
    "1.2.3": "Capacity",      # Disk Space Monitoring
    "1.2.7": "Security",     # Account Lockout - attacks
    "1.2.10": "Fault",       # Scheduled Task Failures
    "1.2.17": "Availability", # Certificate Expiration - outages
    "1.2.19": "Configuration", # GPO Processing Failures
    "1.2.42": "Performance",  # .NET CLR Performance
    "1.2.46": "Fault",        # DFS-R Replication Backlog
    "1.2.47": "Fault",        # Application Crash (WER) Trending
    "1.2.64": "Compliance",   # Event Log Overflow - security events lost
    "1.2.69": "Capacity",    # Page File Exhaustion
    "1.2.80": "Compliance",   # Windows Backup - recovery point
    "1.2.120": "Compliance, Security",  # BitLocker Recovery & Compliance
    # Cat 1.3 - macOS
    "1.3.2": "Compliance",   # FileVault Encryption Status
    "1.3.3": "Security",     # Gatekeeper and SIP
    "1.3.4": "Compliance",   # Software Update Compliance
    "1.3.5": "Fault",        # Application Crash Monitoring
    # Cat 1.4 - Hardware
    "1.4.1": "Fault",        # Hardware Sensor - predictive failure
    "1.4.2": "Fault",        # RAID Degradation
    "1.4.3": "Availability", # Power Supply Failure
    "1.4.4": "Fault",        # Predictive Disk Failure
    "1.4.5": "Compliance",   # Firmware Version Compliance
    "1.4.6": "Fault",        # Memory ECC Error Trending
    # Cat 2 - Virtualization
    "2.1.6": "Configuration", # vMotion Tracking - change management
    "2.1.7": "Availability", # HA Failover Events
    "2.1.10": "Fault",       # vSAN Health - data loss risk
    "2.1.11": "Fault",       # ESXi Host Hardware Alerts
    "2.1.12": "Capacity",    # VM Resource Over-Allocation
    "2.1.14": "Compliance",  # ESXi Patch Compliance
    "2.1.15": "Compliance, Configuration",  # VM Creation/Deletion Audit
    "2.2.2": "Availability", # Hyper-V Replication Health
    "2.2.3": "Fault",        # Cluster Shared Volume Health
    "2.2.4": "Configuration", # Live Migration Tracking
    "2.3.2": "Capacity",     # Host Overcommit Detection
    "2.3.3": "Configuration", # VM Lifecycle Events
    # Cat 3 - Containers/K8s
    "3.1.1": "Fault",        # Container Crash Loops
    "3.1.2": "Fault",        # Container OOM Kills
    "3.1.5": "Security",     # Image Vulnerability Scanning
    "3.1.7": "Capacity",     # Container Sprawl
    "3.1.8": "Fault",        # Docker Daemon Errors
    "3.2.2": "Capacity",     # Pod Scheduling Failures
    "3.2.3": "Availability",  # Node NotReady
    "3.2.4": "Capacity",     # Resource Quota Exhaustion
    "3.2.5": "Capacity",     # Persistent Volume Claims
    "3.2.6": "Fault",        # Deployment Rollout Failures
    "3.2.7": "Availability", # Control Plane Health
    "3.2.8": "Availability", # etcd Cluster Health
    "3.2.11": "Capacity",    # HPA Scaling Events
    "3.2.12": "Security, Compliance",  # RBAC Audit
    "3.2.13": "Availability", # Certificate Expiration
    "3.2.14": "Fault",       # Container Image Pull Failures
    "3.2.15": "Availability", # DaemonSet Completeness
    "3.3.2": "Fault",        # Operator Degraded
    "3.3.3": "Fault",        # Build Failure Monitoring
    "3.3.4": "Security",     # SCC Violation Detection
    "3.4.2": "Security",     # Vulnerability Scan Results
    "3.4.3": "Capacity",     # Storage Quota (registry)
    # Cat 4 - Cloud
    "4.1.6": "Configuration", # EC2 Instance State - audit
    "4.1.14": "Anomaly",     # Cost Anomaly Detection
    "4.1.18": "Configuration", # CloudFormation Drift
    "4.2.11": "Availability", # Resource Health Events
    "4.4.1": "Configuration", # Terraform Drift
    "4.4.4": "Compliance",   # Tagging Compliance
    # Cat 5.9 - Meraki/Cisco (selected)
    "5.9.2": "Performance",   # RSSI/Signal Strength
    "5.9.9": "Capacity",     # Failed DHCP / IP Pool Exhaustion
    "5.9.19": "Availability", # AP Uptime
    "5.9.62": "Compliance",   # Firmware Update Compliance
    "5.9.72": "Compliance",   # Configuration Change Window
    "5.9.85": "Fault",       # Temperature Sensor Threshold
    "5.9.88": "Fault",       # Water Leak Detection
    "5.9.95": "Compliance",  # Device Compliance Status
    # Cat 6 - Storage
    "6.1.4": "Fault",        # Disk Failure Alerts
    "6.1.5": "Availability", # Replication Lag
    "6.1.6": "Availability", # Controller Failover
    "6.1.7": "Capacity",    # Thin Provisioning Overcommit
    "6.1.8": "Capacity",    # Snapshot Space Consumption
    "6.1.9": "Performance",  # Fibre Channel Port Errors
    "6.1.10": "Compliance",  # Storage Array Firmware
    "6.2.2": "Security",     # Access Pattern Anomalies
    "6.2.3": "Security",    # Public Bucket Detection
    "6.2.4": "Configuration", # Lifecycle Policy Compliance
    "6.3.5": "Compliance",   # Restore Test Tracking
    "6.3.6": "Compliance",   # Backup SLA Compliance
    "6.3.8": "Fault",        # Tape Library Health
    "6.4.2": "Security",     # Ransomware Indicator
    "6.4.3": "Fault",        # DFS Replication Health
    "6.4.4": "Security, Configuration",  # Share Permission Changes
    "6.4.5": "Security",     # Large File Transfer - exfiltration
    # Cat 7 - Database
    "7.1.2": "Fault",        # Deadlock Monitoring
    "7.1.3": "Capacity",    # Connection Pool Exhaustion
    "7.1.6": "Compliance",   # Backup Success Verification
    "7.1.7": "Security",     # Login Failure Monitoring
    "7.1.12": "Availability", # Database AG Health
    "7.1.13": "Configuration", # Schema Change Detection
    "7.1.15": "Security, Compliance",  # Privilege Escalation Audit
    "7.1.16": "Capacity",   # Open Cursor Leak
    "7.2.1": "Availability", # Cluster Membership Changes
    "7.2.6": "Fault",        # GC Pause Detection
    "7.2.7": "Capacity",     # Connection Count
    "7.2.10": "Availability", # Elasticsearch Cluster Health
    "7.3.2": "Availability", # Automated Failover Events
    "7.4.3": "Fault",        # Data Pipeline Health
    # Cat 8 - Application
    "8.1.5": "Availability",  # SSL Certificate Monitoring
    "8.1.6": "Availability", # Upstream Backend Health
    "8.1.10": "Configuration", # Configuration Reload Tracking
    "8.2.5": "Configuration", # Deployment Tracking
    "8.2.10": "Fault",       # Class Loading Issues
    "8.3.4": "Fault",        # Under-Replicated Partitions
    "8.3.5": "Fault",        # Dead Letter Queue
    "8.3.7": "Configuration", # Topic/Queue Creation Audit
    "8.3.9": "Availability", # Partition Leader Elections
    "8.4.4": "Security",     # Authentication Failures
    "8.4.6": "Fault",        # Circuit Breaker Activations
    "8.4.8": "Availability", # mTLS Certificate Expiration
    "8.6.1": "Availability", # SSH Service Availability
    "8.6.2": "Availability", # FTP/SFTP Availability
    "8.6.3": "Availability", # SMTP Service Availability
    "8.6.4": "Availability", # POP3/IMAP Availability
    # Cat 9 - Identity
    "9.1.2": "Security",     # Account Lockout - attacks/source
    "9.1.8": "Availability", # AD Replication Monitoring
    "9.1.9": "Performance",  # LDAP Query Performance
    "9.2.3": "Configuration", # Schema Modification Audit
    "9.3.5": "Availability", # IdP Availability
    "9.4.6": "Availability", # Vault Health Monitoring
    # Cat 10 - Security (already in OVERRIDES; ensure correct)
    "10.3.3": "Availability", # Agent Health - coverage gaps
    "10.3.6": "Security",     # Threat Hunting Indicators
    "10.4.4": "Compliance",  # DLP Policy Violations
    "10.4.7": "Performance", # Quarantine Management
    "10.5.4": "Compliance",   # DLP over Web
    "10.5.6": "Performance",  # Bandwidth Abuse
    "10.5.7": "Compliance",  # Unencrypted Traffic
    "10.6.3": "Compliance",  # Scan Coverage
    "10.6.4": "Compliance",  # Patch Compliance by Team
    "10.6.6": "Compliance",  # Vulnerability SLA
    "10.7.2": "Performance", # Analyst Workload
    "10.7.4": "Fault",       # Playbook Execution
    "10.7.5": "Performance", # Correlation Search Performance
    "10.8.1": "Availability", # Certificate Expiry
    # Cat 11 - M365/Workspace
    "11.1.2": "Compliance",   # Mailbox Audit
    "11.1.6": "Compliance",   # DLP Policy Events
    "11.1.7": "Compliance",   # Admin Activity Audit
    "11.1.8": "Security",     # Inbox Rule - exfiltration
    "11.1.9": "Availability", # Service Health
    "11.1.10": "Capacity",   # License Utilization
    "11.2.2": "Availability", # Gmail Message Flow
    "11.2.6": "Security",     # Third-Party App Access
    "11.3.6": "Security",    # Toll Fraud Detection
    "11.3.7": "Availability", # Phone Registration Status
    # Cat 12 - DevOps
    "12.1.2": "Security, Compliance",  # Branch Protection Bypasses
    "12.1.4": "Security",    # Secret Exposure
    "12.1.5": "Compliance",  # Repository Access Audit
    "12.1.6": "Compliance",  # Force Push Detection
    "12.2.5": "Fault",       # Failed Deployment
    "12.2.8": "Security",   # Security Scan in Pipeline
    "12.3.2": "Security",   # Dependency Vulnerability
    "12.3.3": "Security",   # Package Download Anomalies
    "12.3.4": "Compliance",  # License Compliance
    "12.4.1": "Configuration", # Terraform Plan/Apply
    "12.4.2": "Configuration", # Configuration Drift
    "12.4.3": "Fault",       # Ansible Playbook Outcomes
    "12.4.4": "Compliance",  # Puppet/Chef Compliance
    "12.4.5": "Compliance",  # IaC Policy Violations
    # Cat 13 - Splunk
    "13.1.1": "Capacity",    # Indexer Queue Fill
    "13.1.3": "Availability", # Forwarder Connectivity
    "13.1.5": "Availability", # Skipped Search Detection
    "13.1.7": "Fault",       # KV Store Health
    "13.1.8": "Configuration", # Deployment Server
    "13.1.10": "Availability", # Search Head Cluster
    "13.1.11": "Fault",      # Bucket Replication
    "13.1.12": "Availability", # HEC Endpoint Health
    "13.1.15": "Availability", # Splunk Certificate Expiration
    "13.2.6": "Fault",       # Rules Engine Health
    "13.3.4": "Compliance",  # Monitoring Coverage Gap
    "13.3.5": "Anomaly",    # Alert Storm Detection
    # Cat 14 - Facilities/IoT
    "14.1.2": "Fault",       # UPS Battery
    "14.1.4": "Compliance",  # Access Control Audit
    "14.1.6": "Compliance",  # Environmental Compliance
    "14.2.3": "Fault",       # Safety System Activation
    "14.2.4": "Security",    # Network Segmentation
    "14.2.5": "Compliance",  # Firmware Version (OT)
    "14.2.6": "Security",    # Unauthorized Access (ICS)
    "14.4.1": "Availability", # Smart Sensor Fleet Health
    "14.4.5": "Security",    # IoT Firmware Compliance
    # Cat 15 - Data Center
    "15.1.1": "Fault",       # UPS Battery Health
    "15.1.4": "Fault",       # Generator Test Results
    "15.1.6": "Fault",       # Circuit Breaker Trips
    "15.2.3": "Availability", # CRAC/CRAH Health
    "15.2.5": "Fault",       # Water Leak Detection
    "15.3.1": "Compliance",  # Badge Access Audit
    "15.3.4": "Availability", # Camera System Health
}

OVERRIDES = {
    # Cat 1 - Server & Compute
    "1.1.1": "Performance, Capacity",  # CPU Utilization Trending
    "1.1.2": "Performance",  # Memory Pressure Detection
    "1.1.13": "Fault",  # Zombie Process - application bugs, exhaust PID
    "1.1.18": "Configuration, Compliance",  # User Account Changes - security auditing and compliance
    "1.1.19": "Fault",  # Filesystem Read-Only - disk failure, corruption
    "1.1.20": "Availability, Fault",  # Reboot Detection - unexpected reboots
    "1.1.21": "Security",  # Kernel Module Loading - rootkits, unauthorized
    "1.1.22": "Configuration",  # Sysctl Parameter Changes
    "1.1.23": "Fault",  # Kernel Core Dump - process crashes
    "1.1.24": "Fault",  # Kernel Ring Buffer Error Rate
    "1.1.12": "Configuration",  # NTP Time Sync Drift - config/correlation
    # Cat 2 - Virtualization
    "2.1.5": "Capacity",  # VM Snapshot Sprawl - consumes space
    "2.1.9": "Capacity",  # VM Sprawl Detection - waste resources
    "2.1.13": "Anomaly",  # vCenter Alarm Correlation - correlation/trending
    "2.2.5": "Compliance",  # Integration Services Version - version/compliance
    # Cat 10 - Security Infrastructure
    "10.1.2": "Security",  # Wildfire / Sandbox Verdicts - malware detection
    "10.1.4": "Security",  # DNS Sinkhole Hits - compromise indicator
    "10.1.5": "Security",  # SSL Decryption Coverage - security visibility
    "10.2.1": "Performance",  # Alert Severity Trending - SOC workload
    "10.2.2": "Security",  # Top Targeted Hosts - attack prioritization
    "10.2.3": "Security",  # Signature Coverage Gaps - threat detection
    "10.2.4": "Performance",  # False Positive Tracking - tuning
    "10.2.5": "Security",  # Lateral Movement Detection
    "10.3.2": "Security",  # Quarantine Action Monitoring
    "10.3.4": "Security",  # Behavioral Detection Alerts
    "10.3.5": "Security",  # Endpoint Isolation Events
    "10.3.7": "Availability",  # EDR Coverage Gaps - blind spots
    "10.3.8": "Security",  # Ransomware Canary Detection
    "10.4.5": "Security",  # Spoofed Email Detection
    "10.4.6": "Security",  # Email Volume Anomalies - exfiltration
    "10.5.1": "Security",  # Blocked Category Trending - security policy
    "10.5.2": "Security",  # Shadow IT Detection
}

# Network (cat 5) explicit mapping 5.1.1–5.8.8 (same as add_monitoring_type.py). 5.9.x uses inference.
NETWORK_TYPE_BY_UC = {
    "5.1.1": "Availability", "5.1.2": "Performance", "5.1.3": "Performance, Capacity",
    "5.1.4": "Availability", "5.1.5": "Availability", "5.1.6": "Availability, Anomaly",
    "5.1.7": "Configuration, Compliance", "5.1.8": "Performance, Capacity",
    "5.1.9": "Availability, Fault", "5.1.10": "Configuration, Compliance",
    "5.1.11": "Fault", "5.1.12": "Anomaly, Security", "5.1.13": "Security",
    "5.1.14": "Security", "5.1.15": "Fault", "5.1.16": "Anomaly",
    "5.1.17": "Performance, Fault", "5.1.18": "Availability, Configuration",
    "5.1.19": "Capacity, Fault", "5.1.20": "Anomaly, Availability",
    "5.1.21": "Performance", "5.1.22": "Availability", "5.1.23": "Availability",
    "5.2.1": "Security", "5.2.2": "Configuration, Compliance", "5.2.3": "Security",
    "5.2.4": "Availability", "5.2.5": "Security", "5.2.6": "Security, Anomaly",
    "5.2.7": "Anomaly, Performance", "5.2.8": "Security", "5.2.9": "Security",
    "5.2.10": "Compliance", "5.2.11": "Performance, Capacity", "5.2.12": "Capacity",
    "5.2.13": "Capacity", "5.2.14": "Availability", "5.2.15": "Security",
    "5.2.16": "Security", "5.2.17": "Performance", "5.2.18": "Security",
    "5.3.1": "Availability", "5.3.2": "Availability", "5.3.3": "Performance, Capacity",
    "5.3.4": "Fault", "5.3.5": "Performance", "5.3.6": "Performance",
    "5.3.7": "Performance, Anomaly", "5.3.8": "Security", "5.3.9": "Capacity, Performance",
    "5.3.10": "Performance", "5.3.11": "Security, Anomaly", "5.3.12": "Fault",
    "5.4.1": "Availability", "5.4.2": "Availability", "5.4.3": "Performance, Capacity",
    "5.4.4": "Security", "5.4.5": "Capacity", "5.4.6": "Fault, Performance",
    "5.4.7": "Security", "5.4.8": "Security", "5.4.9": "Performance, Anomaly",
    "5.4.10": "Security", "5.4.11": "Performance",
    "5.5.1": "Availability", "5.5.2": "Availability", "5.5.3": "Performance",
    "5.5.4": "Availability", "5.5.5": "Availability", "5.5.6": "Fault",
    "5.5.7": "Performance, Capacity", "5.5.8": "Performance", "5.5.9": "Performance",
    "5.5.10": "Performance, Capacity",
    "5.6.1": "Capacity", "5.6.2": "Security, Anomaly", "5.6.3": "Availability",
    "5.6.4": "Security", "5.6.5": "Capacity", "5.6.6": "Security",
    "5.6.7": "Configuration, Compliance", "5.6.8": "Performance",
    "5.6.9": "Performance", "5.6.10": "Security", "5.6.11": "Capacity",
    "5.6.12": "Performance, Capacity",
    "5.7.1": "Performance, Capacity", "5.7.2": "Anomaly", "5.7.3": "Performance, Capacity",
    "5.7.4": "Performance, Security", "5.7.5": "Security", "5.7.6": "Security",
    "5.7.7": "Performance", "5.7.8": "Performance", "5.7.9": "Security",
    "5.7.10": "Anomaly, Security",
    "5.8.1": "Availability", "5.8.2": "Availability", "5.8.3": "Fault",
    "5.8.4": "Configuration", "5.8.5": "Compliance", "5.8.6": "Compliance",
    "5.8.7": "Configuration", "5.8.8": "Availability",
}
