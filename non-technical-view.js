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
      ]}
    ]
  },
  "5": {
    outcomes: [
      "Know when routers, switches, or firewalls have problems.",
      "See when links go down or routing gets confused.",
      "Spot hardware issues like bad power supplies or fans."
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
      ]}
    ]
  },
  "8": {
    outcomes: [
      "Know when your websites or apps are slow or throwing errors.",
      "See when certificates are about to expire.",
      "Spot when message queues or app servers are backing up."
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
      "Track email and web security events in one place."
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
      "Track Teams, meetings, and collaboration health."
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
      ]}
    ]
  },
  "12": {
    outcomes: [
      "See when builds or deployments fail.",
      "Know when secrets or credentials leak into code.",
      "Track pipeline health and security scan results."
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
      ]}
    ]
  },
  "13": {
    outcomes: [
      "Know when the monitoring system itself is overloaded or slow.",
      "See when search heads or indexers have problems.",
      "Track forwarders and data flow so nothing is missed."
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
      ]}
    ]
  },
  "14": {
    outcomes: [
      "See when building systems or industrial equipment misbehaves.",
      "Know when sensors or controllers report problems.",
      "Spot environmental or safety-related events."
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
