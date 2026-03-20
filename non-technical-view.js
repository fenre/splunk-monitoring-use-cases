/**
 * Non-technical view: plain-language outcomes and "areas of monitoring" per category.
 * Used when the user selects "Non-technical" in the header.
 */
window.NON_TECHNICAL = {
  "1": {
    outcomes: [
      "See when computers or servers are overloaded, running out of space, or acting strangely.",
      "Get early warning before something breaks so you can fix it.",
      "Know when someone changes important system settings or files."
    ],
    areas: [
      { name: "Hardware & health", description: "Is the machine running properly? We watch things like temperature, disk space, and whether the computer is struggling.", ucs: [
        { id: "1.1.1", why: "Spot when a server's processor is maxing out before users notice slowdowns." },
        { id: "1.1.3", why: "See when a disk is filling up so you can add space before it runs out." },
        { id: "1.4.2", why: "Get an alert when a disk array loses a drive, so you can replace it in time." }
      ]},
      { name: "When things go wrong", description: "Crashes, errors, and failures. We spot them so your team can fix problems quickly.", ucs: [
        { id: "1.1.6", why: "Know immediately when an important program crashes on a server." },
        { id: "1.1.11", why: "Detect when a Linux server has a critical kernel panic (the equivalent of a blue screen)." },
        { id: "1.2.11", why: "Catch Windows Blue Screen of Death events across your fleet." }
      ]},
      { name: "Who did what", description: "Changes to important files or settings. We keep an eye so nothing is tampered with without you knowing.", ucs: [
        { id: "1.1.18", why: "Track when user accounts are created, changed, or deleted on servers." },
        { id: "1.1.70", why: "Alert when someone modifies the system's user database — a key security signal." },
        { id: "1.2.8", why: "See when someone is added to a powerful admin group on Windows." }
      ]},
      { name: "Network on the server", description: "How the server talks to the rest of the network. We notice when connections fail or behave oddly.", ucs: [
        { id: "1.1.15", why: "Spot network card errors that can cause slow or dropped connections." },
        { id: "1.1.55", why: "Detect when servers can't look up website or service addresses (DNS failures)." },
        { id: "1.1.58", why: "Know when a redundant network link fails over, which could signal a problem." }
      ]},
      { name: "Mac endpoints", description: "macOS laptops and desktops — encryption status, security settings, and resource usage.", ucs: [
        { id: "1.3.2", why: "Check that disk encryption (FileVault) is turned on — unencrypted laptops are a data breach risk." },
        { id: "1.3.1", why: "Watch CPU, memory, and disk on Mac endpoints to help IT triage user complaints." },
        { id: "1.3.3", why: "Make sure Gatekeeper and System Integrity Protection haven't been disabled." }
      ]}
    ]
  },
  "2": {
    outcomes: [
      "Know if your virtual machines have enough room to run smoothly.",
      "See when a host is overloaded or when something fails over.",
      "Plan ahead so you don't run out of capacity."
    ],
    areas: [
      { name: "Capacity & space", description: "Do your virtual machines have enough storage and resources? We track usage and trends.", ucs: [
        { id: "2.1.3", why: "Track storage usage trends so you can add space before VMs run out." },
        { id: "2.1.5", why: "Find forgotten snapshots that quietly eat up storage space." },
        { id: "2.1.9", why: "Spot when too many VMs are created and resources start to spread thin." }
      ]},
      { name: "Health & failures", description: "When something goes wrong in the virtual world — failovers, hardware alerts, cluster issues — we surface it.", ucs: [
        { id: "2.1.7", why: "Know when a host fails and VMs automatically move to another — a sign something broke." },
        { id: "2.1.11", why: "Get hardware alerts from the physical servers running your VMs." },
        { id: "2.2.3", why: "Monitor the shared storage that Hyper-V clusters depend on." }
      ]},
      { name: "Performance", description: "Are VMs getting the CPU and memory they need? We help you see when they're being squeezed.", ucs: [
        { id: "2.1.1", why: "See when a physical host is running out of processing power for its VMs." },
        { id: "2.1.2", why: "Detect when memory pressure forces the host to reclaim memory from VMs." },
        { id: "2.1.12", why: "Find VMs that have been given more resources than the host can actually deliver." }
      ]},
      { name: "KVM, Proxmox & oVirt", description: "Open-source virtualisation — Proxmox clusters, ZFS storage, backups, and KVM daemon health.", ucs: [
        { id: "2.3.11", why: "Check whether Proxmox backup jobs succeeded — failed backups mean no recovery point." },
        { id: "2.3.14", why: "Watch ZFS pool health — a degraded pool means a disk failed and data is at risk." },
        { id: "2.3.16", why: "Monitor the libvirt daemon that manages all KVM VMs — if it hangs, VMs become unmanageable." }
      ]},
      { name: "Across all platforms", description: "Cross-platform checks — VM density, backup coverage, and end-of-life operating systems.", ucs: [
        { id: "2.4.3", why: "Track how many VMs run on each host — too many means you're at risk if a host fails." },
        { id: "2.4.2", why: "Find VMs with no recent backup — a single failure could mean permanent data loss." },
        { id: "2.4.1", why: "Spot VMs running end-of-life operating systems that no longer get security patches." }
      ]}
    ]
  },
  "3": {
    outcomes: [
      "See when containers or pods keep crashing or restarting.",
      "Know if your clusters are healthy and who's in charge.",
      "Spot when things run out of memory or hit limits."
    ],
    areas: [
      { name: "Crashes & restarts", description: "Containers or pods that keep failing or restarting. We help you find and fix them.", ucs: [
        { id: "3.1.1", why: "Find containers that keep crashing and restarting in a loop." },
        { id: "3.2.1", why: "Track how often pods restart — a key sign of application trouble." },
        { id: "3.2.10", why: "Spot the classic CrashLoopBackOff state where a pod can't start successfully." }
      ]},
      { name: "Cluster health", description: "Is the control plane and orchestration layer working? We monitor the brain of your container system.", ucs: [
        { id: "3.2.7", why: "Watch the Kubernetes control plane — if this goes down, nothing gets scheduled." },
        { id: "3.2.8", why: "Monitor the etcd database that stores all cluster state and configuration." },
        { id: "3.2.3", why: "Know when a worker node becomes unavailable and can no longer run workloads." }
      ]},
      { name: "Resources & limits", description: "When containers run out of memory or hit their limits. We show you where the pinch is.", ucs: [
        { id: "3.1.2", why: "Catch when containers are killed because they ran out of memory." },
        { id: "3.2.4", why: "See when a team has used up their allocated share of cluster resources." },
        { id: "3.1.3", why: "Detect when containers are being throttled because they hit CPU limits." }
      ]},
      { name: "OpenShift", description: "Red Hat OpenShift-specific monitoring — security constraints, builds, and cluster upgrades.", ucs: [
        { id: "3.3.4", why: "Catch pods that try to run with more permissions than allowed — could be an attack." },
        { id: "3.3.3", why: "Track build failures that block application deployments." },
        { id: "3.3.1", why: "Make sure OpenShift cluster upgrades don't stall mid-way." }
      ]},
      { name: "Container registries", description: "Where container images are stored. We monitor pushes, pulls, and security.", ucs: [
        { id: "3.4.8", why: "Warn before a registry certificate expires — expired certs stop all image pulls." },
        { id: "3.4.5", why: "Spot failed logins and denied pulls that may indicate credential misuse." },
        { id: "3.4.1", why: "Audit who pushed or pulled what images — supply chain visibility." }
      ]}
    ]
  },
  "4": {
    outcomes: [
      "See how your cloud is being used and who did what.",
      "Catch risky or unusual activity in your cloud accounts.",
      "Keep an eye on cost and changes to important settings."
    ],
    areas: [
      { name: "Who did what in the cloud", description: "Logins, API calls, and changes in AWS, Azure, or Google Cloud. We give you a clear picture.", ucs: [
        { id: "4.1.1", why: "Spot API calls that were denied — often the first sign of misconfiguration or misuse." },
        { id: "4.1.2", why: "Alert whenever the all-powerful root account is used — this should be rare." },
        { id: "4.2.1", why: "Track every change and action in your Azure environment through activity logs." }
      ]},
      { name: "Security & threats", description: "Suspicious activity, open buckets, or security findings. We help you stay safe.", ucs: [
        { id: "4.1.8", why: "Get threat alerts from AWS GuardDuty — it watches for malicious activity in your account." },
        { id: "4.2.9", why: "Surface security alerts from Microsoft Defender for Cloud across your Azure resources." },
        { id: "4.3.5", why: "Pull in security findings from Google Cloud's Security Command Center." }
      ]},
      { name: "Cost & changes", description: "Spend trends and important configuration changes so you stay in control.", ucs: [
        { id: "4.1.14", why: "Detect unexpected spikes in cloud spending before the bill arrives." },
        { id: "4.1.7", why: "Know when someone changes who can access your cloud storage buckets." },
        { id: "4.2.12", why: "Get alerts when Azure spending approaches or exceeds your budget." }
      ]},
      { name: "Multi-cloud overview", description: "When you use more than one cloud provider. We bring everything together in one view.", ucs: [
        { id: "4.4.3", why: "See spending across AWS, Azure, and GCP in a single cost dashboard." },
        { id: "4.4.14", why: "Detect when audit logging is disabled in any cloud — that's a dangerous blind spot." },
        { id: "4.4.6", why: "Pull security findings from all clouds into one place for unified prioritization." }
      ]}
    ]
  },
  "5": {
    outcomes: [
      "Know when routers, switches, firewalls, or wireless access points have problems.",
      "See when links go down, SD-WAN tunnels degrade, or routing gets confused.",
      "Spot hardware issues like bad power supplies or fans.",
      "Track who's using bandwidth and detect suspicious traffic patterns.",
      "Monitor Meraki cloud-managed networks from a single pane of glass.",
      "Measure how your network performs from your users' perspective — across the internet, cloud, and SD-WAN.",
      "Monitor carrier signaling protocols (SIP, Diameter, RADIUS) that underpin voice and mobile services."
    ],
    areas: [
      { name: "Hardware status", description: "Are your routers, switches, and firewalls healthy? We watch for failures and warnings.", ucs: [
        { id: "5.1.11", why: "Get an alert when a power supply or cooling fan fails in a network device." },
        { id: "5.1.8", why: "Watch CPU and memory on network devices — overloaded devices drop traffic." },
        { id: "5.1.9", why: "Know when a device reboots or reloads unexpectedly." }
      ]},
      { name: "Connections & routing", description: "When links go up or down, or when routing protocols like BGP or OSPF have issues. We keep you informed.", ucs: [
        { id: "5.1.1", why: "See when network links go up or down — the most fundamental network alert." },
        { id: "5.1.4", why: "Track BGP peer state changes — this affects how traffic reaches the internet." },
        { id: "5.1.5", why: "Monitor OSPF neighbor relationships — internal routing breaks when these drop." }
      ]},
      { name: "Who gets in", description: "Authentication and access to network devices. We track logins and policy changes.", ucs: [
        { id: "5.2.2", why: "Audit every firewall policy change so you know what was modified and by whom." },
        { id: "5.2.10", why: "Track admin logins to firewalls — who logged in, from where, and when." },
        { id: "5.1.14", why: "Catch failed SNMP authentication — could mean someone is probing your network." }
      ]},
      { name: "Addresses & names", description: "DHCP and DNS: who got which IP, and whether name resolution is working. We monitor both.", ucs: [
        { id: "5.6.5", why: "Alert when a DHCP pool is running out of IP addresses to hand out." },
        { id: "5.6.1", why: "Track DNS query volume — sudden changes can indicate problems or attacks." },
        { id: "5.6.2", why: "Spot spikes in 'name not found' DNS errors that could mean a misconfiguration." }
      ]},
      { name: "Load balancers", description: "The devices that spread traffic across your servers. We watch pool health and virtual server availability.", ucs: [
        { id: "5.3.1", why: "Alert when a server drops out of the load balancer pool — less capacity for users." },
        { id: "5.3.2", why: "Know when a virtual IP goes down — the application is completely unreachable." },
        { id: "5.3.11", why: "See when rate limiting kicks in — reveals ongoing attacks or traffic spikes." }
      ]},
      { name: "Wireless", description: "WiFi access points, rogue AP detection, and RF quality. We help you keep wireless reliable and secure.", ucs: [
        { id: "5.4.4", why: "Detect unauthorised rogue access points that could be used for eavesdropping." },
        { id: "5.4.2", why: "Track client connection failures — frustrated users and potential auth or RF issues." },
        { id: "5.4.6", why: "Spot radio interference events that degrade WiFi quality." }
      ]},
      { name: "SD-WAN", description: "Software-defined WAN links connecting your sites. We watch tunnel health and application performance.", ucs: [
        { id: "5.5.1", why: "Monitor tunnel health — loss, latency, and jitter directly affect application experience." },
        { id: "5.5.2", why: "Know when a remote site goes offline — the edge device has stopped responding." },
        { id: "5.5.3", why: "Detect when business-critical apps violate their SLA over the WAN." }
      ]},
      { name: "Network flow & traffic", description: "NetFlow, sFlow, and IPFIX data showing who is talking to whom and how much bandwidth is used.", ucs: [
        { id: "5.7.1", why: "Find the top bandwidth consumers on your network — essential for congestion troubleshooting." },
        { id: "5.7.3", why: "Break down bandwidth by application so you can prioritise with QoS." },
        { id: "5.7.5", why: "Detect unusually large outbound transfers — possible data exfiltration." }
      ]},
      { name: "Network management platforms", description: "DNA Center, SNMP traps, and device backups. We centralize alerts from your management tools.", ucs: [
        { id: "5.8.1", why: "Get AI/ML-driven network alerts from DNA Center alongside everything else in Splunk." },
        { id: "5.8.3", why: "Consolidate SNMP traps from all devices to reduce tool sprawl." },
        { id: "5.8.5", why: "Track whether network device configs are being backed up — missing backups mean manual rebuilds." }
      ]},
      { name: "Cisco Meraki", description: "Cloud-managed networking — APs, switches, security appliances, and cameras. We monitor the full Meraki stack.", ucs: [
        { id: "5.9.19", why: "Make sure all Meraki access points are online and catch unexpected outages." },
        { id: "5.9.38", why: "Watch uplink health and failover events on your Meraki appliances." },
        { id: "5.9.55", why: "Track internet failover events and how long it takes to recover." }
      ]},
      { name: "Internet & digital experience", description: "How does the network look from outside your walls? ThousandEyes tests the path from users to apps — across ISPs, cloud providers, and SD-WAN.", ucs: [
        { id: "5.10.1", why: "Track network latency from agents to servers — slow paths mean slow apps." },
        { id: "5.10.18", why: "Get alerted when ThousandEyes detects an internet outage affecting your services." },
        { id: "5.10.8", why: "See BGP reachability on a map — know if your routes are being seen by the world." }
      ]},
      { name: "Carrier signaling (Telco)", description: "SIP, Diameter, and RADIUS signaling that powers voice calls and mobile data sessions. We watch the protocols that carriers depend on.", ucs: [
        { id: "5.11.1", why: "Track Diameter signaling health — failures here mean subscribers can't authenticate or use data." },
        { id: "5.11.4", why: "Monitor SIP trunk success rates — failed calls mean lost revenue and unhappy customers." },
        { id: "5.11.5", why: "Detect registration storms that can overwhelm voice infrastructure within minutes." }
      ]}
    ]
  },
  "6": {
    outcomes: [
      "See when storage is filling up or getting slow.",
      "Know when disks or controllers fail.",
      "Make sure backups actually ran and succeeded."
    ],
    areas: [
      { name: "Capacity & speed", description: "How full are your volumes, and how fast is data moving? We track both.", ucs: [
        { id: "6.1.1", why: "Watch storage volumes filling up so you can act before they're full." },
        { id: "6.1.2", why: "Detect when storage is getting slow — this directly affects application performance." },
        { id: "6.1.3", why: "Track read/write operations to spot when storage is being pushed too hard." }
      ]},
      { name: "Hardware failures", description: "Disk failures, controller problems, and failovers. We alert you so you can act.", ucs: [
        { id: "6.1.4", why: "Get an immediate alert when a disk fails so it can be replaced." },
        { id: "6.1.6", why: "Know when a storage controller fails over — the backup kicked in, but something broke." },
        { id: "6.1.9", why: "Catch connection errors between servers and storage that can cause data issues." }
      ]},
      { name: "Backups", description: "Did the backup run? Did it succeed? We help you avoid nasty surprises.", ucs: [
        { id: "6.3.1", why: "See at a glance what percentage of backup jobs succeeded." },
        { id: "6.3.3", why: "Catch when a scheduled backup didn't run at all — before you need it." },
        { id: "6.3.6", why: "Track whether backups meet your agreed recovery time targets." }
      ]},
      { name: "Object storage", description: "Cloud buckets and object storage — including when something is accidentally left open to the world.", ucs: [
        { id: "6.2.3", why: "Alert when a cloud storage bucket is publicly accessible — a common data leak risk." },
        { id: "6.2.1", why: "Track how much data is stored in cloud buckets and how fast it's growing." },
        { id: "6.2.2", why: "Spot unusual access patterns that could indicate unauthorized use." }
      ]},
      { name: "File shares & services", description: "File access auditing, permission changes, and backup target capacity. We help you protect shared data.", ucs: [
        { id: "6.4.1", why: "Full audit trail of who accessed which files — required for SOX, HIPAA, and PCI." },
        { id: "6.4.4", why: "Detect when share permissions are changed — accidental changes can expose sensitive data." },
        { id: "6.4.7", why: "Watch backup storage filling up — full targets mean failed backups." }
      ]}
    ]
  },
  "7": {
    outcomes: [
      "See when databases are slow, stuck, or unavailable.",
      "Know when too many connections are used or something is deadlocked.",
      "Track who changed what in your data systems."
    ],
    areas: [
      { name: "Availability & performance", description: "Is the database up and responding? Are queries slow or timing out? We monitor both.", ucs: [
        { id: "7.1.1", why: "Find slow-running queries that are making your applications feel sluggish." },
        { id: "7.1.12", why: "Monitor database availability groups — if these break, the database goes down." },
        { id: "7.1.11", why: "Track how well the database uses its memory cache — low hit ratios mean slow queries." }
      ]},
      { name: "Locks & connections", description: "Deadlocks, connection pool exhaustion, and replication issues. We help you avoid outages.", ucs: [
        { id: "7.1.2", why: "Detect deadlocks where two queries block each other and nothing moves." },
        { id: "7.1.3", why: "Alert when all database connections are used up — new requests will fail." },
        { id: "7.1.4", why: "Watch replication lag — if the backup database falls behind, disaster recovery is at risk." }
      ]},
      { name: "Who changed what", description: "Privilege changes and important schema or data changes. We keep an audit trail.", ucs: [
        { id: "7.1.15", why: "Catch when someone gains elevated privileges in the database." },
        { id: "7.1.13", why: "Track changes to database structure — tables, columns, and indexes." },
        { id: "7.1.7", why: "Monitor failed login attempts to databases — potential breach attempts." }
      ]},
      { name: "NoSQL databases", description: "MongoDB, Elasticsearch, Cassandra, and similar. We watch cluster health, connections, and memory.", ucs: [
        { id: "7.2.1", why: "Know when a node joins or leaves the cluster — unexpected changes may mean a failure." },
        { id: "7.2.7", why: "Watch connection counts — approaching limits means new requests will be rejected." },
        { id: "7.2.9", why: "Track memory usage — high evictions mean the cache is too small and queries slow down." }
      ]},
      { name: "Cloud-managed databases", description: "RDS, Aurora, Cloud SQL — managed databases where the cloud provider handles infrastructure but you still need visibility.", ucs: [
        { id: "7.3.2", why: "Know when a managed database fails over — brief outage, but you need to check the impact." },
        { id: "7.3.1", why: "Use cloud-native Performance Insights to find the slowest queries without installing agents." },
        { id: "7.3.3", why: "Watch read replica lag — stale replicas mean apps could serve outdated data." }
      ]},
      { name: "Data warehouses", description: "Snowflake, Redshift, BigQuery, and similar analytics platforms. We track cost, performance, and scaling.", ucs: [
        { id: "7.4.4", why: "See how much each query costs — find runaway queries burning through credits." },
        { id: "7.4.2", why: "Track auto-scaling events to check whether scaling policies match real workload." }
      ]}
    ]
  },
  "8": {
    outcomes: [
      "Know when your websites or apps are slow or throwing errors.",
      "See when certificates are about to expire.",
      "Spot when message queues or app servers are backing up.",
      "Test your web apps and APIs from outside to see what users really experience."
    ],
    areas: [
      { name: "Web & errors", description: "HTTP errors, response times, and uptime. We help you keep sites and APIs healthy.", ucs: [
        { id: "8.1.1", why: "Track error rates on your web servers — rising errors mean users are having trouble." },
        { id: "8.1.2", why: "Monitor response times so you know when your site is getting slow." },
        { id: "8.1.4", why: "Find the specific pages or endpoints that are causing the most errors." }
      ]},
      { name: "Certificates", description: "SSL/TLS certificates expiring or misconfigured. We remind you before they break.", ucs: [
        { id: "8.1.5", why: "Get advance warning before an SSL certificate expires and your site shows security errors." },
        { id: "8.4.8", why: "Track service-to-service certificates that protect internal communication." },
        { id: "8.6.9", why: "Monitor mail server certificates so email delivery doesn't break." }
      ]},
      { name: "Queues & backlogs", description: "Message queues and event streams. We show when things are piling up or falling behind.", ucs: [
        { id: "8.3.1", why: "See when message consumers fall behind — data is piling up waiting to be processed." },
        { id: "8.3.2", why: "Track queue depth to know when messages are building up faster than they're handled." },
        { id: "8.3.5", why: "Monitor dead letter queues — messages that failed to process and need attention." }
      ]},
      { name: "App server health", description: "Java, runtimes, and application servers. We watch memory and responsiveness.", ucs: [
        { id: "8.2.1", why: "Watch Java memory usage — when it fills up, the application slows or crashes." },
        { id: "8.2.3", why: "Detect when all worker threads are busy — new requests will be queued or dropped." },
        { id: "8.2.4", why: "Track application error rates to spot problems before they escalate." }
      ]},
      { name: "Caching layers", description: "Redis, Memcached, and other caches that speed up your applications. We watch memory, evictions, and replication.", ucs: [
        { id: "8.5.2", why: "Track cache memory usage — when it runs out, data gets evicted and apps slow down." },
        { id: "8.5.3", why: "Watch eviction rates — high evictions mean the cache is too small for your workload." },
        { id: "8.5.5", why: "Monitor Redis replication lag — stale replicas can serve outdated data." }
      ]},
      { name: "Synthetic testing", description: "ThousandEyes probes your websites and APIs from around the world. We show when things slow down or break.", ucs: [
        { id: "8.7.1", why: "Track HTTP server availability and response time from multiple global vantage points." },
        { id: "8.7.4", why: "Monitor page load completion — know when users can't fully load your site." },
        { id: "8.7.8", why: "Run scripted transaction tests that simulate real user workflows end-to-end." }
      ]}
    ]
  },
  "9": {
    outcomes: [
      "See when logins fail or someone tries to get in who shouldn't.",
      "Know when privileged groups or permissions change.",
      "Keep an eye on single sign-on and identity providers."
    ],
    areas: [
      { name: "Logins & authentication", description: "Failed logins, lockouts, and suspicious sign-in patterns. We help you spot trouble.", ucs: [
        { id: "9.1.1", why: "Detect brute-force login attempts — someone is trying many passwords." },
        { id: "9.1.2", why: "Track account lockouts to find users under attack or with expired passwords." },
        { id: "9.3.1", why: "See when multi-factor authentication challenges fail — could be a stolen password." }
      ]},
      { name: "Who has power", description: "Changes to admin groups, privileged access, and permissions. We track them so you stay in control.", ucs: [
        { id: "9.1.3", why: "Alert when someone is added to a privileged group like Domain Admins." },
        { id: "9.4.1", why: "Audit what privileged users do during their elevated sessions." },
        { id: "9.4.3", why: "Track when emergency break-glass accounts are used — this should be very rare." }
      ]},
      { name: "Directories & policies", description: "Active Directory, LDAP, and group policies. We monitor changes and availability.", ucs: [
        { id: "9.1.7", why: "Know when Group Policy Objects are modified — they control security settings everywhere." },
        { id: "9.1.8", why: "Monitor Active Directory replication — when it breaks, logins can fail." },
        { id: "9.2.3", why: "Detect changes to the LDAP schema — rare and potentially dangerous modifications." }
      ]},
      { name: "Single sign-on", description: "Identity providers and SSO. We make sure your login system is up and behaving.", ucs: [
        { id: "9.3.5", why: "Monitor whether your login system (identity provider) is up and responding." },
        { id: "9.3.2", why: "Spot impossible travel — someone logs in from two far-apart locations too quickly." },
        { id: "9.3.3", why: "Detect suspicious authentication tokens that may indicate a compromised session." }
      ]}
    ]
  },
  "10": {
    outcomes: [
      "See when the firewall or security tools find something bad.",
      "Know when endpoints are isolated or threats are detected.",
      "Track email, web, and intrusion detection events in one place.",
      "Manage certificates and catch weak cryptography before it becomes a problem."
    ],
    areas: [
      { name: "Firewall & threats", description: "Blocked traffic, malware verdicts, and security alerts from your firewall. We surface what matters.", ucs: [
        { id: "10.1.1", why: "Track the trend of threats your firewall is catching — are attacks increasing?" },
        { id: "10.1.2", why: "See what the sandbox thinks about suspicious files — malware or clean?" },
        { id: "10.1.4", why: "Catch when devices try to contact known malicious domains (DNS sinkhole)." }
      ]},
      { name: "Endpoints", description: "When a laptop or server is isolated or when EDR finds something. We keep you in the loop.", ucs: [
        { id: "10.3.5", why: "Know when a computer is isolated from the network because a threat was found." },
        { id: "10.3.1", why: "Track malware detection trends across all your computers and servers." },
        { id: "10.3.3", why: "Make sure your security agents are healthy and running on all endpoints." }
      ]},
      { name: "Email security", description: "Malicious attachments, phishing clicks, and mail flow issues. We help you respond quickly.", ucs: [
        { id: "10.4.1", why: "See how many phishing emails are being caught by your email security." },
        { id: "10.4.2", why: "Track malicious attachments that were blocked before reaching inboxes." },
        { id: "10.4.3", why: "Know when users click on suspicious links in emails so you can respond." }
      ]},
      { name: "Intrusion detection", description: "IDS/IPS alerts from Snort, Suricata, Firepower, and similar. We surface attack patterns and lateral movement.", ucs: [
        { id: "10.2.1", why: "Trend IDS alerts over time to reveal attack campaigns and tuning opportunities." },
        { id: "10.2.2", why: "Find which internal hosts are attacked the most — prioritise remediation there." },
        { id: "10.2.5", why: "Detect lateral movement — an attacker is already inside and moving between systems." }
      ]},
      { name: "Web security", description: "Secure web gateways and proxies. We show blocked categories, malware downloads, and data leakage.", ucs: [
        { id: "10.5.3", why: "Every blocked malware download is a prevented infection — see the trend." },
        { id: "10.5.4", why: "Catch sensitive data being uploaded to unauthorized cloud services." },
        { id: "10.5.1", why: "Track blocked web categories — spikes may indicate an infection or policy abuse." }
      ]},
      { name: "Certificates & PKI", description: "Internal certificate authorities, weak ciphers, and certificate lifecycle. We help you avoid outages and attacks.", ucs: [
        { id: "10.8.2", why: "Audit who issued which certificates — rogue issuance enables man-in-the-middle attacks." },
        { id: "10.8.3", why: "Find certificates using weak algorithms that are vulnerable to attack." },
        { id: "10.8.39", why: "Make sure your security tools are still reporting — silence could mean tampering." }
      ]},
      { name: "Vulnerabilities & alerts", description: "Vulnerability scans and overall alert volume. We help you prioritize and tune.", ucs: [
        { id: "10.6.1", why: "Track critical vulnerabilities across your systems — what needs patching first?" },
        { id: "10.7.1", why: "Monitor overall security alert volume — spot trends and avoid alert fatigue." },
        { id: "10.6.2", why: "Measure how quickly vulnerabilities get fixed once they're found." }
      ]}
    ]
  },
  "11": {
    outcomes: [
      "Know when email isn't flowing or mailboxes have issues.",
      "See suspicious logins or rule changes in email and collaboration.",
      "Track Teams, meetings, and collaboration health.",
      "Know when meeting quality drops because of the network — before users complain.",
      "Monitor voice quality and call routing at the network level — independent of any PBX platform.",
      "Track building occupancy, environmental conditions, and asset locations."
    ],
    areas: [
      { name: "Mail flow & health", description: "Is email being delivered? Are mailboxes and Exchange healthy? We monitor both.", ucs: [
        { id: "11.1.1", why: "Track whether emails are flowing normally — delays affect everyone." },
        { id: "11.1.9", why: "Monitor the overall health of your Microsoft 365 services." },
        { id: "11.3.9", why: "Watch mailbox sizes and quotas — full mailboxes bounce incoming mail." }
      ]},
      { name: "Who did what", description: "Logins, rule changes, and audit events in Microsoft 365, Google Workspace, and similar. We give you visibility.", ucs: [
        { id: "11.1.2", why: "Audit who accessed which mailboxes and what they did." },
        { id: "11.1.8", why: "Catch suspicious inbox rules — attackers use these to hide forwarded emails." },
        { id: "11.2.4", why: "Detect unusual login patterns in Google Workspace accounts." }
      ]},
      { name: "Collaboration & meetings", description: "Teams, Webex, and other collaboration tools. We watch for outages and odd behavior.", ucs: [
        { id: "11.1.4", why: "Track how Teams is being used — adoption, activity, and any issues." },
        { id: "11.3.8", why: "Monitor Webex meeting quality and participation trends." },
        { id: "11.3.1", why: "Watch call quality scores — bad audio quality means poor meetings." }
      ]},
      { name: "Meeting & call quality (ThousandEyes)", description: "ThousandEyes monitors the network path to Webex, Teams, and Zoom. We show when the network is hurting meeting quality.", ucs: [
        { id: "11.3.27", why: "Monitor voice quality (MOS scores) on RTP streams — scores below 3.5 mean poor calls." },
        { id: "11.3.28", why: "See the network path to Webex data centers and pinpoint where latency or loss happens." },
        { id: "11.3.29", why: "Check if your network is ready for Microsoft Teams — from every office location." }
      ]},
      { name: "Wire-level voice & carrier routing (Telco)", description: "Voice quality measured directly from network packets, emergency call tracking, and call routing KPIs — for carriers and enterprises alike.", ucs: [
        { id: "11.3.32", why: "Measure voice quality (MOS) directly from RTP packets — works with any phone system, not just Cisco." },
        { id: "11.3.33", why: "Track every emergency call (911/112) to make sure they all get through — a regulatory must-have." },
        { id: "11.3.34", why: "Calculate answer seizure ratio per trunk — the number-one KPI for voice service quality." }
      ]},
      { name: "Location & environment (Cisco Spaces)", description: "Building occupancy, environmental sensors, and asset tracking using Meraki and Cisco Spaces.", ucs: [
        { id: "11.4.1", why: "See real-time and historical occupancy per building and floor — supports space planning." },
        { id: "11.4.3", why: "Monitor temperature, humidity, and air quality using Meraki MT sensors." },
        { id: "11.4.4", why: "Track high-value assets in real time and get alerts when they leave a geofenced area." }
      ]}
    ]
  },
  "12": {
    outcomes: [
      "See when builds or deployments fail.",
      "Know when secrets or credentials leak into code.",
      "Track pipeline health and security scan results.",
      "Audit every infrastructure-as-code change and catch policy violations."
    ],
    areas: [
      { name: "Builds & deployments", description: "Failed builds, failed deployments, and pipeline status. We help you fix things fast.", ucs: [
        { id: "12.2.1", why: "Track build success rates — dropping rates mean something is wrong in the code." },
        { id: "12.2.5", why: "Know immediately when a deployment to production fails." },
        { id: "12.2.3", why: "Measure how frequently you deploy — a key indicator of development velocity." }
      ]},
      { name: "Secrets & code", description: "Passwords or keys accidentally committed, or branch protection bypassed. We help you catch it.", ucs: [
        { id: "12.1.4", why: "Alert when passwords or API keys are accidentally committed to code." },
        { id: "12.1.2", why: "Know when branch protection rules are bypassed — a security risk." },
        { id: "12.1.6", why: "Detect force pushes that can overwrite code history — intentional or accidental." }
      ]},
      { name: "Dependencies & packages", description: "Vulnerable dependencies and package issues. We keep your supply chain in view.", ucs: [
        { id: "12.3.2", why: "Get alerts when a library your code depends on has a known vulnerability." },
        { id: "12.3.1", why: "Monitor the health of your artifact repository where packages are stored." },
        { id: "12.3.4", why: "Track software license compliance so you avoid legal surprises." }
      ]},
      { name: "Infrastructure as Code", description: "Terraform, Ansible, and policy-as-code. We audit every infrastructure change.", ucs: [
        { id: "12.4.1", why: "Track every Terraform apply — know exactly what changed in your infrastructure and when." },
        { id: "12.4.5", why: "Catch policy violations that prevent non-compliant infrastructure from being deployed." },
        { id: "12.4.7", why: "Audit container image builds and pushes to protect the software supply chain." }
      ]}
    ]
  },
  "13": {
    outcomes: [
      "Know when the monitoring system itself is overloaded or slow.",
      "See when search heads or indexers have problems.",
      "Track forwarders and data flow so nothing is missed.",
      "See ThousandEyes test health alongside your Splunk monitoring in one place."
    ],
    areas: [
      { name: "Platform health", description: "Indexer queues, search performance, and cluster status. We watch the monitoring system itself.", ucs: [
        { id: "13.1.1", why: "Watch indexer queue fill — when queues back up, data can be delayed or lost." },
        { id: "13.1.10", why: "Monitor the search head cluster — if it's unhealthy, nobody can search." },
        { id: "13.1.2", why: "Track how many searches run at once — too many and everything slows down." }
      ]},
      { name: "Data flow", description: "Are forwarders connected? Is data landing as expected? We help you avoid blind spots.", ucs: [
        { id: "13.1.3", why: "Know when a forwarder stops sending data — you might be missing events." },
        { id: "13.1.9", why: "Track how long it takes data to go from source to searchable — delays matter." },
        { id: "13.1.12", why: "Monitor the HTTP Event Collector — the main way cloud and apps send data in." }
      ]},
      { name: "Services & rules", description: "ITSI, service health, and rules engines. We keep an eye on the extra layers you rely on.", ucs: [
        { id: "13.2.1", why: "Track the health scores of your business services — are they degrading?" },
        { id: "13.2.6", why: "Make sure the rules engine that triggers alerts and actions is working." },
        { id: "13.2.2", why: "Get notified when key performance indicators start dropping." }
      ]},
      { name: "ThousandEyes integration", description: "ThousandEyes data flowing into Splunk — alerts, events, and service health. We show if the integration is healthy.", ucs: [
        { id: "13.3.15", why: "View ThousandEyes alerts by severity in Splunk — see what's critical at a glance." },
        { id: "13.3.19", why: "Track ThousandEyes service health through ITSI — KPIs and service scores in one view." },
        { id: "13.3.22", why: "Correlate ThousandEyes network data with Splunk APM — is it the network or the app?" }
      ]}
    ]
  },
  "14": {
    outcomes: [
      "See when building systems or industrial equipment misbehaves.",
      "Know when sensors or controllers report problems.",
      "Spot environmental or safety-related events.",
      "Monitor MQTT and OPC-UA data pipelines from edge to cloud."
    ],
    areas: [
      { name: "Buildings & environment", description: "HVAC, UPS, and building systems. We monitor so you know when something's wrong.", ucs: [
        { id: "14.1.1", why: "Watch heating and cooling systems so building comfort stays on track." },
        { id: "14.1.2", why: "Monitor UPS batteries — if they fail, equipment loses power during an outage." },
        { id: "14.1.6", why: "Track environmental compliance to avoid regulatory issues." }
      ]},
      { name: "Industrial & control systems", description: "PLCs, sensors, and OT equipment. We watch health and safety-related events.", ucs: [
        { id: "14.2.1", why: "Monitor the health of PLCs and RTUs that control industrial processes." },
        { id: "14.2.3", why: "Know immediately when a safety system activates — something may be dangerous." },
        { id: "14.2.2", why: "Detect when process variables drift outside normal ranges." }
      ]},
      { name: "Anomalies & trends", description: "When readings or processes go out of normal range. We help you catch drift early.", ucs: [
        { id: "14.3.1", why: "Catch temperature anomalies before they become equipment-damaging problems." },
        { id: "14.3.2", why: "Detect unusual vibration that could signal a failing motor or bearing." },
        { id: "14.4.8", why: "Spot when sensors drift out of calibration and start giving bad readings." }
      ]},
      { name: "MQTT & OPC-UA (Edge Hub)", description: "Industrial messaging protocols connecting sensors and PLCs to Splunk via Edge Hub and gateways.", ucs: [
        { id: "14.5.11", why: "Catch failed MQTT logins and access denials — may indicate credential abuse or attack." },
        { id: "14.5.5", why: "Track data backlog when Edge Hub loses cloud connectivity — 3 million points can pile up." },
        { id: "14.5.9", why: "Warn before OPC-UA certificates expire — expired certs break secure data collection." }
      ]}
    ]
  },
  "15": {
    outcomes: [
      "Know when power or cooling has issues in the data center.",
      "See when batteries or cooling units need attention.",
      "Track temperature and physical environment."
    ],
    areas: [
      { name: "Power & batteries", description: "UPS health, battery status, and power redundancy. We help you avoid outages.", ucs: [
        { id: "15.1.1", why: "Monitor UPS battery health so you know power backup is ready when needed." },
        { id: "15.1.3", why: "Check that redundant power feeds are both active — losing one is risky." },
        { id: "15.1.6", why: "Alert when a circuit breaker trips — something drew too much power." }
      ]},
      { name: "Cooling", description: "Temperature, CRAC units, and cooling failures. We keep an eye on the environment.", ucs: [
        { id: "15.2.1", why: "Track temperatures in each zone of the data center so hot spots are caught early." },
        { id: "15.2.3", why: "Monitor cooling unit health — if CRAC/CRAH units fail, temperatures rise fast." },
        { id: "15.2.5", why: "Detect water leaks before they cause equipment damage." }
      ]},
      { name: "Physical security", description: "Access and environmental alarms. We surface events that matter.", ucs: [
        { id: "15.3.1", why: "Audit who entered the data center and when — badge access logs." },
        { id: "15.3.2", why: "Alert when someone accesses the facility outside normal business hours." },
        { id: "15.3.5", why: "Know when server cabinet doors are opened — physical access to hardware." }
      ]}
    ]
  },
  "16": {
    outcomes: [
      "See how many tickets you have and whether you're meeting SLAs.",
      "Know when changes and incidents are linked.",
      "Track how long it takes to fix things and how often changes succeed."
    ],
    areas: [
      { name: "Tickets & SLAs", description: "Incident volume, SLA compliance, and ticket trends. We give you a clear picture.", ucs: [
        { id: "16.1.1", why: "Track incident ticket volume and trends — is the number going up or down?" },
        { id: "16.1.2", why: "Monitor whether your team is meeting SLA response and resolution targets." },
        { id: "16.1.8", why: "Find tickets that have been sitting too long without resolution." }
      ]},
      { name: "Changes", description: "Change success rate and links between changes and incidents. We help you learn from failures.", ucs: [
        { id: "16.1.4", why: "Track what percentage of changes go smoothly versus causing problems." },
        { id: "16.1.9", why: "Link incidents to recent changes — 'did a change cause this outage?'" },
        { id: "16.1.5", why: "Detect when multiple changes are scheduled at the same time — risky overlap." }
      ]},
      { name: "Configuration data", description: "CMDB quality and consistency. We help you trust your asset data.", ucs: [
        { id: "16.2.1", why: "Score how accurate and complete your asset database is." },
        { id: "16.2.2", why: "Check that discovered assets match what's recorded in the CMDB." },
        { id: "16.2.3", why: "Find orphaned records — assets in the database that no longer exist." }
      ]},
      { name: "Business availability", description: "Service availability, escalation speed, and major incident tracking. We give you the big picture.", ucs: [
        { id: "16.3.2", why: "See at a glance which hosts and services have been up or down — a Nagios-style heatmap." },
        { id: "16.3.4", why: "Track how long it takes to escalate or hand off tickets — delays hurt resolution." },
        { id: "16.3.6", why: "Make sure every major incident has a post-mortem — learning and accountability." }
      ]}
    ]
  },
  "17": {
    outcomes: [
      "Know who's allowed on the network and who was blocked.",
      "See when devices fail posture checks or policies change.",
      "Track VPN and remote access for odd or risky behavior."
    ],
    areas: [
      { name: "Network access", description: "Who got on the network, who was blocked, and why. We keep you in the loop.", ucs: [
        { id: "17.1.1", why: "Track network access authentication trends — successful and denied." },
        { id: "17.1.2", why: "See when devices are denied network access because they fail security checks." },
        { id: "17.1.6", why: "Monitor devices that get on the network via MAC bypass instead of full authentication." }
      ]},
      { name: "Device posture", description: "When a device fails security checks or doesn't meet policy. We help you enforce standards.", ucs: [
        { id: "17.3.2", why: "See how devices score on trust — are they up-to-date and secure?" },
        { id: "17.3.5", why: "Track posture assessment results over time — are more devices compliant?" },
        { id: "17.1.8", why: "Know when NAC policies change — did someone relax the rules?" }
      ]},
      { name: "VPN & remote access", description: "Sessions, locations, and suspicious remote access. We help you spot abuse.", ucs: [
        { id: "17.2.1", why: "Track how many people are connected via VPN at any given time." },
        { id: "17.2.3", why: "Spot when someone connects from an unusual or suspicious location." },
        { id: "17.2.8", why: "Detect when the same account is connected from multiple locations simultaneously." }
      ]}
    ]
  },
  "18": {
    outcomes: [
      "See when the network fabric or software-defined network has faults.",
      "Know when policies or firewall rules in the fabric change.",
      "Track how endpoints move and connect."
    ],
    areas: [
      { name: "Fabric health", description: "Faults, connectivity, and overall health of ACI, NSX, or similar. We surface issues.", ucs: [
        { id: "18.1.1", why: "Monitor the overall health score of your network fabric." },
        { id: "18.1.7", why: "Watch the APIC controllers that manage the fabric — if they're unhealthy, so is the network." },
        { id: "18.2.5", why: "Track transport node connectivity — the foundation of your virtual network." }
      ]},
      { name: "Policies & rules", description: "Policy and firewall rule changes in the fabric. We help you stay in control.", ucs: [
        { id: "18.1.5", why: "Audit changes to tenant configurations — who changed what and when." },
        { id: "18.2.1", why: "See which distributed firewall rules are being hit — are they working as intended?" },
        { id: "18.3.8", why: "Track every configuration change in your SDN with rollback awareness." }
      ]},
      { name: "Endpoints", description: "Where endpoints are and how they move. We give you visibility into the virtual network.", ucs: [
        { id: "18.1.3", why: "Track endpoints as they move between leaf switches in the fabric." },
        { id: "18.1.4", why: "Analyze which security contracts and filters are being used or ignored." },
        { id: "18.2.2", why: "Verify that micro-segmentation policies are actually being enforced." }
      ]}
    ]
  },
  "19": {
    outcomes: [
      "Know when blades, servers, or HCI nodes have hardware problems.",
      "See when storage or disk issues appear in converged systems.",
      "Track cluster and node health in one place."
    ],
    areas: [
      { name: "Hardware health", description: "Blades, servers, and hardware faults. We watch so you can replace before failure.", ucs: [
        { id: "19.1.1", why: "Monitor the health of blade and rack servers — catch problems before they cause outages." },
        { id: "19.1.4", why: "Track hardware fault trends — are faults increasing in a particular chassis?" },
        { id: "19.1.6", why: "Watch power consumption and temperatures on compute hardware." }
      ]},
      { name: "Cluster & nodes", description: "HCI cluster health, node status, and connectivity. We keep you informed.", ucs: [
        { id: "19.2.1", why: "Monitor overall cluster health — the single most important HCI indicator." },
        { id: "19.2.4", why: "Check that workload is balanced across nodes — imbalance causes performance issues." },
        { id: "19.2.7", why: "Watch the controller VMs that manage storage — if they're unhealthy, data is at risk." }
      ]},
      { name: "Storage in the box", description: "Disk failures, latency, and I/O in converged systems. We help you avoid surprises.", ucs: [
        { id: "19.2.3", why: "Track storage latency — slow storage means slow everything." },
        { id: "19.2.5", why: "Get alerts when disks fail so replacements can be ordered immediately." },
        { id: "19.2.2", why: "Monitor storage pool capacity to plan for growth." }
      ]}
    ]
  },
  "20": {
    outcomes: [
      "See how much you're spending in the cloud and where.",
      "Know when resources are idle or over-provisioned.",
      "Plan capacity and budget with trends and alerts."
    ],
    areas: [
      { name: "Spend & budget", description: "Daily spend, trends, and budget alerts. We help you stay on track.", ucs: [
        { id: "20.1.1", why: "See daily cloud spending so you can spot trends and surprises early." },
        { id: "20.1.5", why: "Get an alert when spending approaches your budget limit." },
        { id: "20.1.2", why: "Detect unusual spikes in cloud cost — something may have been misconfigured." }
      ]},
      { name: "Waste & efficiency", description: "Idle resources and rightsizing. We help you save money.", ucs: [
        { id: "20.1.4", why: "Find cloud resources that are running but not doing anything — wasting money." },
        { id: "20.2.5", why: "Get recommendations for right-sizing — often you're paying for more than you need." },
        { id: "20.2.11", why: "Find orphaned resources like unattached disks and unused IPs still being charged." }
      ]},
      { name: "Capacity planning", description: "Growth trends for compute and storage. We help you plan ahead.", ucs: [
        { id: "20.2.1", why: "Forecast when you'll need more computing power based on growth trends." },
        { id: "20.2.2", why: "Predict when storage will fill up so you can plan purchases." },
        { id: "20.2.7", why: "Model seasonal patterns — some workloads spike at predictable times." }
      ]}
    ]
  }
};
