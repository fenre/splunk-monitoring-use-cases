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
      { name: "Routers & switches", description: "Are your network devices healthy? We watch for link failures, routing problems, and hardware issues.", ucs: [
        { id: "5.1.1", why: "See when network links go up or down — the most fundamental network alert." },
        { id: "5.1.4", why: "Track BGP peer state changes — this affects how traffic reaches the internet." },
        { id: "5.1.11", why: "Get an alert when a power supply or cooling fan fails in a network device." }
      ]},
      { name: "Firewalls", description: "Your security perimeter. We track blocked traffic, policy changes, and threat events.", ucs: [
        { id: "5.2.2", why: "Audit every firewall policy change so you know what was modified and by whom." },
        { id: "5.2.3", why: "Surface threat detection events — the firewall caught something suspicious." },
        { id: "5.2.10", why: "Track admin logins to firewalls — who logged in, from where, and when." }
      ]},
      { name: "Load balancers", description: "The devices that spread traffic across your servers. We watch pool health and availability.", ucs: [
        { id: "5.3.1", why: "Alert when a server drops out of the load balancer pool — less capacity for users." },
        { id: "5.3.2", why: "Know when a virtual server address goes down — the application is completely unreachable." },
        { id: "5.3.6", why: "Detect when response times increase — users are waiting longer than they should." }
      ]},
      { name: "WiFi & wireless", description: "WiFi access points, rogue devices, and signal quality. We help you keep wireless reliable and secure.", ucs: [
        { id: "5.4.4", why: "Detect unauthorised access points that could be used for eavesdropping." },
        { id: "5.4.1", why: "Know immediately when a wireless access point goes offline." },
        { id: "5.4.2", why: "Track client connection failures — frustrated users and potential issues." }
      ]},
      { name: "SD-WAN", description: "Software-defined WAN links connecting your branch offices. We watch tunnel health and application performance.", ucs: [
        { id: "5.5.1", why: "Monitor tunnel health — loss, latency, and jitter directly affect application experience." },
        { id: "5.5.2", why: "Know when a remote site goes offline — the edge device has stopped responding." },
        { id: "5.5.3", why: "Detect when business-critical apps violate their performance targets over the WAN." }
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
      { name: "Cisco Meraki", description: "Cloud-managed networking — access points, switches, security appliances, cameras, and sensors. All in one view.", ucs: [
        { id: "5.9.19", why: "Make sure all access points are online and catch unexpected outages." },
        { id: "5.9.43", why: "See which firewall rules are being hit and what traffic is being denied." },
        { id: "5.9.85", why: "Get alerts when environmental sensors detect temperatures outside safe ranges." }
      ]},
      { name: "Internet & digital experience", description: "How does the network look from your users' perspective? ThousandEyes tests the path from users to apps — across the internet, cloud, and SD-WAN.", ucs: [
        { id: "5.10.1", why: "Track network delay from agents to servers — slow paths mean slow apps." },
        { id: "5.10.18", why: "Get alerted when an internet outage is detected that affects your services." },
        { id: "5.10.25", why: "Monitor remote worker connectivity health — is the network causing their issues?" }
      ]},
      { name: "Carrier signaling", description: "The protocols that power mobile networks and voice calls. We watch for failures that affect subscribers.", ucs: [
        { id: "5.11.1", why: "Track signaling health — failures here mean subscribers can't authenticate or use data." },
        { id: "5.11.4", why: "Monitor voice trunk success rates — failed calls mean lost revenue and unhappy customers." },
        { id: "5.11.5", why: "Detect registration storms that can overwhelm voice infrastructure within minutes." }
      ]},
      { name: "Call records & voice analytics", description: "Call records from voice platforms. We analyse call patterns, failures, and trends.", ucs: [
        { id: "5.12.1", why: "Track call failure statistics — rising failure rates mean network or routing problems." },
        { id: "5.12.5", why: "Monitor voice quality scores — low scores mean poor call quality for users." },
        { id: "5.12.10", why: "Detect toll fraud — unauthorised calls running up huge charges." }
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
      { name: "Network services", description: "Essential network services like email delivery, file transfer, and infrastructure tools. We check they're running.", ucs: [
        { id: "8.6.3", why: "Monitor email delivery service availability — if it goes down, no emails get sent." },
        { id: "8.6.5", why: "Watch email queue depth — backed-up queues mean delayed messages." },
        { id: "8.6.9", why: "Track mail server certificates so email delivery doesn't break." }
      ]},
      { name: "Synthetic testing", description: "ThousandEyes probes your websites and APIs from around the world. We show when things slow down or break.", ucs: [
        { id: "8.7.1", why: "Track website availability and response time from multiple global locations." },
        { id: "8.7.4", why: "Monitor page load completion — know when users can't fully load your site." },
        { id: "8.7.8", why: "Run scripted tests that simulate real user workflows end to end." }
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
      { name: "Location & spaces", description: "Cisco Spaces — building occupancy, workspace usage, and environmental monitoring.", ucs: [
        { id: "11.4.1", why: "Track building occupancy over time to plan space and manage capacity." },
        { id: "11.4.3", why: "Monitor temperature, humidity, and air quality in your spaces." },
        { id: "11.4.6", why: "Detect ghost bookings — rooms reserved but never used." }
      ]},
      { name: "Video conferencing", description: "Zoom, Webex, and Teams meeting quality. We help you identify connection problems and poor video quality.", ucs: [
        { id: "11.5.1", why: "Track Zoom meeting quality metrics — jitter and packet loss mean poor video and audio." },
        { id: "11.5.4", why: "Monitor the health of Webex room devices so meetings start on time." },
        { id: "11.5.8", why: "Analyse Teams meeting quality across your organisation." }
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
      { name: "Building management", description: "HVAC, UPS, power consumption, and access control. We help you keep buildings comfortable, secure, and running.", ucs: [
        { id: "14.1.1", why: "Monitor heating and cooling performance — system failures mean uncomfortable or unsafe conditions." },
        { id: "14.1.2", why: "Track UPS battery health — when power fails, this is your last line of defence." },
        { id: "14.1.4", why: "Audit who entered which doors and when — for safety and compliance." }
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
        { id: "16.2.11", why: "Discover shadow IT — systems running that aren't in your official inventory." }
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
      { name: "Zero Trust & SASE", description: "Conditional access, device trust, and micro-segmentation. We help you verify every connection.", ucs: [
        { id: "17.3.1", why: "Track conditional access enforcement — are the right policies being applied?" },
        { id: "17.3.2", why: "Monitor device trust scores — low scores mean devices aren't meeting security requirements." },
        { id: "17.3.3", why: "Audit micro-segmentation — is traffic properly restricted between network zones?" }
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
      { name: "Hyper-converged infrastructure", description: "Nutanix, vSAN, VxRail, and similar. We track cluster health, storage capacity, and node balance.", ucs: [
        { id: "19.2.1", why: "Watch overall cluster health — a degraded cluster puts workloads at risk." },
        { id: "19.2.5", why: "Get alerted when a disk fails so it can be replaced before data is lost." },
        { id: "19.2.2", why: "Track storage pool capacity — running out of storage stops everything." }
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
      { name: "Healthcare", description: "Clinical systems, cold chain compliance, and patient flow. We help healthcare organisations deliver care reliably.", ucs: [
        { id: "21.3.1", why: "Monitor EHR response times — slow clinical systems waste clinician time and delay care." },
        { id: "21.3.5", why: "Alert when pharmaceutical cold chain temperatures drift — protecting vaccine and medication integrity." },
        { id: "21.3.7", why: "Track electronic signature audit trails for FDA 21 CFR Part 11 compliance." }
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
      "See how well you meet the requirements of regulations like GDPR, NIS2, DORA, and more.",
      "Get evidence for auditors and compliance reviews automatically.",
      "Spot compliance gaps before regulators or auditors find them."
    ],
    areas: [
      { name: "Privacy regulations", description: "GDPR and CCPA — tracking personal data, handling data requests, and monitoring for breaches.", ucs: [
        { id: "22.1.1", why: "Detect personal data appearing in application logs where it shouldn't be — a GDPR risk." },
        { id: "22.1.3", why: "Monitor breach notification timelines — GDPR requires notification within 72 hours." },
        { id: "22.4.1", why: "Track CCPA consumer data requests — access and deletion requests must be handled on time." }
      ]},
      { name: "Cybersecurity frameworks", description: "NIS2, ISO 27001, and NIST CSF — measuring your security posture against recognised standards.", ucs: [
        { id: "22.2.1", why: "Track NIS2 incident detection and 24-hour early warning reporting obligations." },
        { id: "22.6.1", why: "Monitor how well your ISO 27001 security controls are working across the board." },
        { id: "22.7.1", why: "Dashboard your NIST CSF maturity across all five functions — Identify, Protect, Detect, Respond, Recover." }
      ]},
      { name: "Financial regulation", description: "DORA, MiFID II, and SOC 2 — resilience testing, transaction reporting, and trust service compliance.", ucs: [
        { id: "22.3.1", why: "DORA ICT risk management dashboard — track digital resilience for financial services." },
        { id: "22.5.1", why: "Monitor MiFID II trade reporting completeness — missing reports mean regulatory fines." },
        { id: "22.8.1", why: "Continuous monitoring of SOC 2 trust service criteria — evidence collection for auditors." }
      ]}
    ]
  }
};
