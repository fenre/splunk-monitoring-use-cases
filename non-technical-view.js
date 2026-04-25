/**
 * Non-technical view: plain-language outcomes and "areas of monitoring" per category.
 * Used when the user selects "Non-technical" in the header.
 */
window.NON_TECHNICAL = {
  "1": {
    outcomes: [
      "See when computers or servers are overloaded, running out of space, or acting strangely.",
      "Get early warning before something breaks so you can fix it before users notice.",
      "Know when someone changes important system settings or files — intentionally or not."
    ],
    areas: [
      { name: "Performance & capacity", description: "Are your servers keeping up? We watch processor load, memory, and disk space so you know before things get slow or full.", ucs: [
        { id: "1.1.1", why: "Spot when a server's processor is maxing out before users notice slowdowns." },
        { id: "1.1.3", why: "See when a disk is filling up so you can add space before it runs out." },
        { id: "1.2.2", why: "Watch memory usage on Windows servers — when it runs low, applications crash." }
      ]},
      { name: "Crashes & outages", description: "Crashes, blue screens, and services that stop working. We catch them so your team can respond quickly.", ucs: [
        { id: "1.1.11", why: "Detect when a Linux server has a critical kernel panic — the equivalent of a blue screen." },
        { id: "1.2.11", why: "Catch Windows Blue Screen of Death events across your fleet." },
        { id: "1.2.4", why: "Know immediately when an important Windows service stops running." }
      ]},
      { name: "Security & access", description: "Who logged in, what did they change, and should they have been allowed? We track it all.", ucs: [
        { id: "1.1.8", why: "Detect when someone is trying many passwords to break into a server (brute-force attack)." },
        { id: "1.2.8", why: "Alert when someone is added to a powerful admin group on Windows." },
        { id: "1.1.9", why: "Catch unauthorized use of administrator commands on Linux." }
      ]},
      { name: "Hardware health", description: "Physical problems like failing disks, overheating, or broken power supplies. We alert you before they cause outages.", ucs: [
        { id: "1.4.2", why: "Get an alert when a disk array loses a drive, so you can replace it in time." },
        { id: "1.4.4", why: "Predict disk failures before they happen using built-in health sensors." },
        { id: "1.4.3", why: "Know immediately when a power supply fails so you can replace it." }
      ]},
      { name: "Mac laptops & desktops", description: "macOS endpoints — encryption status, security settings, and resource usage.", ucs: [
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
      { name: "Performance & resources", description: "Are virtual machines getting the processor and memory they need? We help you see when they're being squeezed.", ucs: [
        { id: "2.1.1", why: "See when a physical host is running out of processing power for its virtual machines." },
        { id: "2.1.2", why: "Detect when memory pressure forces the host to reclaim memory from virtual machines." },
        { id: "2.1.42", why: "Track how long virtual machines wait for processor time — high wait times mean slow applications." }
      ]},
      { name: "Storage & snapshots", description: "Do your virtual machines have enough storage? We track usage and catch forgotten snapshots eating up space.", ucs: [
        { id: "2.1.3", why: "Track storage usage trends so you can add space before virtual machines run out." },
        { id: "2.1.5", why: "Find forgotten snapshots that quietly eat up storage space." },
        { id: "2.1.4", why: "Detect storage slowdowns that make applications feel sluggish." }
      ]},
      { name: "Health & failures", description: "Failovers, hardware alerts, and cluster issues. We surface them so your team can investigate.", ucs: [
        { id: "2.1.7", why: "Know when a host fails and virtual machines automatically move to another — a sign something broke." },
        { id: "2.1.11", why: "Get hardware alerts from the physical servers running your virtual machines." },
        { id: "2.1.22", why: "Monitor the vCenter management platform — if it goes down, you lose visibility into everything." }
      ]},
      { name: "Hyper-V", description: "Microsoft Hyper-V virtual machines — replication, cluster storage, and live migrations.", ucs: [
        { id: "2.2.2", why: "Watch replication health — if it falls behind, disaster recovery is at risk." },
        { id: "2.2.3", why: "Monitor the shared storage that Hyper-V clusters depend on." },
        { id: "2.2.10", why: "Track cluster node health and quorum — losing quorum means the whole cluster stops." }
      ]},
      { name: "KVM, Proxmox & oVirt", description: "Open-source virtualisation — Proxmox clusters, ZFS storage, backups, and KVM daemon health.", ucs: [
        { id: "2.3.11", why: "Check whether Proxmox backup jobs succeeded — failed backups mean no recovery point." },
        { id: "2.3.14", why: "Watch ZFS pool health — a degraded pool means a disk failed and data is at risk." },
        { id: "2.3.16", why: "Monitor the service that manages all KVM virtual machines — if it hangs, VMs become unmanageable." }
      ]},
      { name: "Across all platforms", description: "Cross-platform checks — virtual machine density, backup coverage, and end-of-life operating systems.", ucs: [
        { id: "2.4.3", why: "Track how many virtual machines run on each host — too many means you're at risk if a host fails." },
        { id: "2.4.2", why: "Find virtual machines with no recent backup — a single failure could mean permanent data loss." },
        { id: "2.4.1", why: "Spot virtual machines running old operating systems that no longer get security patches." }
      ]},
      { name: "IGEL thin clients", description: "We monitor your IGEL thin client fleet — device availability, firmware compliance, security events, and the management server that controls them all.", ucs: [
        { id: "2.5.1", why: "See which thin clients are online and which are offline across all your sites, so you know before users complain." },
        { id: "2.5.2", why: "Find devices running outdated or unapproved firmware that could have security gaps or compatibility issues." },
        { id: "2.5.3", why: "Watch the IGEL management server health — if it goes down, you lose control of all your endpoints." }
      ]},
      { name: "Citrix Virtual Apps & Desktops", description: "We monitor the full Citrix CVAD stack — session logon performance, ICA latency, VDA registration, controller health, PVS streaming, profile loading, StoreFront, licensing, and compliance recording.", ucs: [
        { id: "2.6.1", why: "Break down slow Citrix logons into individual phases so you know exactly what is causing delays for users." },
        { id: "2.6.2", why: "Track the responsiveness users actually feel in their Citrix sessions — keystroke to screen response." },
        { id: "2.6.4", why: "Know when virtual desktop agents go unregistered and can no longer serve users — reducing available capacity." }
      ]},
      { name: "uberAgent digital experience", description: "Citrix uberAgent monitors the actual user experience — experience scores, application hangs, startup times, browser speed, boot duration, and endpoint security threats inside Citrix sessions.", ucs: [
        { id: "2.6.17", why: "A single 0-to-10 score tells you whether users are having a good or bad experience right now." },
        { id: "2.6.18", why: "Detect applications that freeze and show 'Not Responding' — invisible to most monitoring tools." },
        { id: "2.6.27", why: "Spot security threats inside Citrix sessions that network tools cannot see." }
      ]}
    ]
  },
  "3": {
    outcomes: [
      "See when containers or application pods keep crashing or restarting.",
      "Know if your clusters are healthy and have enough resources.",
      "Spot security issues like containers running with too many permissions."
    ],
    areas: [
      { name: "Docker containers", description: "Containers that crash, run out of memory, or use too many resources. We help you find and fix them.", ucs: [
        { id: "3.1.1", why: "Find containers that keep crashing and restarting in a loop." },
        { id: "3.1.2", why: "Catch when containers are killed because they ran out of memory." },
        { id: "3.1.6", why: "Detect containers running with full system privileges — a serious security risk." }
      ]},
      { name: "Kubernetes clusters", description: "The system that runs your containers at scale. We watch the cluster brain, worker nodes, and storage.", ucs: [
        { id: "3.2.10", why: "Spot pods stuck in CrashLoopBackOff — they keep trying to start and failing." },
        { id: "3.2.3", why: "Know when a worker node becomes unavailable and can no longer run workloads." },
        { id: "3.2.7", why: "Watch the control plane — if it goes down, nothing gets scheduled." }
      ]},
      { name: "OpenShift", description: "Red Hat OpenShift — security policies, builds, and cluster upgrades.", ucs: [
        { id: "3.3.4", why: "Catch pods that try to run with more permissions than allowed — could be an attack." },
        { id: "3.3.3", why: "Track build failures that block application deployments." },
        { id: "3.3.1", why: "Make sure OpenShift cluster upgrades don't stall mid-way." }
      ]},
      { name: "Container registries", description: "Where container images are stored. We watch for security issues and access problems.", ucs: [
        { id: "3.4.2", why: "Get vulnerability scan results for your container images before they run in production." },
        { id: "3.4.5", why: "Spot failed logins and denied access that may indicate credential misuse." },
        { id: "3.4.8", why: "Warn before a registry certificate expires — expired certificates stop all image downloads." }
      ]},
      { name: "Service mesh & serverless", description: "The networking layer between your services and serverless containers. We watch traffic flow and security.", ucs: [
        { id: "3.5.1", why: "Monitor traffic between microservices to see how they talk to each other." },
        { id: "3.5.2", why: "Check sidecar proxy health — when proxies fail, services can't communicate." },
        { id: "3.5.3", why: "Get warned before encryption certificates expire — expired certificates break service-to-service security." }
      ]},
      { name: "eBPF & kernel-level observability", description: "Deep kernel-level visibility into network flows, process activity, and service performance — without changing application code.", ucs: [
        { id: "3.5.13", why: "We see every network connection between containers at the kernel level — catching unexpected communication that application monitoring misses." },
        { id: "3.5.14", why: "We detect suspicious processes, file access, and privilege escalation inside containers before attackers can do damage." },
        { id: "3.5.15", why: "We automatically measure service speed and errors without changing any code — instant visibility for legacy and third-party applications." }
      ]},
      { name: "Container & Kubernetes trending", description: "We chart pod restarts, vulnerabilities, deployment velocity, resource usage, error rates, and traffic over weeks and months so you see whether your container platform is getting healthier or needs attention.", ucs: [
        { id: "3.6.1", why: "We track pod restart rates over 30 days so you can see whether your workloads are stabilizing or getting less reliable." },
        { id: "3.6.2", why: "We chart critical container image vulnerabilities over time so you know if your patching is keeping up with new threats." },
        { id: "3.6.5", why: "We trend Kubernetes warning and error events daily so you catch systemic problems before they become outages." }
      ]}
    ]
  },
  "4": {
    outcomes: [
      "See how your cloud is being used and who did what.",
      "Catch risky or unusual activity in your cloud accounts.",
      "Keep an eye on spending and changes to important security settings."
    ],
    areas: [
      { name: "Amazon Web Services (AWS)", description: "Your AWS cloud — logins, security alerts, and changes to critical settings like who can access what.", ucs: [
        { id: "4.1.2", why: "Alert whenever the all-powerful root account is used — this should be extremely rare." },
        { id: "4.1.8", why: "Get threat alerts from AWS GuardDuty — it watches for malicious activity in your account." },
        { id: "4.1.14", why: "Detect unexpected spikes in cloud spending before the bill arrives." }
      ]},
      { name: "Microsoft Azure", description: "Your Azure cloud — activity logs, identity security, and resource health.", ucs: [
        { id: "4.2.2", why: "Spot suspicious sign-in patterns in your Azure identity system (Entra ID)." },
        { id: "4.2.9", why: "Surface security alerts from Microsoft Defender across your Azure resources." },
        { id: "4.2.12", why: "Get alerts when Azure spending approaches or exceeds your budget." }
      ]},
      { name: "Google Cloud (GCP)", description: "Your Google Cloud — audit logs, security findings, and cluster health.", ucs: [
        { id: "4.3.1", why: "Track every action and change in your Google Cloud environment through audit logs." },
        { id: "4.3.5", why: "Pull in security findings from Google Cloud's Security Command Center." },
        { id: "4.3.7", why: "Monitor BigQuery usage and cost — runaway queries can burn through your budget." }
      ]},
      { name: "Multi-cloud overview", description: "When you use more than one cloud provider. We bring everything together in one view.", ucs: [
        { id: "4.4.3", why: "See spending across AWS, Azure, and Google Cloud in a single cost dashboard." },
        { id: "4.4.14", why: "Detect when audit logging is disabled in any cloud — that's a dangerous blind spot." },
        { id: "4.4.6", why: "Pull security findings from all clouds into one place for unified prioritisation." }
      ]},
      { name: "Serverless & functions", description: "AWS Lambda, Azure Functions, and similar. Short-lived code that runs on demand — we watch for errors and limits.", ucs: [
        { id: "4.5.1", why: "Track function errors — failed functions mean broken workflows." },
        { id: "4.5.2", why: "Monitor cold start delays — slow starts hurt user experience for the first request." },
        { id: "4.5.3", why: "Alert when concurrency limits are hit — functions start getting rejected." }
      ]},
      { name: "Cloud infrastructure trending", description: "We chart resource counts, function usage, security findings, storage growth, network volumes, and API activity over months so you see where your cloud is heading.", ucs: [
        { id: "4.6.1", why: "We track how many cloud instances you have over 90 days so you can spot runaway growth or orphaned resources before they hit your bill." },
        { id: "4.6.3", why: "We trend new versus resolved cloud security findings so you know if your security posture is improving or falling behind." },
        { id: "4.6.4", why: "We chart storage growth monthly so you can forecast costs and set lifecycle policies before storage bills surprise you." }
      ]}
    ]
  },
  "5": {
    outcomes: [
      "Know when routers, switches, firewalls, or wireless access points have problems.",
      "See when links go down, tunnels degrade, or routing gets confused.",
      "Track who's using bandwidth and spot suspicious traffic patterns.",
      "Monitor cloud-managed networks and measure how users experience the network."
    ],
    areas: [
      { name: "Routers & switches", description: "Are your network devices healthy? We watch Cisco, Juniper, Arista, and HPE Aruba switches and routers for link failures, routing problems, and hardware issues.", ucs: [
        { id: "5.1.1", why: "See when network links go up or down — the most fundamental network alert." },
        { id: "5.1.56", why: "Monitor Juniper chassis alarms — power supply, fan, and temperature alerts." },
        { id: "5.1.60", why: "Track Arista MLAG redundancy health — failures here can blackhole traffic." }
      ]},
      { name: "Firewalls", description: "Your security perimeter — Cisco, Palo Alto, Fortinet, Juniper, Check Point, and more. We track blocked traffic, policy changes, high availability, and threat events.", ucs: [
        { id: "5.2.2", why: "Audit every firewall policy change so you know what was modified and by whom." },
        { id: "5.2.47", why: "We detect when paired firewalls fail over—planned or not—so repeated problems get fixed before users feel them." },
        { id: "5.2.52", why: "We flag traffic that doesn’t match how your network is laid out—whether it’s a mistake or someone spoofing addresses." }
      ]},
      { name: "Load balancers & ADCs", description: "The devices that spread traffic across your servers — F5 BIG-IP, Citrix ADC (NetScaler), and others. We watch pool health, availability, SSL certificates, HA failover, and GSLB across data centers.", ucs: [
        { id: "5.3.1", why: "Alert when a server drops out of the load balancer pool — less capacity for users." },
        { id: "5.3.13", why: "Know when a Citrix ADC virtual server goes down — all applications behind it become unreachable." },
        { id: "5.3.16", why: "Detect Citrix ADC failover events — the secondary took over, so something broke on the primary." }
      ]},
      { name: "WiFi & wireless", description: "WiFi access points from Cisco Meraki, HPE Aruba, and others. We watch for rogue devices, signal quality, and coverage gaps.", ucs: [
        { id: "5.4.1", why: "Know immediately when a wireless access point goes offline." },
        { id: "5.4.33", why: "Monitor Aruba AP radio status across the fleet — detect coverage holes before users complain." },
        { id: "5.4.35", why: "Track Aruba wireless intrusion events — rogue APs, evil twin attacks, and RF threats." }
      ]},
      { name: "SD-WAN", description: "Software-defined WAN links connecting your branch offices. We watch tunnel health, application performance, security at the edge, and the management platform itself.", ucs: [
        { id: "5.5.1", why: "Monitor tunnel health — loss, latency, and jitter directly affect application experience." },
        { id: "5.5.12", why: "Track individual tunnel sessions — when they flap repeatedly, the underlying circuit is unreliable." },
        { id: "5.5.17", why: "Catch security threats at branch offices — malware and intrusions that bypass the central firewall." }
      ]},
      { name: "DNS & DHCP", description: "How devices find each other on the network. We watch name resolution and IP address assignment.", ucs: [
        { id: "5.6.5", why: "Alert when a pool of network addresses is running out — new devices won't be able to connect." },
        { id: "5.6.1", why: "Track name lookup volume — sudden changes can indicate problems or attacks." },
        { id: "5.6.4", why: "Detect DNS tunneling — attackers hiding data inside normal name lookups." }
      ]},
      { name: "Network traffic analysis", description: "NetFlow and similar data showing who is talking to whom and how much bandwidth is used.", ucs: [
        { id: "5.7.1", why: "Find the top bandwidth consumers on your network — essential for congestion troubleshooting." },
        { id: "5.7.5", why: "Detect unusually large outbound transfers — possible data theft." },
        { id: "5.7.3", why: "Break down bandwidth by application so you can prioritise the most important traffic." }
      ]},
      { name: "Network management", description: "Centralised management tools, SNMP traps, and device backups. We consolidate alerts from your management platforms.", ucs: [
        { id: "5.8.1", why: "Get AI-driven network alerts from Cisco DNA Center alongside everything else." },
        { id: "5.8.5", why: "Track whether network device configs are being backed up — missing backups mean manual rebuilds." },
        { id: "5.8.3", why: "Consolidate alerts from all devices into one place to reduce tool sprawl." }
      ]},
      { name: "Internet & digital experience", description: "How does the network look from your users' perspective? ThousandEyes tests the path from users to apps — across the internet, cloud, and SD-WAN.", ucs: [
        { id: "5.9.1", why: "Track network delay from agents to servers — slow paths mean slow apps." },
        { id: "5.9.18", why: "Get alerted when an internet outage is detected that affects your services." },
        { id: "5.9.25", why: "Monitor remote worker connectivity health — is the network causing their issues?" }
      ]},
      { name: "Streaming telemetry (gNMI)", description: "Modern, high-resolution data streaming from network devices — replacing slow SNMP polling with real-time counters, optic health, and routing updates every few seconds.", ucs: [
        { id: "5.11.1", why: "Stream interface traffic every 30 seconds instead of every 5 minutes — catch congestion that SNMP misses." },
        { id: "5.11.5", why: "Watch optical transceiver health — dimming lasers and rising temperatures warn you before a link fails." },
        { id: "5.11.3", why: "Get instant notification when a BGP peer drops — seconds instead of minutes via syslog." }
      ]},
      { name: "Carrier signaling", description: "The protocols that power mobile networks and voice calls. We watch for failures that affect subscribers.", ucs: [
        { id: "5.10.1", why: "Track signaling health — failures here mean subscribers can't authenticate or use data." },
        { id: "5.10.4", why: "Monitor voice trunk success rates — failed calls mean lost revenue and unhappy customers." },
        { id: "5.10.5", why: "Detect registration storms that can overwhelm voice infrastructure within minutes." }
      ]},
      { name: "Call records & voice analytics", description: "Call records from voice platforms. We analyse call patterns, failures, and trends.", ucs: [
        { id: "5.12.1", why: "Track call failure statistics — rising failure rates mean network or routing problems." },
        { id: "5.12.5", why: "Monitor voice quality scores — low scores mean poor call quality for users." },
        { id: "5.12.10", why: "Detect toll fraud — unauthorised calls running up huge charges." }
      ]},
      { name: "Cisco Catalyst Center", description: "Your network management brain — we watch every device, every user connection, every wireless signal, and every security advisory that Catalyst Center tracks, so your team knows about problems before users do.", ucs: [
        { id: "5.8.1", why: "Get assurance and issue alerts from Cisco DNA Center (Catalyst Center) alongside the rest of your network telemetry — catch degrading health before it becomes an outage." },
        { id: "5.1.8", why: "See CPU and memory load on your switches and routers — capacity pressure often shows up before links fail or routing flaps." },
        { id: "5.1.26", why: "Track firmware and software versions across the fleet — outdated builds are a common path to unpatched security issues." }
      ]}
    ]
  },
  "6": {
    outcomes: [
      "See when storage is filling up or getting slow.",
      "Know when disks or controllers fail so you can act before data is lost.",
      "Make sure backups actually ran and succeeded — before you need them."
    ],
    areas: [
      { name: "Storage health & capacity", description: "How full are your storage systems, and how fast is data moving? We track capacity, speed, and failures.", ucs: [
        { id: "6.1.1", why: "Watch storage volumes filling up so you can act before they're full." },
        { id: "6.1.2", why: "Detect when storage is getting slow — this directly affects application performance." },
        { id: "6.1.4", why: "Get an immediate alert when a disk fails so it can be replaced." }
      ]},
      { name: "SAN fabric (Cisco MDS)", description: "Fibre Channel switches connecting servers to storage. We watch for slow devices, link congestion, and unauthorised connections.", ucs: [
        { id: "6.1.28", why: "Detect slow-drain devices before one sluggish port impacts hundreds of servers." },
        { id: "6.1.27", why: "Track inter-switch link utilisation — congested links cause storage slowdowns." },
        { id: "6.1.30", why: "Spot unknown devices logging into the SAN fabric — a security and stability concern." }
      ]},
      { name: "Cloud & object storage", description: "Cloud buckets and object storage — including when something is accidentally left open to the world.", ucs: [
        { id: "6.2.3", why: "Alert when a cloud storage bucket is publicly accessible — a common data leak risk." },
        { id: "6.2.1", why: "Track how much data is stored in cloud buckets and how fast it's growing." },
        { id: "6.2.2", why: "Spot unusual access patterns that could indicate unauthorised use." }
      ]},
      { name: "Backups", description: "Did the backup run? Did it succeed? We help you avoid nasty surprises when you need to recover.", ucs: [
        { id: "6.3.1", why: "See at a glance what percentage of backup jobs succeeded." },
        { id: "6.3.3", why: "Catch when a scheduled backup didn't run at all — before you need it." },
        { id: "6.3.6", why: "Track whether backups meet your agreed recovery time targets." }
      ]},
      { name: "File shares & access", description: "Who accessed which files, and were permissions changed? We help you protect shared data and detect threats.", ucs: [
        { id: "6.4.1", why: "Full audit trail of who accessed which files — often required for compliance." },
        { id: "6.4.2", why: "Detect patterns that look like ransomware — mass file encryption in progress." },
        { id: "6.4.4", why: "Alert when file share permissions are changed — accidental changes can expose sensitive data." }
      ]}
    ]
  },
  "7": {
    outcomes: [
      "See when databases are slow, stuck, or unavailable.",
      "Know when too many connections are used or queries are blocking each other.",
      "Track who changed what in your data systems."
    ],
    areas: [
      { name: "Database performance", description: "Is the database up and responding? Are queries slow? We monitor availability and speed.", ucs: [
        { id: "7.1.1", why: "Find slow-running queries that are making your applications feel sluggish." },
        { id: "7.1.2", why: "Detect deadlocks where two queries block each other and nothing moves." },
        { id: "7.1.3", why: "Alert when all database connections are used up — new requests will fail." }
      ]},
      { name: "Database security & changes", description: "Privilege changes, failed logins, and important structure changes. We keep an audit trail.", ucs: [
        { id: "7.1.15", why: "Catch when someone gains elevated privileges in the database." },
        { id: "7.1.7", why: "Monitor failed login attempts to databases — potential breach attempts." },
        { id: "7.1.13", why: "Track changes to database structure — tables, columns, and indexes." }
      ]},
      { name: "NoSQL databases", description: "MongoDB, Elasticsearch, Cassandra, and similar. We watch cluster health, connections, and memory.", ucs: [
        { id: "7.2.1", why: "Know when a database node joins or leaves the cluster — unexpected changes may mean a failure." },
        { id: "7.2.7", why: "Watch connection counts — approaching limits means new requests will be rejected." },
        { id: "7.2.10", why: "Monitor Elasticsearch cluster health — a red status means searches may fail." }
      ]},
      { name: "Cloud-managed databases", description: "Managed databases where the cloud provider handles infrastructure but you still need visibility into performance.", ucs: [
        { id: "7.3.2", why: "Know when a managed database fails over — brief outage, but you need to check the impact." },
        { id: "7.3.1", why: "Use cloud-native performance insights to find the slowest queries without installing agents." },
        { id: "7.3.3", why: "Watch read replica lag — stale replicas mean apps could serve outdated data." }
      ]},
      { name: "Data warehouses & analytics", description: "Snowflake, Redshift, BigQuery, and similar analytics platforms. We track cost, performance, and scaling.", ucs: [
        { id: "7.4.4", why: "See how much each query costs — find runaway queries burning through credits." },
        { id: "7.4.2", why: "Track auto-scaling events to check whether scaling policies match real workload." },
        { id: "7.4.3", why: "Monitor data pipeline health — broken pipelines mean stale reports." }
      ]},
      { name: "Search platforms", description: "Elasticsearch, OpenSearch, and Solr. We monitor cluster health, disk limits, and indexing performance.", ucs: [
        { id: "7.5.1", why: "Know when your search cluster goes red or yellow — searches may fail or return incomplete results." },
        { id: "7.5.2", why: "Detect when data chunks can't be distributed properly — can cause data loss or slow queries." },
        { id: "7.5.8", why: "Alert before disk fills up and the search engine locks itself to protect data." }
      ]},
      { name: "Database trending", description: "Long-term trends for database health — connection pressure, slow queries, replication delay, backup growth, and index maintenance. We help you plan capacity and catch regressions early.", ucs: [
        { id: "7.6.1", why: "We track how full database connection pools get over time — so you can scale or tune before new requests are rejected." },
        { id: "7.6.2", why: "We count slow queries day by day — rising trends often mean a bad release or missing indexes." },
        { id: "7.6.3", why: "We watch replication lag across replicas — growing lag means riskier failovers and stale reads." }
      ]}
    ]
  },
  "8": {
    outcomes: [
      "Know when your websites or apps are slow or throwing errors.",
      "See when certificates are about to expire before they break things.",
      "Spot when message queues or app servers are backing up.",
      "Test your web apps from outside to see what real users experience."
    ],
    areas: [
      { name: "Websites & web servers", description: "Error rates, response times, and uptime. We help you keep sites and APIs healthy.", ucs: [
        { id: "8.1.1", why: "Track error rates on your web servers — rising errors mean users are having trouble." },
        { id: "8.1.2", why: "Monitor response times so you know when your site is getting slow." },
        { id: "8.1.5", why: "Get advance warning before an SSL certificate expires and your site shows security errors." }
      ]},
      { name: "Application servers", description: "Java, .NET, Node.js, and other runtimes. We watch memory, threads, and responsiveness.", ucs: [
        { id: "8.2.1", why: "Watch Java memory usage — when it fills up, the application slows or crashes." },
        { id: "8.2.3", why: "Detect when all worker threads are busy — new requests will be queued or dropped." },
        { id: "8.2.4", why: "Track application error rates to spot problems before they escalate." }
      ]},
      { name: "Message queues & streaming", description: "Systems that pass messages between applications. We show when things are piling up or falling behind.", ucs: [
        { id: "8.3.1", why: "See when message consumers fall behind — data is piling up waiting to be processed." },
        { id: "8.3.2", why: "Track queue depth to know when messages are building up faster than they're handled." },
        { id: "8.3.5", why: "Monitor dead letter queues — messages that failed to process and need attention." }
      ]},
      { name: "APIs & service mesh", description: "The connections between your applications. We watch error rates, speed, and security certificates.", ucs: [
        { id: "8.4.1", why: "Track API error rates by endpoint — find which connections are failing." },
        { id: "8.4.2", why: "Monitor API response times — slow APIs cascade into slow applications." },
        { id: "8.4.8", why: "Get warned before service-to-service security certificates expire." }
      ]},
      { name: "Caching layers", description: "Redis, Memcached, and other caches that speed up your applications. We watch memory, evictions, and health.", ucs: [
        { id: "8.5.2", why: "Track cache memory usage — when it runs out, data gets evicted and apps slow down." },
        { id: "8.5.3", why: "Watch eviction rates — high evictions mean the cache is too small for your workload." },
        { id: "8.5.5", why: "Monitor cache replication lag — stale replicas can serve outdated data." }
      ]},
      { name: "Network services & infrastructure tools", description: "Essential network services like SSH, NTP, DNS, and tools like Vault and Consul. We check they're running.", ucs: [
        { id: "8.6.1", why: "Monitor SSH service availability — if it goes down, teams can't reach servers remotely." },
        { id: "8.6.11", why: "Track HashiCorp Vault seal status — a sealed vault blocks all secret access." },
        { id: "8.6.16", why: "Watch NTP clock drift — out-of-sync clocks break authentication and logging." }
      ]},
      { name: "Application trending", description: "Trends in sessions, API speed, reliability budgets, caches, and message queues. We help product and platform teams see direction, not just today's snapshot.", ucs: [
        { id: "8.7.1", why: "We track how many user sessions run each day or week — a simple signal for growth and capacity." },
        { id: "8.7.2", why: "We chart API latency at typical and worst-case percentiles — tail latency is where user pain hides." },
        { id: "8.7.3", why: "We show how fast your error budget is shrinking — so you can slow releases before reliability goals break." }
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
      { name: "Logins & Active Directory", description: "Failed logins, lockouts, and suspicious sign-in patterns. We help you spot trouble in your directory.", ucs: [
        { id: "9.1.1", why: "Detect brute-force login attempts — someone is trying many passwords." },
        { id: "9.1.2", why: "Track account lockouts to find users under attack or with expired passwords." },
        { id: "9.1.3", why: "Alert when someone is added to a privileged group like Domain Admins." }
      ]},
      { name: "Directories & infrastructure", description: "LDAP directories, Active Directory replication, and group policies. We monitor changes and availability.", ucs: [
        { id: "9.1.8", why: "Monitor Active Directory replication — when it breaks, logins can fail." },
        { id: "9.1.7", why: "Know when Group Policy Objects are modified — they control security settings everywhere." },
        { id: "9.2.3", why: "Detect changes to the directory schema — rare and potentially dangerous modifications." }
      ]},
      { name: "Single sign-on & identity", description: "Identity providers and SSO. We make sure your login system is up and behaving.", ucs: [
        { id: "9.3.5", why: "Monitor whether your login system (identity provider) is up and responding." },
        { id: "9.3.2", why: "Spot impossible travel — someone logs in from two far-apart locations too quickly." },
        { id: "9.3.1", why: "Track multi-factor authentication failures — could indicate stolen passwords." }
      ]},
      { name: "Privileged access", description: "What do admins do with their elevated access? We audit sessions, break-glass use, and credential rotation.", ucs: [
        { id: "9.4.1", why: "Audit what privileged users do during their elevated sessions." },
        { id: "9.4.3", why: "Track when emergency break-glass accounts are used — this should be very rare." },
        { id: "9.4.4", why: "Make sure privileged passwords are rotated on schedule — stale passwords are a risk." }
      ]},
      { name: "Okta & Duo", description: "Cloud identity providers. We track authentication failures, MFA bypass attempts, and suspicious activity.", ucs: [
        { id: "9.5.1", why: "Track Okta authentication failures — rising rates may indicate a credential attack." },
        { id: "9.5.2", why: "Detect MFA bypass attempts — attackers try to work around your second factor." },
        { id: "9.5.14", why: "Catch Duo push fraud — attackers bombard users with MFA prompts hoping they accept." }
      ]},
      { name: "Endpoint & mobile devices", description: "Phones, tablets, and laptops enrolled in mobile device management. We check they follow your security policies.", ucs: [
        { id: "9.6.1", why: "See which devices comply with your security policies — and which don't." },
        { id: "9.6.3", why: "Get alerts when a managed device leaves an approved area." },
        { id: "9.6.5", why: "Track lost or stolen devices — know when lost mode is activated and recovery progress." }
      ]},
      { name: "Identity & access trending", description: "We chart how logins, privileged use, multi-factor adoption, and identity-provider health change over weeks and months so you spot drift before it becomes an incident.", ucs: [
        { id: "9.7.1", why: "See whether successful and failed logins are trending up or down over the quarter — a simple way to catch attacks or overload." },
        { id: "9.7.2", why: "Track how many people actually use multi-factor authentication over time — proof you are closing risky gaps." },
        { id: "9.7.7", why: "Know whether your login service stays reliably available week to week — outages hit everyone at once." }
      ]}
    ]
  },
  "10": {
    outcomes: [
      "See when security tools find something bad — blocked threats, malware, and suspicious activity.",
      "Over 2,000 pre-built detection rules are ready to deploy from Splunk Enterprise Security.",
      "Track email, web, and intrusion detection events in one place.",
      "Check that your detection rules are actually working and not going stale."
    ],
    areas: [
      { name: "Firewall & threat prevention", description: "Blocked traffic, malware verdicts, and security alerts from your firewall. We surface what matters.", ucs: [
        { id: "10.1.1", why: "Track the trend of threats your firewall is catching — are attacks increasing?" },
        { id: "10.1.2", why: "See what the sandbox thinks about suspicious files — malware or clean?" },
        { id: "10.1.4", why: "Catch when devices try to contact known malicious domains." }
      ]},
      { name: "Intrusion detection", description: "IDS/IPS alerts that detect attack patterns, scanning, and lateral movement inside your network.", ucs: [
        { id: "10.2.1", why: "Trend intrusion alerts over time to reveal attack campaigns and tuning opportunities." },
        { id: "10.2.2", why: "Find which internal hosts are attacked the most — prioritise remediation there." },
        { id: "10.2.5", why: "Detect lateral movement — an attacker is already inside and moving between systems." }
      ]},
      { name: "Endpoint protection", description: "When a laptop or server is isolated or when your endpoint security finds something. We keep you in the loop.", ucs: [
        { id: "10.3.5", why: "Know when a computer is isolated from the network because a threat was found." },
        { id: "10.3.1", why: "Track malware detection trends across all your computers and servers." },
        { id: "10.3.3", why: "Make sure your security agents are healthy and running on all endpoints." }
      ]},
      { name: "Email security", description: "Phishing, malicious attachments, and suspicious links. We help you respond quickly.", ucs: [
        { id: "10.4.1", why: "See how many phishing emails are being caught by your email security." },
        { id: "10.4.2", why: "Track malicious attachments that were blocked before reaching inboxes." },
        { id: "10.4.3", why: "Know when users click on suspicious links in emails so you can respond." }
      ]},
      { name: "Web security", description: "Secure web gateways and proxies. We show blocked categories, malware downloads, and data leakage.", ucs: [
        { id: "10.5.3", why: "Every blocked malware download is a prevented infection — see the trend." },
        { id: "10.5.4", why: "Catch sensitive data being uploaded to unauthorised cloud services." },
        { id: "10.5.2", why: "Detect shadow IT — employees using unapproved cloud services." }
      ]},
      { name: "Vulnerability management", description: "Vulnerability scans and patching progress. We help you know what needs fixing first.", ucs: [
        { id: "10.6.1", why: "Track critical vulnerabilities across your systems — what needs patching first?" },
        { id: "10.6.2", why: "Measure how quickly vulnerabilities get fixed once they're found." },
        { id: "10.6.3", why: "Check how many of your systems are actually being scanned for vulnerabilities." }
      ]},
      { name: "Security operations (SIEM & SOAR)", description: "Your security operations center — alert volume, analyst workload, and automated response. Over 2,000 pre-built detections included.", ucs: [
        { id: "10.7.1", why: "Monitor overall security alert volume — spot trends and avoid alert fatigue." },
        { id: "10.7.3", why: "Track how long it takes to detect and respond to threats — your key security metrics." },
        { id: "10.7.6", why: "Measure false positive rates so your analysts aren't drowning in noise." }
      ]},
      { name: "Certificates & encryption", description: "Certificate lifecycle, weak ciphers, and certificate authority health. We help you avoid outages and attacks.", ucs: [
        { id: "10.8.1", why: "Get warned before certificates expire — expired certificates break websites and services." },
        { id: "10.8.2", why: "Audit who issued which certificates — rogue issuance enables man-in-the-middle attacks." },
        { id: "10.8.3", why: "Find certificates using weak algorithms that are vulnerable to attack." }
      ]},
      { name: "AI & emerging threats", description: "Detections for AI abuse, prompt injection, and unauthorised model usage. We watch for next-generation threats.", ucs: [
        { id: "10.9.1", why: "Detect suspicious AI process execution on systems where it shouldn't be running." },
        { id: "10.9.4", why: "Catch prompt injection attempts being sent to your AI services." },
        { id: "10.9.3", why: "Alert when someone downloads unauthorised AI models to your infrastructure." }
      ]},
      { name: "Detection health", description: "Are your security rules actually working? We track false positives, stale rules, and coverage gaps.", ucs: [
        { id: "10.10.1", why: "Measure false positive rates so your analysts focus on real threats." },
        { id: "10.10.3", why: "Find detection rules that haven't fired in 90+ days — they might be broken or irrelevant." },
        { id: "10.10.5", why: "Map your detections to the MITRE ATT&CK framework and find the gaps in your coverage." }
      ]},
      { name: "Vendor-specific security", description: "Deep monitoring for specific security products — FortiGate, Palo Alto, CrowdStrike, Zscaler, and more.", ucs: [
        { id: "10.11.1", why: "Track firewall policy violations — which rules are being hit and why." },
        { id: "10.11.2", why: "Trend intrusion prevention events to spot attack patterns against your network." },
        { id: "10.11.4", why: "See which web categories are being blocked — unusual spikes may signal compromise." }
      ]},
      { name: "Financial fraud detection", description: "ATM fraud, wire transfer anomalies, and card velocity checks. We help financial institutions catch suspicious transactions.", ucs: [
        { id: "10.12.1", why: "Detect patterns of ATM fraud — unusual withdrawal sequences across locations." },
        { id: "10.12.2", why: "Spot anomalous wire transfers that deviate from normal business patterns." },
        { id: "10.12.3", why: "Catch rapid-fire card transactions that indicate stolen credentials." }
      ]},
      { name: "Cross-vendor security analytics", description: "Vendor-agnostic security analytics that work across any product using normalised data models.", ucs: [
        { id: "10.13.1", why: "Track failed login ratios across all systems — rising rates mean trouble." },
        { id: "10.13.3", why: "Detect impossible travel — someone logging in from two distant locations too quickly." },
        { id: "10.13.4", why: "Catch service accounts being used interactively — they should only be used by machines." }
      ]},
      { name: "Industrial & OT security", description: "Protecting SCADA, PLCs, and industrial control systems. We watch for unauthorised changes and protocol violations.", ucs: [
        { id: "10.14.2", why: "Detect when unauthorised industrial protocols appear on your OT network." },
        { id: "10.14.4", why: "Alert when controller programs are changed outside of approved maintenance windows." },
        { id: "10.14.1", why: "Make sure the OT security monitoring tools themselves are healthy and configured." }
      ]},
      { name: "Machine learning & behavioral analytics", description: "We use AI and machine learning to spot threats that fixed rules cannot catch — suspicious user behaviour, hidden attack patterns, and phishing emails that slip past filters.", ucs: [
        { id: "10.15.1", why: "We compare each person's login activity to their team — if someone logs in far more than their peers, it could mean their account is compromised." },
        { id: "10.15.3", why: "We detect malware calling home to attackers by spotting unnaturally regular communication patterns hidden in normal traffic." },
        { id: "10.15.6", why: "We use AI to read incoming emails and score them for phishing — catching cleverly worded scams that traditional filters miss." }
      ]},
      { name: "Security operations trending", description: "Trends for the security operations centre — attack surface, alert quality, detection and response times, email threats, firewall activity, risk scores, and endpoint protection coverage.", ucs: [
        { id: "10.16.1", why: "We watch how your exposed services and ports change over time — unexpected growth can mean misconfiguration or shadow systems." },
        { id: "10.16.3", why: "We measure how quickly threats are detected quarter by quarter — leadership can see whether investments in detection are paying off." },
        { id: "10.16.4", why: "We track how long it takes to contain issues after detection — so you can improve playbooks and staffing where it matters." }
      ]}
    ]
  },
  "11": {
    outcomes: [
      "Know when email, Teams, or Webex have problems.",
      "See when files are shared outside the organisation or data protection rules are broken.",
      "Track call quality and meeting reliability."
    ],
    areas: [
      { name: "Microsoft 365", description: "Email flow, Teams, SharePoint, and OneDrive. We watch for outages, suspicious sharing, and admin changes.", ucs: [
        { id: "11.1.1", why: "Know when email delivery slows down or stops — your most critical communication channel." },
        { id: "11.1.5", why: "See when files are shared with people outside your organisation in SharePoint or OneDrive." },
        { id: "11.1.6", why: "Track data loss prevention violations — sensitive data going where it shouldn't." }
      ]},
      { name: "Google Workspace", description: "Gmail, Drive, Meet, and admin console. We track security settings, sharing, and suspicious logins.", ucs: [
        { id: "11.2.3", why: "Detect when files in Google Drive are shared in unusual ways — possible data leak." },
        { id: "11.2.4", why: "Spot suspicious login patterns to your Google Workspace accounts." },
        { id: "11.2.6", why: "See which third-party apps have access to your company's Google data." }
      ]},
      { name: "Voice & meetings", description: "Call quality, video meetings, and voice trunks. We help you identify poor audio, dropped calls, and capacity issues.", ucs: [
        { id: "11.3.1", why: "Monitor call quality scores — low scores mean choppy audio and frustrated users." },
        { id: "11.3.3", why: "Track jitter, latency, and packet loss on voice calls — the main causes of bad call quality." },
        { id: "11.3.6", why: "Detect toll fraud — unauthorised calls running up your phone bill." }
      ]},
      { name: "On-premises phone system (CUCM)", description: "Cisco phone system routing, quality, gateways, and cluster health. We help you keep on-premises voice services reliable.", ucs: [
        { id: "11.3.35", why: "We trace how calls travel through your phone system — finding misconfigured routes that cause failed or expensive calls." },
        { id: "11.3.38", why: "We watch phone gateway capacity so callers don't get busy signals during peak hours." },
        { id: "11.3.39", why: "We monitor the phone system database sync between servers — if it breaks, phone settings stop updating." }
      ]},
      { name: "Contact center", description: "Agent performance, call queues, IVR self-service, and customer wait times. We help you keep your contact center running smoothly.", ucs: [
        { id: "11.3.42", why: "We track how agents spend their time — finding those stuck in 'not ready' who reduce the team's capacity." },
        { id: "11.3.43", why: "We measure how many callers get help from the automated phone menu without needing a live agent." },
        { id: "11.3.44", why: "We monitor customer wait times by team — so billing support isn't understaffed while sales is overstaffed." }
      ]},
      { name: "Messaging & presence", description: "Jabber instant messaging, presence status, and voicemail. We keep your real-time communication tools working.", ucs: [
        { id: "11.3.47", why: "We track which Jabber versions your team uses — outdated versions can have security problems." },
        { id: "11.3.48", why: "We monitor instant messaging and presence services — when they fail, everyone shows as 'unknown' status." },
        { id: "11.3.49", why: "We watch the voicemail system so messages don't get lost or delayed." }
      ]},
      { name: "Pexip video conferencing", description: "Pexip Infinity video meetings, call quality, node capacity, and gateway routing. We help you keep video meetings running across SIP, Teams, and WebRTC.", ucs: [
        { id: "11.3.52", why: "We monitor call quality for every participant — finding the sites and endpoints with choppy video before users complain." },
        { id: "11.3.53", why: "We watch conferencing node load so new meetings don't get rejected because a server ran out of capacity." },
        { id: "11.3.55", why: "We catch platform alarms — licensing warnings, node failures, certificate expiry — before they cause meeting outages." }
      ]},
      { name: "Mail transport & relay", description: "On-premises mail servers, SMTP relays, and mail queue health. We help you keep email flowing.", ucs: [
        { id: "11.4.1", why: "Monitor SMTP service availability — if it goes down, no emails get sent." },
        { id: "11.4.3", why: "Watch email queue depth — backed-up queues mean delayed messages." },
        { id: "11.4.7", why: "Track mail server TLS certificates so email delivery doesn't break." }
      ]},
      { name: "Video conferencing", description: "Zoom, Webex, and Teams meeting quality. We help you identify connection problems and poor video quality.", ucs: [
        { id: "11.5.1", why: "Track Zoom meeting quality metrics — jitter and packet loss mean poor video and audio." },
        { id: "11.5.4", why: "Monitor the health of Webex room devices so meetings start on time." },
        { id: "11.5.8", why: "Analyse Teams meeting quality across your organisation." }
      ]},
      { name: "Meeting room analytics", description: "Room utilisation, no-shows, AV equipment health, and signage. We help you get more from your meeting spaces.", ucs: [
        { id: "11.5.9", why: "We find rooms booked but never used — freeing them up for people who actually need them." },
        { id: "11.5.10", why: "We spot when two people book a twenty-person boardroom — so you can right-size your room inventory." },
        { id: "11.5.11", why: "We detect broken screens, cameras, and microphones before your next meeting starts." }
      ]}
    ]
  },
  "12": {
    outcomes: [
      "See when builds fail or deployments break.",
      "Measure how fast your team delivers software (DORA metrics).",
      "Catch security issues in the code pipeline before they reach production."
    ],
    areas: [
      { name: "Source control", description: "Git repositories, branch protections, and code reviews. We catch risky changes and exposed secrets.", ucs: [
        { id: "12.1.4", why: "Detect when secrets (passwords, API keys) are accidentally committed to source code." },
        { id: "12.1.2", why: "Alert when branch protection rules are bypassed — code could reach production unchecked." },
        { id: "12.1.3", why: "Track pull request review times — slow reviews slow down the whole team." }
      ]},
      { name: "Build & deploy pipelines", description: "CI/CD success rates, build times, and deployment frequency. We help you ship reliably.", ucs: [
        { id: "12.2.1", why: "Track build success rates — falling rates mean the code or environment has problems." },
        { id: "12.2.3", why: "Measure deployment frequency (a DORA metric) — how often you ship to production." },
        { id: "12.2.4", why: "Track lead time for changes (a DORA metric) — from commit to production." }
      ]},
      { name: "Artifacts & packages", description: "Package repositories, dependency security, and license compliance.", ucs: [
        { id: "12.3.2", why: "Get alerts when your code depends on a package with known vulnerabilities." },
        { id: "12.3.4", why: "Track software license compliance — prevent legal issues from open-source usage." },
        { id: "12.3.9", why: "Check that software bills of materials (SBOMs) are being generated for your builds." }
      ]},
      { name: "Infrastructure as code", description: "Terraform, Ansible, Puppet, and CloudFormation. We track drift, failures, and policy violations.", ucs: [
        { id: "12.4.2", why: "Detect when your actual infrastructure has drifted from what's defined in code." },
        { id: "12.4.5", why: "Catch infrastructure-as-code policy violations before they're deployed." },
        { id: "12.4.3", why: "Track Ansible playbook outcomes — know which automation tasks succeeded or failed." }
      ]},
      { name: "GitOps & deployment", description: "ArgoCD, Flux, and automated deployment tools. We track sync failures, rollbacks, and drift.", ucs: [
        { id: "12.5.1", why: "Detect when ArgoCD can't sync your desired state — deployments are blocked." },
        { id: "12.5.7", why: "Track rollback frequency — frequent rollbacks signal quality problems." },
        { id: "12.5.10", why: "Measure deployment lead time from Git commit to running in production." }
      ]},
      { name: "DevOps trending", description: "We watch delivery and security metrics over time — how often you ship, how long builds wait, and whether quality scans keep improving.", ucs: [
        { id: "12.6.1", why: "We trend delivery health (deployment frequency, lead time, failures, recovery) month by month so leaders see improvement or drift early." },
        { id: "12.6.2", why: "We track open security findings from scans over sprints — so you know remediation is keeping up with new code." },
        { id: "12.6.3", why: "We watch how long jobs sit in build queues — long waits slow every release even when pipelines succeed." }
      ]}
    ]
  },
  "13": {
    outcomes: [
      "Make sure your monitoring tools are working properly — if they break, you're blind.",
      "Know when Splunk indexers, forwarders, or searches have problems.",
      "Track AI and LLM usage, cost, and security."
    ],
    areas: [
      { name: "Splunk platform health", description: "Are your Splunk indexers, forwarders, and search heads healthy? We watch the tool that watches everything else.", ucs: [
        { id: "13.1.1", why: "Detect when indexer queues are filling up — data ingestion is falling behind." },
        { id: "13.1.3", why: "Know when forwarders lose connection — you stop getting data from those sources." },
        { id: "13.1.4", why: "Track daily license usage so you don't hit your limit unexpectedly." }
      ]},
      { name: "Splunk ITSI (premium)", description: "IT Service Intelligence — service health scores, KPIs, and intelligent alerting.", ucs: [
        { id: "13.2.1", why: "Watch service health scores across your IT estate — the big-picture view." },
        { id: "13.2.2", why: "Get alerted when a key performance indicator starts degrading before it breaches." },
        { id: "13.2.3", why: "Track incident episodes and mean time to resolve across your services." }
      ]},
      { name: "Third-party monitoring", description: "Prometheus, Nagios, Grafana, PagerDuty, and ThousandEyes. We bring external monitoring data into one place.", ucs: [
        { id: "13.3.1", why: "Pull alerts from Nagios or Zabbix into Splunk alongside everything else." },
        { id: "13.3.2", why: "Ingest Prometheus metrics so you can correlate them with logs and events." },
        { id: "13.3.5", why: "Detect alert storms — too many alerts firing at once, often from a single root cause." }
      ]},
      { name: "AI & LLM observability", description: "Large language model usage, cost, GPU utilisation, and security. We help you run AI responsibly.", ucs: [
        { id: "13.4.1", why: "Track LLM API speed and errors — slow or failing AI calls break user-facing features." },
        { id: "13.4.2", why: "See how many tokens each application uses and what it costs — AI spending can spike fast." },
        { id: "13.4.9", why: "Detect prompt injection attempts — attackers try to trick AI into doing harmful things." }
      ]},
      { name: "ML-powered platform intelligence", description: "We use machine learning to predict problems before they happen — license overages, queue bottlenecks, and service slowdowns that basic alerts miss.", ucs: [
        { id: "13.1.46", why: "We watch every data source for sudden silence — if a source stops sending data, we catch it within minutes instead of hours." },
        { id: "13.1.47", why: "We forecast your Splunk license usage 30 days ahead, so you know before you hit your limit." },
        { id: "13.1.51", why: "We combine multiple service health signals to predict SLO breaches before any single metric looks bad on its own." }
      ]},
      { name: "ITSI machine learning extensions", description: "Advanced AI for IT Service Intelligence — entity-level anomaly detection and automated root-cause analysis.", ucs: [
        { id: "13.2.37", why: "We watch each server for subtle, correlated changes across CPU, memory, and response time that individually look fine but together signal trouble." },
        { id: "13.2.38", why: "When a service degrades, we automatically identify which specific component is causing the problem — saving minutes of manual investigation." }
      ]},
      { name: "Deep learning & model health", description: "Advanced neural network detections and monitoring that your deployed AI models stay accurate over time.", ucs: [
        { id: "13.4.13", why: "We train AI to read your log files and flag lines that look 'wrong' — catching problems no rule was written for." },
        { id: "13.4.14", why: "We turn server metrics into a picture and use image recognition AI to spot complex failure patterns across many metrics at once." },
        { id: "13.4.15", why: "We track the accuracy of all deployed ML models — so you know when a model needs retraining before its detections go stale." }
      ]},
      { name: "OpenTelemetry & observability pipelines", description: "The data collection infrastructure that feeds your monitoring. We make sure telemetry flows reliably from every service.", ucs: [
        { id: "13.3.15", why: "We watch the data pipeline that carries your traces and metrics — if it backs up, you lose visibility right when you need it most." },
        { id: "13.5.3", why: "We check that every service's traces are complete — broken traces mean you can't follow a request from start to finish." },
        { id: "13.5.19", why: "We detect when a new metric label creates millions of data points overnight — catching cost explosions before your bill arrives." }
      ]},
      { name: "Distributed tracing & APM", description: "Follow every user request across all your services. We find slow transactions, errors, and broken connections.", ucs: [
        { id: "13.5.1", why: "We catch when a service gets slower after a deployment — before enough users complain to reach support." },
        { id: "13.5.2", why: "We track error rates by service and operation — so each team sees exactly where their failures are." },
        { id: "13.5.8", why: "We find the slow database queries that make your services laggy — bridging the gap between app and database teams." }
      ]},
      { name: "Real user & synthetic monitoring", description: "How fast your website loads for real users and automated tests. We catch performance regressions before they hurt SEO and conversions.", ucs: [
        { id: "13.5.9", why: "We track Google's Core Web Vitals for your pages — poor scores mean lower search rankings and frustrated users." },
        { id: "13.5.10", why: "We detect JavaScript errors hitting your users — crashes and broken features that backend monitoring can't see." },
        { id: "13.5.11", why: "We run automated multi-step tests of your critical user journeys from multiple locations around the world." }
      ]},
      { name: "SRE patterns & SLOs", description: "Site Reliability Engineering frameworks — error budgets, golden signals, and service level objectives that balance speed with reliability.", ucs: [
        { id: "13.5.16", why: "We alert you when you're burning through your error budget too fast — before a minor issue becomes a breach of your reliability commitment." },
        { id: "13.5.17", why: "We track error budget consumption per service — when it's exhausted, the team focuses on reliability instead of new features." },
        { id: "13.5.15", why: "We combine latency, traffic, errors, and saturation into a single health score per service — instantly showing which services need attention." }
      ]}
    ]
  },
  "14": {
    outcomes: [
      "See when sensors, controllers, or building systems have problems.",
      "Get alerted when temperatures, vibrations, or pressures are outside safe ranges.",
      "Track industrial protocol health and detect suspicious activity in your OT network."
    ],
    areas: [
      { name: "Building management & smart buildings", description: "HVAC efficiency, energy management, elevators, fire safety, water systems, lighting, parking, and indoor air quality. We help you run comfortable, efficient, and sustainable buildings.", ucs: [
        { id: "14.1.27", why: "We track chiller plant efficiency — chillers use 30-50% of building energy, so even small improvements save thousands." },
        { id: "14.1.37", why: "We detect elevator door faults weeks before failure — preventing passenger entrapments and emergency calls." },
        { id: "14.1.42", why: "We centralise fire alarm panel events across all buildings — so trouble conditions get resolved before they compromise safety." }
      ]},
      { name: "Industrial control systems", description: "SCADA, PLCs, and safety systems. We watch for anomalies, unauthorised access, and protocol violations.", ucs: [
        { id: "14.2.1", why: "Monitor PLC and RTU health — these controllers run your physical processes." },
        { id: "14.2.3", why: "Track safety system activations — every activation is a potential incident." },
        { id: "14.2.6", why: "Detect unauthorised access to industrial control systems — a serious safety and security risk." }
      ]},
      { name: "Splunk Edge Hub", description: "Edge sensors for temperature, vibration, air quality, and sound. We collect and analyse data right at the source.", ucs: [
        { id: "14.3.1", why: "Detect temperature anomalies from edge sensors — early warning for equipment or environment problems." },
        { id: "14.3.2", why: "Monitor vibration on machinery — changes in vibration patterns predict mechanical failures." },
        { id: "14.3.7", why: "Watch the data pipeline from edge to cloud — if it breaks, you lose visibility." }
      ]},
      { name: "IoT sensors & platforms", description: "Smart sensors, asset trackers, and IoT fleet health. We make sure your devices are connected and reporting.", ucs: [
        { id: "14.4.1", why: "Check the health of your sensor fleet — are all devices connected and reporting?" },
        { id: "14.4.6", why: "Spot devices that haven't reported in — they might be offline or malfunctioning." },
        { id: "14.4.5", why: "Track firmware versions across your IoT fleet — outdated firmware is a security risk." }
      ]},
      { name: "Industrial protocols", description: "MQTT, OPC-UA, Modbus, and other industrial protocols. We watch message flow, connections, and security.", ucs: [
        { id: "14.5.1", why: "Track MQTT message rates and subscriptions — drops mean sensors aren't reporting." },
        { id: "14.5.2", why: "Monitor OPC-UA server connections — when they fail, data from industrial equipment stops flowing." },
        { id: "14.5.11", why: "Catch MQTT authentication failures — someone or something is trying to connect without permission." }
      ]},
      { name: "Deep protocol inspection", description: "Zeek-based deep inspection of ICS protocols — S7comm, Modbus, DNP3, BACnet, and more.", ucs: [
        { id: "14.6.1", why: "Track PLC read and write operations — unusual patterns could indicate tampering." },
        { id: "14.6.5", why: "Audit Modbus function codes — some codes should rarely appear in normal operations." },
        { id: "14.6.20", why: "Detect unknown protocols on your OT network — they should not be there." }
      ]},
      { name: "Litmus Edge industrial IoT gateway", description: "We monitor Litmus Edge gateways that connect factory PLCs and sensors to your data platform. We watch connectivity, data pipelines, and fleet health across sites.", ucs: [
        { id: "14.7.1", why: "We check that every Litmus Edge gateway is connected and reporting — if it drops off, you lose visibility into that part of the factory." },
        { id: "14.7.4", why: "We audit whether all expected sensor readings are arriving — missing data means dashboards and alarms go blind." },
        { id: "14.7.7", why: "We track the health of your entire Litmus Edge fleet across sites — so one failing gateway does not go unnoticed." }
      ]},
      { name: "IoT & OT trending", description: "We watch plant and fleet metrics over weeks and months — who is online, data quality, equipment effectiveness, and maintenance signals.", ucs: [
        { id: "14.8.1", why: "We track what share of your devices are reporting — drops warn you before you lose visibility on the plant floor." },
        { id: "14.8.2", why: "We trend bad or missing sensor readings — so data quality problems are fixed before dashboards and alarms go blind." },
        { id: "14.8.3", why: "We watch overall equipment effectiveness over time — to see whether maintenance and changeovers really improve output." }
      ]},
      { name: "OT network security (Cyber Vision / Nozomi)", description: "We detect threats, rogue devices, and unauthorized changes in your industrial network — using deep packet inspection of OT protocols from Cisco Cyber Vision or Nozomi Networks Guardian.", ucs: [
        { id: "14.9.2", why: "We alert you when a new device appears on your industrial network — it could be a rogue device or an attacker's tool." },
        { id: "14.9.7", why: "We detect when someone downloads new logic to a PLC — unauthorized program changes can alter physical processes with safety consequences." },
        { id: "14.9.3", why: "We track known vulnerabilities on your OT assets — so you can prioritise patching before attackers exploit them." }
      ]}
    ]
  },
  "15": {
    outcomes: [
      "Know when power, cooling, or physical security in your data center has problems.",
      "Get early warning for temperature spikes, battery failures, and water leaks.",
      "Track who enters your data center and when."
    ],
    areas: [
      { name: "Power & UPS", description: "Uninterruptible power supplies, generators, and power distribution. We make sure your data center stays powered.", ucs: [
        { id: "15.1.1", why: "Monitor UPS battery health — when power fails, batteries keep everything running until generators start." },
        { id: "15.1.3", why: "Check that power redundancy is in place — losing a feed shouldn't cause an outage." },
        { id: "15.1.5", why: "Track Power Usage Effectiveness (PUE) — how efficiently your data center uses energy." }
      ]},
      { name: "Cooling & environment", description: "Temperature, humidity, and cooling systems. We help you prevent overheating and environmental damage.", ucs: [
        { id: "15.2.1", why: "Monitor temperatures zone by zone — catch hot spots before equipment overheats." },
        { id: "15.2.5", why: "Detect water leaks immediately — water near electrical equipment is an emergency." },
        { id: "15.2.3", why: "Track cooling unit health — if a CRAC unit fails, temperatures will rise fast." }
      ]},
      { name: "Physical security", description: "Badge access, cameras, and cabinet intrusions. We audit who enters and flag anything unusual.", ucs: [
        { id: "15.3.1", why: "Full audit of badge swipes — who entered which room and when." },
        { id: "15.3.2", why: "Alert when someone accesses the data center outside of business hours." },
        { id: "15.3.4", why: "Monitor camera system health — if cameras go offline, you lose visibility." }
      ]},
      { name: "Indoor location & building intelligence", description: "People movement, space engagement, and environmental response. We help you understand how your buildings are really used.", ucs: [
        { id: "15.3.38", why: "We track how people move through your building — finding traffic bottlenecks and optimising layouts." },
        { id: "15.3.39", why: "We measure how much time people spend in different areas — showing which spaces are popular and which are ignored." },
        { id: "15.3.40", why: "We check that heating and cooling respond properly when sensors detect problems — catching automation failures." }
      ]}
    ]
  },
  "16": {
    outcomes: [
      "Know if incidents are being resolved within agreed timeframes.",
      "See when changes cause problems and catch unapproved changes.",
      "Keep your asset database accurate and up to date."
    ],
    areas: [
      { name: "Incidents & tickets", description: "Service desk metrics — ticket volumes, SLA compliance, and resolution times.", ucs: [
        { id: "16.1.1", why: "Track incident volume trends — spot spikes early and allocate resources." },
        { id: "16.1.2", why: "Monitor SLA compliance — are tickets being resolved within agreed timeframes?" },
        { id: "16.1.3", why: "Measure mean time to resolve by category — find which areas take longest to fix." }
      ]},
      { name: "Configuration & assets", description: "Your CMDB — asset inventory, data quality, and relationship integrity.", ucs: [
        { id: "16.2.1", why: "Score CMDB data quality — inaccurate asset records lead to wrong decisions." },
        { id: "16.2.3", why: "Find orphaned assets in your CMDB that no longer match real infrastructure." },
        { id: "16.2.5", why: "Discover shadow IT — systems running that aren't in your official inventory." }
      ]},
      { name: "Business services", description: "End-to-end service availability, first-contact resolution, and major incident tracking.", ucs: [
        { id: "16.3.1", why: "Calculate business process health by combining health data from multiple services." },
        { id: "16.3.10", why: "Track business service availability across all supporting components." },
        { id: "16.3.6", why: "Make sure post-mortem reviews happen after major incidents — learn from every failure." }
      ]},
      { name: "Change & release", description: "Change management — approvals, success rates, and the link between changes and incidents.", ucs: [
        { id: "16.4.1", why: "Detect unauthorised changes — changes made without approval are a top cause of outages." },
        { id: "16.4.3", why: "Correlate failed changes with incident spikes — did a change cause the outage?" },
        { id: "16.4.4", why: "Track release deployment success rates — failed releases mean delayed features and more risk." }
      ]},
      { name: "ITSM trending", description: "We watch service desk and change metrics over time — backlogs, success rates, knowledge use, resolution speed, and escalations.", ucs: [
        { id: "16.5.1", why: "We track how long work sits in the queue by age — growing older backlogs warn you before customers feel the pain." },
        { id: "16.5.2", why: "We trend how often changes finish successfully — a falling rate means your change process or testing needs attention." },
        { id: "16.5.3", why: "We measure how often people solve issues with self-service knowledge — so you see whether help articles really reduce ticket load." }
      ]}
    ]
  },
  "17": {
    outcomes: [
      "See who connects to your network and whether their device is compliant.",
      "Know when VPN tunnels have problems or someone logs in from an unusual location.",
      "Track your progress toward Zero Trust — device trust, micro-segmentation, and conditional access."
    ],
    areas: [
      { name: "Network access control", description: "Who and what is allowed on your network. We track authentication, compliance posture, and rogue devices.", ucs: [
        { id: "17.1.2", why: "See which devices fail endpoint compliance checks — they might be vulnerable or unmanaged." },
        { id: "17.1.12", why: "Detect rogue devices connecting to your network — unknown devices are a risk." },
        { id: "17.1.4", why: "Track guest network usage — is the guest network being abused?" }
      ]},
      { name: "VPN & remote access", description: "VPN tunnels, remote sessions, and geographical anomalies. We help you secure remote work.", ucs: [
        { id: "17.2.2", why: "Track VPN authentication failures — rising rates could mean a credential attack." },
        { id: "17.2.3", why: "Spot VPN logins from unusual countries or regions." },
        { id: "17.2.5", why: "Monitor VPN tunnel stability — frequent drops degrade the remote work experience." }
      ]},
      { name: "Zero Trust & SASE", description: "Conditional access, device trust, and micro-segmentation — including Zscaler, Palo Alto Prisma, and Cato Networks. We help you verify every connection.", ucs: [
        { id: "17.3.1", why: "Track conditional access enforcement — are the right policies being applied?" },
        { id: "17.3.25", why: "Monitor Cato Networks cloud security events — IPS, anti-malware, and firewall all in one." },
        { id: "17.3.29", why: "Track Cato SD-WAN tunnel health — when a tunnel drops, the entire site loses connectivity." }
      ]}
    ]
  },
  "18": {
    outcomes: [
      "See the health of your data center network fabric — ACI, NSX, or SDN.",
      "Know when network policies aren't being enforced or segments aren't properly isolated.",
      "Track fabric faults and controller health."
    ],
    areas: [
      { name: "Cisco ACI", description: "Application Centric Infrastructure — fabric health, policy enforcement, and controller (APIC) status.", ucs: [
        { id: "18.1.1", why: "Track the overall fabric health score — a single number that shows if the network is healthy." },
        { id: "18.1.4", why: "See which security policies are being hit or missed — are your rules working?" },
        { id: "18.1.7", why: "Monitor the APIC controllers — if they go down, you can't manage the fabric." }
      ]},
      { name: "VMware NSX", description: "NSX distributed firewall, micro-segmentation, and overlay network health.", ucs: [
        { id: "18.2.1", why: "Track distributed firewall rule hits — see how traffic is being filtered between VMs." },
        { id: "18.2.2", why: "Audit micro-segmentation enforcement — is isolation working as intended?" },
        { id: "18.2.5", why: "Monitor transport node connectivity — when it breaks, virtual network communication fails." }
      ]},
      { name: "SDN & overlay networks", description: "VXLAN tunnels, EVPN routing, and SDN controllers. We watch the virtual plumbing of your network.", ucs: [
        { id: "18.3.4", why: "Monitor VXLAN tunnel health — broken tunnels mean VMs can't communicate across hosts." },
        { id: "18.3.3", why: "Track SDN controller health — it's the brain of your software-defined network." },
        { id: "18.3.5", why: "Watch EVPN routing events — MAC mobility and route changes can indicate problems." }
      ]},
      { name: "Nexus Dashboard & NX-OS fabric", description: "Cisco's management platform for data center switches. We monitor anomalies, compliance, and network health.", ucs: [
        { id: "18.4.1", why: "See anomalies detected by Cisco's AI-driven network insights — problems found before users notice." },
        { id: "18.4.2", why: "Know when switch configurations drift from the intended design — drift causes outages." },
        { id: "18.4.5", why: "Monitor the routing backbone of your data center fabric — if it breaks, everything breaks." }
      ]}
    ]
  },
  "19": {
    outcomes: [
      "See the health of your physical compute hardware and hyper-converged clusters.",
      "Know when disks fail, nodes are unbalanced, or firmware falls out of compliance.",
      "Track storage and compute capacity across your HCI environment."
    ],
    areas: [
      { name: "Cisco UCS", description: "Blade servers, service profiles, and fabric interconnects. We watch hardware health and compliance.", ucs: [
        { id: "19.1.1", why: "Monitor blade and rack server health — catch hardware faults early." },
        { id: "19.1.2", why: "Track service profile compliance — misconfigured profiles can cause unexpected behaviour." },
        { id: "19.1.3", why: "Check firmware compliance across your UCS fleet — mixed versions cause interop issues." }
      ]},
      { name: "Cisco Intersight", description: "Cloud-based server management. We track alarms, firmware, warranties, and configuration changes across your entire compute fleet.", ucs: [
        { id: "19.1.19", why: "See all server alarms in one place — faster response to hardware problems." },
        { id: "19.1.20", why: "Know which servers have outdated firmware — a common cause of unexpected failures." },
        { id: "19.1.24", why: "Get warned before support contracts expire — no coverage means slower repairs." }
      ]},
      { name: "Hyper-converged infrastructure", description: "Nutanix, vSAN, VxRail, and similar. We track cluster health, storage capacity, and node balance.", ucs: [
        { id: "19.2.1", why: "Watch overall cluster health — a degraded cluster puts workloads at risk." },
        { id: "19.2.5", why: "Get alerted when a disk fails so it can be replaced before data is lost." },
        { id: "19.2.2", why: "Track storage pool capacity — running out of storage stops everything." }
      ]},
      { name: "Azure Stack HCI", description: "Microsoft on-premises hyper-converged clusters. We watch cluster health, storage pools, updates, and cloud connection so virtual machines stay available.", ucs: [
        { id: "19.3.1", why: "Catch cluster validation or quorum problems early — they can block live migration when you need it most." },
        { id: "19.3.2", why: "See when storage pools are full or cache tiers are out of balance — slow storage affects every virtual machine." },
        { id: "19.3.4", why: "Know when Azure Arc stops reporting — without it, patching and policy may not reach your servers." }
      ]}
    ]
  },
  "20": {
    outcomes: [
      "See how much you're spending on cloud and where the money goes.",
      "Know when you're about to run out of capacity — servers, storage, or network.",
      "Track software license usage so you don't overpay or fall out of compliance."
    ],
    areas: [
      { name: "Cloud spending", description: "Daily cloud costs, budget alerts, and waste identification across AWS, Azure, and Google Cloud.", ucs: [
        { id: "20.1.2", why: "Detect unusual spikes in cloud spending before the bill arrives." },
        { id: "20.1.4", why: "Find idle cloud resources you're paying for but not using." },
        { id: "20.1.6", why: "See how costs break down by team — hold the right people accountable." }
      ]},
      { name: "Capacity planning", description: "Forecasting when you'll need more compute, storage, or bandwidth.", ucs: [
        { id: "20.2.1", why: "Predict when you'll run out of compute capacity so you can plan ahead." },
        { id: "20.2.2", why: "Forecast storage growth — will you have enough space in 30, 60, or 90 days?" },
        { id: "20.2.5", why: "Get right-sizing recommendations — find over-provisioned resources wasting money." }
      ]},
      { name: "Licenses & subscriptions", description: "Software license usage, renewal tracking, and compliance reporting.", ucs: [
        { id: "20.3.1", why: "Compare assigned vs active SaaS licenses — you may be paying for seats nobody uses." },
        { id: "20.3.4", why: "Catch license compliance gaps before a software audit finds them." },
        { id: "20.3.3", why: "Track subscription renewals so nothing lapses unexpectedly." }
      ]}
    ]
  },
  "21": {
    outcomes: [
      "Get monitoring tailored to your specific industry — energy, healthcare, manufacturing, transport, and more.",
      "See operational metrics that matter to your business, not just generic IT numbers.",
      "Track compliance with industry-specific regulations."
    ],
    areas: [
      { name: "Energy & utilities", description: "Power grids, substations, smart meters, and renewable energy. We help utilities keep the lights on.", ucs: [
        { id: "21.1.1", why: "Monitor SCADA alarm rates — alarm flooding makes it hard for operators to spot real problems." },
        { id: "21.1.2", why: "Detect when remote terminal units in substations stop communicating." },
        { id: "21.1.5", why: "Compare actual renewable energy output to forecast — gaps affect grid stability and revenue." }
      ]},
      { name: "Manufacturing", description: "OEE, production yields, predictive maintenance, and supply chain. We help keep the factory floor running.", ucs: [
        { id: "21.2.1", why: "Calculate Overall Equipment Effectiveness — the gold standard for production efficiency." },
        { id: "21.2.2", why: "Correlate unplanned downtime with root causes so you can prevent recurrence." },
        { id: "21.2.5", why: "Detect vibration changes in machinery before they lead to breakdowns." }
      ]},
      { name: "Healthcare & DIPS Arena", description: "Clinical systems, cold chain compliance, patient flow, and DIPS Arena EHR monitoring for Norwegian hospitals. We help healthcare organisations deliver care reliably.", ucs: [
        { id: "21.3.1", why: "Monitor EHR response times — slow clinical systems waste clinician time and delay care." },
        { id: "21.3.18", why: "Track DIPS Arena application performance — Norway's dominant hospital system serving 4.3 million patients." },
        { id: "21.3.22", why: "Watch DIPS Communicator message delivery — failed health messages can delay lab results and referrals." }
      ]},
      { name: "Transport & logistics", description: "Fleet tracking, delivery SLAs, and cargo monitoring. We help logistics operations run on time.", ucs: [
        { id: "21.4.1", why: "Track fleet vehicle locations and trigger alerts when they leave permitted zones." },
        { id: "21.4.9", why: "Monitor last-mile delivery SLA compliance — are deliveries arriving on time?" },
        { id: "21.4.10", why: "Detect temperature excursions for perishable goods during transport." }
      ]},
      { name: "Oil, gas & mining", description: "Pipeline monitoring, wellhead telemetry, and emissions tracking. Safety-critical operations.", ucs: [
        { id: "21.5.1", why: "Detect pipeline pressure and flow anomalies — early warning for leaks or blockages." },
        { id: "21.5.4", why: "Correlate flare stack events with emissions data — regulatory and environmental reporting." },
        { id: "21.5.8", why: "Analyse safety system trips to find recurring causes and improve safety." }
      ]},
      { name: "Retail & e-commerce", description: "POS terminals, e-commerce performance, and in-store systems. We help retail keep selling.", ucs: [
        { id: "21.6.1", why: "Monitor POS terminal response times — slow checkouts frustrate customers." },
        { id: "21.6.6", why: "Track e-commerce checkout funnel performance — delays here lose sales." },
        { id: "21.6.3", why: "Monitor in-store network health — if WiFi goes down, many retail systems break." }
      ]},
      { name: "Aviation & airports", description: "Baggage systems, gate allocation, and passenger flow. We help airports run smoothly.", ucs: [
        { id: "21.7.1", why: "Track baggage handling throughput and catch misroutes — lost bags cost money and trust." },
        { id: "21.7.3", why: "Monitor aircraft turnaround times — delays cascade through the entire schedule." },
        { id: "21.7.9", why: "Track passenger flow and terminal capacity to reduce congestion." }
      ]},
      { name: "Telecom operations", description: "Cell sites, core network elements, and subscriber provisioning. We help telcos keep networks running.", ucs: [
        { id: "21.8.1", why: "Monitor RAN cell site availability — outages directly affect subscribers." },
        { id: "21.8.3", why: "Track subscriber provisioning completion rates — failures mean customers can't use their service." },
        { id: "21.8.8", why: "Watch 5G gNodeB performance — the foundation of next-generation mobile services." }
      ]},
      { name: "Water & wastewater", description: "Treatment plants, pump stations, and water quality. Safety-critical utility monitoring.", ucs: [
        { id: "21.9.1", why: "Monitor treatment process parameters — deviations can affect water safety." },
        { id: "21.9.4", why: "Detect early warning signs of sewer overflows — a public health and environmental risk." },
        { id: "21.9.7", why: "Track water loss and non-revenue water — leaks cost money and waste resources." }
      ]},
      { name: "Insurance & claims", description: "Claims processing, fraud detection, and workload management.", ucs: [
        { id: "21.10.1", why: "Track claims processing cycle times — slow processing frustrates policyholders." },
        { id: "21.10.6", why: "Detect fraud rings — patterns of coordinated fraudulent claims." },
        { id: "21.10.3", why: "Balance adjuster workloads so no one is overwhelmed and claims are handled fairly." }
      ]}
    ]
  },
  "22": {
    outcomes: [
      "We monitor compliance with 30+ regulations across GDPR, HIPAA, PCI DSS, NERC CIP, NIST, SOX, DORA, NIS2, and regional frameworks worldwide.",
      "We automatically collect and organise evidence for auditors, assessors, and regulators — saving weeks of manual preparation.",
      "We spot compliance gaps, missed deadlines, and control failures before regulators or auditors find them.",
      "We cover sector-specific requirements for healthcare, finance, energy, critical infrastructure, and government — each with regulation-specific monitoring."
    ],
    areas: [
      { name: "GDPR compliance", description: "EU General Data Protection Regulation — personal data detection, breach notification, data subject rights, processor oversight, DPIA tracking, consent enforcement, international transfers, and privacy-by-design evidence across all key GDPR articles.", whatItIs: "The EU privacy law that protects personal data about anyone in Europe. It sets rules for how companies collect, store, share, and delete that data — and gives people the right to see, correct, or remove what is held about them.", whoItAffects: "Any organisation that holds or processes personal data about people in the EU or EEA, no matter where the organisation itself is based. Small businesses are covered too, not just large enterprises.", splunkValue: "We watch where personal data lives, detect breaches that trigger the 72-hour notification clock, capture evidence that access / deletion / portability requests were handled on time, and flag cross-border transfers that lack a current legal agreement — so an EU DPA can be answered with live data, not PowerPoint.", primer: "docs/regulatory-primer.md#41-gdpr--general-data-protection-regulation-eueea--t1", evidencePack: "docs/evidence-packs/gdpr.md", ucs: [
        { id: "22.1.7", why: "We monitor encryption and pseudonymisation of systems processing personal data — Article 32 requires appropriate security measures." },
        { id: "22.1.11", why: "We verify that personal data is actually deleted after an erasure request — catching incomplete right-to-be-forgotten execution." },
        { id: "22.1.30", why: "We detect unauthorised cloud services processing personal data — shadow IT that bypasses your GDPR controls." }
      ]},
      { name: "UK GDPR", description: "UK General Data Protection Regulation — the post-Brexit UK version of GDPR. Inherits the full GDPR clause set with UK-specific adjustments for ICO notification, national security exemptions, and UK Data Protection Act 2018 interaction.", whatItIs: "The UK's own version of GDPR, kept almost identical to the EU rules but enforced by the UK Information Commissioner's Office (ICO) instead of European regulators. It applies whether you are in the UK or outside it.", whoItAffects: "Any organisation holding personal data about people in the UK. After Brexit, UK operations handling UK residents' data rely on this law even if they previously only prepared for EU GDPR.", splunkValue: "Because UK GDPR inherits GDPR's clauses, the same catalogue detections apply — we re-badge the evidence so an ICO audit sees UK-specific coverage, and we flag UK-only gaps such as ICO 72-hour breach notification routing.", primer: "docs/regulatory-primer.md#42-uk-gdpr--uk-general-data-protection-regulation-uk--t2--derivative", evidencePack: "docs/evidence-packs/uk-gdpr.md", ucs: [
        { id: "22.1.7", why: "Inherited from GDPR Art.32 — encryption of personal data systems satisfies the UK ICO security obligation." },
        { id: "22.1.11", why: "Inherited deletion-verification coverage — UK residents have the same right to erasure as EU residents." },
        { id: "22.1.30", why: "Inherited shadow-IT detection — unsanctioned UK data flows surface even though the UK is now a third country for EU transfers." }
      ]},
      { name: "CCPA privacy", description: "California Consumer Privacy Act — consumer data requests, opt-out tracking, sensitive PI categories, automated decision profiling, dark pattern detection, and sale-of-data monitoring.", whatItIs: "California's privacy law that gives residents the right to see what personal data is held about them, delete it, correct it, and opt out of its sale or sharing. CPRA extended CCPA with stricter rules for sensitive personal information.", whoItAffects: "Businesses that sell to California residents and meet any of these: annual revenue over USD 25M, personal data on 100k+ Californians, or 50 %+ revenue from selling or sharing personal data.", splunkValue: "We track consumer request response times, watch opt-out signal propagation across marketing and analytics, detect dark-pattern consent designs, and catch sales of data that happened without the opt-out being honoured.", ucs: [
        { id: "22.4.1", why: "We track CCPA consumer data requests — access and deletion requests must be handled on time." },
        { id: "22.4.12", why: "We monitor automated decision-making systems for bias and profiling — consumers have the right to opt out." },
        { id: "22.4.20", why: "We detect dark pattern designs in consent flows — deceptive UI that undermines genuine consumer choice." }
      ]},
      { name: "NIS2 compliance", description: "EU NIS2 directive — incident reporting timelines, supply chain risk, encryption monitoring, MFA enforcement, training tracking, OT-specific requirements, and board-level governance evidence.", whatItIs: "The EU's updated cybersecurity law for important and essential service providers. It raises the bar on risk management, incident reporting, and personal board-member accountability for cyber governance.", whoItAffects: "Operators in 18 sectors including energy, transport, banking, healthcare, water, digital infrastructure, public administration, and cloud / data-centre providers in the EU. Medium and large entities are automatically in scope.", splunkValue: "We start the 24-hour early-warning clock the moment an incident is detected, capture supply-chain risk telemetry, evidence MFA and patching compliance, and produce board-level dashboards that demonstrate the Article 21 risk-management measures are working.", primer: "docs/regulatory-primer.md#410-nis2--network-and-information-security-directive-2-eu--t1", evidencePack: "docs/evidence-packs/nis2.md", ucs: [
        { id: "22.2.1", why: "We track NIS2 incident detection and 24-hour early warning reporting obligations." },
        { id: "22.2.9", why: "We dashboard the effectiveness of all cybersecurity measures — MFA, patching, backups, training — as Article 21 requires." },
        { id: "22.2.35", why: "We validate OT network segmentation for essential entities — industrial control systems have specific NIS2 requirements." }
      ]},
      { name: "ISO 27001:2022", description: "International information-security management system standard. Annex A.5 / A.6 / A.7 / A.8 controls across organisational, people, physical, and technological domains, with continuous monitoring and improvement evidence.", whatItIs: "The world's most widely recognised information-security management standard. An accredited auditor checks that the organisation has a working security programme — not just written policies — and awards certification every three years with yearly surveillance audits.", whoItAffects: "Any organisation seeking a recognised ISMS certification to demonstrate security maturity to customers, regulators, and insurers. Common in technology, finance, healthcare, and public-sector procurement bids.", splunkValue: "We give the ISMS owner live evidence that Annex A controls are operating — access reviews, log monitoring, backups, change management, supplier risk, and incident response — so surveillance audits become a data pull rather than a month-long evidence hunt.", primer: "docs/regulatory-primer.md#47-iso-270012022--information-security-management-system-global--t1", evidencePack: "docs/evidence-packs/iso-27001.md", ucs: [
        { id: "22.6.1", why: "We monitor how well your ISO 27001 security controls are working across the board." },
        { id: "22.6.20", why: "We track Annex A.8 technological controls — privileged access, logging, network segmentation, and cryptography." },
        { id: "22.6.7", why: "We capture evidence for Annex A.5 organisational controls — policies, roles, asset ownership, and supplier agreements." }
      ]},
      { name: "NIST CSF 2.0", description: "NIST Cybersecurity Framework 2.0 — six functions (Govern, Identify, Protect, Detect, Respond, Recover) with the new Govern function covering oversight, strategy, and supply-chain risk.", whatItIs: "A voluntary framework from the US National Institute of Standards and Technology that helps organisations describe and improve their cybersecurity posture. Version 2.0 added a dedicated Govern function and explicit cyber supply-chain risk management.", whoItAffects: "Any organisation that needs a common language to describe cyber risk and capability maturity — widely adopted in the US private sector, by US federal agencies (alongside 800-53), and increasingly in EU and APAC procurement questionnaires.", splunkValue: "We produce maturity scores for each CSF function and category, highlight the weakest sub-categories, and generate evidence packs the CISO can show the board — aligning cyber investment to the function that needs it most.", primer: "docs/regulatory-primer.md#48-nist-csf-20--cybersecurity-framework-us--global--t1", evidencePack: "docs/evidence-packs/nist-csf.md", ucs: [
        { id: "22.7.1", why: "We dashboard your NIST CSF maturity across all six functions — including the new Govern function." },
        { id: "22.7.12", why: "We score GV.SC-* supply-chain categories — the single biggest v2.0 addition for third-party risk." },
        { id: "22.7.20", why: "We track Detect → Respond → Recover throughput so board reports show actual response muscle, not theoretical capability." }
      ]},
      { name: "DORA digital resilience", description: "EU Digital Operational Resilience Act for financial services — ICT risk management, incident reporting, third-party oversight, TLPT testing, concentration risk, information sharing, and exit strategies.", whatItIs: "The EU's single rulebook for operational resilience in the financial sector. It consolidates scattered ICT requirements into one regulation covering risk management, incident reporting, testing, third-party oversight, and information-sharing arrangements.", whoItAffects: "All EU regulated financial entities — banks, insurers, investment firms, crypto-asset service providers, payment institutions — plus the critical ICT third parties they depend on.", splunkValue: "We classify incidents against DORA's seven major-incident criteria to trigger the 4-hour clock, track TLPT lifecycle evidence, measure concentration risk across cloud and critical ICT providers, and evidence the 2-hour major-incident initial report with timestamps.", primer: "docs/regulatory-primer.md#411-dora--digital-operational-resilience-act-eu--t1", evidencePack: "docs/evidence-packs/dora.md", ucs: [
        { id: "22.3.11", why: "We automatically classify incidents as major using DORA's seven criteria — triggering the 4-hour reporting deadline." },
        { id: "22.3.25", why: "We track threat-led penetration testing (TLPT) lifecycle — from scoping through execution to remediation evidence." },
        { id: "22.3.21", why: "We monitor ICT concentration risk — how dependent you are on a single cloud or service provider." }
      ]},
      { name: "MiFID II", description: "EU Markets in Financial Instruments Directive II — algorithmic trading controls, best execution, market abuse detection, transaction reporting, and record-keeping for regulated trading activity.", whatItIs: "The EU regulation governing investment firms, trading venues, and market infrastructure. It mandates detailed transaction reporting, best execution proof, market-abuse surveillance, and strict algorithmic-trading risk controls.", whoItAffects: "Investment firms and trading venues authorised to operate in the EU, plus algorithmic traders and high-frequency-trading participants.", splunkValue: "We monitor trade-reporting completeness and latency, detect circuit-breaker events and algo kill-switch activations, and correlate order-flow anomalies against market-abuse patterns — the evidence ESMA and national competent authorities ask for on inspection.", ucs: [
        { id: "22.5.1", why: "We monitor MiFID II trade reporting completeness — missing reports mean regulatory fines." },
        { id: "22.5.10", why: "We detect algorithmic trading circuit breaker events — required controls to prevent market disruption." },
        { id: "22.5.14", why: "We watch pre-trade and post-trade controls firing rates so algo-trading risk remains within policy." }
      ]},
      { name: "SOC 2", description: "AICPA SOC 2 Trust Services Criteria across all CC categories plus availability, confidentiality, and processing integrity — continuous monitoring evidence for Type 1 and Type 2 attestation reports.", whatItIs: "A US attestation report issued by an independent CPA that proves a service provider has designed (Type 1) and operated (Type 2) controls around security, availability, processing integrity, confidentiality, and privacy. It is the dominant vendor-assurance report in North America.", whoItAffects: "Technology and service providers whose customers require SOC 2 — especially SaaS platforms, managed services, hosting providers, fintech, healthtech, and any B2B vendor handling customer data.", splunkValue: "We collect Type 2 evidence continuously — access reviews, change management, backup tests, incident response, vulnerability SLAs — so the auditor field-work is a query instead of an interview, and the Type 2 reporting window is fully evidenced rather than sampled.", primer: "docs/regulatory-primer.md#46-soc-2--aicpa-trust-services-criteria-us--global--t1", evidencePack: "docs/evidence-packs/soc-2.md", ucs: [
        { id: "22.8.1", why: "We continuously monitor SOC 2 trust service criteria — collecting evidence for auditors." },
        { id: "22.8.12", why: "We evidence SOC 2 logical access controls (CC6) — user provisioning, least privilege, and periodic review." },
        { id: "22.8.28", why: "We evidence Availability and Processing Integrity — backup testing, restore drills, and job-completion monitoring." }
      ]},
      { name: "HIPAA healthcare", description: "We monitor ePHI access, security safeguards, breach notification timelines, business associate oversight, and privacy rule compliance across Administrative, Technical, and Physical safeguards.", whatItIs: "The US federal law protecting Protected Health Information (PHI). Its Security Rule sets Administrative, Physical, and Technical safeguards; its Breach Notification Rule runs a 60-day clock; its Privacy Rule limits who may use or disclose PHI.", whoItAffects: "US healthcare providers, health plans, healthcare clearinghouses, and any Business Associate that handles PHI on their behalf (cloud hosters, billing firms, analytics vendors, MSPs).", splunkValue: "We detect unauthorised patient-record access (the 'snooping' pattern auditors always ask about), prove ePHI encryption at rest and in transit, start the 60-day breach clock the moment discovery happens, and produce a business-associate evidence pack on demand.", primer: "docs/regulatory-primer.md#44-hipaa-security--health-insurance-portability-and-accountability-act-security-rule-us--t1", evidencePack: "docs/evidence-packs/hipaa-security.md", ucs: [
        { id: "22.10.1", why: "We track risk analysis completion and risk management plans — the foundation of HIPAA Security Rule compliance." },
        { id: "22.10.33", why: "We detect when staff access patient records they are not treating — preventing snooping and privacy violations." },
        { id: "22.10.43", why: "We track breach discovery timelines — ensuring the 60-day notification requirement is met." }
      ]},
      { name: "PCI DSS v4.0", description: "All 12 PCI DSS v4.0 requirements — network security, secure configurations, data protection, encryption, malware defence, secure development, access control, authentication, physical security, logging, testing, and security policies.", whatItIs: "The Payment Card Industry Data Security Standard — the global rulebook card brands impose on any merchant or service provider that stores, processes, or transmits cardholder data. v4.0 strengthens authentication, logging, and customised-approach flexibility.", whoItAffects: "Any organisation that touches card data — from small merchants (SAQ) to tier-1 merchants and service providers (RoC with QSA). Non-compliance carries card-brand fines and acquirer-contract consequences.", splunkValue: "We evidence each of the 12 requirements continuously, detect PANs that slipped into logs or non-CDE systems, watch critical file integrity on the cardholder environment, and pre-populate the RoC workbook with timestamped query evidence for every control.", primer: "docs/regulatory-primer.md#43-pci-dss-v40--payment-card-industry-data-security-standard-global--t1", evidencePack: "docs/evidence-packs/pci-dss.md", ucs: [
        { id: "22.11.1", why: "We review network security controls around payment systems — so assessors see active governance of card data boundaries." },
        { id: "22.11.14", why: "We detect payment card numbers in logs — so stored data stays within retention and masking rules." },
        { id: "22.11.67", why: "We track all access to payment systems — reconstructing who did what for investigations and audits." }
      ]},
      { name: "SOX / ITGC", description: "Sarbanes-Oxley IT General Controls — logical access, change management, computer operations, financial system controls, and audit evidence for financial reporting integrity.", whatItIs: "The US federal law that makes executives of publicly listed companies personally accountable for financial reporting accuracy. IT General Controls (ITGC) are the subset of controls over the IT systems that process financial data — access, change, and operations.", whoItAffects: "US-listed public companies and their subsidiaries — and often private companies preparing for IPO. External auditors test ITGC every year under PCAOB guidance; deficiencies flow into management's Section 404 assertions.", splunkValue: "We catch privileged access to financial systems without a ticket, detect emergency changes that bypassed approval, evidence user-access reviews and termination timeliness, and produce year-end ITGC evidence packs with sample-set timestamps auditors can independently walk through.", primer: "docs/regulatory-primer.md#45-sox-itgc--sarbanes-oxley-it-general-controls-us--t1", evidencePack: "docs/evidence-packs/sox-itgc.md", ucs: [
        { id: "22.12.1", why: "We track user provisioning and deprovisioning for financial systems — access must match job responsibilities." },
        { id: "22.12.8", why: "We monitor emergency changes to production financial systems — each must be retrospectively approved." },
        { id: "22.12.22", why: "We verify financial close process controls — ensuring data integrity during period-end processing." }
      ]},
      { name: "NERC CIP power grid", description: "North American Electric Reliability Corporation Critical Infrastructure Protection — CIP-002 through CIP-014 covering BES Cyber Systems, electronic security perimeters, physical security, personnel, change management, incident reporting, and supply chain.", whatItIs: "The mandatory cybersecurity standard for North America's bulk electric system. NERC CIP requires grid operators to identify critical cyber assets, wall them off behind Electronic Security Perimeters, and prove compliance to regional entities such as WECC, RFC, and SERC.", whoItAffects: "Registered entities on the North American bulk electric system — generation operators, transmission owners, balancing authorities, reliability coordinators, and their contractors — in the US, Canada, and parts of Mexico.", splunkValue: "We evidence BES Cyber System categorisation, monitor Electronic Security Perimeter traffic for unapproved protocols, log privileged-access sessions to EMS / SCADA, and prepare the CIP-008 incident response artefacts a regional audit team expects to see.", ucs: [
        { id: "22.13.1", why: "We validate BES Cyber System categorisation — ensuring all critical assets are properly identified and classified." },
        { id: "22.13.15", why: "We monitor Electronic Security Perimeter boundaries — detecting unauthorised traffic traversal into control system networks." },
        { id: "22.13.38", why: "We track cyber security incident identification and classification — supporting CIP-008 reporting requirements." }
      ]},
      { name: "NIST 800-53", description: "Comprehensive NIST 800-53 Rev. 5 control monitoring across Audit, Access Control, Identification, System Integrity, Incident Response, Configuration, Assessment, Communications, Risk, and Contingency families.", whatItIs: "The US federal catalogue of security and privacy controls. Version Rev.5 integrates privacy, supply-chain risk, and outcome-based language; it is the underpinning control set for FedRAMP authorisations and many state and sector programmes.", whoItAffects: "US federal agencies, contractors supporting federal systems, FedRAMP cloud providers, and organisations that voluntarily adopt 800-53 as a gold-standard baseline (common in healthcare, finance, and critical infrastructure).", splunkValue: "We evidence each control family — AU-2 logging completeness, AC-2 account lifecycle, SI-4 system monitoring, CM-6 configuration compliance, and more — with per-control dashboards and tstats-backed reports suitable for a FedRAMP ConMon package.", primer: "docs/regulatory-primer.md#49-nist-800-53-rev5--security-and-privacy-controls-us--t1", evidencePack: "docs/evidence-packs/nist-800-53.md", ucs: [
        { id: "22.14.1", why: "We verify that all required events are being logged per AU-2 — the foundation of any audit programme." },
        { id: "22.14.16", why: "We monitor account management lifecycle — creation, modification, disabling, and removal per AC-2." },
        { id: "22.14.41", why: "We track system monitoring activities per SI-4 — detecting anomalies and unauthorized access attempts." }
      ]},
      { name: "IEC 62443 industrial", description: "Industrial automation and control system security — zones and conduits, security requirements from SR 1.1 through SR 5.4, component security, and IACS programme evidence.", whatItIs: "The international standard family for industrial automation and control system security. It defines zones, conduits, security levels (SL-C/T), and detailed requirements for IACS programmes, system integrators, and component vendors.", whoItAffects: "Owner-operators of industrial automation systems (manufacturing, utilities, oil and gas, pharma), system integrators building control systems, and component vendors supplying PLCs, HMIs, and historians.", splunkValue: "We watch zone-boundary traffic for unapproved protocols, evidence human-user identification on HMIs and engineering workstations, and prepare the IACS programme artefacts that certifiers look for during SL-C assessments.", ucs: [
        { id: "22.15.1", why: "We verify the security programme covers all industrial automation systems — not just IT-connected ones." },
        { id: "22.15.46", why: "We monitor zone boundary traffic — ensuring only approved protocols cross between security zones." },
        { id: "22.15.11", why: "We track human user identification and authentication on control systems — SR 1.1 requires this for all IACS users." }
      ]},
      { name: "TSA Pipeline security", description: "Post-Colonial Pipeline TSA Security Directives — network segmentation, access control, incident response, architecture reviews, and continuous monitoring for pipeline SCADA systems.", whatItIs: "US Transportation Security Administration security directives, tightened after the 2021 Colonial Pipeline ransomware attack. They mandate IT/OT segmentation, access control, incident reporting, and annual cybersecurity architecture reviews for pipeline operators.", whoItAffects: "Hazardous-liquid and natural-gas pipeline owner-operators in the United States designated as critical by TSA.", splunkValue: "We prove IT/OT segmentation continuously, log privileged access to pipeline SCADA, evidence the 24-hour incident reporting timeline to CISA, and capture the architecture-review artefacts TSA inspectors verify on site.", ucs: [
        { id: "22.16.1", why: "We validate IT/OT segmentation for pipeline control systems — the core TSA security directive requirement." },
        { id: "22.16.7", why: "We track OT incident detection and TSA reporting compliance — pipeline incidents must be reported promptly." },
        { id: "22.16.19", why: "We monitor pipeline SCADA system availability — ensuring continuous operation of critical control systems." }
      ]},
      { name: "FDA Part 11 pharma", description: "Electronic records and signatures for regulated pharmaceutical and medical device environments — audit trails, operator attribution, data integrity (ALCOA+), and GxP system validation.", whatItIs: "US FDA 21 CFR Part 11 — the rules that let pharmaceutical, biotech, and medical-device companies use electronic records and signatures instead of paper. It demands comprehensive audit trails, operator attribution, and data-integrity guarantees under the ALCOA+ principles.", whoItAffects: "Pharmaceutical, biotech, and medical-device manufacturers, CROs, and labs that run GxP systems (QMS, MES, LIMS, electronic batch records) under FDA jurisdiction — plus their equivalents in ICH-member regions.", splunkValue: "We watch GxP system audit-trail completeness, detect disabled or bypassed audit trails, prove operator identity on every signed record, and flag ALCOA+ exceptions that will otherwise surface during an FDA 483 inspection.", ucs: [
        { id: "22.17.1", why: "We verify audit trail completeness for all electronic records — every change must be captured with who, what, when." },
        { id: "22.17.11", why: "We track operator attribution for all system actions — Part 11 requires knowing exactly who performed each step." },
        { id: "22.17.16", why: "We monitor ALCOA+ data integrity principles — ensuring records are Attributable, Legible, Contemporaneous, Original, and Accurate." }
      ]},
      { name: "API 1164 pipeline SCADA", description: "American Petroleum Institute standard for SCADA security — RTU/HMI access, command authentication, field device integrity, network segmentation, and pipeline cybersecurity compliance.", whatItIs: "The American Petroleum Institute's recommended-practice standard for pipeline SCADA cybersecurity. It complements TSA directives with detailed guidance on operator authentication, command authorisation, field-device integrity, and secure remote access.", whoItAffects: "Oil and gas pipeline operators in North America that follow API's recommended practice, often alongside TSA security directives and NIST 800-82 industrial guidance.", splunkValue: "We monitor operator authentication on HMIs and engineering workstations, log and justify control commands issued to the field, and detect firmware or configuration drift on RTUs and PLCs before it becomes a safety event.", ucs: [
        { id: "22.18.1", why: "We monitor operator authentication on SCADA systems — only authorised personnel should control pipeline operations." },
        { id: "22.18.8", why: "We verify SCADA command authentication — critical control commands must be authorised before execution." },
        { id: "22.18.22", why: "We track firmware versions and configuration changes on field devices — detecting unauthorised modifications to PLCs and RTUs." }
      ]},
      { name: "FISMA / FedRAMP", description: "US Federal information security — continuous monitoring, authorisation to operate, POA&M management, PIV authentication, and federal incident reporting.", whatItIs: "The Federal Information Security Modernization Act requires US federal agencies to run a continuous monitoring programme over their systems. FedRAMP extends that to cloud providers that want to sell to the federal government, with a standardised authorisation-to-operate.", whoItAffects: "US federal agencies, their contractors, and cloud service providers pursuing FedRAMP authorisation (Low, Moderate, High impact levels). State agencies and higher education often adopt FISMA-aligned programmes as well.", splunkValue: "We produce the ConMon deliverables — vulnerability metrics, POA&M ageing, inventory, configuration compliance, and incident metrics — in the format expected by the JAB and agency authorising officials, not a home-grown template.", ucs: [
        { id: "22.19.1", why: "We track ISCM dashboard metrics — the continuous monitoring programme that underpins every federal ATO." },
        { id: "22.19.6", why: "We manage Plan of Action and Milestones — tracking known weaknesses and remediation commitments." },
        { id: "22.19.11", why: "We ensure federal incident reporting timelines are met — US-CERT notification within required timeframes." }
      ]},
      { name: "CMMC defence", description: "Cybersecurity Maturity Model Certification — protecting Controlled Unclassified Information in the defence supply chain with Level 2 and Level 3 practices.", whatItIs: "The US Department of Defense cybersecurity maturity framework. It standardises how defence contractors protect Controlled Unclassified Information, with three maturity levels and third-party certification for Level 2 and Level 3.", whoItAffects: "Every contractor and subcontractor in the DoD supply chain that handles Federal Contract Information (Level 1) or Controlled Unclassified Information (Levels 2 and 3) — roughly 300,000 organisations.", splunkValue: "We evidence every CMMC practice continuously, map catalogue coverage to 800-171 controls, prove the self-assessment scoring is data-backed rather than attested, and pre-build the evidence package a C3PAO expects during Level 2 or Level 3 assessment.", primer: "docs/regulatory-primer.md#412-cmmc-20--cybersecurity-maturity-model-certification-us--t1", evidencePack: "docs/evidence-packs/cmmc.md", ucs: [
        { id: "22.20.1", why: "We track CUI identification and marking — the starting point for protecting defence information." },
        { id: "22.20.11", why: "We monitor for advanced persistent threats targeting CUI environments — Level 3 enhanced detection." },
        { id: "22.20.16", why: "We collect self-assessment evidence and practice implementation scores — readiness for CMMC certification." }
      ]},
      { name: "EU AI Act", description: "High-risk AI system logging, traceability, human oversight, conformity assessment, and post-market monitoring under the EU Artificial Intelligence Act.", whatItIs: "The EU's horizontal regulation on artificial intelligence. It bans unacceptable AI uses, imposes strict obligations on high-risk AI systems (healthcare, employment, credit, law enforcement, biometric, safety-critical), and adds general-purpose AI model transparency duties.", whoItAffects: "Providers, deployers, importers, and distributors of AI systems placed on the EU market — including non-EU vendors whose AI is used in the EU. Obligations apply whether you built the model or merely integrate an upstream one.", splunkValue: "We capture the Article 12 automatic logs, track model version and training-data lineage, evidence human-override events under Article 14, and maintain the post-market monitoring artefacts national market-surveillance authorities will request.", ucs: [
        { id: "22.21.1", why: "We ensure high-risk AI systems maintain automatic recording of events — Article 12 requires comprehensive logging." },
        { id: "22.21.6", why: "We track model version history and training data lineage — traceability is mandatory for high-risk AI." },
        { id: "22.21.11", why: "We log human override actions on AI decisions — Article 14 requires meaningful human oversight capability." }
      ]},
      { name: "PSD2 payments", description: "EU Payment Services Directive — strong customer authentication, fraud monitoring, Open Banking API security, transaction integrity, and incident reporting to national authorities.", whatItIs: "The EU's Payment Services Directive (2). It mandates Strong Customer Authentication for electronic payments, forces banks to open APIs to licensed third parties, and introduces a common major-incident reporting regime under the EBA guidelines.", whoItAffects: "Banks, payment institutions, electronic money institutions, and licensed third-party providers (account information service providers and payment initiation service providers) operating in the EEA.", splunkValue: "We watch SCA challenge rates by channel, detect fraud patterns in real time, monitor third-party API access to Open Banking interfaces, and evidence major-incident reporting to national competent authorities within EBA timelines.", ucs: [
        { id: "22.22.1", why: "We monitor strong customer authentication challenge rates — ensuring SCA is applied where required." },
        { id: "22.22.7", why: "We detect transaction fraud patterns — real-time scoring and unusual payment behaviour." },
        { id: "22.22.13", why: "We track third-party provider API access — monitoring who uses your Open Banking interfaces and how." }
      ]},
      { name: "EU Cyber Resilience Act", description: "Product security requirements — security-by-default evidence, vulnerability handling, SBOM maintenance, incident reporting to ENISA, and secure development lifecycle.", whatItIs: "The EU's horizontal regulation on products with digital elements. It imposes security-by-design, vulnerability handling, and 24-hour actively-exploited-vulnerability reporting obligations on manufacturers of connected products sold in the EU.", whoItAffects: "Manufacturers, importers, and distributors of products with digital elements placed on the EU market — IoT device makers, software vendors, connected-appliance manufacturers, industrial-automation vendors.", splunkValue: "We evidence secure-by-default configurations in production, maintain SBOMs and track dependency vulnerabilities, trigger the 24-hour exploited-vulnerability notification clock to ENISA, and record the coordinated vulnerability disclosure artefacts the CRA demands.", ucs: [
        { id: "22.23.1", why: "We verify security-by-default configurations in products — the CRA requires products to ship secure out of the box." },
        { id: "22.23.6", why: "We track coordinated vulnerability disclosure — handling reported vulnerabilities within required timelines." },
        { id: "22.23.11", why: "We maintain and monitor Software Bills of Materials — tracking component vulnerabilities across your product portfolio." }
      ]},
      { name: "eIDAS 2.0 trust services", description: "EU electronic identification — qualified trust service audit trails, EU Digital Identity Wallet security, timestamping integrity, and certificate lifecycle management.", whatItIs: "The EU regulation on electronic identification and trust services. Version 2.0 introduces the EU Digital Identity Wallet, expands qualified trust service categories, and tightens audit and supervision requirements on trust service providers.", whoItAffects: "Qualified and non-qualified trust service providers (certificate authorities, timestamp authorities, eSignature and eSeal providers), EU Digital Identity Wallet providers, and relying parties that accept qualified credentials.", splunkValue: "We audit certificate issuance and revocation, track wallet credential presentation integrity, verify qualified timestamp traceability, and evidence the supervision artefacts national supervisory bodies demand during conformity assessment.", ucs: [
        { id: "22.24.1", why: "We audit certificate issuance and revocation — qualified trust services must maintain complete audit trails." },
        { id: "22.24.5", why: "We track EU Digital Identity Wallet issuance and credential presentations — monitoring the security of wallet operations." },
        { id: "22.24.9", why: "We verify qualified timestamp accuracy — timestamps must be traceable to coordinated universal time." }
      ]},
      { name: "AML / CFT", description: "Anti-money laundering and counter-terrorist financing — transaction monitoring, suspicious activity reports, KYC lifecycle, sanctions screening, PEP monitoring, and institution-wide risk assessment.", whatItIs: "The global regime requiring financial and designated non-financial businesses to detect and report money laundering and terrorist financing. Delivered via FATF recommendations, EU AMLD directives, the US Bank Secrecy Act, and equivalent national rules.", whoItAffects: "Banks, payment firms, e-money institutions, crypto-asset service providers, real estate, gambling, dealers in high-value goods, accountants, auditors, and legal professionals performing designated activities.", splunkValue: "We detect structuring / smurfing, monitor SAR / STR filing timeliness, run real-time sanctions screening, surface PEP and adverse-media hits, and produce the institution-wide AML/CFT risk assessment evidence supervisors expect.", ucs: [
        { id: "22.25.1", why: "We detect structuring and smurfing patterns — transactions deliberately kept below reporting thresholds." },
        { id: "22.25.8", why: "We track SAR filing timelines — suspicious activity reports must be filed within regulatory deadlines." },
        { id: "22.25.18", why: "We perform real-time sanctions screening — every transaction checked against current sanctions lists." }
      ]},
      { name: "Norwegian regulations", description: "Sikkerhetsloven national security, Kraftberedskapsforskriften power preparedness, Petroleumsforskriften oil and gas HSE, and Personopplysningsloven data protection specific to Norway.", whatItIs: "Norway's national regulatory stack for security-classified information (Sikkerhetsloven), grid operator preparedness (NVE's Kraftberedskapsforskriften), offshore petroleum HSE (PSA's Petroleumsforskriften), and supplementary data protection (Personopplysningsloven on top of GDPR).", whoItAffects: "Norwegian public administration, operators of classified systems, power system operators regulated by NVE, offshore oil and gas operators regulated by PSA / Havtil, and any controller processing Norwegian personal data.", splunkValue: "We evidence classified-information system controls, track NVE preparedness metrics, capture HSE-critical OT telemetry from offshore platforms, and localise GDPR evidence so Datatilsynet inspections see Norwegian-specific coverage.", ucs: [
        { id: "22.26.1", why: "We monitor classified information systems per Sikkerhetsloven — protecting national security information." },
        { id: "22.26.6", why: "We track power system availability and SCADA access — NVE requires preparedness evidence for grid operators." },
        { id: "22.26.11", why: "We monitor offshore platform control systems — PSA requires safety-critical system integrity monitoring." }
      ]},
      { name: "UK NIS & FCA/PRA", description: "UK NIS Regulations for essential services, FCA operational resilience, PRA outsourcing requirements, Senior Managers and Certification Regime, and Cyber Essentials certification.", whatItIs: "The UK's post-Brexit regulatory stack: the UK NIS Regulations for operators of essential services, FCA and PRA operational-resilience rules for financial firms, the Senior Managers and Certification Regime, and the government-backed Cyber Essentials scheme.", whoItAffects: "UK operators of essential services (energy, transport, health, water, digital infrastructure, digital services), FCA-authorised firms, PRA-supervised banks and insurers, and public-sector and supply-chain entities required to hold Cyber Essentials.", splunkValue: "We evidence NIS security measures, track operational resilience impact tolerances and severe-but-plausible scenario testing, monitor material-outsourcing registers, and generate SM&CR personal-accountability artefacts.", ucs: [
        { id: "22.27.1", why: "We monitor security measures for operators of essential services — UK NIS requires demonstrable security." },
        { id: "22.27.11", why: "We track important business service resilience — FCA requires firms to set and test impact tolerances." },
        { id: "22.27.19", why: "We monitor material outsourcing registers — PRA requires oversight of third-party dependencies." }
      ]},
      { name: "German KRITIS / BSI", description: "IT-Sicherheitsgesetz 2.0 critical infrastructure, BSI-KritisV sector thresholds, BSI IT-Grundschutz methodology, and BAIT/KAIT banking and insurance IT governance.", whatItIs: "Germany's national cybersecurity stack: IT-SiG 2.0 obligations on critical-infrastructure operators, BSI-KritisV thresholds that determine who is KRITIS, BSI IT-Grundschutz as a baseline methodology, and BAIT / KAIT for banks and insurers supervised by BaFin.", whoItAffects: "Operators of KRITIS sectors in Germany (energy, water, food, transport, health, finance, IT/telecoms, media, government, waste disposal), BaFin-regulated financial and insurance firms, and federal administration bodies using IT-Grundschutz.", splunkValue: "We support BSI 24-hour incident reporting, evidence IT-Grundschutz module implementation, capture BAIT / KAIT IT-governance artefacts, and maintain the KRITIS asset inventory and sector-threshold calculations supervisors check.", ucs: [
        { id: "22.28.1", why: "We track critical infrastructure operator reporting to BSI — incidents must be reported within 24 hours." },
        { id: "22.28.6", why: "We monitor KRITIS asset inventory and sector threshold compliance — operators must know what they protect." },
        { id: "22.28.11", why: "We track BSI IT-Grundschutz module compliance — the German standard for baseline security." }
      ]},
      { name: "APAC data protection", description: "Data protection across Asia-Pacific — China PIPL, Singapore PDPA, Japan APPI, Thailand PDPA, and Korea K-ISMS — covering cross-border transfers, breach notification, security safeguards, and consent management.", whatItIs: "A patchwork of national data-protection laws across APAC: China PIPL (with strict cross-border transfer rules), Singapore PDPA (with a Do-Not-Call regime), Japan APPI (aligned with GDPR for adequacy), Thailand PDPA, and Korea's K-ISMS / PIPA regime.", whoItAffects: "Any organisation that processes personal data about APAC residents — regional headquarters, multinational HR platforms, e-commerce, ad-tech, and cloud service providers operating in Asia-Pacific.", splunkValue: "We localise breach-notification timelines per jurisdiction, enforce data-localisation under PIPL, monitor DPO appointment and reporting obligations, and cross-reference each APAC regime against the catalogue's GDPR-aligned detections.", ucs: [
        { id: "22.29.1", why: "We enforce data localisation requirements under China PIPL Article 38 — personal data must stay within borders unless transfer conditions are met." },
        { id: "22.29.7", why: "We track breach notification timelines by jurisdiction — each APAC country has different requirements." },
        { id: "22.29.19", why: "We monitor DPO appointment compliance — several APAC laws require designated data protection officers." }
      ]},
      { name: "APAC financial regulation", description: "Financial sector technology risk across Asia-Pacific — MAS TRM Singapore, HKMA Hong Kong, RBI India, and APRA CPS 234 Australia.", whatItIs: "APAC-specific financial-sector technology-risk regimes: MAS Technology Risk Management (Singapore), HKMA cybersecurity guidance (Hong Kong), RBI technology risk and cyber resilience (India), and APRA CPS 234 (Australia) on information security.", whoItAffects: "Banks, insurers, asset managers, capital markets participants, and licensed fintechs supervised by MAS, HKMA, RBI, or APRA. Many rules reach into service providers of regulated firms as well.", splunkValue: "We evidence technology-risk management controls, capture cybersecurity-assessment evidence on the timelines each regulator expects, and translate CPS 234 control-testing requirements into continuous-evidence dashboards.", ucs: [
        { id: "22.30.1", why: "We monitor technology risk management per MAS guidelines — Singapore financial institutions must demonstrate IT governance." },
        { id: "22.30.8", why: "We track cybersecurity assessments per HKMA requirements — Hong Kong banks must regularly test their defences." },
        { id: "22.30.20", why: "We verify APRA CPS 234 information security capability — Australian financial institutions must maintain and test controls." }
      ]},
      { name: "Australia & New Zealand", description: "Privacy Act and Notifiable Data Breaches scheme, ASD Essential Eight maturity, APRA CPS 234 detail, and New Zealand ISM compliance.", whatItIs: "The Australian privacy and cybersecurity stack — Privacy Act with Notifiable Data Breaches, ASD's Essential Eight maturity model, APRA CPS 234 information security for regulated entities — plus New Zealand's Information Security Manual for government agencies.", whoItAffects: "Australian entities covered by the Privacy Act (with specific thresholds and exemptions), APRA-regulated banks / insurers / superannuation funds, federal agencies using Essential Eight, and New Zealand public-sector agencies covered by the ISM.", splunkValue: "We assess Notifiable Data Breach thresholds, score Essential Eight maturity continuously, evidence CPS 234 information-security capability, and evidence the NZ ISM control baseline for agency accreditation.", ucs: [
        { id: "22.31.1", why: "We assess notifiable data breaches under Australian law — determining if a breach is likely to cause serious harm." },
        { id: "22.31.6", why: "We monitor ASD Essential Eight controls — application control, patching, MFA, and admin privilege restriction." },
        { id: "22.31.14", why: "We track CPS 234 information security roles and control testing — Australian prudential requirements for financial institutions." }
      ]},
      { name: "Americas regulations", description: "LGPD Brazil data protection, FISMA/FedRAMP federal compliance, CMMC defence supply chain, and CJIS criminal justice information security.", whatItIs: "A group of Americas-region regimes: Brazil's LGPD data-protection law, US federal FISMA / FedRAMP for government and cloud providers, CMMC for the DoD supply chain, and CJIS for criminal-justice information handled by law enforcement.", whoItAffects: "Any organisation handling Brazilian personal data (LGPD), US federal or FedRAMP cloud services, US defence-supply-chain CUI (CMMC), or US criminal-justice information systems (CJIS).", splunkValue: "We generate LGPD consent artefacts, populate ConMon packages for FedRAMP, prepare CMMC Level 2/3 practice evidence, and enforce CJIS advanced-authentication and audit-trail requirements.", ucs: [
        { id: "22.32.1", why: "We track LGPD consent management — Brazilian data protection requires documented legal basis for processing." },
        { id: "22.32.9", why: "We monitor continuous monitoring metrics for FedRAMP — federal cloud authorisations require ongoing compliance evidence." },
        { id: "22.32.22", why: "We log access to criminal justice information — CJIS requires advanced authentication and complete audit trails." }
      ]},
      { name: "Middle East cybersecurity", description: "National cybersecurity frameworks — UAE NESA, Saudi Arabia SAMA and PDPL, Qatar QCB — covering critical infrastructure, financial services, and data protection requirements.", whatItIs: "Middle East national cybersecurity and data-protection regimes: UAE NESA IAS (now NCSS) for national critical infrastructure, Saudi Arabia SAMA cybersecurity framework and SDAIA PDPL data protection, Qatar QCB information-security guidance, and similar regimes across the GCC.", whoItAffects: "Critical-infrastructure operators and financial institutions in the UAE, Saudi Arabia, Qatar and neighbouring GCC states, plus any organisation processing personal data of residents of those jurisdictions under emerging national privacy laws.", splunkValue: "We evidence NESA / NCSS control implementations, populate SAMA cybersecurity framework artefacts, enforce Saudi PDPL consent and localisation rules, and deliver the regulator-specific dashboards each national authority requires.", ucs: [
        { id: "22.33.1", why: "We track UAE national cybersecurity standard compliance — NESA requires critical infrastructure operators to demonstrate security." },
        { id: "22.33.6", why: "We monitor SAMA cybersecurity framework compliance — Saudi financial institutions must meet specific security controls." },
        { id: "22.33.11", why: "We enforce Saudi PDPL data protection — personal data processing must comply with the new privacy law." }
      ]},
      { name: "SWIFT CSP", description: "SWIFT Customer Security Programme — secure zone protection, operator account control, system hardening, intrusion detection, and annual attestation evidence.", whatItIs: "SWIFT's Customer Security Programme mandates baseline security controls for every user of the SWIFT network and requires an annual self-attestation (now independently assessed) of compliance with the Customer Security Controls Framework.", whoItAffects: "Every organisation that connects to SWIFT — banks, central banks, broker-dealers, large corporates, and service bureaus — regardless of size. Non-compliance can be reported to counterparties and national regulators.", splunkValue: "We evidence secure-zone segregation, operator-authentication strength, intrusion detection on SWIFT hosts, and produce the CSCF workbook with timestamped query evidence instead of screenshots for the annual KYC-SA attestation.", ucs: [
        { id: "22.34.1", why: "We monitor the SWIFT secure zone environment — protecting the infrastructure that processes financial messages." },
        { id: "22.34.4", why: "We track operator authentication and session integrity — every SWIFT operator action must be attributable." },
        { id: "22.34.10", why: "We collect annual KYC-SA attestation evidence — demonstrating compliance to counterparties." }
      ]},
      { name: "Compliance trending", description: "We chart posture scores, audit closure, control tests, incident response time, and policy violations over time so you see direction, not a single snapshot.", whatItIs: "A cross-framework trending layer. Instead of reporting a single snapshot score on audit day, we track how each framework's posture moves quarter over quarter, surfacing the controls whose trend is declining before they turn into findings.", whoItAffects: "CISOs, privacy officers, compliance leaders, and audit committees that need to show direction of travel to boards, regulators, and insurers.", splunkValue: "We ingest every control's pass/fail signal, chart compliance score curves by framework and business unit, and compute time-to-close for findings — so leadership reporting becomes evidence-based rather than narrative-based.", ucs: [
        { id: "22.9.1", why: "We track how overall compliance scores move across major frameworks quarter by quarter — so leadership sees whether posture is improving." },
        { id: "22.9.2", why: "We watch open versus closed audit findings and how long fixes take — so backlogs and slow remediation surface before the next audit." },
        { id: "22.9.6", why: "We trend framework-specific compliance over time — so you see which regulation is improving and which needs attention." }
      ]},
      { name: "Evidence continuity & log integrity", description: "We prove your audit logs are complete, unbroken, and tamper-evident — so auditors across GDPR, HIPAA, PCI, SOC 2, and SOX accept the same chain of custody.", whatItIs: "The foundational control every framework relies on: the organisation must produce complete, contemporaneous, and tamper-evident audit logs. A gap or missing source destroys the evidentiary value of everything else.", whoItAffects: "Every organisation with an audit obligation — privacy, financial, healthcare, or operational. In practice, any team that will ever have to defend a control decision to a third party.", splunkValue: "We watch for collection gaps across sources, detect tampering of stored logs, confirm off-site replication, and produce the chain-of-custody timeline a forensic investigator or regulator expects.", primer: "docs/regulatory-primer.md#31-2235--evidence-continuity-and-log-integrity", ucs: [
        { id: "22.35.1", why: "We watch for gaps in security logging so you can prove to auditors that nothing slipped through the cracks." },
        { id: "22.35.2", why: "We detect if anyone tampers with stored audit logs — turning a silent integrity failure into actionable evidence within minutes." },
        { id: "22.35.3", why: "We monitor that every audit log is replicated to a second location — protecting against a single storage failure wiping your evidence trail." }
      ]},
      { name: "Data subject rights fulfilment", description: "We track every request from individuals asking to see, correct, or delete their personal data — and prove they were handled on time and completely.", whatItIs: "The end-to-end lifecycle of privacy requests individuals can make under GDPR, UK GDPR, CCPA, LGPD, PDPA, and equivalent laws — access, rectification, erasure, portability, restriction, and objection — with deadlines that range from 30 to 45 days depending on jurisdiction.", whoItAffects: "Any organisation processing personal data subject to a privacy law with data-subject rights provisions.", splunkValue: "We time-stamp every request, measure response times against each legal deadline, verify that deletion actually reached backups and analytics stores, and produce the audit trail a DPA can follow end to end.", primer: "docs/regulatory-primer.md#32-2236--data-subject-rights-fulfillment", ucs: [
        { id: "22.36.1", why: "We track how long it takes to answer every data access or deletion request — so you never miss a regulatory deadline." },
        { id: "22.36.2", why: "We verify deletion requests actually removed data everywhere — not just from the main system while copies linger in backups or data warehouses." },
        { id: "22.36.3", why: "We monitor data export requests for portability — so individuals get their data in machine-readable form as the law requires." }
      ]},
      { name: "Consent & lawful basis", description: "We follow consent through every step — from the cookie banner to the backend — so you know marketing, analytics, and profiling only run on data that was lawfully collected.", whatItIs: "The record of why the organisation is lawfully processing each piece of personal data — consent, contract, legal obligation, vital interest, public task, or legitimate interest — and evidence that downstream systems respect withdrawal and preference changes.", whoItAffects: "Any organisation relying on consent or another lawful basis under GDPR, CCPA, LGPD, PDPA, or equivalent laws — especially marketing, analytics, ad-tech, and profiling teams.", splunkValue: "We correlate consent-ledger state with downstream marketing and analytics activity, detect tags that fire against 'reject all', and flag marketing audiences built on expired or missing consent.", primer: "docs/regulatory-primer.md#33-2237--consent-lifecycle-and-lawful-basis", ucs: [
        { id: "22.37.1", why: "We watch when people withdraw consent and prove downstream systems stopped processing their data — the key signal regulators look for." },
        { id: "22.37.2", why: "We detect advertising or tracking scripts that ignore 'reject all' in the cookie banner — the single most common GDPR/CCPA enforcement trigger." },
        { id: "22.37.3", why: "We monitor marketing lists for expired or missing consent — so no one gets messaged without a lawful basis on file." }
      ]},
      { name: "Cross-border transfers", description: "We watch where personal data actually goes — so transfers to other countries only happen under the right legal framework and never by accident.", whatItIs: "The rules that permit personal data to flow to other countries — GDPR Chapter V (SCCs, BCRs, adequacy decisions, derogations), UK IDTA, China PIPL Article 38, LGPD, and APPI equivalents. Accidental or undocumented transfers are a headline enforcement risk.", whoItAffects: "Any organisation whose cloud, backups, analytics, or business partners result in personal data moving between jurisdictions — in practice almost every multinational.", splunkValue: "We detect unauthorised copies of personal data to foreign cloud regions, verify SCC / DPA coverage per data flow, and flag email attachments or file shares that move personal data outside the approved jurisdiction.", primer: "docs/regulatory-primer.md#34-2238--cross-border-transfer-controls", ucs: [
        { id: "22.38.1", why: "We detect unauthorised copies of personal data to foreign cloud regions — a key red line under GDPR and national data-localisation rules." },
        { id: "22.38.2", why: "We verify every cross-border transfer has a current legal agreement (SCC or DPA) — no paperwork gaps when regulators ask." },
        { id: "22.38.3", why: "We monitor email attachments and file-share activity for personal data leaving the approved jurisdiction." }
      ]},
      { name: "Incident notification timeliness", description: "We turn the clock on every reportable incident and measure each regulatory deadline — 24h, 72h, 4h — across GDPR, HIPAA, NIS2, DORA, and national rules.", whatItIs: "The cross-framework set of regulator-notification deadlines an organisation must hit after detecting a qualifying incident: GDPR 72h, NIS2 24h early warning, DORA 4h major-incident, HIPAA 60-day breach, plus many national overlays.", whoItAffects: "Every organisation subject to at least one incident-reporting regime — in practice virtually every business in a regulated sector or with regulated personal data.", splunkValue: "We start each clock automatically when the trigger condition is detected, alert before a deadline is about to miss, capture the submission trail to each regulator, and record the individual-notification evidence per breach.", primer: "docs/regulatory-primer.md#35-2239--incident-notification-timeliness", ucs: [
        { id: "22.39.1", why: "We alert when a breach notification deadline is about to be missed — so regulators hear about it on time and fines are avoided." },
        { id: "22.39.2", why: "We track every regulator communication through to acknowledgement — proving the notification actually landed with the right authority." },
        { id: "22.39.3", why: "We notify affected individuals within legal deadlines — and keep an audit trail of what each person was told." }
      ]},
      { name: "Privileged access evidence", description: "We watch every administrator, break-glass, and elevated-access session — and provide recordings, approvals, and timelines as evidence that access was justified.", whatItIs: "The control expected by every framework of any maturity — privileged access is justified, just-in-time, logged, and reviewed. Failures here produce the most impactful audit findings in financial and healthcare audits.", whoItAffects: "Any organisation with privileged technical users — so, everyone with technology infrastructure. The depth of control expected scales with the sensitivity of the data and the regulator.", splunkValue: "We flag break-glass access with no ticket, ensure privileged sessions are recorded, detect shared or generic admin accounts, and feed the access-review process with live data instead of spreadsheet snapshots.", primer: "docs/regulatory-primer.md#36-2240--privileged-access-evidence", ucs: [
        { id: "22.40.1", why: "We flag break-glass admin access with no ticket or approval — the single most damaging audit finding in financial and healthcare audits." },
        { id: "22.40.2", why: "We track privileged-session recording completeness — so every admin action on regulated systems has a replayable video record." },
        { id: "22.40.3", why: "We detect shared or generic admin accounts still in active use — and enforce named accountability." }
      ]},
      { name: "Encryption & key management", description: "We prove every database, backup, and communication channel is encrypted — and that the keys protecting them are rotated, separated, and stored safely.", whatItIs: "The technical baseline every framework demands: data at rest and in transit is encrypted with modern algorithms, keys are rotated inside their cryptoperiod, and key material is stored in an HSM or managed KMS with least-privilege access.", whoItAffects: "Every organisation storing or transmitting sensitive data — in practice every modern business.", splunkValue: "We detect systems storing sensitive data without encryption, watch key-age against rotation SLAs, detect weak cipher suites and expiring TLS certificates, and monitor KMS administrative events.", primer: "docs/regulatory-primer.md#37-2241--encryption-and-key-management-attestation", ucs: [
        { id: "22.41.1", why: "We detect systems storing sensitive data without encryption — turning a silent gap into a remediation ticket before audit day." },
        { id: "22.41.2", why: "We monitor key rotation so cryptographic keys never exceed their allowed lifetime — a key requirement under PCI DSS and NIST." },
        { id: "22.41.3", why: "We watch for weak cipher suites and expiring TLS certificates — the common source of unexpected service outages and audit exceptions." }
      ]},
      { name: "Change management & baselines", description: "We confirm every production change on regulated systems had a ticket, an approver, and a test record — and flag changes that drift away from the approved baseline.", whatItIs: "The control every framework requires around changes to regulated systems — every change has a ticket, an approver, a test record, and a rollback plan. Baseline-drift monitoring is the complementary control ensuring the approved state persists.", whoItAffects: "Any organisation where IT changes can affect regulated processes — ePHI systems, financial-reporting systems, card-data environments, OT systems, and more.", splunkValue: "We correlate each production-change event with an approved ticket, detect emergency changes, flag configuration drift against the approved baseline, and produce the change-management sample-set auditors request.", primer: "docs/regulatory-primer.md#38-2242--change-management-and-configuration-baseline", ucs: [
        { id: "22.42.1", why: "We detect production changes that bypassed the change-management ticket — so unauthorised changes are investigated, not rubber-stamped." },
        { id: "22.42.2", why: "We alert on host configuration drift away from the approved security baseline — catching bad changes that compromise the control posture." }
      ]},
      { name: "Vulnerability & patch SLAs", description: "We measure how quickly critical vulnerabilities are fixed — by severity, by system, and by regulation — so SLAs are met, not just documented.", whatItIs: "The control expected by every framework: each vulnerability has a severity-driven fix deadline, progress is tracked, and exceptions are documented. Missing a patch SLA is a very common audit finding.", whoItAffects: "Any organisation running software that receives security updates — which is every business. Regulated sectors have explicit SLAs; unregulated ones still face breach-notification exposure.", splunkValue: "We track every critical vulnerability against its patch deadline, highlight systems that repeatedly miss their SLA, and feed exception-management with age, severity, exploit maturity, and CISA KEV signals.", primer: "docs/regulatory-primer.md#39-2243--vulnerability-management-and-patch-slas", ucs: [
        { id: "22.43.1", why: "We track every critical vulnerability against its patch deadline — and escalate anything about to breach the regulatory SLA." },
        { id: "22.43.2", why: "We watch which systems repeatedly slip their patching deadline — so the cause is fixed, not just the individual finding." }
      ]},
      { name: "Third-party & supply-chain risk", description: "We extend your monitoring to vendors who process your data — so regulator questions about supplier oversight are answered with live evidence, not an annual questionnaire.", whatItIs: "The control set around third parties who process regulated data — risk assessments, DPAs, sub-processor disclosure, SBOM tracking, and ongoing monitoring. Many regulators now audit supplier oversight before auditing internal controls.", whoItAffects: "Any organisation that outsources technology or data processing — cloud, SaaS, MSP, BPO, payment processors, analytics vendors, marketing vendors, and supply-chain partners.", splunkValue: "We track every vendor risk assessment to expiry, publish an accurate sub-processor list matching DPA disclosures, and surface SBOM findings across the vendor estate so supply-chain incidents can be acted on.", primer: "docs/regulatory-primer.md#310-2244--third-party-and-supply-chain-risk", ucs: [
        { id: "22.44.1", why: "We track every vendor risk assessment to expiry — so no supplier is ever processing your data on an outdated attestation." },
        { id: "22.44.2", why: "We publish the list of sub-processors actually used — matching what the law requires you to disclose to customers." },
        { id: "22.44.3", why: "We monitor Software-Bill-of-Materials findings across vendors — so software-supply-chain incidents are spotted and acted on." }
      ]},
      { name: "Backup integrity & recovery testing", description: "We prove backups work, are protected from ransomware, and can actually restore — by measuring drill success, not just backup job status.", whatItIs: "The control DORA, HIPAA, NIS2, and ISO 27001 demand: backups are taken, protected from tampering (immutability / air gap), tested by actual restore drills, and measured against recovery-time and recovery-point objectives.", whoItAffects: "Any organisation with data it cannot afford to lose — in practice every business.", splunkValue: "We verify restore drills succeeded, alert when immutability or air-gap protection is disabled, and measure RTO achievement per critical system against the numbers the regulator asks for by name.", primer: "docs/regulatory-primer.md#311-2245--backup-integrity-and-recovery-testing", ucs: [
        { id: "22.45.1", why: "We verify that every restore drill succeeded — turning a 'we back up nightly' assumption into auditable evidence." },
        { id: "22.45.2", why: "We alert when immutability or air-gap protection is disabled on critical backups — the signal that ransomware preparation has begun." },
        { id: "22.45.3", why: "We track how long a critical system takes to recover in a drill — the RTO number that DORA, HIPAA and NIS2 ask for by name." }
      ]},
      { name: "Training & awareness", description: "We measure who has completed mandatory training, phishing simulation results, and role-based learning — so the human side of compliance is evidenced continuously.", whatItIs: "The human-side control every framework embeds — mandatory training completion, phishing simulation performance, and role-based learning such as secure-coding, privileged-user, and developer-security training.", whoItAffects: "Every organisation with employees or regular contractors — and any partner whose access demands training before handling regulated data.", splunkValue: "We join training-platform completion data with HR source-of-truth, detect missed deadlines, measure phishing-click trends over time, and show whether awareness is actually improving or just being recorded.", primer: "docs/regulatory-primer.md#312-2246--training-and-awareness", ucs: [
        { id: "22.46.1", why: "We track which staff missed a mandatory training deadline — so HR and CISO can close gaps before the audit." },
        { id: "22.46.2", why: "We measure phishing simulation click rates over time — so you know whether awareness is really improving, not just that campaigns are running." }
      ]},
      { name: "Control testing freshness", description: "We measure when each compliance control was last tested — so your audit evidence stays fresh instead of quietly going stale.", whatItIs: "The meta-control every mature framework expects: every control is tested on a defined cadence, test results are recorded, exceptions are investigated, and evidence never ages past the reviewer's tolerance.", whoItAffects: "Any organisation operating a control-testing programme — internal audit, second-line assurance, or control-owner self-testing.", splunkValue: "We track test results per control, alert when a cadence is breached, chart coverage against policy requirements, and produce the management-evidence report the audit committee expects each quarter.", primer: "docs/regulatory-primer.md#313-2247--control-testing-evidence-freshness", ucs: [
        { id: "22.47.1", why: "We alert when a control test is overdue — catching stale controls before the auditor does." },
        { id: "22.47.2", why: "We chart the cadence of control testing versus policy requirements — so leadership sees evidence quality at a glance." }
      ]},
      { name: "Segregation of duties", description: "We detect when the same person can request, approve, and release a sensitive change — the toxic combinations that SOX, PCI and healthcare audits look for.", whatItIs: "The control SOX, PCI DSS, and major healthcare audits embed throughout — no single person can request, approve, and release a sensitive change. Toxic role combinations are analysed, monitored, and mitigated before auditors uncover them.", whoItAffects: "Any organisation with financial systems, card-data environments, healthcare data, or high-privilege operations — very often including privileged IT roles.", splunkValue: "We detect conflicting role assignments in financial and operational systems, monitor temporary elevations against business-need expiry, and evidence compensating controls when an SoD conflict cannot be resolved.", primer: "docs/regulatory-primer.md#314-2248--segregation-of-duties-enforcement", ucs: [
        { id: "22.48.1", why: "We flag people who have conflicting roles in financial systems — the combinations auditors write findings about." },
        { id: "22.48.2", why: "We monitor temporary role grants and ensure they are removed when the business need ends — instead of drifting into permanent access." }
      ]},
      { name: "Retention & disposal", description: "We confirm data is actually deleted when retention periods expire — and that litigation holds pause deletion exactly when required.", whatItIs: "The control at the tail end of every data lifecycle — records are kept only as long as needed, deleted when retention expires, and paused on litigation hold when required. Weak retention is a privacy-regulator favourite.", whoItAffects: "Any organisation with retention obligations — which is every business subject to privacy, financial, tax, healthcare, or sectoral record-keeping law.", splunkValue: "We detect personal data retained past its legal retention period, verify scheduled deletion jobs actually executed, and alert on litigation-hold changes that happened without a matching legal ticket.", primer: "docs/regulatory-primer.md#315-2249--retention-and-disposal-automation", ucs: [
        { id: "22.49.1", why: "We detect personal data retained past its legal retention period — turning silent retention drift into a ticket your DPO can close." },
        { id: "22.49.2", why: "We verify scheduled deletion jobs actually ran — so expired data does not sit in backups and data warehouses forever." },
        { id: "22.49.3", why: "We alert on litigation-hold changes that happen without a matching legal ticket — protecting you from spoliation claims." }
      ]}
    ]
  },
  "23": {
    outcomes: [
      "We turn your business data into actionable insights — revenue performance, customer behaviour, marketing effectiveness, and operational efficiency all in one place.",
      "We help you see the numbers that matter to the boardroom, not just the server room — customer churn, pipeline health, hiring velocity, and supplier performance.",
      "We detect business anomalies early — revenue shortfalls, expense fraud, stockouts, and SLA breaches — so you can act before they become crises."
    ],
    areas: [
      { name: "Customer experience", description: "We track how customers interact with your website and apps — where they drop off, what makes them buy, and how satisfied they are.", ucs: [
        { id: "23.1.1", why: "We show where customers abandon the purchase journey — so you fix the step that loses the most revenue." },
        { id: "23.1.2", why: "We measure cart abandonment and its revenue impact — so you know how much money walks out the digital door." },
        { id: "23.1.4", why: "We track customer satisfaction scores over time — so you spot drops before they become churn." }
      ]},
      { name: "Revenue & sales", description: "We monitor your sales pipeline, bookings, churn risk, and pricing — giving leadership a live view of revenue health instead of waiting for month-end reports.", ucs: [
        { id: "23.2.1", why: "We track how fast deals move through the pipeline — so you know if you'll hit the quarterly target." },
        { id: "23.2.2", why: "We show revenue bookings against plan in near-real-time — so mid-course corrections happen while there's still time." },
        { id: "23.2.3", why: "We identify customers showing churn risk signals — so you can save accounts before they cancel." }
      ]},
      { name: "Marketing performance", description: "We connect marketing spend to revenue — showing which campaigns and channels actually deliver return on investment.", ucs: [
        { id: "23.3.1", why: "We calculate ROI for each marketing channel — so you invest in what works and cut what doesn't." },
        { id: "23.3.2", why: "We track the full lead-to-revenue funnel — so you see where leads leak and whether marketing delivers quality." },
        { id: "23.3.3", why: "We consolidate email campaign performance — so you see which messages drive engagement and which drive unsubscribes." }
      ]},
      { name: "People & HR analytics", description: "We help HR leaders understand their workforce — attrition patterns, hiring speed, diversity progress, and training compliance.", ucs: [
        { id: "23.4.1", why: "We analyse where people are leaving and why — so you can act before losing key talent." },
        { id: "23.4.2", why: "We track how long it takes to fill positions — so you spot hiring bottlenecks before they hurt the business." },
        { id: "23.4.4", why: "We monitor mandatory training completion — so you're audit-ready and your people are up to date." }
      ]},
      { name: "Supply chain & operations", description: "We track orders, inventory, suppliers, and deliveries — showing where your operations are smooth and where they're breaking down.", ucs: [
        { id: "23.5.1", why: "We measure the order-to-cash cycle — so you see which stages are slow and where cash gets stuck." },
        { id: "23.5.2", why: "We flag products about to run out of stock — so you avoid lost sales and unhappy customers." },
        { id: "23.5.3", why: "We score supplier delivery performance — so you know which partners you can rely on." }
      ]},
      { name: "Finance & procurement", description: "We monitor cash collection, expenses, budgets, and payment processing — catching anomalies and variance before they become problems.", ucs: [
        { id: "23.6.1", why: "We show outstanding receivables by age — so you collect cash before debts go bad." },
        { id: "23.6.2", why: "We detect unusual expense patterns — so policy violations and potential fraud are caught early." },
        { id: "23.6.4", why: "We monitor payment gateway success rates — because every declined payment is lost revenue." }
      ]},
      { name: "Customer support", description: "We measure support quality — resolution times, first-contact resolution, customer effort — so you deliver excellent service efficiently.", ucs: [
        { id: "23.7.1", why: "We show ticket volume, backlog, and SLA compliance — so support leaders know where to focus." },
        { id: "23.7.2", why: "We track first-contact resolution rates — because resolving issues without escalation saves money and makes customers happier." },
        { id: "23.7.3", why: "We measure how much effort customers expend to get help — so you can simplify the hardest experiences." }
      ]},
      { name: "Executive dashboards", description: "We build the board-level view — 8-12 KPIs covering revenue, customers, people, and risk on a single page that's always current.", ucs: [
        { id: "23.8.1", why: "A single scorecard with the metrics the CEO and CFO check every week — always live, never stale." },
        { id: "23.8.2", why: "Operational efficiency metrics — revenue per employee, automation rate, cost per transaction — showing if you're getting more productive." },
        { id: "23.8.3", why: "A consolidated risk heatmap across financial, operational, customer, people, and cyber domains — one view of all business risks." }
      ]},
      { name: "ESG & sustainability", description: "We track environmental, social, and governance metrics — carbon emissions, energy use, waste, water, and reporting readiness for mandatory disclosures.", ucs: [
        { id: "23.9.1", why: "We track carbon emissions across Scope 1, 2, and 3 — so you measure progress toward net-zero commitments." },
        { id: "23.9.2", why: "We monitor energy consumption per facility — so you find waste and prove efficiency improvements." },
        { id: "23.9.5", why: "We check whether your ESG data is complete before reporting deadlines — so there are no last-minute scrambles." }
      ]}
    ]
  }
};
