---
title: Infrastructure Monitoring Domain Master Guide — Server & Compute (cat-1), Virtualization (cat-2), Network Infrastructure (cat-5), Storage & Backup (cat-6), Data Center Physical Infrastructure (cat-15), Data Center Fabric & SDN (cat-18), Compute Infrastructure (cat-19) end-to-end with Splunk Enterprise Security, Splunk SOAR, Splunk ITSI, Splunk OpenTelemetry Collector, Cisco Catalyst Center / Catalyst SD-WAN / Meraki / ThousandEyes / ACI / Nexus Dashboard / UCS / Intersight, VMware vSphere + NSX, Hyper-V, KVM / Proxmox / oVirt, Citrix / VDI, NetApp ONTAP, Dell PowerStore / Unity / PowerScale (Isilon), Pure Storage, Veeam, Commvault, Ceph, BMS / UPS / HVAC, Cisco Connected Lighting / DNA Spaces
type: domain-guide
domains: [Infrastructure, Servers, Virtualization, Network, Storage, Data Center Physical, SDN, Compute]
categories: [1, 2, 5, 6, 15, 18, 19]
product: Splunk Enterprise Security (ES) 8 + Splunk SOAR + Splunk Mission Control + Splunk IT Service Intelligence (ITSI) + Splunk OpenTelemetry Collector + Splunk Stream + Splunk Add-on for Unix and Linux (Splunk_TA_nix) + Splunk Add-on for Microsoft Windows (Splunk_TA_windows) + Splunk Add-on for Microsoft Active Directory + Splunk Add-on for VMware + Splunk Add-on for Microsoft Hyper-V + Splunk Add-on for Cisco IOS (TA-cisco_ios) + Splunk Add-on for Cisco ASA + Splunk Add-on for Cisco UCS + Splunk Add-on for Cisco ACI + Cisco Catalyst Add-on for Splunk + Cisco Enterprise Networking App for Splunk + Cisco DC Networking App for Splunk + Cisco ThousandEyes Add-on for Splunk + Splunk Add-on for Cisco Meraki + Splunk Add-on for Cisco Catalyst SD-WAN + Splunk Add-on for NetApp Data ONTAP + Splunk Add-on for Dell PowerStore + Splunk Add-on for Pure Storage + Splunk Add-on for Veeam Backup & Replication + Splunk Add-on for Commvault + Splunk Add-on for Infoblox + Splunk Add-on for F5 BIG-IP + Splunk Add-on for Palo Alto Networks + Splunk Add-on for Fortinet FortiGate + Splunk Add-on for Aruba Central + Splunk Add-on for Juniper + Splunk Add-on for Arista + Splunk Connect for Syslog (SC4S) + Splunk Connect for SNMP (SC4SNMP) + Splunk Edge Hub + Splunk Edge Processor
product_aliases: [infrastructure, infrastructure monitoring, infra monitoring, infra mon, infra ops, IT operations, ITOps, IT ops, IT operations management, ITOM, IT infrastructure management, ITIM, IT operations analytics, ITOA, AIOps, AI Ops, hybrid cloud monitoring, on-premises, on-prem, on premises, datacenter, data center, data centre, data centres, DC, on-prem datacenter, colocation, colo, hosting, dedicated server, bare metal, bare-metal, baremetal, server, servers, server estate, server fleet, server inventory, host, hosts, hostname, host fleet, host inventory, endpoint, endpoint host, end-point, server os, operating system, OS monitoring, server health, host health, system health, system monitoring, sysmon, sys mon, system monitoring agent, agent-based monitoring, agentless monitoring, agentless, agent, monitoring agent, telemetry agent, observability agent, OTel agent, OpenTelemetry agent, OpenTelemetry collector, OTel collector, otelcol, OTel SDK, OpenTelemetry SDK, gauges metrics histograms, prometheus metrics, prometheus exporter, node exporter, blackbox exporter, exporters, statsd, statsd exporter, telegraf, fluentd, fluent bit, fluentbit, vector, vector observability, beats, filebeat, metricbeat, packetbeat, heartbeat, auditbeat, winlogbeat, journalbeat, syslog-ng, rsyslog, syslog over TLS, syslog over TCP, syslog over UDP, syslog forwarder, log forwarder, log shipper, log aggregator, log aggregation, log collection, log management, SIEM source, SIEM data source, SIEM connector, SIEM forwarder, syslog priority, RFC 3164, RFC 5424, syslog framing, octet counting framing, non-transparent framing, syslog severity, syslog facility, syslog parser, syslog regex, syslog pipeline, splunk syslog, splunk universal forwarder, splunk uf, universal forwarder, UF, splunk heavy forwarder, splunk hf, heavy forwarder, HF, splunk indexer, indexer cluster, splunk search head, search head, search head cluster, SHC, splunk deployment server, deployment server, splunk monitoring console, monitoring console, MC, splunk DMC, splunk distributed management console, splunk forwarder management, splunk btool, btool, splunk inputs.conf, splunk props.conf, splunk transforms.conf, splunk indexes.conf, splunk outputs.conf, splunk server.conf, splunk web.conf, splunk authentication.conf, splunk passwords.conf, conf file, conf files, splunk app, splunk add-on, splunk TA, splunk technology add-on, technology add-on, TA, splunk app for, splunk add-on for, splunkbase, splunk Base, splunk-base, splunk base app, splunkbase app, splunkbase TA, splunk app vetting, app vetting, splunk cloud vetting, splunk cloud appinspect, AppInspect, splunk AppInspect, AppInspect API, splunk SmartStore, SmartStore, S2, splunk indexer SmartStore, splunk indexer cache, splunk hot bucket, splunk warm bucket, splunk cold bucket, splunk frozen, splunk frozen bucket, splunk archive, splunk DataSets, DataSets, splunk DataSet, splunk dataset rollup, splunk dataset summary, splunk dataset metric, splunk dataset acceleration, splunk DataModel, data model, splunk data model, datamodel, accelerated data model, DMA, data model acceleration, splunk index acceleration, tsidx, splunk tsidx, tsidx file, tsidx files, splunk knowledge bundle, knowledge bundle, kb bundle, splunk lookup, lookup file, lookup table, KV Store, kvstore, splunk kvstore, splunk kv store, splunk kv-store, splunk savedsearches.conf, savedsearches.conf, splunk macros.conf, splunk macro, splunk eventtype, eventtypes.conf, splunk tag, tags.conf, splunk workflow_actions.conf, workflow actions, splunk role, splunk capability, capability, splunk authentication, authentication.conf, splunk SAML, splunk LDAP, splunk PingFederate, splunk Okta, splunk Auth0, splunk SCIM, splunk RBAC, role-based access control, splunk index ACL, index ACL, ACL, splunk authz, authz, splunk authz token, splunk auth token, splunk session token, splunk credentials, splunk passwords.conf, splunk login, splunk SSO, single sign-on, MFA, multi-factor authentication, splunk MFA, server lifecycle, server provisioning, server commissioning, decommissioning, decommission, decom, decommissioned, server decommissioning, asset retirement, EOL, end of life, EOSL, end of service life, EoL, EoSL, hardware refresh, hardware refresh cycle, server refresh, OS migration, server migration, lift and shift, lift-and-shift, rehost, replatform, refactor, retire, repurchase, server consolidation, datacenter consolidation, server retirement, retirement, hardware retirement, lifecycle management, hardware lifecycle, software lifecycle, ALM, application lifecycle, asset management, IT asset management, ITAM, configuration management database, CMDB, ServiceNow CMDB, BMC Helix CMDB, Atrium CMDB, configuration item, CI, CI lifecycle, CI relationship, dependency mapping, application dependency mapping, ADM, network dependency, network dependency mapping, NDM, server dependency mapping, business service mapping, BSM, application service mapping, ASM, ServiceNow Discovery, BMC Discovery, ADDM, application dependency and discovery, ADDM, BMC Atrium Discovery, BMC ADDM, Discovery, agentless discovery, network discovery, IPAM, IP address management, IPAM tool, IPAM solution, address management, NetBox, NetBox plugin, NetBox webhook, NetBox API, NetBox export, Nautobot, Nautobot plugin, Nautobot job, Nautobot apps, Source of Truth, SoT, source of truth, network source of truth, NSoT, golden config, golden configuration, configuration drift, config drift, infrastructure drift, infra drift, IaC drift, infrastructure as code drift, IaC, infrastructure as code, terraform, Terraform Cloud, Terraform Enterprise, OpenTofu, opentofu, ansible, Ansible Tower, Ansible Automation Platform, AAP, Red Hat Ansible Automation Platform, AWX, AWX project, Ansible playbook, Ansible role, Ansible inventory, Ansible Lightspeed, ansible-lint, Salt Stack, SaltStack, Salt master, Salt minion, salt-cloud, salt cloud, puppet, Puppet Enterprise, PE, Puppet Hiera, Puppet Bolt, chef, Chef Infra, Chef Inspec, Chef Habitat, Chef Effortless, vRO, vRealize Orchestrator, VMware Aria Automation, vRA, Aria Automation, vRealize Operations, vROps, Aria Operations, vRealize Log Insight, Aria Operations for Logs, vRealize Network Insight, vRNI, Aria Operations for Networks, NetApp Active IQ Unified Manager, AIQUM, NetApp BlueXP, BlueXP, BlueXP economic efficiency, NetApp Cloud Manager, NetApp Cloud Insights, Cloud Insights, NetApp Spot, Spot, Spot by NetApp, Dell APEX, APEX, Dell APEX Cloud Services, APEX Block, Dell PowerProtect, PowerProtect, PowerProtect Data Manager, PPDM, PowerProtect DD, PowerProtect Data Domain, DDVE, Data Domain Virtual Edition, Dell CloudIQ, CloudIQ, Pure1, Pure Storage Pure1, Pure Cloud Block Store, CBS, Pure FlashArray, FlashArray, FlashBlade, Pure FlashBlade, FlashBlade File, FlashBlade Object, Pure Portworx, Portworx, Portworx Enterprise, PX, Pure Evergreen, Evergreen, Evergreen Forever, Evergreen Storage, Evergreen Subscription, NetApp ONTAP, ONTAP, ONTAP REST, ONTAP CLI, ONTAP Manager, ONTAP System Manager, ONTAP Active IQ, AIQ, ONTAP REST API, ONTAP EMS, NetApp Data Fabric, NetApp Astra, Astra, NetApp Astra Trident, Trident, Astra Control, NetApp ONTAP Select, NetApp ONTAP S3, ONTAP S3 storage, NetApp StorageGRID, StorageGRID, StorageGRID Webscale, NetApp E-Series, E-Series, NetApp SolidFire, SolidFire, NetApp Element, Element, NetApp HCI, NetApp Keystone, Keystone, NetApp Spot Wave, Spot Ocean, Spot Eco, Dell EMC, Dell EMC PowerScale, PowerScale, Dell EMC Isilon, Isilon, Isilon OneFS, OneFS, OneFS REST, OneFS API, Isilon SyncIQ, SyncIQ, Isilon SmartConnect, SmartConnect, OneFS Insightiq, InsightIQ, Dell EMC Unity, Unity, Unity XT, Unity Hybrid, UnityVSA, Unisphere, Unisphere REST, Dell EMC PowerStore, PowerStore, PowerStore X, PowerStore T, PowerStore Manager, Dell EMC PowerMax, PowerMax, Symmetrix, VMAX, VMAX All Flash, VMAX3, Solutions Enabler, SymCLI, Dell EMC PowerVault, PowerVault, MD3, MD32, ME4, ME5, Dell EMC ECS, ECS, Elastic Cloud Storage, Dell ObjectScale, ObjectScale, Dell EMC Avamar, Avamar, Avamar Virtual Edition, AVE, Dell EMC NetWorker, NetWorker, NetWorker Management Console, NMC, Dell EMC RecoverPoint, RecoverPoint, RP4VMs, RecoverPoint for VMs, Dell EMC ScaleIO, ScaleIO, VxFlex, VxFlex OS, PowerFlex, PowerFlex OS, PowerFlex Manager, Dell PowerFlex, Dell EMC VxRail, VxRail, VxRail Manager, VxRail Appliance, Dell EMC VxBlock, VxBlock, Vblock, Dell EMC VPLEX, VPLEX, VPLEX Local, VPLEX Metro, VPLEX Geo, Dell EMC Symmetrix VMAX, Symmetrix VMAX, Mainframe Storage, IBM DS, DS8000, DS8K, IBM FlashSystem, FlashSystem, FlashSystem 7000, FlashSystem 9000, IBM SVC, SAN Volume Controller, SVC, IBM Spectrum Storage, Spectrum, IBM Spectrum Virtualize, Spectrum Virtualize, IBM Spectrum Scale, Spectrum Scale, GPFS, IBM Cloud Object Storage, COS, IBM Spectrum Protect, Spectrum Protect, TSM, Tivoli Storage Manager, IBM Storage, Veeam, Veeam Backup & Replication, VBR, Veeam B&R, Veeam ONE, Veeam Service Provider Console, VSPC, Veeam Cloud Connect, VCC, Veeam Backup Enterprise Manager, VBEM, Veeam Backup for Microsoft 365, VBO, Veeam Backup for Microsoft Azure, Veeam Backup for AWS, Veeam Kasten, Kasten, Kasten K10, Kasten K8s, Kasten by Veeam, Commvault, Commvault Complete Data Protection, Commvault HyperScale, Commvault Metallic, Metallic, Commvault Cloud, CommServe, CommCell, Commvault Activate, Commvault Hedvig, Hedvig, Commvault Auto Recovery, Cohesity, Cohesity DataPlatform, Cohesity DataProtect, Cohesity Helios, Cohesity Marketplace, Rubrik, Rubrik Security Cloud, RSC, Rubrik Polaris, Polaris, Rubrik Sonar, Sonar, Rubrik Radar, Radar, Druva, Druva CloudRanger, Druva inSync, Druva Phoenix, Veritas NetBackup, NetBackup, NBU, NetBackup Appliance, NetBackup Flex, Veritas Backup Exec, Backup Exec, BE, Veritas Enterprise Vault, Enterprise Vault, EV, Veritas APTARE IT Analytics, APTARE, NAKIVO, NAKIVO Backup & Replication, Acronis Cyber Backup, Acronis, Acronis Cyber Protect, Arcserve, Arcserve UDP, Arcserve Backup, Unitrends, Unitrends Recovery Series, BackupAssist, BackupAssist Classic, MSP360, CloudBerry, MSP360 Backup, Quest NetVault, NetVault, Quest QoreStor, QoreStor, vSphere, VMware vSphere, VMware ESXi, ESXi, vCenter, vCenter Server, vCenter Server Appliance, VCSA, vSphere Client, vSphere Web Client, vSphere host client, vSphere DRS, DRS, Distributed Resource Scheduler, vSphere HA, HA, vSphere High Availability, vSphere FT, vSphere Fault Tolerance, vMotion, vMotion compatibility, EVC, Enhanced vMotion Compatibility, Storage vMotion, vDS, vSwitch, virtual switch, distributed virtual switch, VMware NSX, NSX-T, NSX-V, NSX Manager, NSX Edge, NSX Controller, NSX-T Manager, NSX-T Edge, NSX Distributed Firewall, DFW, Geneve, Geneve overlay, NSX Federation, NSX Intelligence, NSX Advanced Threat Prevention, NSX ATP, NSX Network Detection and Response, NDR, vSAN, VMware vSAN, vSAN ESA, vSAN OSA, vSAN Express Storage Architecture, vSAN Original Storage Architecture, vSphere with Tanzu, Tanzu Mission Control, TMC, Tanzu Application Service, TAS, Tanzu Kubernetes Grid, TKG, Tanzu Standard, Tanzu Advanced, Pivotal Container Service, PKS, vRealize, vRealize Suite, vROps, vRealize Operations, VMware Aria Operations, vRA, vRealize Automation, VMware Aria Automation, vRLI, vRealize Log Insight, VMware Aria Operations for Logs, vRNI, vRealize Network Insight, VMware Aria Operations for Networks, vRBC, vRealize Business for Cloud, VMware Aria Cost, Cost Insight, vCloud Director, vCD, VMware Cloud Director, vCloud Foundation, VCF, VMware Cloud Foundation, VCF SDDC, SDDC Manager, VMware Cloud, VMC, VMC on AWS, VMware Cloud on AWS, VMware Cloud on Dell EMC, AVS, Azure VMware Solution, GCVE, Google Cloud VMware Engine, OCVS, Oracle Cloud VMware Solution, IBM Cloud for VMware, VMware Horizon, Horizon, Horizon View, Horizon Universal Subscription, Horizon Cloud, App Volumes, Dynamic Environment Manager, DEM, ThinApp, VMware Workspace ONE, Workspace ONE, WS1, WS1 UEM, AirWatch, VMware AirWatch, Carbon Black, Carbon Black Cloud, CBC, VMware Carbon Black, CBC Endpoint, CBC Workload, CBC Container Security, CBC App Control, CB Defense, CB Response, CB ThreatHunter, CB Audit and Remediation, Hyper-V, Microsoft Hyper-V, Hyper-V Server, Hyper-V Manager, SCVMM, System Center Virtual Machine Manager, Failover Cluster, Failover Clustering, Cluster Shared Volume, CSV, ReFS, Resilient File System, Storage Spaces, Storage Spaces Direct, S2D, Azure Stack HCI, Azure Stack Hub, Azure Stack Edge, Azure Local, Microsoft Azure Local, Hyper-V Replica, HV Replica, Hyper-V Live Migration, KVM, Kernel-based Virtual Machine, libvirt, libvirtd, virsh, virt-manager, virt-viewer, qemu, QEMU, qemu-kvm, qcow2, qcow, raw image, OVA, OVF, Open Virtualization Format, Proxmox, Proxmox VE, Proxmox VE Cluster, Proxmox Backup Server, PBS, oVirt, oVirt Engine, RHV, Red Hat Virtualization, KubeVirt, OpenShift Virtualization, Citrix XenServer, XenServer, Citrix Hypervisor, Citrix Virtual Apps, Citrix Virtual Desktops, CVAD, Citrix DaaS, Citrix Cloud, Citrix StoreFront, StoreFront, Citrix Receiver, Citrix Workspace App, Citrix Workspace, Citrix ADC, NetScaler ADC, NetScaler, Citrix Gateway, NetScaler Gateway, Citrix Director, Director, Citrix Studio, Studio, Citrix Provisioning, PVS, Citrix MCS, Machine Creation Services, Citrix Profile Management, UPM, FlexCast Management Architecture, FMA, IPMI, IPMI 2.0, BMC, baseboard management controller, iDRAC, Dell iDRAC, iLO, HP iLO, HPE iLO, Cisco IMC, CIMC, Cisco Integrated Management Controller, Lenovo XCC, XClarity Controller, IBM IMM, IMM2, Supermicro IPMI, Supermicro BMC, Redfish, DMTF Redfish, Redfish API, Redfish event, AHCI, NVMe, NVMe over Fabrics, NVMe-oF, FC-NVMe, ROCE, RoCE, RDMA over Converged Ethernet, iWARP, InfiniBand, IB, EDR InfiniBand, HDR InfiniBand, NDR InfiniBand, Mellanox, NVIDIA Mellanox, ConnectX, BlueField, NVIDIA BlueField, BlueField DPU, DPU, data processing unit, SmartNIC, SmartDPU, ZTE, ZTE 5G, EDAC, ECC, ECC memory, error correcting code, ECC RAM, IPMI sensor, IPMI SEL, system event log, SEL, BMC SEL, predictive failure, PFA, predictive failure analysis, drive predictive failure, S.M.A.R.T., SMART data, SMART attribute, drive health, disk health, drive failure, predictive disk failure, RAID, RAID controller, RAID 0, RAID 1, RAID 5, RAID 6, RAID 10, RAID 50, RAID 60, hardware RAID, software RAID, mdraid, ZFS, ZFS RAIDZ, RAIDZ1, RAIDZ2, RAIDZ3, btrfs, lvm, LVM, logical volume manager, LVM thin provisioning, LVM snapshot, multipath, dm-multipath, multipathd, MPIO, FC SAN, fibre channel, FC, FC switch, Brocade FC, Cisco MDS, Cisco MDS 9000, Cisco MDS NX-OS, FC SAN port channel, FC zoning, soft zoning, hard zoning, NPIV, N_Port ID virtualization, FCoE, fibre channel over ethernet, FCIP, fibre channel over IP, iSCSI, iSCSI target, iSCSI initiator, iSCSI MPIO, iSCSI portal, iSCSI offload, NFS, NFS v3, NFS v4, NFS v4.1, NFS v4.2, NFSv3, NFSv4, NFSv4.1, NFSv4.2, NFS server, NFS client, NFS export, NFS mount, NFSroot, pNFS, parallel NFS, SMB, SMB2, SMB3, SMB 1.0, SMB1, SMB 2.0, SMB 3.0, SMB 3.1.1, CIFS, SMB share, SMB client, SMB server, NetBIOS, NetBIOS over TCP, NBT, NBT-NS, LLMNR, mDNS, DDNS, dynamic DNS, AAAA record, SRV record, CNAME, PTR record, A record, MX record, TXT record, SPF, SPF record, DMARC, DKIM, DNSSEC, DNS over TLS, DoT, DNS over HTTPS, DoH, EDNS0, DNSCrypt, recursive resolver, authoritative DNS, Anycast DNS, anycast, BGP anycast, OSPFv3, IS-IS, intermediate system to intermediate system, EIGRP, RIP, RIPv2, BGP, BGP confederation, BGP route reflector, RR, BGP MED, MED, AS_PATH, AS path, ASN, ASBR, autonomous system border router, ABR, area border router, NSSA, not so stubby area, MPLS, MPLS L3VPN, MPLS L2VPN, VPLS, EVPN, EVPN VXLAN, EVPN MPLS, BFD, bidirectional forwarding detection, BFD echo, micro-BFD, NETCONF, RESTCONF, gNMI, gNMI dial-in, gNMI dial-out, gNMI subscribe, gNMI ON_CHANGE, gNMI SAMPLE, gNMI POLL, OpenConfig, OpenConfig YANG, IETF YANG, YANG model, YANG, NETCONF protocol, RESTCONF protocol, model-driven telemetry, MDT, model driven telemetry, gRPC, gRPC dial-in, gRPC dial-out, gRPC streaming, sFlow, sFlow v5, IPFIX, IPFIX templates, NetFlow, NetFlow v5, NetFlow v9, Flexible NetFlow, FNF, NTA, network traffic analysis, NPB, network packet broker, packet broker, packet broker SPAN, SPAN, RSPAN, ERSPAN, port mirroring, traffic mirroring, network tap, optical tap, fiber tap, copper tap, NPM, network performance monitoring, NDP, network detection and response, NDR, NDR network, network detection and response, ZTNA, zero trust network access, SASE, secure access service edge, SSE, security service edge, CASB, cloud access security broker, SWG, secure web gateway, FWaaS, firewall as a service, ZTNA, SDP, software defined perimeter, micro-segmentation, microsegmentation, micro segmentation, cisco TrustSec, TrustSec, SXP, SGT, security group tag, scalable group tag, Cisco SGT, group based policy, GBP, software defined access, SDA, SDA fabric, fabric edge, fabric border, fabric control plane, FC, fabric WAN, FC-WAN, fusion router, transit network, IP transit, control plane node, edge node, EVPN-VXLAN fabric, ACI, Cisco ACI, Application Centric Infrastructure, APIC, Application Policy Infrastructure Controller, ACI tenant, ACI VRF, ACI BD, bridge domain, ACI EPG, endpoint group, ACI contract, contract subject, ACI L3Out, L3 outside, ACI L2Out, ACI multi-pod, multi-pod, ACI multi-site, multi-site, ACI Service Graph, service graph, PBR, policy based routing, ACI ESG, endpoint security group, ACI vzAny, vzAny, ACI MO, managed object, ACI DN, distinguished name, ACI fault, ACI event, ACI audit, NX-OS, Nexus 9000, Nexus 7000, Nexus 5000, Nexus 3000, Nexus 2000, FEX, fabric extender, vPC, virtual port-channel, vPC peer keepalive, vPC peer link, FabricPath, OTV, overlay transport virtualization, LISP, locator/ID separation protocol, VXLAN, VXLAN BGP EVPN, VTEP, VXLAN tunnel endpoint, ITE, ingress tunnel endpoint, ETE, egress tunnel endpoint, Nexus Dashboard, ND, NDFC, Nexus Dashboard Fabric Controller, NDI, Nexus Dashboard Insights, NDO, Nexus Dashboard Orchestrator, MSO, Multi-Site Orchestrator, NIA, Network Insights Advisor, NIR, Network Insights Resources, Cisco DCNM, Data Center Network Manager, DCNM, Cisco UCS, UCS, Cisco Unified Computing System, UCS Manager, UCSM, UCS Director, UCSD, UCS Central, UCS Mini, UCS B-Series, UCS C-Series, UCS X-Series, UCS S-Series, X-Fabric, IFM, Intersight Fabric Manager, UCS Fabric Interconnect, FI, Fabric Interconnect, UCS chassis, UCS blade, UCS rack, UCS service profile, UCS template, UCS pool, UCS policy, Cisco Intersight, Intersight, Intersight Workload Optimizer, IWO, Intersight Cloud Orchestrator, ICO, Intersight Kubernetes Service, IKS, Intersight Workload Engine, IWE, Intersight Virtualization, Intersight RMF, Intersight Cloud Connect, Intersight Assist, Intersight Service for Terraform, Intersight HyperFlex, Intersight saaS, HyperFlex, HX, HXDP, HyperFlex Data Platform, HyperFlex Edge, HX Edge, HyperFlex Connect, HX Connect, HyperFlex CSI, HX CSI, HyperFlex All-Flash, HX All-Flash, HyperFlex Standard, HyperFlex Plus, Cisco SmartZone, Cisco Crosswork, Cisco Crosswork Network Controller, CNC, Cisco WAN Automation Engine, WAE, Cisco Network Services Orchestrator, NSO, Cisco YANG Suite, YANG Suite, Cisco Modeling Labs, CML, Cisco Smart Account, Smart Account, Cisco Smart Software Manager, CSSM, Cisco DUO, Duo, Cisco Catalyst Center, Catalyst Center, DNA Center, DNAC, Cisco DNA Center, Catalyst Center Assurance, Catalyst Center Automation, SWIM, software image management, PnP, plug and play, plug-and-play, ZTP, zero touch provisioning, Day 0, Day 1, Day N, ThousandEyes, Cisco ThousandEyes, ThousandEyes Endpoint Agent, ThousandEyes Cloud Agent, ThousandEyes Enterprise Agent, ThousandEyes Internet Insights, ThousandEyes WAN Insights, ThousandEyes Test, ThousandEyes Browser Test, ThousandEyes HTTP Server Test, ThousandEyes Web Transactions, ThousandEyes Voice Test, ThousandEyes BGP Monitor, ThousandEyes Path Visualization, ThousandEyes OTel, ThousandEyesOTel, Cisco Catalyst SD-WAN, Catalyst SD-WAN, Cisco SD-WAN, vManage, vManage Cluster, vManage Multitenancy, vBond, vBond Orchestrator, vSmart, vSmart controller, OMP, Overlay Management Protocol, IPSec SD-WAN, vEdge, cEdge, Cisco vEdge, Cisco cEdge, Cisco SD-WAN policy, application aware routing, AAR, Cisco Meraki, Meraki, Meraki Dashboard, Meraki MX, Meraki MR, Meraki MS, Meraki MV, Meraki MT, Meraki Systems Manager, MSM, Meraki Insight, Meraki Webhook, Meraki API, Meraki Dashboard API, Meraki Sense, Meraki Vision, Cisco DNA Spaces, DNA Spaces, Spaces, Cisco Spaces, Cisco Spaces Connector, location services, indoor location, indoor positioning, RTLS, real-time location services, BLE beacon, Cisco Spaces SDK, Cisco IoT Operations Dashboard, IoT OD, Cisco Industrial Asset Vision, Cyber Vision, Cisco Cyber Vision, Industrial Network Director, IND, Cisco DNA Encrypted Traffic Analytics, ETA, Encrypted Traffic Analytics, Cisco Stealthwatch, Stealthwatch, Stealthwatch Enterprise, Stealthwatch Cloud, SWC, Cisco Secure Network Analytics, SNA, Secure Network Analytics, Cisco SD-Access, SDA, Software Defined Access, Cisco Identity Services Engine, ISE, Cisco ISE, ISE PSN, ISE PAN, ISE pxGrid, pxGrid, Cisco Secure Workload, Secure Workload, Tetration, Cisco Tetration, Tetration Analytics, Cisco AppDynamics, AppDynamics, AppDynamics Controller, AppDynamics SaaS, AppDynamics On-Prem, AppD, Splunk Network Data Stream, NDS, network data stream, splunk wire data, Splunk Stream, Splunk Stream forwarder, Splunk Stream wire data, network data stream, NetApp Active IQ, AIQ, AIQ Unified Manager, AIQUM, BlueXP, NetApp Cloud Insights, Cloud Insights, Pure1 Meta, F5 BIG-IP, F5, BIG-IP, LTM, GTM, ASM, AFM, APM, F5 LTM, F5 GTM, F5 ASM, F5 AFM, F5 APM, F5 Distributed Cloud, F5 XC, F5 NGINX, NGINX, NGINX Plus, NGINX App Protect, F5 iRule, iRule, iRules, iControl, iControlREST, iControl REST, iControlSOAP, F5 BIG-IQ, BIG-IQ, BIG-IQ Centralized Management, BIG-IQ DataCollection Device, F5 iApp, iApp, F5 iApps, F5 iWorkflow, iWorkflow, F5 LineRate, F5 SilverLine, BIG-IP DNS, BIG-IP Edge Client, F5 Access, F5 Carrier-Grade NAT, CGNAT, F5 Cloud Edition, BlueCat, BlueCat Address Manager, BAM, BlueCat DNS, BlueCat DHCP, BlueCat Adaptive Plugins, Infoblox, Infoblox NIOS, NIOS, Infoblox BloxOne, BloxOne, Infoblox DDI, DDI, DNS DHCP IPAM, Infoblox DNS Firewall, Infoblox Threat Insight, Infoblox Reporting, Infoblox Grid, Grid, Infoblox Cloud Network Automation, CNA, Infoblox Network Insight, Infoblox Discovery, Infoblox vDiscovery, Infoblox SecurityTrails, Microsoft DNS, Active Directory DNS, AD DNS, Microsoft DHCP, Microsoft DHCP Server, ISC BIND, BIND, BIND DNS, named, named.conf, BIND9, dnsmasq, Knot DNS, Unbound DNS, Unbound, NSD, PowerDNS, PowerDNS Authoritative, PowerDNS Recursor, recursor, dnsdist, NSD, OpenDNSSEC, KSK, ZSK, key signing key, zone signing key, RRSIG, NSEC, NSEC3, DS record, DNSKEY, NSD, BIND ACL, BIND view, response policy zone, RPZ, DNS RPZ, sinkhole DNS, DNS sinkhole, DNS firewall, recursive DNS, authoritative DNS, secondary DNS, slave DNS, master DNS, primary DNS, root DNS, root server, root hints, root zone, gTLD, ccTLD, ICANN, IANA, registrar, registry, EPP, extensible provisioning protocol, EPP-OT, RFC 5731, WHOIS, RDAP, registration data access protocol, certificate, certificate management, certificate lifecycle, ACME, ACME protocol, Let's Encrypt, certbot, certificate transparency, CT, CT log, CRL, certificate revocation list, OCSP, online certificate status protocol, OCSP stapling, must staple, X.509, X509, PKI, public key infrastructure, root CA, intermediate CA, subordinate CA, certificate authority, CA, code signing, code signing cert, EV cert, OV cert, DV cert, wildcard cert, SAN cert, multi-domain cert, MicrosoftCA, Microsoft Enterprise CA, EJBCA, OpenSSL, openssl s_client, openssl x509, mkcert, easy-rsa, smallstep, step-ca, HashiCorp Vault PKI, Vault PKI, Vault Enterprise, Vault HCP, OpenBao, openbao, Boundary, Consul, Consul Connect, Consul service mesh, Nomad, Waypoint, Packer, Vagrant, Vagrant Cloud, vault agent, vault sidecar, secret rotation, dynamic secret, password rotation, root password rotation, ssh ca, SSH certificate authority, ssh certificate, ssh-cert, ssh public key, ssh private key, ed25519, RSA 2048, RSA 4096, ECDSA, secp256r1, P-256, P-384, P-521, secp384r1, secp521r1, X25519, X25519MLKEM768, ML-KEM, ML-DSA, post-quantum, post quantum, post quantum cryptography, PQC, NIST PQC, hybrid kex, hybrid key exchange]
splunkbase_urls:
  - https://splunkbase.splunk.com/app/833
  - https://splunkbase.splunk.com/app/742
  - https://splunkbase.splunk.com/app/1352
  - https://splunkbase.splunk.com/app/3457
  - https://splunkbase.splunk.com/app/4022
  - https://splunkbase.splunk.com/app/5580
  - https://splunkbase.splunk.com/app/6656
  - https://splunkbase.splunk.com/app/6657
  - https://splunkbase.splunk.com/app/7538
  - https://splunkbase.splunk.com/app/7539
  - https://splunkbase.splunk.com/app/7777
  - https://splunkbase.splunk.com/app/7719
indexes:
  - os
  - os_metrics
  - wineventlog
  - perfmon
  - linux_secure
  - auditd
  - vmware
  - vmware_perf
  - vmware_inv
  - hyperv
  - kvm
  - citrix
  - networking
  - cisco_syslog
  - cisco_dnac
  - cisco_meraki
  - cisco_aci
  - cisco_ucs
  - sdwan
  - vmanage
  - storage
  - netapp
  - powerstore
  - pure
  - veeam
  - commvault
  - facilities
  - ups_pdu
  - hvac_bms
  - physical_security
  - smart_licensing
sourcetypes:
  - cpu
  - vmstat
  - df
  - ps
  - top
  - WinHostMon
  - WinEventLog:Security
  - WinEventLog:System
  - WinEventLog:Application
  - PerfMon:CPU
  - PerfMon:Memory
  - PerfMon:LogicalDisk
  - PerfMon:Network
  - linux_secure
  - auditd
  - vmware:perf
  - vmware:inv
  - vmware:events
  - vmware:tasks
  - hyperv:event
  - hyperv:perf
  - libvirt:log
  - qemu:log
  - citrix:broker
  - citrix:storefront
  - citrix:adc:syslog
  - cisco:ios
  - cisco:nxos
  - cisco:asa
  - cisco:dnac:issue
  - cisco:dnac:device
  - cisco:dnac:client
  - cisco:dnac:audit
  - cisco:dnac:swim
  - cisco:dnac:securityadvisory
  - cisco:meraki:devices
  - cisco:meraki:webhook
  - cisco:meraki:sensorreadingshistory
  - cisco:aci:faults
  - cisco:aci:events
  - cisco:aci:audit
  - cisco:aci:health
  - cisco:ucs:fault
  - cisco:ucs:event
  - cisco:ucs:audit
  - cisco:ucs:fsm
  - cisco:vmanage:rest
  - cisco:vmanage:syslog
  - cisco:vmanage:bfd
  - cisco:vmanage:tunnel
  - cisco:vmanage:omp
  - cisco:dcnetworking:health
  - cisco:dcnetworking:fabric
  - cisco:thousandeyes:test
  - cisco:thousandeyes:alert
  - ThousandEyesOTel
  - cisco:nexusdashboard:event
  - cisco:nexusdashboard:insight
  - cisco:smart_licensing:event
  - netapp:ontap:ems
  - netapp:ontap:rest
  - netapp:aiqum:perf
  - dell:powerstore:rest
  - dell:powerscale:onefs:audit
  - dell:powerscale:onefs:cluster
  - pure:flasharray:rest
  - veeam:backup:job
  - veeam:backup:repository
  - commvault:event
  - commvault:job
  - bms:water
  - bms:air
  - bms:power
  - bms:fire
  - ups:snmp
  - hvac:snmp
  - badge:reader
  - meraki:mt
  - meraki:mv
  - infoblox:dns
  - infoblox:dhcp
  - infoblox:audit
  - bluecat:audit
  - microsoft:dns:analytical
  - bind:query
  - f5:bigip:ltm
  - f5:bigip:asm
  - f5:bigip:apm
  - stream:cisco_hsl_netflow
  - stream:netflow
  - stream:ipfix
  - stream:zeek:conn
  - stream:zeek:dns
  - juniper:junos
  - arista:eos:syslog
  - aruba:central:rest
  - aruba:airwave:rest
ta_versions: "Splunk_TA_nix 9.x; Splunk_TA_windows 9.x; TA-cisco_ios 6.x; Splunk Add-on for VMware 6.x; Cisco Catalyst Add-on for Splunk (7538) 1.4+; Cisco Enterprise Networking App for Splunk (7539); Splunk Add-on for Cisco Meraki (5580) 2.4+; Cisco DC Networking App for Splunk (7777); Splunk Add-on for Cisco ACI (4022) 2.x; Cisco ThousandEyes Add-on for Splunk (7719); Splunk Add-on for Cisco Catalyst SD-WAN (6656); Cisco Catalyst SD-WAN App for Splunk (6657); Splunk Add-on for NetApp Data ONTAP 4.x; Splunk Add-on for Pure Storage; Splunk Add-on for Veeam Backup & Replication; Splunk Connect for Syslog 3.x; Splunk Connect for SNMP 1.x; Splunk OpenTelemetry Collector for Network Devices"
splunk_versions: "9.0, 9.1, 9.2, 9.3, 9.4 (current), 10.0+; Splunk Cloud Platform"
cross_products: [Linux Servers (cat 1.1 — linux-servers.md), Windows Servers (cat 1.2 — windows-servers.md), macOS Endpoints (cat 1.3 — macos.md), Bare-Metal / Hardware (cat 1.4 — bare-metal-hardware.md), VMware vSphere (cat 2.1 — vmware.md), Microsoft Hyper-V (cat 2.2 — hyperv.md), KVM/Proxmox/oVirt (cat 2.3 — kvm-proxmox-ovirt.md), VDI / Citrix (cat 2.4-2.6 — citrix-virtual-apps-desktops.md), Cisco Catalyst Networks (cat 5.1 — cisco-networks.md), Firewalls (cat 5.2 — firewalls.md), Load Balancers / ADCs (cat 5.3 — load-balancers-adcs.md), Wireless Infrastructure (cat 5.4 — wireless-infrastructure.md), SD-WAN (cat 5.5 — sd-wan-network-management.md), DNS / DHCP (cat 5.6 — dns-dhcp.md), Network Flow Data (cat 5.7 — network-flow.md), Network Management Platforms (cat 5.8 — sd-wan-network-management.md), Cisco ThousandEyes (cat 5.9 — cisco-thousandeyes.md), Carrier Signaling (cat 5.10 — carrier-signaling-telecom.md), gNMI Streaming (cat 5.11 — gnmi-streaming.md), Telecom CDR (cat 5.12 — carrier-signaling-telecom.md), Cisco Catalyst Center (cat 5.13 — catalyst-center.md), Storage SAN/NAS (cat 6.1 — storage-san-nas.md), Object Storage (cat 6.2 — object-storage.md), Backup & Recovery (cat 6.3 — backup-recovery.md), File Services (cat 6.4 — file-services.md), Database Trending (cat 6.6 — database-platforms.md), Power & UPS (cat 15.1 — datacenter-physical.md), HVAC / Cooling (cat 15.2 — datacenter-physical.md), Physical Security (cat 15.3 — datacenter-physical.md), Cisco ACI (cat 18.1 — cisco-aci.md), VMware NSX (cat 18.2 — vmware-nsx.md), Other SDN / EVPN-VXLAN (cat 18.3 — sdn-evpn-vxlan.md), Nexus Dashboard (cat 18.4 — nexus-dashboard.md), Cisco UCS (cat 19.1 — cisco-ucs.md), HyperFlex / HCI (cat 19.2 — cisco-hyperflex.md), Azure Stack HCI (cat 19.3 — azure-stack-hci.md), Compliance master (cat 22 — compliance-business.md), Splunk ITSI (cat 13.2 — splunk-itsi.md), Splunk Platform Health (cat 13.1 — splunk-platform-health.md)]
compliance_frameworks: [SOC 2 Type II — CC6 (logical access) + CC7 (system operations) + CC8 (change management) + CC9 (risk mitigation) + A1 (availability), ISO 27001:2022 (Annex A 93 controls — esp. A.5.9 inventory + A.8.16 monitoring + A.8.20 network security + A.8.21 network services security), ISO/IEC 27017 (cloud) + 27018 (PII clouds), HIPAA Security Rule §164.308 (Admin) + §164.310 (Physical) + §164.312 (Technical), PCI DSS 4.0 (esp. Req 1 NSC + Req 2 secure config + Req 6 secure dev + Req 7 access + Req 8 identification + Req 10 logging + Req 11 vulnerability + Req 12 policy), GDPR Art. 25 (data protection by design) + 30 (RoPA) + 32 (security of processing), NIS2 Directive (EU) 2022/2555 — Annex II "essential entities" — esp. Art. 21(2)(d) access control + 21(2)(e) BC/DR + 21(2)(g) network and information system security + 21(2)(h) cryptography, DORA Art. 5-23 (financial sector ICT risk + incident classification + TLPT), CMMC 2.0 Level 1/2/3 (CUI), NIST CSF 2.0 (Govern + Identify + Protect + Detect + Respond + Recover), NIST SP 800-53 r5 (all 20 control families esp. AU + AC + CM + CP + IR + SC + SI + SR), NIST SP 800-171 r3 (CUI), NIST SP 800-92 (log management), NIST SP 800-184 (ransomware recovery), NIST SP 800-207 (Zero Trust), FedRAMP Moderate / High (rev 5 baselines), FISMA + OMB A-130, GLBA Safeguards Rule (FTC final rule 2023), FFIEC CAT + IT Examination Handbook (Architecture Infrastructure and Operations booklet), NYDFS 23 NYCRR 500, NERC CIP-002 thru CIP-013 (electric sector), TSA Pipeline Security Directive SD-2 + SD-3, FAR Subpart 4.16 + DFARS 252.204-7012, IRS Pub 1075 (FTI), CJIS Security Policy v5.9.4, ISA/IEC 62443 (OT/ICS — for OT-adjacent infrastructure), MITRE ATT&CK (Enterprise) + D3FEND, OWASP Top 10 + ASVS, CIS Critical Security Controls v8 (esp. CIS Control 1 inventory + 2 software inventory + 3 data protection + 4 secure config + 7 vulnerability + 8 audit log + 13 network monitoring + 16 application software security + 17 incident response), CIS Foundations Benchmarks (per-platform), DISA STIG (Linux + Windows + Cisco IOS-XE / NX-OS / IOS / ASA + VMware + Microsoft AD), Cisco Validated Designs (CVDs), VMware Validated Designs (VVDs)]
maturity_tiers: {crawl: 28, walk: 75, run: 60}
last_updated: 2026-05-09
---

# Infrastructure Monitoring Domain Master Guide

> Splunk's value in infrastructure monitoring comes from
> **collapsing seven historically siloed engineering disciplines —
> servers, virtualization, network, storage, data-center physical,
> SDN/fabric, and converged compute — into one correlated timeline
> with shared identity, time, and change context**. Outage triage
> happens in minutes, not hours, when one analyst can pivot from a
> thermal alarm on a UPS through a chassis BMC PFA event into a
> hypervisor HA restart storm and out into the application
> connection failures the user actually noticed. This domain guide
> bridges seven catalogue pillars — Server & Compute (cat-1, 275
> UCs), Virtualization (cat-2, 124 UCs), Network Infrastructure
> (cat-5, 490 UCs), Storage & Backup (cat-6, 81 UCs), Data Center
> Physical Infrastructure (cat-15, 81 UCs), Data Center Fabric &
> SDN (cat-18, 76 UCs), and Compute Infrastructure (cat-19, 72 UCs)
> — into one sequenced operational programme. It is the **front
> door** for CIO, Infrastructure Director, NOC Manager, Network
> Architect, Storage Lead, Facilities Director, Virtualization
> Lead, and SRE / Platform Lead readers. Per-product depth lives in
> the integration guides linked below.

## Table of Contents

- [Audience and Use](#audience-and-use)
- [Quick Start — From Zero to First Detection in 30 Days](#quick-start--from-zero-to-first-detection-in-30-days)
- [Architecture and Data Flow](#architecture-and-data-flow)
- [Domain 1 — Server & Compute (cat 1, 275 UCs)](#domain-1--server--compute-cat-1-275-ucs)
- [Domain 2 — Virtualization (cat 2, 124 UCs)](#domain-2--virtualization-cat-2-124-ucs)
- [Domain 3 — Network Infrastructure (cat 5, 490 UCs)](#domain-3--network-infrastructure-cat-5-490-ucs--cisco-gold-standard)
- [Domain 4 — Storage & Backup (cat 6, 81 UCs)](#domain-4--storage--backup-cat-6-81-ucs)
- [Domain 5 — Data Center Physical Infrastructure (cat 15, 81 UCs)](#domain-5--data-center-physical-infrastructure-cat-15-81-ucs)
- [Domain 6 — Data Center Fabric & SDN (cat 18, 76 UCs)](#domain-6--data-center-fabric--sdn-cat-18-76-ucs)
- [Domain 7 — Compute Infrastructure (cat 19, 72 UCs)](#domain-7--compute-infrastructure-cat-19-72-ucs)
- [Cross-Domain Correlation Anchor](#cross-domain-correlation-anchor)
- [CMDB and Asset Identity Anchor](#cmdb-and-asset-identity-anchor)
- [Crawl / Walk / Run Roadmap (28 / 75 / 60 UCs)](#crawl--walk--run-roadmap-28--75--60-ucs)
- [Sizing and Capacity Planning](#sizing-and-capacity-planning)
- [Compliance Mapping](#compliance-mapping)
- [Reference Dashboards](#reference-dashboards)
- [SPL Examples](#spl-examples)
- [Troubleshooting](#troubleshooting)
- [SOAR Playbook Catalogue](#soar-playbook-catalogue)
- [Cross-Product Integration](#cross-product-integration)
- [References](#references)

## Audience and Use

| Audience | What you get from this guide | Where to go for depth |
|---|---|---|
| **CIO** | Cross-domain visibility into infrastructure resilience, MTTR trends, capacity runway, and refresh-cycle posture | All cross-product guides; service tree in `splunk-itsi.md` |
| **Infrastructure Director** | KPI scorecards per domain (servers / virt / network / storage / facilities), compliance evidence pack roll-up | `compliance-business.md`, `splunk-itsi.md` |
| **NOC Manager / 24×7 Lead** | Cross-domain alert prioritisation, war-room runbooks, on-call paging discipline | All Reference Dashboards rows; `service-management-itsm.md` |
| **Network Architect** | Catalyst Center + Catalyst SD-WAN + ACI + Nexus Dashboard + ThousandEyes correlation patterns | `catalyst-center.md`, `sd-wan-network-management.md`, `cisco-aci.md`, `nexus-dashboard.md`, `cisco-thousandeyes.md` |
| **Network Engineer** | Per-vendor syslog / SNMP / gNMI collection, BGP / OSPF / EIGRP / HSRP / VRRP narratives | `cisco-networks.md`, `gnmi-streaming.md` |
| **Wireless Lead** | Catalyst WLC + Aruba Central + Mist + Meraki MR overlay, RF KPI baselines | `wireless-infrastructure.md` |
| **Storage Lead** | NetApp ONTAP EMS + REST + AIQ-UM, Dell PowerStore / Unity / PowerScale, Pure FlashArray, Ceph, Veeam, Commvault | `storage-san-nas.md`, `object-storage.md`, `backup-recovery.md` |
| **Virtualization Lead** | vSphere CPU Ready / balloon / swap / snapshot governance + cross-hypervisor (Hyper-V, KVM/Proxmox, Citrix) | `vmware.md`, `hyperv.md`, `kvm-proxmox-ovirt.md`, `citrix-virtual-apps-desktops.md` |
| **Facilities Director / DCIM Lead** | UPS / generator / ATS / HVAC / cooling / Legionella + physical-access correlation | `datacenter-physical.md`, `meraki-mt.md`, `splunk-edge-hub.md` |
| **HCI / Compute Platform Lead** | Cisco UCS XML API / IMC / Intersight, HyperFlex HXDP, Azure Stack HCI / VxRail / VxBlock, Nutanix-like footprints | `cisco-ucs.md`, `cisco-hyperflex.md`, `azure-stack-hci.md`, `intersight.md` |
| **Linux / Windows Server Lead** | OS metric ingestion, EventLog / `auditd` / WinHostMon, security overlays | `linux-servers.md`, `windows-servers.md` |
| **SRE / Platform Lead** | Cross-domain SLO modeling using shared identity, host, and change-window context | `application-monitoring.md` (SLO discipline), `splunk-itsi.md` |
| **Compliance Officer** | NIS2 / DORA<sup class="ref">[<a href="#ref-5">5</a>]</sup> / SOC 2 / ISO 27001 / NERC CIP / PCI DSS / FedRAMP infrastructure-control evidence | `compliance-business.md`, `docs/evidence-packs/` |

## Quick Start — From Zero to First Detection in 30 Days

### Week 1 — Server & Identity Foundation

1. **`Splunk_TA_nix`** (833) on every Linux UF; **`Splunk_TA_windows`** (742) on every Windows UF.
2. Standardise indexes: `os`, `wineventlog`, `linux_secure`, `auditd`, `perfmon`.
3. Enable **CIM Performance** + **Authentication** data model acceleration.
4. **First three detections enabled:**
   - UC-1.1.7 OOM Killer Events
   - UC-1.1.8 SSH Brute-Force Detection
   - UC-1.2.1 Windows Service Crash (Event ID 7031/7034)

### Week 2 — Network + DC Fabric Foundation

5. **SC4S** terminating Cisco IOS / IOS-XE / NX-OS / Meraki MX / Catalyst SD-WAN syslog.
6. **TA-cisco_ios** (1352) for IOS syslog field extraction.
7. **Cisco Catalyst Add-on** (7538) polling Catalyst Center Assurance + Inventory + Audit endpoints.
8. **Splunk Add-on for Cisco ACI** (4022) for fabric faults + events + audit (if applicable).
9. **First three detections enabled:**
   - UC-5.1.1 Interface Up/Down
   - UC-5.1.4 BGP Peer State Changes
   - UC-5.13.1 Catalyst Center Issue Severity Trend

### Week 3 — Virtualization + Storage Foundation

10. **Splunk Add-on for VMware** (vCenter credential vault + cluster KPI extraction).
11. **NetApp / Dell / Pure** REST modular inputs (per array vendor present).
12. **First three detections enabled:**
    - UC-2.1.21 ESXi Host Unexpected Reboot
    - UC-2.1.3 Datastore Capacity Trending
    - UC-6.1.1 Volume Capacity Trending

### Week 4 — Facilities + Cross-Domain Correlation

13. **SC4SNMP** for UPS / PDU / HVAC SNMP traps + scheduled polls.
14. Cross-CMDB **`business_service`** + **`tier`** lookups.
15. **First three detections enabled:**
    - UC-15.1.1 UPS Battery Health
    - UC-15.1.13 Transfer Switch Events
    - UC-19.1.1 Blade/Rack Server Health (Cisco UCS) — or vendor-equivalent

By day 30 you have **15 production detections** anchoring an
end-to-end correlated timeline from facility power → chassis BMC →
hypervisor → guest OS → network path → storage array → user
experience.

## Architecture and Data Flow

```mermaid
flowchart LR
    subgraph "OS / Compute Source Plane (cat-1)"
        LIN[Linux servers<br/>RHEL / Ubuntu / SLES /<br/>Amazon Linux / Oracle Linux]
        WIN[Windows Server<br/>2016 / 2019 / 2022 / 2025]
        MAC[macOS endpoints<br/>endpoint posture]
        BARE[Bare-metal hardware<br/>EDAC + IPMI + BMC + Redfish]
    end

    subgraph "Virtualization Plane (cat-2)"
        VS[VMware vSphere<br/>ESXi + vCenter]
        HV[Microsoft Hyper-V<br/>+ SCVMM]
        KVM[KVM / Proxmox / oVirt /<br/>RHV / KubeVirt]
        VDI[Citrix CVAD + Horizon /<br/>VMware Horizon /<br/>VDI estates]
    end

    subgraph "Network Source Plane (cat-5)"
        IOS[Cisco IOS / IOS-XE /<br/>NX-OS / Catalyst]
        SDWAN[Cisco Catalyst SD-WAN<br/>vManage / cEdge / vEdge]
        WLC[Wireless: Cisco WLC /<br/>Aruba / Mist / Meraki MR]
        FW[Firewalls: Cisco Secure FW /<br/>Palo Alto / Fortinet / Check Point]
        ADC[Load Balancers / ADCs<br/>F5 BIG-IP / Citrix ADC / NGINX]
        DDI[DNS / DHCP / IPAM<br/>Infoblox / BlueCat / Microsoft / BIND]
        FLOW[NetFlow / IPFIX / sFlow /<br/>Zeek / Stream wire data]
        GNMI[gNMI / model-driven<br/>telemetry / OpenConfig YANG]
        DNAC[Cisco Catalyst Center<br/>Assurance + Intent + Audit]
        TE[Cisco ThousandEyes<br/>Cloud / Enterprise / Endpoint Agent]
        CARR[Carrier signaling /<br/>SS7 / Diameter / SIP / CDR]
        OTHER[Juniper Junos /<br/>Aruba Central / Arista EOS]
    end

    subgraph "Storage Source Plane (cat-6)"
        NETAPP[NetApp ONTAP<br/>EMS + REST + AIQ-UM]
        DELLP[Dell PowerStore /<br/>Unity / PowerScale (Isilon)]
        PURE[Pure FlashArray / FlashBlade<br/>Pure1 telemetry]
        CEPH[Ceph + RADOSGW]
        OBJ[Object: S3 + StorageGRID +<br/>ECS + Scality + MinIO]
        FILES[NFS / SMB / CIFS<br/>file services]
        BU[Backup: Veeam +<br/>Commvault + NetBackup +<br/>Cohesity + Rubrik]
    end

    subgraph "Facilities Source Plane (cat-15)"
        UPS[UPS / generators /<br/>ATS / PDU SNMP]
        HVAC[HVAC / CRAC / chillers /<br/>cooling towers]
        WATER[Water / leak detection /<br/>Legionella]
        BMS[BMS / BACnet object]
        BADGE[Physical access /<br/>badge / biometrics /<br/>video metadata]
    end

    subgraph "Fabric / SDN Source Plane (cat-18)"
        ACI[Cisco ACI<br/>APIC + faultInst + audit]
        NSX[VMware NSX<br/>distributed firewall + IDS/IPS]
        SDN[Other SDN<br/>EVPN-VXLAN / FabricPath]
        ND[Cisco Nexus Dashboard<br/>NDFC / NDI / NDO]
    end

    subgraph "Compute Source Plane (cat-19)"
        UCS[Cisco UCS<br/>XML API + syslog + IMC]
        HX[Cisco HyperFlex<br/>HXDP REST]
        AZHCI[Azure Stack HCI<br/>+ VxRail + VxBlock]
        INT[Cisco Intersight SaaS<br/>+ IWO + IKS]
    end

    subgraph "Splunk Ingest / Edge Tier"
        UF[Universal Forwarder]
        HF[Heavy Forwarder<br/>scripted / modular inputs]
        SC4S[SC4S syslog]
        SC4SNMP[SC4SNMP]
        REST[REST API modular<br/>OAuth2 + token + cookie]
        HEC[Splunk HEC<br/>OTel + JSON event/metric]
        STREAM[Splunk Stream<br/>wire data]
        OTEL[Splunk OpenTelemetry<br/>Collector for Network<br/>Devices + Servers]
        EP[Splunk Edge Processor]
    end

    LIN --> UF
    WIN --> UF
    MAC --> UF
    BARE --> SC4SNMP

    VS --> HF
    HV --> UF
    KVM --> HF
    VDI --> HF

    IOS --> SC4S
    SDWAN --> SC4S
    SDWAN --> REST
    WLC --> SC4S
    FW --> SC4S
    ADC --> SC4S
    DDI --> SC4S
    FLOW --> STREAM
    GNMI --> OTEL
    DNAC --> REST
    TE --> HEC
    CARR --> HF
    OTHER --> SC4S

    NETAPP --> REST
    DELLP --> REST
    PURE --> REST
    CEPH --> UF
    OBJ --> HF
    FILES --> UF
    BU --> REST

    UPS --> SC4SNMP
    HVAC --> SC4SNMP
    WATER --> HEC
    BMS --> HEC
    BADGE --> SC4S

    ACI --> REST
    NSX --> SC4S
    SDN --> SC4S
    ND --> REST

    UCS --> HF
    HX --> REST
    AZHCI --> UF
    INT --> REST

    UF --> EP
    HF --> EP
    SC4S --> EP
    SC4SNMP --> EP
    REST --> EP
    HEC --> EP
    STREAM --> EP
    OTEL --> EP

    EP --> IDX[Splunk Indexer Cluster<br/>+ TSIDX acceleration]

    IDX --> CIM[CIM data models —<br/>Performance + Network_Traffic +<br/>Authentication + Change +<br/>Inventory + Vulnerabilities]

    CIM --> ITSI[Splunk ITSI<br/>infrastructure service tree —<br/>facility → chassis → host →<br/>VM → app → user]
    CIM --> ES[Splunk ES<br/>+ ESCU + RBA risk scoring]
    CIM --> SOAR[Splunk SOAR<br/>infrastructure playbooks]
    CIM --> OBS[Splunk Observability<br/>Cloud + APM bridge]

    ITSI --> SCORECARD[Infrastructure scorecards<br/>+ Glass Tables<br/>per service / facility]
    ES --> NOTABLE[Notable events +<br/>risk objects +<br/>analyst disposition]
    SOAR --> WORKFLOW[Automated remediation +<br/>ServiceNow integration]

    classDef compute fill:#fef3c7,stroke:#f59e0b,color:#78350f
    classDef virt fill:#fce7f3,stroke:#db2777,color:#831843
    classDef network fill:#e1f5ff,stroke:#0ea5e9,color:#075985
    classDef storage fill:#dcfce7,stroke:#16a34a,color:#166534
    classDef fac fill:#fef2f2,stroke:#ef4444,color:#7f1d1d
    classDef fabric fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
    classDef ucs fill:#fde68a,stroke:#ca8a04,color:#713f12
    classDef ingest fill:#f1f5f9,stroke:#64748b,color:#334155
    classDef analytics fill:#ddd6fe,stroke:#6d28d9,color:#4c1d95

    class LIN,WIN,MAC,BARE compute
    class VS,HV,KVM,VDI virt
    class IOS,SDWAN,WLC,FW,ADC,DDI,FLOW,GNMI,DNAC,TE,CARR,OTHER network
    class NETAPP,DELLP,PURE,CEPH,OBJ,FILES,BU storage
    class UPS,HVAC,WATER,BMS,BADGE fac
    class ACI,NSX,SDN,ND fabric
    class UCS,HX,AZHCI,INT ucs
    class UF,HF,SC4S,SC4SNMP,REST,HEC,STREAM,OTEL,EP ingest
    class IDX,CIM,ITSI,ES,SOAR,OBS,SCORECARD,NOTABLE,WORKFLOW analytics
```

### Core principles repeated throughout

1. **Identity is the universal join.** `host`, `serial`, `device_id`,
   `business_service`, `tier`, `environment`, `site`, and
   `data_center` must be consistently extracted across every source.
   CMDB lookups bridge these nightly. Without identity discipline,
   cross-domain correlation is theatre.
2. **Time discipline first.** UTC at the indexer, NTP-synchronised
   sources, `_time` extracted before `host`. Daylight-saving and
   timezone drift will sabotage every forensic investigation.
3. **Two planes of telemetry per domain.** Server: metrics + events.
   Network: structured (REST / gNMI) + syslog / SNMP. Storage: REST
   inventory + EMS / event. Virtualization: vCenter perf counters +
   guest OS. Both planes are required; one alone yields blind spots.
4. **Vendor-native instrumentation first, second-party second.**
   Cisco Catalyst Center Assurance > grep'ing IOS syslog.
   NetApp EMS + REST > NFS RTT proxies. VMware Performance Manager >
   guest OS counters. Roll up to second-party only when first-party
   doesn't expose the signal.
5. **Baseline-driven thresholds, not magic numbers.** Production OLTP
   ≠ dev burst workload. Use percentile envelopes per
   `(business_service, tier, environment)` cohort with maintenance-
   window suppression.
6. **Splunk ITSI is the synthesis layer.** Service trees model
   facility → chassis → host → VM → application → user dependencies.
   KPI base searches on accelerated CIM Performance + Network_Traffic;
   thresholds on entity rules.
7. **Splunk ES + ESCU + RBA for security overlays.** Infrastructure
   compromise (lateral movement, privilege escalation, credential
   theft, ransomware staging) layers onto operational health
   timelines through Risk-Based Alerting risk objects.
8. **Cross-domain correlation is the unfair advantage.** SOC, NOC,
   and Facilities historically lived in separate consoles. Splunk
   collapses them into one searchable timeline. Treat this as the
   primary value proposition, not metric fidelity per source.
9. **Cisco gold-standard pattern is the reference.** Where Cisco
   ships first-party Splunk integrations (Catalyst Center,
   ThousandEyes, Catalyst SD-WAN, ACI, Nexus Dashboard, UCS,
   Intersight, Cyber Vision, Meraki), they define the ingestion
   contract and Splunk app behaviour the community uses as the
   yardstick.

---

## Domain 1 — Server & Compute (cat 1, 275 UCs)

> Per-product depth: `linux-servers.md`, `windows-servers.md`,
> `macos.md`, `bare-metal-hardware.md`.

### Subcategory map

| Sub | Focus | UCs | Deep-dive guide |
|---|---|---|---|
| 1.1 | Linux Servers | 131 | `linux-servers.md` |
| 1.2 | Windows Servers | 127 | `windows-servers.md` |
| 1.3 | macOS Endpoints | 6 | `macos.md` |
| 1.4 | Bare-Metal / Hardware | 11 | `bare-metal-hardware.md` |

### Operating-system metrics and monitoring stance

**CPU, memory, disk, and processes** remain the canonical
foundation because they translate directly into saturation,
latency, and queueing — the three leverage points of capacity
management.

- **Linux — WHAT/WHY/HOW:** Collect utilization from
  `/proc`-derived scripted metrics (`cpu`, `vmstat`, `df`, `ps`,
  `top`-equivalent scripts) via **Splunk Add-on for Unix and Linux
  (`Splunk_TA_nix`, Splunkbase 833)**. *Why:* Without normalized
  CPU steal / iowait / runnable-queue context, Linux hosts hide
  disk-backed slowdowns that masquerade as "CPU problems."
  *How:* Deploy Universal Forwarders with TA inputs enabled at
  sensible intervals (typically 60–300s depending on cardinality);
  route `index=os` sourcetypes (`cpu`, `vmstat`, `df`) into
  accelerated Performance-model searches where alert latency demands
  sub-minute freshness.

- **Windows — WHAT/WHY/HOW:** Pair **Windows Event Log** security
  channels with **Performance Monitor** counters (PerfMon) and
  WMI-backed scripted queries via **`Splunk_TA_windows`**
  (Splunkbase 742). *Why:* Windows separates interactive saturation
  (processor queue, privileged time) from storage stalls (logical
  disk latency, avg. disk queue length). *How:* Enable WinHostMon /
  PerfMon inputs for `% Processor Time`, `Available MBytes`, paging
  file `% Usage`, logical disk `% Free Space`; ingest Security.evtx
  alongside for privileged-use auditing.

- **macOS — WHAT/WHY/HOW:** Endpoint fleets rarely justify
  bare-metal KPI parity with servers; prioritize integrity-relevant
  signals (auth events, privilege escalation paths, MDM posture)
  plus lightweight CPU/mem/disk snapshots where operational
  analytics justify UF footprint. Pair with EDR (SentinelOne /
  CrowdStrike / Defender) telemetry for endpoint-grade detection.

### Security events and compliance

Linux **`auditd`** trails (`audit.log`) anchor privileged-command
accountability when forwarded via syslog or UF file tails;
Windows **Advanced Audit Policy** selections align Security.evtx
categories (logon, account management, privilege use) to SOC/SOX
sampling expectations.

Compliance framing typically blends:

1. **Preventive controls** — patch cadence proxies via OS
   versioning fields pulled into lookups.
2. **Detective controls** — authentication anomalies and `sudo` /
   `RunAs` spikes correlated with change tickets.
3. **Corrective controls** — orchestration callbacks triggered by
   Splunk alerts (limited here by organizational maturity).

### Bare-metal reliability signals

Hardware-adjacent failures escape OS counters until workloads
crash silently; prioritize EDAC/IPMI/BMC/Redfish narratives:

| Critical UC | Risk addressed |
|---|---|
| UC-1.1.102 EDAC Memory Error Tracking | Row/column ECC faults preceding DIMM replacement |
| UC-1.1.103 IPMI Sensor Threshold Violations | Power/temp/current excursions visible only out-of-band |
| UC-1.1.104 Thermal Throttling Detection | Firmware slowing CPUs before thermal shutdown |
| UC-1.1.105 Fan Speed Anomalies | Cooling subsystem degradation vs HVAC faults |
| UC-1.1.106 Power Supply State Changes | Redundancy loss preceding cascading faults |

**WHAT/WHY/HOW for BMC ingestion:** Ship SEL/IPMI syslog streams
or periodic sensor polls into Splunk via SC4SNMP receivers or
scripted Redfish pulls (Heavy Forwarder). *Why:* Operating systems
frequently lack sensors when BMC asserts predictive failures.
*How:* Normalize vendor-specific severity tokens into Splunk
lookups (`bmc_vendor`, `regex_extract`, `severity_map`) so
correlated dashboards combine Linux OS KPIs with BMC thermal /
power timelines without double-counting transient spikes during
chassis firmware flashes.

### Linux syslog, `rsyslog`, `auditd`, and journal pipeline hardening

**WHAT:** Forward **syslog** (`/var/log/messages`, application
logs, authentication trails) alongside **`auditd`** binary-format
audit trails (`/var/log/audit/audit.log`) using Splunk UF
`monitor://` inputs or **`imjournal`** / `imfile` hops through a
Heavy Forwarder when checksum guarantees matter.

**WHY:** Performance metrics (`cpu`, `vmstat`) alone miss
credential-theft timelines — Splunk correlation chains rely on
temporal alignment between syscall-level audit records (`execve`,
`chmod`, `mount`) and network-facing syslog authentication
failures.

**HOW:** Apply Splunk **`props.conf`** `LINE_BREAKER` /
`TIME_PREFIX` tuned per distro; tag `host`, `source`, `sourcetype`
consistently (`linux_secure`, `auditd`). Map audit keys
(`type=SYSCALL`, `type=USER_LOGIN`) into CIM **Authentication**
where feasible; throttle noisy daemons via `whitelist` /
`blacklist` transforms while preserving tamper-evident chains for
Tier-1 hosts.

### Windows Event Log depth and PerfMon pairing

**WHAT:** Harvest **Microsoft-Windows-Security**, **System**,
**Application**, and workload-specific channels (SQL Server, IIS,
Hyper-V) with unified timestamp normalization and channel-aware
rendering (`renderXml=false` where KV extraction suffices).

**WHY:** Critical-path outages often surface first as
**Event ID 7031/7034** service termination cascades before PerfMon
saturation charts move — dual-plane ingestion avoids blind spots.

**HOW:** Splunk **`Splunk_TA_windows`** `WinEventLog://` stanzas
reference explicit channels; combine with **`perfmon://`**
checkpointed counters (`\Processor(_Total)\% Processor Time`,
`\LogicalDisk(*)\Avg. Disk sec/Read`) sampled at ≤60s for
operational dashboards vs ≤15s for tier-0 golden signals.

### Critical UCs

| UC | Why critical |
|---|---|
| UC-1.1.7 OOM Killer Events | Memory-pressure kill signatures preceding instability |
| UC-1.1.8 SSH Brute-Force Detection | Credential-stuffing narratives |
| UC-1.1.9 Unauthorized Sudo Usage | Privilege escalation forensic pivot |
| UC-1.1.10 Cron Job Failure Monitoring | Scheduled-task automation drift |
| UC-1.1.23 Kernel Core Dump Generation | Application / kernel crash signatures |
| UC-1.1.102 EDAC Memory Error Tracking | DIMM replacement signal |
| UC-1.2.1 Windows Service Crash | 7031/7034 cascade detection |
| UC-1.2.18 Windows Failed Logon Anomaly | Privilege brute-force |
| UC-1.2.50 Windows BitLocker Status | Disk encryption posture |

---

## Domain 2 — Virtualization (cat 2, 124 UCs)

> Per-product depth: `vmware.md`, `hyperv.md`,
> `kvm-proxmox-ovirt.md`, `citrix-virtual-apps-desktops.md`.

### Subcategory map

| Sub | Focus | UCs | Deep-dive guide |
|---|---|---|---|
| 2.1 | VMware vSphere | 35 | `vmware.md` |
| 2.2 | Microsoft Hyper-V | 18 | `hyperv.md` |
| 2.3 | KVM / Proxmox / oVirt / RHV | 14 | `kvm-proxmox-ovirt.md` |
| 2.4 | Cross-platform abstractions | 9 | `vmware.md` |
| 2.5 | VDI estates | 22 | `citrix-virtual-apps-desktops.md` |
| 2.6 | Citrix delivery tiers | 26 | `citrix-virtual-apps-desktops.md` |

### Splunk integration baseline

Use **`Splunk Add-on for VMware`** for inventory-aware KPI
extraction across clusters, hosts, and VMs — avoid flattening raw
hypervisor telemetry without CMDB linkage. Critical sourcetypes:
`vmware:perf` (counters), `vmware:inv` (inventory), `vmware:events`
(state changes), `vmware:tasks` (admin actions).

Anchor operational resilience:

| Critical UC | Signal |
|---|---|
| UC-2.1.21 ESXi Host Unexpected Reboot | Host isolation / PSOD-class outages |
| UC-2.1.22 vCenter Service Health | Control-plane dependency failures |
| UC-2.1.23 VM Unexpected Power State Changes | HA/restart storms vs automation drift |
| UC-2.1.3 Datastore Capacity Trending | Thin-provision exhaustion cascades |

### VMware vendor-aligned hypervisor KPI practices (gold reference)

These practices derive from VMware capacity-planning doctrine
(`esxtop` / vSphere Performance charts); Splunk surfaces them
through TA-backed extracts or REST KPI pulls — **WHAT/WHY/HOW**
triplets apply throughout.

#### CPU Ready time (%RDY)

- **WHAT:** Track CPU Ready (`%RDY`) per vCPU cohort — not raw CPU
  utilization — to quantify scheduler wait attributable to
  contention.
- **WHY:** Guests may report low CPU usage while latent-ready
  queues indicate undersized reservations during bursts;
  utilization-only dashboards green-light overloaded clusters.
- **HOW:** Capture `%RDY` from Performance Manager counters
  (`cpu.ready.summation` normalized by interval × vCPU), baseline
  weekly rolling medians/p95 per cluster/datastore cohort, alert
  when sustained Ready exceeds cohort percentile thresholds derived
  from historical steady-state windows (avoid static magic numbers).

#### Balloon driver (`vmmemctl`)

- **WHAT:** Monitor balloon target/active balloon KB
  (`mem.vmmemctl`), correlated with active memory (`mem.active`).
- **WHY:** Ballooning is VMware Tools-mediated reclaim signaling
  memory pressure earlier than swapping; sustained balloon growth
  precedes guest paging storms.
- **HOW:** Trend balloon slopes alongside reservation/overcommit
  ratios; suppress benign bursts tied to scheduled desktop pools
  using CMDB-backed scheduled suppression tokens.

#### Swap activity (`swapinRate` / `swapoutRate`)

- **WHAT:** Split VMkernel swap metrics from datastore latency
  spikes.
- **WHY:** Swap indicates worst-tier reclaim — latency-sensitive
  workloads crater before datastore KPI fires if clusters
  oversubscribe RAM aggressively.
- **HOW:** Combine swap counters with datastore queues
  (`disk.queueLatency`) for causality narratives in Splunk
  dashboards; elevate alerts when swap persists beyond rolling
  baseline envelopes absent correlated backup windows.

#### Snapshot growth & orphaned snapshots

- **WHAT:** Track snapshot chain depth, aggregate snapshot GB per
  VM, delta-VMDK churn vs backup SLA snapshots.
- **WHY:** Snapshots inflate datastore utilization silently and
  degrade SCSI latency — classic latent outage vector during
  patching cycles.
- **HOW:** Scheduled searches comparing snapshot inventories daily;
  correlate Splunk alerts with backup orchestrator APIs where
  snapshot retention exceeds policy baselines.

#### Baseline-driven thresholds + service mapping + alert grouping

- **WHAT:** Replace global static thresholds with workload-tier
  baselines (percentile envelopes over aligned windows). Map
  VMs/clusters to business services with CMDB IDs reflected as
  Splunk indexed fields (`business_service`, `tier`). Aggregate
  correlated host/cluster alarms within configurable suppression
  windows coinciding with VMware Maintenance Mode entries or CI/CD
  resize bursts.
- **WHY:** Production OLTP behaves unlike dev burst workloads;
  uniform thresholds yield chronic alert fatigue across tiers.
  Incident bridges prioritize blast radius when datastore
  contention threatens tier-1 ERP clusters vs sandbox tiers.
  Rolling storms duplicate pager noise during intentional
  migrations (Storage vMotion waves).
- **HOW:** Store baseline stats via summary indexing
  (`summary index = vmware_baselines`) keyed by
  `(cluster, tier, business_service)`; alerts evaluate deviation
  multiples vs baseline. Splunk alert throttle keyed on
  `(cluster, domain)` plus Splunk lookups referencing approved
  maintenance calendars.

### Hyper-V, KVM / Proxmox / oVirt, VDI, and Citrix overlays

VMware dominates enterprise hypervisor mindshare, yet Splunk
estates routinely aggregate heterogeneous stacks — each exposes
distinct choke points:

**Hyper-V — WHAT/WHY/HOW:** Ingest **Hyper-V Worker** Event Log
clusters (`Microsoft-Windows-Hyper-V-Worker/Admin`), **VMMS**
service health, synthetic CSV exports from **`Get-VM`** scheduled
scripts, and SCVMM Orchestration logs where System Center persists
automation intent. *Why:* Hyper-V clusters signal localized CSV
disconnections (`Event ID 5120/5121`) independent of VMware
datastore narratives. *How:* Splunk UF on cluster nodes plus
centralized Hyper-V host grouping macros (`hyperv_cluster`,
`csv_volume_guid`) correlate CSV reconnect storms with upstream
SAN latency searches from Category 6.

**KVM / Proxmox / oVirt — WHAT/WHY/HOW:** Normalize
**`libvirt`** / `qemu` logs, Proxmox **`pvestatd`** JSON exports
via scripted inputs, and oVirt REST VM statistics where burst-heavy
workloads demand kernel-side KVM scheduling visibility (`vcpu`
steal analogs via `/proc/stat` deltas per guest cgroup). *Why:*
Open ecosystems lack VMware's unified Performance Manager — Splunk
becomes the aggregator of truth for scheduler fairness signals.
*How:* Heavy Forwarder pulls bridge API credentials into KV stores;
dashboards overlay storage pools (`thin_lv_full`) with guest CPU
steal proxies.

**VDI — WHAT/WHY/HOW:** Horizon / Citrix landscapes prioritize
**session latency**, **protocol degradation**, **launch failures**,
and **brokering queue depth** ahead of generic CPU charts. *Why:*
User-perceived outages stem from protocol-tier contention even when
ESXi Ready % looks acceptable. *How:* Splunk indexes Citrix
Delivery Controller events (`Citrix Broker/Licensing`), VMware
Horizon Connection Server logs (`ldap`, `certificate`, `blast`)
merged with VMware KPIs above — baseline **logon duration
percentiles** weekly.

**Citrix — WHAT/WHY/HOW:** Pull Citrix ADC (**NetScaler**) syslog
(`EVENT_MSG` / `SSLVPN`) alongside Citrix Virtual Apps session
reliability metrics (`WFICA`, `Citrix Workspace App`). *Why:*
Gateway saturation presents as ICA RTT spikes invisible inside
guest OS monitors alone. *How:* Splunk transforms map Citrix ADC
expressions (`citrix_adc_syslog`) into multi-field extractions
correlating VIP (`vserver`) with ThousandEyes SaaS HTTP tests where
hybrid workers traverse competing paths.

---

## Domain 3 — Network Infrastructure (cat 5, 490 UCs) — Cisco gold standard

> Per-product depth: `cisco-networks.md`, `catalyst-center.md`,
> `cisco-thousandeyes.md`, `sd-wan-network-management.md`,
> `firewalls.md`, `wireless-infrastructure.md`,
> `load-balancers-adcs.md`, `dns-dhcp.md`, `network-flow.md`,
> `gnmi-streaming.md`, `carrier-signaling-telecom.md`.

### Subcategory map

| Sub | Focus | UCs | Deep-dive guide |
|---|---|---|---|
| 5.1 | Routers / Switches (IOS / IOS-XE / NX-OS) | 70 | `cisco-networks.md` |
| 5.2 | Firewalls (Cisco Secure FW + PAN + Fortinet + Check Point + Meraki MX) | 41 | `firewalls.md` |
| 5.3 | Load Balancers / ADCs (F5 + Citrix + NGINX) | 22 | `load-balancers-adcs.md` |
| 5.4 | Wireless Infrastructure | 27 | `wireless-infrastructure.md` |
| 5.5 | SD-WAN | 25 | `sd-wan-network-management.md` |
| 5.6 | DNS / DHCP / IPAM | 31 | `dns-dhcp.md` |
| 5.7 | Network Flow Data | 25 | `network-flow.md` |
| 5.8 | Network Management Platforms | 29 | `sd-wan-network-management.md` |
| 5.9 | Cisco ThousandEyes | 54 | `cisco-thousandeyes.md` |
| 5.10 | Carrier Signaling | 12 | `carrier-signaling-telecom.md` |
| 5.11 | gNMI / gRPC Streaming | 14 | `gnmi-streaming.md` |
| 5.12 | Telecom CDR | 10 | `carrier-signaling-telecom.md` |
| 5.13 | Cisco Catalyst Center | 78 | `catalyst-center.md` |
| 5.14 | Cisco Meraki | 18 | `wireless-infrastructure.md`, `firewalls.md` |
| 5.15 - 5.19 | Specialised network verticals | ~34 | `multi-cloud-serverless.md`, network-specific guides |

### Non-Cisco ecosystem alignment

| Focus | Typical Splunk angle |
|---|---|
| Juniper Junos syslog | **`Splunk_TA_juniper`** — structured facility parsing |
| Arista EOS streaming | Syslog via SC4S with EOS-specific parsers + gNMI dial-out |
| Aruba Central / WLAN controllers | REST exports + syslog hybrids |
| F5 BIG-IP | AFM/LTM logs + iHealth snapshots via scripted pulls |
| BlueCat / Infoblox DDI | Audit syslog + Grid replication events |
| NetFlow / IPFIX + Zeek | Flow codecs (`stream:*`) beside IDS narratives |

### Cisco Catalyst Center (78 UCs — sub 5.13)

Cisco Catalyst Center (formerly DNA Center) exemplifies controller-
led assurance across campus fabrics. Cisco IT publicly cites
transformational outcomes — **97% reduction in critical/high
software vulnerabilities** through disciplined lifecycle governance
and **59% faster software upgrades** via standardized automation
pipelines — underscoring why Splunk correlation across Catalyst
Center telemetry yields measurable operational ROI versus
fragmented CLI scraping.

#### Assurance vs Intent APIs — WHAT/WHY/HOW

**Assurance API (experience-centric KPIs):** consume endpoints
exposing network/client/device **health scores** (WLAN RF,
onboarding latency, QoE aggregates). Splunk amplifies breadth
across IT domains without rebuilding ML pipelines manually.
Configure **`TA_cisco_catalyst` account inputs** hitting Catalyst
Center HTTPS endpoints; normalize responses into
`cisco:dnac:issue`, `cisco:dnac:device`, `cisco:dnac:client`.

**Intent API (structured automation-facing datasets):** poll
Intent endpoints for inventory (`network-device`), topology
overlays (`topology`), fabrics (`site`, `fabric-site`), wireless
assurance summaries. Intent responses include MoRef-style handles
you can pivot on in Splunk lookups (serial → site mapping) for
downstream service modeling.

| Sourcetype (TA output) | Example `GET` path | Health / issue semantics |
|---|---|---|
| `cisco:dnac:networkhealth` | `/dna/intent/api/v1/network-health` | Aggregate network score & good/bad counts |
| `cisco:dnac:devicehealth` | `/dna/intent/api/v1/device-health` | Per-device `overallHealth`, reachability |
| `cisco:dnac:clienthealth` | `/dna/intent/api/v1/client-health` | Wired/wireless client score rollups |
| `cisco:dnac:issue` | `/dna/intent/api/v1/issues` | Assurance issue objects (`issueId`, `priority`, `status`) |
| `cisco:dnac:device` | `/dna/intent/api/v1/network-device` | Inventory / `softwareVersion` / `managementIpAddress` |
| `cisco:dnac:client` | `/dna/intent/api/v1/client-detail` | Per-client MAC, host type, connection type, health JSON |
| `cisco:dnac:swim` | `/dna/intent/api/v1/image/importation` | Image compliance vs golden target |
| `cisco:dnac:securityadvisory` | `/dna/intent/api/v1/security-advisory/advisory` | PSIRT/CVE device coverage |

**Note:** Exact query parameters (`deviceId`, `siteId`,
`macAddress`) vary by Catalyst Center release — validate against
the TA's shipped Python/REST helpers before crafting ad-hoc `curl`
probes in production change windows.

| Splunkbase artefact | App ID | Role |
|---|---|---|
| Cisco Catalyst Add-on for Splunk | 7538 | Credential-backed scripted/API inputs |
| Cisco Enterprise Networking App for Splunk | 7539 | Dashboards/macros bridging Catalyst Center + IOS-XE/NX-OS |

### Cisco ThousandEyes (54 UCs — sub 5.9)

ThousandEyes treats Internet/SaaS paths as first-class observables
— distinct from SNMP/syslog device-only narratives. Hop-by-hop
Path Visualization overlays latency/packet-loss attribution across
autonomous systems. Traditional ICMP-only pings collapse multi-
provider faults into ambiguous endpoint failures; path graphs
localize ISP brownouts versus DNS hijacks versus SaaS ingress
saturation.

ThousandEyes tests emit normalized metrics Splunk indexes via
**`ThousandEyesOTel`** OpenTelemetry streams hitting Splunk **HEC**
(recommended ingestion architecture per ThousandEyes streaming
guides). Splunk dashboards replicate storytelling layering:

1. Executive KPI strip — SLA adherence vs synthetic availability budget.
2. Middle tier — geographic variance tiles (`GeoLatency`).
3. Detail hop table — ASN-level deltas with correlated internal change markers.

| UC | ThousandEyes tie-in |
|---|---|
| UC-5.9.5 Path Hop Count Analysis | Path length regression |
| UC-5.9.6 Network Path Change Detection | Route flaps vs DC moves |
| UC-5.9.34 HTTP Server Availability Monitoring | Test targets tied to SaaS SLAs |

| App | Splunkbase ID | Sourcetypes |
|---|---|---|
| Cisco ThousandEyes | 7719 | `ThousandEyesOTel`, `cisco:thousandeyes:test`, `cisco:thousandeyes:alert` |

### Cisco Catalyst SD-WAN (sub 5.5 + 5.8)

Cisco Catalyst SD-WAN overlays application-aware steering with
security service edge adjacencies — Splunk delivers single-pane
operational/security fusion. Cisco SD-WAN Manager dashboards
(`Enhanced Monitor Overview`, Release 20.7.1+) emphasize
customizable dashlets with global topology overlays summarizing
overlay vs underlay health. Splunk mirrors dashlet KPI families via
syslog (`cisco:vmanage:syslog`), IPS signatures
(`cisco:vmanage:ips`), NetFlow (`stream:cisco_hsl_netflow`) parsing
aligned with **Splunk Add-on for Cisco Catalyst SD-WAN**
(Splunkbase 6656) and **Cisco Catalyst SD-WAN App** (Splunkbase
6657). IOS-XE 17.10+ compatibility gates Splunk app expectations
around telemetry richness.

### Cisco Meraki (sub 5.14)

Meraki blends wireless telemetry with MT environmental sensors —
Splunk dashboards unify WLAN KPIs with sensor anomaly timelines.
**`Splunk_TA_cisco_meraki`** (Splunkbase 5580; release notes
highlight multi-org aggregation improvements including 3.3.0)
merges organizations via consolidated API credential scopes.
Sourcetypes: `meraki:devices`, `meraki:sensorreadingshistory`,
`meraki:webhook`, `meraki:dashboard:audit`.

### IOS / IOS-XE routers & switches (sub 5.1)

Classic Cisco forwarding-plane instrumentation feeds Splunk via
syslog (facility-oriented severity tokens), SNMP traps for hardware
redundancy transitions, and streaming telemetry adjuncts.

**TA:** **`TA-cisco_ios`** (Splunkbase 1352) supplies Cisco IOS
syslog transforms accelerating interface/protocol narratives.

| UC | Operational interpretation |
|---|---|
| UC-5.1.1 Interface Up/Down | Link-loss segmentation vs bounce churn |
| UC-5.1.4 BGP Peer State Changes | EBGP / IBGP peering instability |
| UC-5.1.11 Power Supply / Fan Failures | Hardware redundancy breaches |
| UC-5.1.16 Route Table Flapping | Control-plane instability |
| UC-5.1.20 EIGRP Neighbor Flapping | IGP reconvergence storms |
| UC-5.1.23 HSRP/VRRP State Changes | Default-gateway failover narratives |

### Other horizontal control planes — Firewalls + ADCs + Wireless + DNS/DHCP + Flow + gNMI + Carrier

Horizontal control-plane roles each map to measurable blast-radius
classes. The full per-domain narratives live in their respective
deep-dive guides; cross-references are flagged here so the
infrastructure master stays a navigation hub:

- **Firewalls (sub 5.2):** Palo Alto `traffic`/`threat`, Cisco
  Secure Firewall eStreamer, Fortinet, Check Point. Anchor UCs:
  UC-5.2.13 Session Table Exhaustion, UC-5.2.14 Firewall HA
  Failover. → `firewalls.md`.
- **Load Balancers / ADCs (sub 5.3):** F5 BIG-IP LTM/AFM, Citrix
  ADC, NGINX. Pool member health, SSL handshake failures, iHealth
  diagnostics. → `load-balancers-adcs.md`.
- **Wireless Infrastructure (sub 5.4):** Cisco Catalyst WLC + Aruba
  Central + Mist + Meraki MR. RF metrics (`SNR`, retry rate,
  channel utilization) contextualize Catalyst Center Assurance
  scores. → `wireless-infrastructure.md`.
- **DNS / DHCP / IPAM (sub 5.6):** Infoblox Grid syslog, BlueCat
  Address Manager, Microsoft DNS analytical, ISC BIND structured
  syslog. Anchor UCs: UC-5.6.5 DHCP Scope Exhaustion, UC-5.6.10
  DNSSEC Validation Failures. → `dns-dhcp.md`.
- **Network Flow Data (sub 5.7):** NetFlow v5/v9/IPFIX, sFlow,
  Zeek `conn.log` / `dns.log`. CIM Network Traffic acceleration
  powers UC-5.7.4 East-West Traffic Monitoring + UC-5.7.10
  Long-Duration Flow Detection. → `network-flow.md`.
- **gNMI / gRPC streaming telemetry (sub 5.11):** OpenConfig YANG
  paths via gNMI ON_CHANGE dial-out/dial-in collectors feeding
  Splunk HEC. NX-OS / Arista EOS line-rate counters for microburst
  analytics. UC-5.11.1 Interface Utilization via gNMI Streaming
  Counters, UC-5.11.3 BGP Peer State Change Detection via
  ON_CHANGE. → `gnmi-streaming.md`.
- **Carrier signaling & telecom CDR (sub 5.10 + 5.12):** SS7 /
  Diameter adjunct logs (where permissible), SIP ladder diagrams
  normalized to syslog, CDR batches via SFTP into tenant-partitioned
  indexes. → `carrier-signaling-telecom.md`.

---

## Domain 4 — Storage & Backup (cat 6, 81 UCs)

> Per-product depth: `storage-san-nas.md`, `object-storage.md`,
> `backup-recovery.md`, `file-services.md`.

### Subcategory map

| Sub | Focus | UCs | Deep-dive guide |
|---|---|---|---|
| 6.1 | SAN / NAS arrays | 30 | `storage-san-nas.md` |
| 6.2 | Object Storage | 11 | `object-storage.md` |
| 6.3 | Backup & Recovery | 24 | `backup-recovery.md` |
| 6.4 | File Services (NFS/SMB) | 8 | `file-services.md` |
| 6.6 | Database Trending | 8 | `database-platforms.md` |

### Capacity, latency, IOPS — unified lens

**WHAT:** Track utilization growth rates, thin-provisioning
headroom, controller queue depth, front-end Fibre Channel /
NVMe-oF latency percentiles.

**WHY:** Storage failures often present as latency tail events
before absolute space exhaustion — IOPS saturation matters for
bursty DB workloads even when capacity KPIs remain green.

**HOW:** Splunk ingestion from array APIs (`ONTAP`, `PowerStore`,
`Pure1`, `Isilon REST`) harmonized via TAs or custom modular
inputs — summary index daily growth projections (`predict` command
windows) feeding capacity burn-down dashboards.

### Vendor-specific array telemetry

**NetApp ONTAP — WHAT/WHY/HOW:** Subscribe to **EMS** event
catalogs (`wafl.cp.toolong`, `disk.hardware.error`) alongside REST
**`/api/storage/aggregates`** capacity payloads and Unified Manager
(AIQ-UM) performance polls. *Why:* WAFL checkpoint latency
precedes NFS timeouts observable only indirectly at hosts. *How:*
Splunk modular inputs stagger `/api/cluster` contexts per SVM —
dashboards correlate EMS severity with NFSv4 **`v4_x_err`** syslog
tails forwarded from NAS gateways.

**Dell EMC PowerStore / Unity — WHAT/WHY/HOW:** Pull REST
**`instance`** / `metric` families for node CPU/memory headroom
plus replication session states (`ReplicationSession`). *Why:*
Active/active Metro fabrics shift failure domains — Splunk must
pair replication lag seconds with VMware datastore latency from
Domain 2. *How:* OAuth-stored credentials inside Splunk credential
locker with rotating refresh tokens scripted nightly.

**Pure Storage FlashArray — WHAT/WHY/HOW:** Pure1 REST exposes
**`array`, `volume`, `host`** latency histograms (`usec_per_op`) —
trend drive rebuild states (`hardware.components`) alongside
predictive failure counters per Pure Operations Guide thresholds.
*Why:* All-flash arrays mask wear until parallel rebuild windows
coincide with peak OLTP bursts. *How:* Scheduled searches persist
`capacity` and `thin_provisioning` snapshot fields into summary
indexes powering UC-6.1.19 Pure Storage Array Health.

**Dell PowerScale (Isilon) — WHAT/WHY/HOW:** OneFS
**`isi_audit_categories`** syslog plus REST
**`/platform/*/cluster/status`** quorum narratives feed Splunk
alongside SMB/NFS latency proxies. *Why:* Scale-out NAS outages
cluster as **`JOB_ENGINE`** backlog spikes — capacity alone stays
green while metadata storms persist. *How:* Correlate UC-6.1.11
Isilon Cluster Health dashboards with SMB **`tcp`** connection
resets captured at adjacent Catalyst Center client metrics.

**Ceph — WHAT/WHY/HOW:** **`ceph -w`** / `ceph.log`, RADOSGW
access logs, Prometheus **`ceph_exporter`** scrape endpoints via
Splunk HEC OTel bridging. *Why:* Placement-group `degraded` /
`peering` states precede client IO stalls — Splunk overlays OSD
maps with host disk SMART narratives from Domain 1. *How:*
Implementation narrative captured in UC-6.1.14 Ceph Cluster Health.

### Backup and recovery analytics

**Veeam — WHAT/WHY/HOW:** Pull **Backup Enterprise Manager** SQL
views or REST **`BackupSessions`** / `ReplicaSessions` endpoints
via scripted inputs — fields include `Result`, `Duration`,
`TransferredSize`, `DedupRatio`, `IsIncremental`. *Why:* Veeam
dedupe anomalies precede repository fullness faster than datastore
KPIs alone when synthetic fulls balloon unexpectedly. *How:* Splunk
lookups translate `JobName` tokens into CMDB `business_service`
fields — failed backups escalate only when SLA tiers intersect
immutable retention gaps.

**Commvault — WHAT/WHY/HOW:** Forward **CommServe** Event Viewer
streams (`EvMgrs_*`), **`Jobs`** XML exports, **`CVPerfMgr`**
counters via ODBC pulls — normalize `jobOptions` / `failureReason`
enumerations vendor publishes per maintenance packs. *Why:* Multi-
tenant MSP overlays demand Splunk RBAC slicing `clientGroup` /
`organizationId`. *How:* Heavy Forwarder modular ODBC inputs
checkpoint `completedJobId` watermarks hourly — dashboards
emphasize `storagePolicyCopy` lag minutes for air-gapped vaults.

### Object storage & shared file services

**Object storage — WHAT/WHY/HOW:** Index S3-compatible access logs
(`GET`/`PUT` latency, `503` bursts), erasure-coded repair metrics
(`repairDuration`), and lifecycle transition failures from
**NetApp StorageGRID**, **Dell ECS**, **Scality RING**, or
cloud-adjacent stacks when Splunk aggregates hybrid bursting
patterns. *Why:* Erasure-coded rebuild windows interact with WAN
replication — Splunk ties object consistency lag to VMware
datastore snapshots when VADP-style backup targets sit on object
endpoints.

**File services — WHAT/WHY/HOW:** SMB
(`Microsoft-Windows-SMBClient/Operational`) alongside NFS `rpc`
timeout counters on Linux file clients provide end-host perspective
on array/controller issues. *Why:* Array controllers may assert
healthy yet client-side `STATUS_NETWORK_NAME_DELETED` storms
indicate split-brain DFS or stale DNS pointers. *How:* Splunk
correlation rules join DFS namespace events with UC-5.6.7 DNS
Record Change Audit timelines from Domain 3.

### Critical UCs

| UC | Tier focus |
|---|---|
| UC-6.1.1 Volume Capacity Trending | Capacity forecasting |
| UC-6.1.11 Isilon Cluster Health | Scale-out NAS resilience |
| UC-6.1.14 Ceph Cluster Health | Open-source SDS quorum narratives |
| UC-6.1.19 Pure Storage Array Health | All-flash endurance |
| UC-6.3.1 Backup Job Success Rate | DR/BCP attestation |
| UC-6.3.5 Veeam Repository Capacity | Backup landing zone |
| UC-6.3.10 Commvault Storage Policy Copy Lag | Air-gapped vault freshness |

---

## Domain 5 — Data Center Physical Infrastructure (cat 15, 81 UCs)

> Per-product depth: `datacenter-physical.md`, `meraki-mt.md` (for
> sensor portfolio), `splunk-edge-hub.md` (for protocol adapters).

### Subcategory map

| Sub | Focus | UCs | Deep-dive guide |
|---|---|---|---|
| 15.1 | Power / UPS / Generator / ATS | 32 | `datacenter-physical.md` |
| 15.2 | Cooling / Environmental | 27 | `datacenter-physical.md`, `meraki-mt.md` |
| 15.3 | Physical Security | 22 | `datacenter-physical.md` |

### UPS / generators / transfer switches

**WHAT:** Battery health metrics (`batteryReplaceIndicator`,
impedance trends), estimated runtime under load, generator fuel /
reserve autonomy, ATS source transfers.

**WHY:** Facilities failures produce IT incidents that appear
"mysteriously random" unless Splunk overlays UPS SNMP traps with
HVAC narratives — thermal excursions correlate with UPS fan faults
preceding shutdown.

**HOW:** Normalize SNMP OID walks via SC4SNMP / Splunk Modular
Inputs / Edge Hubs — alert when runtime projections drop below
contractual SLA envelopes correlated with concurrent rack PDU
redundancy losses.

| UC | Scenario |
|---|---|
| UC-15.1.1 UPS Battery Health | Cell degradation forecasting |
| UC-15.1.10 UPS Battery Runtime | Load-adjusted autonomy breaches |
| UC-15.1.12 Generator Fuel Level | Extended outage preparedness |
| UC-15.1.13 Transfer Switch Events | Utility/generator source transitions |

### Cooling & environmental

**WHAT:** CRAC humidity/temperature deltas, leak detection probes,
chiller plant performance, refrigerant leak detection (F-Gas
compliance), Legionella prevention monitoring.

**WHY:** Cooling degradations silently throttle CPU turbo bins
(looping back to Domain 1 CPU thermals).

**HOW:** Splunk correlation rules join Meraki MT sensors
(`meraki:sensorreadingshistory`) with Catalyst Center WLAN
Assurance thermal overlays where dense racks threaten RF
absorption anomalies — closing facilities/network causality loops.

### Physical security & access control

**WHAT:** Integrate badge reader syslog (`ACCESS_GRANTED` /
`DENIED`), biometric failures, elevator interlocks, video metadata
markers (where privacy policies permit aggregated counts only),
and intrusion-detection perimeter feeds — Splunk indexes
operational summaries rather than raw PII wherever feasible.

**WHY:** Physical breaches correlate with logical pivots — Splunk
timelines reconcile unauthorized badge retries with privileged VPN
authentications across Domain 3 firewall narratives.

**HOW:** Lookup tables anonymize `badge_id` / `employee_hash`;
Splunk alerts threshold `DENIED` streaks before pairing with
Catalyst Center `client` onboarding anomalies
(`failedDot1xAttempts`) where wireless campuses intersect secured
cages.

---

## Domain 6 — Data Center Fabric & SDN (cat 18, 76 UCs)

> Per-product depth: `cisco-aci.md`, `vmware-nsx.md`,
> `nexus-dashboard.md`, `sdn-evpn-vxlan.md`.

### Subcategory map

| Sub | Focus | UCs | Deep-dive guide |
|---|---|---|---|
| 18.1 | Cisco ACI | 23 | `cisco-aci.md` |
| 18.2 | VMware NSX | 18 | `vmware-nsx.md` |
| 18.3 | Other SDN (EVPN-VXLAN, FabricPath) | 22 | `sdn-evpn-vxlan.md` |
| 18.4 | Nexus Dashboard / NDFC / NDI / NDO | 13 | `nexus-dashboard.md` |

### Cisco ACI (23 UCs — sub 18.1)

APIC exposes hierarchical managed-object graphs — Splunk correlates
faults/events across tenants transparently. APIC assigns **health
scores 0–100** with severity-weighted fault penalties propagated
through MO parent/child hierarchies (`fvTenant`, `l3extOut`, `bd`,
`epg`). Flat syslog severity misses blast-radius prioritization —
score deltas localize remediation paths faster than CLI traversal.

**`Splunk Add-on for Cisco ACI`** (Splunkbase 4022) streams
`cisco:aci:faults`, `cisco:aci:events`, `cisco:aci:audit` — Splunk
dashboards bubble prioritized faults via lookups translating
distinguished-name paths into human-readable tenant/EPG labels.

#### Top-down troubleshooting workflow

Traverse faults → correlated events → MO-level health deltas →
drill into embedded tooling (`iPing`, `iTraceroute`, SPAN
orchestrations exposed via GUI workflows mirrored by Splunk
hyperlinks). Operators shorten MTTR following layered causality
rather than reactive SSH loops. Splunk drilldown searches pivot
`faultId` → `dn` → correlated `event` narratives; optional HEC
ingestion of packet-capture metadata when automation exports pcap
summaries.

| UC | Fabric narrative |
|---|---|
| UC-18.1.1 ACI Fabric Health Score Monitoring | Global spine/leaf posture |
| UC-18.1.17 Multi-Site Health | Inter-site contracts stretched fabrics |
| UC-18.1.20 Contract Violation and Implicit Deny Bursts | Policy-drop forensic timelines |
| UC-18.1.23 APIC Resource Exhaustion | Control-plane saturation |

#### REST endpoints and Splunk mapping

Poll APIC northbound REST namespaces — examples include
`/api/mo/uni/fvTenant` (tenant inventory), `/api/class/faultInst`
(active faults), `/api/class/aaaModLR` (audit commits). Splunk
dashboards join REST-derived fault counts with syslog-adjacent
`cisco:aci:audit` trails — operators prove whether automation
preceded implicit deny bursts versus silent policy drift. Scripted
inputs stagger intervals (`poll_interval_sec`) respecting APIC CPU
guidance.

### Cisco Nexus Dashboard & NX-OS (sub 18.4)

**WHAT:** Nexus Dashboard Fabric Controller (**NDFC**) aggregates
NX-OS telemetry, NetFlow/IPFIX exports, overlay/underlay
operational state for VXLAN/EVPN fabrics.

**WHY:** Campus Catalyst Center Assurance does not replace data-
center fabrics — Splunk overlays NDFC REST + streaming telemetry
alongside ACI feeds for brownfield coexistence.

**HOW:** **`Cisco DC Networking App for Splunk`** (Splunkbase 7777)
centralizes NX-OS / NDFC KPIs (`cisco:dcnetworking:*` families per
packaging) with complementary `cisco:aci:*` joins on `serial` /
`podId` bridging where crosswalks exist.

### VMware NSX (sub 18.2)

**WHAT:** Distributed firewall hit logs, IDS/IPS service chain
events, Tier-0/Tier-1 gateway HA failover semantics, GENEVE
transport health.

**WHY:** Micro-segmentation shifts enforcement closer to workloads
— routing anomalies manifest as firewall permit/deny bursts
versus classical ICMP gaps.

**HOW:** Splunk ingestion via syslog forwarders from NSX Manager
plus aggregated firewall logs normalized into Splunk Common
Information Model (`Network_Traffic`, `Intrusion_Detection`) where
feasible.

| UC | Interpretation |
|---|---|
| UC-18.2.12 NSX Tier-0/Tier-1 Gateway HA Failover | Control-plane redundancy regressions |

---

## Domain 7 — Compute Infrastructure (cat 19, 72 UCs)

> Per-product depth: `cisco-ucs.md`, `cisco-hyperflex.md`,
> `azure-stack-hci.md`, `intersight.md`.

### Subcategory map

| Sub | Focus | UCs | Deep-dive guide |
|---|---|---|---|
| 19.1 | Cisco UCS | 33 | `cisco-ucs.md` |
| 19.2 | Cisco HyperFlex (HCI) | 32 | `cisco-hyperflex.md` |
| 19.3 | Azure Stack HCI | 7 | `azure-stack-hci.md` |

### Cisco UCS (33 UCs — sub 19.1)

UCS Manager exposes hierarchical faults spanning chassis / blades /
FIs / service profiles — Splunk operationalizes XML API streams
alongside syslog semantics.

#### Fault severity taxonomy + FSM nuance

UCS faults categorize **critical / major / minor / warning**
severities across compute / rack / blade / storage subsystems.
Severity classes map to escalation cadence (IMT vs proactive RMA)
— mis-labeled suppressed faults erode SLA compliance. Splunk
lookups convert `severity` + `cause` tuples into ticket priority
classes; dashboards color by canonical vendor codes.

**FSM behavioral nuance:** Prioritize monitoring for **non-FSM
faults** — Finite State Machine transient faults auto-resolve
during normal provisioning while hardware-level faults persist.
Alerting on benign FSM churn misleads pager duty; Splunk
suppresses ephemeral FSM contexts when correlating success events.
SPL `transaction` spans `fault` + `fsmFsm` transitions with
`closed` semantics (per Cisco UCS fault reference).

#### Transport channels + CIMC monitoring

Combine **XML API** pulls, **SNMP** traps, **`Fault`/`Event`/
`Audit` syslogs**. API streams provide structured fields (`dn`,
`descr`, `severity`); syslog offers real-time propagation for link
/ rack sensor events before API poll windows elapse.
**`Splunk Add-on for Cisco UCS`** (see TA documentation for
release-specific input types) configures scheduled XML API scripted
inputs plus optional syslog receivers; Splunk TA supports up to 15
UCS Managers on approximately 8-core / 8GB search-tier resources
per sizing guidance — scale horizontally for larger fabrics.

Track rack server CIMC memory utilization (`memory available` vs
thresholds) alongside host OS memory to catch out-of-band
management regressions preceding host boot failures.

| UC | Operational focus |
|---|---|
| UC-19.1.1 Blade/Rack Server Health | Overall compute availability |
| UC-19.1.11 Service Profile Association Failures | Stateless automation breaks |
| UC-19.1.13 FI Port-Channel Errors | Fabric interconnect resilience |
| UC-19.1.15 Chassis PSU Redundancy Loss | Power-domain risk |
| UC-19.1.19 Intersight Server Alarm Monitoring | Cloud-managed alarm correlation |

### Cisco HyperFlex (sub 19.2)

**WHAT:** HX Connect / HXDP REST APIs expose cluster quorum
health, replication backlog depth, storage IO latency distributions
across SCSI / NFS fronts.

**WHY:** HCI collapses compute / storage networking — silent
replication divergence threatens workload consistency beyond naive
CPU KPI charts.

**HOW:** Splunk modular inputs authenticate REST tokens scoped per
HX cluster — normalize JSON counters (`clusterHealth`,
`resyncPercent`, `dedupeRatio`) into operational dashboards
correlated with VMware datastore KPIs from Domain 2.

### Azure Stack HCI (sub 19.3)

**WHAT:** Hyper-V guarded fabric telemetry, Storage Spaces Direct
(S2D) health, Azure Arc linkage signals.

**WHY:** Hybrid edge footprints inherit dual observability mandates
— on-prem HCI resilience plus Azure control-plane attestations.

**HOW:** Splunk Universal Forwarders on HCI nodes ingest Windows
perfmon + cluster logs alongside Arc heartbeat streams documented
under hybrid-cloud ingestion patterns.

---

## Cross-Domain Correlation Anchor

The most expensive infrastructure outages cross multiple domains
silently. Splunk's value emerges when one query traces a user
complaint back through every infrastructure layer.

### Pattern 1 — Cooling loss → CPU thermal throttle → application latency

```spl
| multisearch
  [ search index=hvac_bms sourcetype="bms:air" metric_name="ahu_supply_temp" 
    | where metric_value > 80 | eval event_class = "cooling_loss" ]
  [ search index=os sourcetype=cpu cpu_temp > 75
    | eval event_class = "thermal_throttle" ]
  [ search index=app_apm response_time_p95 > 2000
    | eval event_class = "latency_spike" ]
| eval site = coalesce(site, building, data_center)
| stats values(event_class) as classes, count by site, _time span=15m
| where mvcount(classes) >= 2
| sort - _time
```

### Pattern 2 — UPS battery → BMC PFA → ESXi reboot → VM HA storm

```spl
| multisearch
  [ search index=ups_pdu sourcetype="ups:snmp" battery_runtime_min < 15 ]
  [ search index=os sourcetype="bmc:redfish" predictive_failure_alert=1 ]
  [ search index=vmware sourcetype="vmware:events" event="HostUnexpectedShutdown" ]
  [ search index=vmware sourcetype="vmware:events" event="HACausedRestart" ]
| eval _key = coalesce(chassis_serial, host, vm)
| stats values(*) as * by _key, _time span=15m
| where event="HACausedRestart"
```

### Pattern 3 — BGP flap → SD-WAN tunnel down → branch outage → Catalyst Center issue

```spl
| multisearch
  [ search index=cisco_syslog sourcetype="cisco:ios" event_id="BGP-3-NOTIFICATION" 
    | eval event_class = "bgp_flap" ]
  [ search index=vmanage sourcetype="cisco:vmanage:bfd" state="down" 
    | eval event_class = "sdwan_tunnel_down" ]
  [ search index=cisco_dnac sourcetype="cisco:dnac:issue" priority IN ("P1","P2")
    | eval event_class = "dnac_issue" ]
| eval _key = coalesce(site_id, branch, location)
| stats values(event_class) as classes, count by _key, _time span=10m
| where mvcount(classes) >= 2
```

---

## CMDB and Asset Identity Anchor

Cross-domain correlation only works when identity is consistent.
The minimum identity contract:

| Field | Meaning | Source of truth |
|---|---|---|
| `host` | Canonical hostname | DNS / CMDB |
| `serial` | Hardware serial | OEM (Cisco, Dell, HP, Lenovo) |
| `mac_address` | Primary management MAC | DHCP / IPAM |
| `business_service` | Business-aligned service name | CMDB |
| `tier` | tier-1 / tier-2 / tier-3 / dev | CMDB |
| `environment` | prod / staging / dev / dr | CMDB |
| `site` | Physical location code | CMDB |
| `data_center` | DC identifier | CMDB |
| `rack` | Rack within DC | DCIM |
| `cluster` | Compute cluster name | vCenter / Hyper-V / Kubernetes |
| `chassis` | Chassis serial | UCS / HPE / Dell |
| `service_owner` | Email of ownership | CMDB |
| `criticality` | critical / high / medium / low | CMDB |

Build nightly KVStore lookup `infra_identity_lookup.csv` from
ServiceNow CMDB / BMC Helix / NetBox / Nautobot exports. Apply via
`automatic_lookup` on every infrastructure index to make these
fields auto-extracted on every event.

---

## Crawl / Walk / Run Roadmap (28 / 75 / 60 UCs)

### Crawl tier (28 UCs — month 1-2)

| UC | Domain | Title |
|---|---|---|
| 1.1.7 | Linux | OOM Killer Events |
| 1.1.8 | Linux | SSH Brute-Force Detection |
| 1.1.9 | Linux | Unauthorized Sudo Usage |
| 1.1.23 | Linux | Kernel Core Dump Generation |
| 1.1.102 | Bare-metal | EDAC Memory Error Tracking |
| 1.2.1 | Windows | Windows Service Crash (7031/7034) |
| 1.2.18 | Windows | Failed Logon Anomaly |
| 1.2.50 | Windows | BitLocker Status |
| 2.1.21 | VMware | ESXi Host Unexpected Reboot |
| 2.1.22 | VMware | vCenter Service Health |
| 2.1.3 | VMware | Datastore Capacity Trending |
| 5.1.1 | Network | Interface Up/Down |
| 5.1.4 | Network | BGP Peer State Changes |
| 5.1.11 | Network | Power Supply / Fan Failures |
| 5.1.23 | Network | HSRP/VRRP State Changes |
| 5.13.1 | Catalyst Ctr | Issue Severity Trend |
| 5.6.5 | DNS/DHCP | DHCP Scope Exhaustion |
| 6.1.1 | Storage | Volume Capacity Trending |
| 6.3.1 | Backup | Backup Job Success Rate |
| 15.1.1 | Facilities | UPS Battery Health |
| 15.1.10 | Facilities | UPS Battery Runtime |
| 15.1.13 | Facilities | Transfer Switch Events |
| 15.2.x | Facilities | Cooling temp anomaly (CRAC) |
| 18.1.1 | Fabric | ACI Fabric Health Score |
| 19.1.1 | UCS | Blade/Rack Server Health |
| 19.1.11 | UCS | Service Profile Association Failures |
| 19.1.13 | UCS | FI Port-Channel Errors |
| 19.1.15 | UCS | Chassis PSU Redundancy Loss |

### Walk tier (75 UCs — month 3-6)

Highlights:
- Catalyst Center full Assurance + Inventory + Audit + SWIM + PSIRT correlation
- ThousandEyes path/SaaS overlays merged with internal change-window markers
- Catalyst SD-WAN tunnel matrix + BFD + OMP route convergence + IPSec cipher compliance
- VMware vSphere CPU Ready / balloon / swap / snapshot governance with baseline thresholds
- NetApp ONTAP EMS + REST + AIQ-UM full coverage
- Dell PowerStore / PowerScale / Pure FlashArray full coverage
- Veeam + Commvault backup analytics with chargeback
- ACI fabric multi-site + service graph + contract violation
- VMware NSX distributed firewall + IDS/IPS service chain
- Cisco UCS XML API + IMC + Intersight cloud correlation
- HyperFlex HXDP REST cluster quorum + replication
- BMC / Redfish PFA + EDAC + thermal correlation across server fleets
- gNMI streaming for microburst analytics
- Wireless RF baselining (Catalyst WLC + Aruba + Mist + Meraki MR)
- Hyper-V CSV reconnect storms + KVM/Proxmox kernel metrics
- Citrix VDI session quality + ICA RTT + Workspace App reliability
- DNS RPZ / DNSSEC / Infoblox Grid replication health
- Object storage S3 latency / lifecycle compliance
- Refrigerant leak / F-Gas compliance / Legionella prevention from Domain 5

### Run tier (60 UCs — month 7+)

Highlights:
- ML-driven capacity forecasting (Splunk MLTK on storage / compute / network)
- ITSI service trees with cascading impact across all 7 domains
- ESCU detection content for infrastructure attack patterns (LotL, ProxyLogon, ZeroLogon, lateral movement)
- RBA risk-objects per host / service for cross-domain risk scoring
- Atomic Red Team / purple-team cycle with infrastructure detection coverage
- SOAR auto-remediation playbooks (revert ACL, restart service, decommission failed disk, evacuate VM)
- Continuous control monitoring evidence packs (NIS2 + DORA + SOC 2 + ISO 27001 + PCI DSS + NERC CIP)
- Multi-vendor SD-WAN benchmarking (Cisco vs Aruba vs Fortinet vs VeloCloud)
- VxRail / VxBlock / Azure Stack HCI hyperconverged service trees
- Predictive maintenance via vibration / temperature / acoustic ML on chassis BMC sensors
- Quantum-readiness audit (post-quantum cryptography for SSH / TLS / IPSec)
- Smart Licensing reservation auto-renewal + entitlement compliance
- DCIM full integration (Sunbird / Schneider Ecostruxure IT / Vertiv) with Splunk

---

## Sizing and Capacity Planning

| Source | Per-1k-server daily volume | Monthly storage |
|---|---|---|
| Linux UF metrics + syslog | 500 MB | 15 GB |
| Linux `auditd` (full audit) | 2-5 GB | 60-150 GB |
| Windows EventLog Security | 1-3 GB | 30-90 GB |
| Windows EventLog System + App | 500 MB | 15 GB |
| Windows PerfMon (15s sample) | 1 GB | 30 GB |
| BMC SEL / Redfish PFA | 100 MB | 3 GB |
| VMware vCenter perf counters | 500 MB - 1 GB | 15-30 GB |
| Cisco IOS / IOS-XE syslog | 200-500 MB | 6-15 GB |
| Cisco Catalyst Center REST | 200 MB | 6 GB |
| Cisco Catalyst SD-WAN | 500 MB | 15 GB |
| Cisco ACI faults + events + audit | 300 MB | 9 GB |
| Cisco UCS XML API + syslog | 200 MB | 6 GB |
| Cisco ThousandEyes OTel | 100 MB | 3 GB |
| Meraki webhook + REST | 200 MB | 6 GB |
| NetFlow / IPFIX (Stream) | 1-5 GB | 30-150 GB |
| F5 BIG-IP LTM/AFM | 500 MB | 15 GB |
| Infoblox Grid syslog + DNS analytical | 1-3 GB | 30-90 GB |
| NetApp ONTAP REST + EMS | 200 MB | 6 GB |
| Dell PowerStore / Unity REST | 200 MB | 6 GB |
| Pure Storage Pure1 REST | 100 MB | 3 GB |
| Veeam Backup REST | 100 MB | 3 GB |
| Commvault EvMgr | 200 MB | 6 GB |
| UPS / PDU / HVAC SNMP | 100 MB | 3 GB |
| BMS / BACnet | 200 MB | 6 GB |
| Badge / physical access | 100 MB | 3 GB |
| Meraki MT sensors | 50 MB | 1.5 GB |

**Worked example (10k-server enterprise + 50 branches + 3 DCs +
100 buildings):**
- Server OS (10k): ~50 GB/day (Linux + Windows + bare-metal)
- Virtualization (3k VMware hosts + 2k Hyper-V + 500 KVM): ~10 GB/day
- Network core + branch (Cisco IOS / NX-OS / SD-WAN): ~30 GB/day
- Catalyst Center + ThousandEyes + Meraki: ~5 GB/day
- Storage (300 arrays NetApp+Dell+Pure): ~6 GB/day
- Backup (Veeam+Commvault): ~5 GB/day
- ACI + Nexus Dashboard + UCS + HyperFlex: ~10 GB/day
- DC physical (3 DCs UPS/HVAC/badge + 100 buildings BMS): ~5 GB/day
- NetFlow / Stream wire data: ~50 GB/day
- DNS/DHCP/Infoblox: ~10 GB/day

→ **~180 GB/day indexed infrastructure data** for a fully-
instrumented programme. SmartStore + Federated Search for Amazon
S3 essential for long-term forensics retention beyond hot+warm
days.

---

## Compliance Mapping

| Framework | Domain | Critical UCs |
|---|---|---|
| **SOC 2 CC7.1** | All | UC-1.1.7, UC-1.1.8, UC-2.1.21, UC-15.1.1, etc. |
| **SOC 2 A1.1-3** | All | Backup + capacity + availability UCs |
| **PCI DSS Req 1** | Network | UC-5.2.x firewall + UC-22.11.1 firewall review |
| **PCI DSS Req 10** | All | All audit-trail UCs |
| **HIPAA §164.312(a)** | All | All access-control UCs |
| **HIPAA §164.312(b)** | All | Audit logging |
| **GDPR<sup class="ref">[<a href="#ref-4">4</a>]</sup> Art. 32** | All | Security of processing |
| **NIS2 Art. 21(2)(d)** | All | Access control |
| **NIS2 Art. 21(2)(g)** | All | Network and info system security |
| **DORA Art. 5-14** | All | ICT risk management |
| **NIST CSF 2.0 PR.AC** | All | Access control protections |
| **NIST CSF 2.0 PR.IR** | All | Infrastructure resilience |
| **NIST CSF 2.0 DE.CM** | All | Continuous monitoring |
| **NIST CSF 2.0 RC.RP** | Backup | Recovery planning |
| **NIST 800-53 r5 AU-2** | All | UC-22.14.1 logging coverage |
| **NIST 800-53 r5 SI-4** | All | System monitoring |
| **NIST 800-53 r5 CP-9** | Backup | Backup |
| **NIST 800-53 r5 PE-3** | Facilities | Physical access control |
| **CIS Control 1** | All | Asset inventory |
| **CIS Control 4** | All | Secure config |
| **CIS Control 8** | All | Audit log management |
| **CIS Control 13** | Network | Network monitoring & defense |
| **DISA STIG (Linux/Windows)** | OS | Per-platform STIG coverage |
| **DISA STIG (Cisco IOS-XE)** | Network | UC-5.5.13 IPSec FIPS compliance |
| **NERC CIP-002** | OT-adjacent | UC-14.9.1 OT inventory + facilities |
| **NERC CIP-007 R4** | OT-adjacent | Security event monitoring |
| **NERC CIP-009** | Backup | Recovery plans |
| **NERC CIP-014** | Facilities | Physical security |
| **TSA Pipeline SD-2** | Facilities | Critical infrastructure |
| **MITRE ATT&CK** | All | Lateral movement + persistence + impact |

See `compliance-business.md` and `docs/evidence-packs/` for per-
framework deep dives.

---

## Reference Dashboards

| Dashboard | Audience | Refresh | Source |
|---|---|---|---|
| Infrastructure Executive Health | CIO + Infra Director | 5 min | All indexes via ITSI |
| NOC War Room Console | NOC Manager + 24×7 | 1 min | All critical UCs |
| Linux Fleet Health | Linux Lead | 5 min | `os`, `linux_secure`, `auditd` |
| Windows Fleet Health | Windows Lead | 5 min | `wineventlog`, `perfmon` |
| Bare-Metal Hardware (BMC PFA) | Hardware Ops | 5 min | `os` BMC sourcetypes |
| VMware vSphere Cluster Health | Virt Lead | 1 min | `vmware:perf`, `vmware:events` |
| Hyper-V CSV Health | Windows Virt Lead | 5 min | `hyperv:event` |
| Citrix VDI Quality | VDI Lead | 5 min | `citrix:broker`, `citrix:adc:syslog` |
| Cisco Catalyst Network Topology | Network Engineer | 1 min | `cisco:dnac:*` |
| Cisco SD-WAN Tunnel Matrix | WAN Architect | 1 min | `cisco:vmanage:bfd` |
| ThousandEyes Path / SaaS SLA | Network + DevX | 5 min | `ThousandEyesOTel` |
| Cisco ACI Fabric Health | Fabric Lead | 1 min | `cisco:aci:health` |
| Nexus Dashboard Insights | Fabric Lead | 5 min | `cisco:nexusdashboard:insight` |
| Cisco UCS Chassis Health | Compute Lead | 5 min | `cisco:ucs:fault` |
| HyperFlex Cluster Health | HCI Lead | 5 min | `cisco:hyperflex:rest` |
| NetApp ONTAP Cluster Capacity | Storage Lead | 1h | `netapp:ontap:rest` |
| Dell PowerStore / Unity Latency | Storage Lead | 5 min | `dell:powerstore:rest` |
| Pure FlashArray Endurance | Storage Lead | 1h | `pure:flasharray:rest` |
| Veeam Backup Compliance | Backup Lead | daily | `veeam:backup:job` |
| UPS / Generator / ATS Status | Facilities | 5 min | `ups:snmp` |
| HVAC / CRAC Cooling Dashboard | Facilities | 5 min | `hvac:snmp`, `bms:air` |
| Legionella Compliance (DHW) | Facilities + Health | 1h | `bms:water` |
| Physical Access Anomalies | Security + Facilities | 5 min | `badge:reader` |
| Cross-Domain Outage Correlation | NOC + Facilities + Net + SOC | 1 min | All indexes |
| Capacity Forecasting (12 months) | CIO + FinOps | weekly | `os_metrics`, `vmware:perf`, storage REST |

---

## SPL Examples

### Linux OOM cascade detection (UC-1.1.7)

```spl
index=os sourcetype=linux_secure OR sourcetype=auditd ("Out of memory" OR "oom-killer")
| rex "Killed process \d+ \((?<killed_process>[^)]+)\)"
| stats count, values(killed_process) as victims, dc(killed_process) as victim_diversity by host, _time span=1h
| where count > 5 OR victim_diversity > 3
| eval severity = if(count > 20, "critical", "high")
```

### VMware CPU Ready percentile baselining (UC-2.1.x)

```spl
index=vmware sourcetype="vmware:perf" counter="cpu.ready.summation"
| eval ready_pct = (value / (interval * 1000)) * 100 / num_vcpu
| stats avg(ready_pct) as avg_ready, perc95(ready_pct) as p95_ready by cluster, host, _time span=15m
| join cluster, host
    [search index=vmware sourcetype="vmware:perf" counter="cpu.ready.summation" earliest=-30d
     | eval ready_pct = (value / (interval * 1000)) * 100 / num_vcpu
     | stats perc95(ready_pct) as baseline_p95 by cluster, host]
| eval anomaly_score = round(p95_ready / baseline_p95, 2)
| where anomaly_score > 2
```

### Cross-domain BGP flap → Catalyst Center issue correlation

```spl
| multisearch
  [ search index=cisco_syslog sourcetype="cisco:ios" event_id="BGP-3-NOTIFICATION" 
    | eval event_class = "bgp_event" ]
  [ search index=cisco_dnac sourcetype="cisco:dnac:issue" 
    | eval event_class = "dnac_issue" ]
| eval entity = coalesce(neighbor_ip, deviceManagementIp, host)
| stats values(event_class) as classes, list(_raw) as evidence, count by entity, _time span=10m
| where mvcount(classes) >= 2
| sort - count
```

### NetApp ONTAP capacity prediction (UC-6.1.1)

```spl
index=netapp sourcetype="netapp:ontap:rest"
| stats max(used_bytes) as used by aggregate, _time span=1d
| timechart span=1d max(used) as used by aggregate
| predict used_aggregate1 future_timespan=180 algorithm=LL
| where 'lower95(used_aggregate1)' > 0.85 * size_aggregate1
```

> `| predict` emits three side-channel fields per forecast:
> `prediction(<field>)`, `lower95(<field>)`, and `upper95(<field>)`.
> The parentheses are part of the field name, so each one has to be
> referenced with single quotes — Splunk's escape for non-identifier
> field names. The earlier formulation `lower95(prediction(...))`
> implied a nested function call (none exists) and would never
> compile.

### Cisco UCS critical-fault aging

```spl
index=cisco_ucs sourcetype="cisco:ucs:fault" severity IN ("critical", "major")
| stats min(_time) as first_seen, max(_time) as last_seen, latest(ack) as ack by faultId, dn, descr
| eval age_hours = (last_seen - first_seen) / 3600
| where age_hours > 4 AND ack="no"
| sort - age_hours
```

### UPS battery + Datastore latency cross-correlation

```spl
| multisearch
  [ search index=ups_pdu sourcetype="ups:snmp" battery_runtime_min < 30 
    | eval event_class = "ups_low_battery" ]
  [ search index=vmware sourcetype="vmware:perf" counter="datastore.totalReadLatency" value > 30
    | eval event_class = "datastore_latency" ]
| eval _key = coalesce(data_center, site, location)
| stats values(event_class) as classes by _key, _time span=15m
| where mvcount(classes) >= 2
```

### Cisco Catalyst Center + ThousandEyes + Splunk APM cross-narrative

```spl
| multisearch
  [ search index=cisco_dnac sourcetype="cisco:dnac:issue" priority IN ("P1","P2") | eval event_class="dnac" ]
  [ search index=thousandeyes sourcetype="ThousandEyesOTel" packet_loss > 5 | eval event_class="te_loss" ]
  [ search index=app_apm response_time_p95 > 2000 | eval event_class="app_slow" ]
| eval entity = coalesce(siteName, agent_name, service)
| stats values(event_class) as classes by entity, _time span=15m
| where mvcount(classes) >= 2
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Splunk_TA_nix` empty `/proc` data | UF running as non-root without sudo | Grant capability or run agent as appropriate user |
| `Splunk_TA_windows` empty PerfMon | WinRM / WMI permissions | Verify service account permissions |
| WinEventLog Security volume too high | Audit policy too broad | Tune Advanced Audit Policy categories |
| `auditd` log volume explosion | Wildcard rule on syscall | Filter by syscall + user pattern |
| VMware perf counter gaps | vCenter API throttling | Increase poll interval; shard credentials |
| Hyper-V CSV reconnect false positives | Maintenance window exclusion missing | Add CMDB-backed maintenance calendar lookup |
| Cisco IOS syslog parse errors | TA-cisco_ios out of date | Upgrade to current TA-cisco_ios version |
| Catalyst Center session 401 | Token expired | Re-authenticate; cache new token in vault |
| Catalyst Center inventory stale | REST polling too slow | Reduce polling interval to 10 min for inventory |
| ACI faultInst polling 429 | APIC CPU guidance breached | Stagger interval; use bulk subscribe |
| ACI multi-pod sync gap | Network connectivity to remote APIC | Verify multi-pod IPN reachability |
| UCS XML API empty response | Manager not in HA active state | Failover to active FI; verify XML API enabled |
| HyperFlex REST 401 | Token rotation skipped | Refresh token via local credential rotation script |
| NetApp REST capacity stale | AIQ-UM not synced | Verify Active IQ Unified Manager poll interval |
| Pure1 REST throttled | API quota exceeded | Reduce poll cadence; combine objects |
| Veeam BackupSession missing fields | EM config behind backup version | Update Veeam Enterprise Manager |
| UPS SNMP trap silent | Community string drift | Verify SNMP community on UPS; SC4SNMP profile |
| HVAC Modbus timeout | Scan budget exceeded | Reduce poll frequency; respect device scan cycle |
| Badge reader gaps | TLS cert mid-roll | Renew TLS cert + re-establish syslog channel |
| Meraki MT sensor offline | Battery / Wi-Fi / firmware | Check Meraki Dashboard alerts; replace battery |
| ThousandEyes OTel HEC 401 | HEC token expired | Rotate HEC token; update OTel exporter |
| NetFlow ingestion gaps | Stream collector overload | Add collector tier; partition by exporter |
| Splunk indexer queue full | Source surge / parsing storm | Tune `props.conf`; investigate ingest spikes |
| ITSI service tree broken | Dependency mapping stale | Refresh CMDB ITSI dependency import |
| Cross-domain correlation flaky | CMDB lookup nightly drift | Increase lookup refresh; add fallback |

---

## SOAR Playbook Catalogue

| Playbook | Trigger UC | Phases | Severity |
|---|---|---|---|
| `linux_oom_response` | UC-1.1.7 | identify victims, restart service, page service owner | High |
| `windows_service_crash_response` | UC-1.2.1 | restart service, escalate after 3 retries | Medium |
| `ssh_brute_force_response` | UC-1.1.8 | block source IP at firewall, page IR | High |
| `bmc_pfa_remediation` | UC-1.1.103 | open RMA ticket, evacuate VMs, schedule replacement | High |
| `esxi_unexpected_reboot` | UC-2.1.21 | check correlated UPS / HVAC / BMC, page Virt + Facilities | Critical |
| `datastore_capacity_warn` | UC-2.1.3 | open capacity ticket, suspend snapshots, vMotion candidates | Medium |
| `bgp_flap_response` | UC-5.1.4 | check correlated SD-WAN tunnel, RCA template, ITSM ticket | High |
| `dnac_issue_response` | UC-5.13.1 | enrich with assurance context, route to network engineer | Medium |
| `sdwan_tunnel_down` | UC-5.5.1 | check ThousandEyes path, page network on-call | High |
| `aci_health_score_drop` | UC-18.1.1 | identify affected tenant, escalate by service tier | High |
| `ucs_chassis_psu_redundancy_loss` | UC-19.1.15 | dispatch facilities check on rack power, RMA PSU | High |
| `hyperflex_replication_lag` | UC-19.2.x | check upstream network, page HCI lead | High |
| `netapp_aggregate_capacity` | UC-6.1.1 | open capacity ticket, suspend old snapshots, schedule expansion | Medium |
| `pure_array_health_degrade` | UC-6.1.19 | open Pure case, validate alternate paths | High |
| `veeam_backup_failure` | UC-6.3.1 | retry job, escalate after 2 retries, page backup admin | High |
| `ups_battery_low_runtime` | UC-15.1.10 | dispatch facilities check, prepare orderly shutdown if extended | Critical |
| `crac_cooling_failure` | UC-15.2.x | check correlated CPU thermals, escalate to facilities | Critical |
| `legionella_compliance_failure` | UC-14.1.40 | dispatch facilities, public health notification, retest | Critical |
| `cross_domain_outage_correlation` | (cross-domain) | aggregate evidence, war-room page, exec notification | Critical |

---

## Cross-Product Integration

| Other guide | Relationship |
|---|---|
| `linux-servers.md` | Cat-1.1 deep dive — Linux OS + auditd + journal |
| `windows-servers.md` | Cat-1.2 deep dive — Windows Event Log + PerfMon |
| `macos.md` | Cat-1.3 deep dive — macOS endpoints |
| `bare-metal-hardware.md` | Cat-1.4 deep dive — BMC + IPMI + Redfish |
| `vmware.md` | Cat-2.1 deep dive — vSphere + ESXi + vCenter |
| `hyperv.md` | Cat-2.2 deep dive — Microsoft Hyper-V + SCVMM |
| `kvm-proxmox-ovirt.md` | Cat-2.3 deep dive — open-source virtualization |
| `citrix-virtual-apps-desktops.md` | Cat-2.5+2.6 deep dive — Citrix CVAD / DaaS |
| `cisco-networks.md` | Cat-5.1 deep dive — Cisco IOS / IOS-XE / NX-OS |
| `firewalls.md` | Cat-5.2 deep dive — Cisco Secure FW + PAN + Fortinet |
| `load-balancers-adcs.md` | Cat-5.3 deep dive — F5 + Citrix ADC + NGINX |
| `wireless-infrastructure.md` | Cat-5.4 deep dive — Cisco WLC + Aruba + Mist + Meraki MR |
| `sd-wan-network-management.md` | Cat-5.5 + 5.8 deep dive — SD-WAN + NMP |
| `dns-dhcp.md` | Cat-5.6 deep dive — Infoblox + BlueCat + Microsoft DNS |
| `network-flow.md` | Cat-5.7 deep dive — NetFlow / IPFIX / Zeek |
| `cisco-thousandeyes.md` | Cat-5.9 deep dive — ThousandEyes |
| `gnmi-streaming.md` | Cat-5.11 deep dive — gNMI / model-driven telemetry |
| `carrier-signaling-telecom.md` | Cat-5.10 + 5.12 deep dive |
| `catalyst-center.md` | Cat-5.13 deep dive — Catalyst Center / DNA Center |
| `storage-san-nas.md` | Cat-6.1 deep dive — NetApp + Dell + Pure + Ceph |
| `object-storage.md` | Cat-6.2 deep dive — S3 + StorageGRID + ECS |
| `backup-recovery.md` | Cat-6.3 deep dive — Veeam + Commvault + Cohesity + Rubrik |
| `file-services.md` | Cat-6.4 deep dive — NFS + SMB + DFS |
| `database-platforms.md` | Cat-6.6 + cat-7 — DB tier monitoring |
| `datacenter-physical.md` | Cat-15 deep dive — UPS + HVAC + physical security |
| `meraki-mt.md` | Cat-14.1 — Meraki MT sensors for facility / IT closet |
| `splunk-edge-hub.md` | Cat-14.3 — Edge Hub for OT-adjacent ingestion |
| `cisco-aci.md` | Cat-18.1 deep dive |
| `vmware-nsx.md` | Cat-18.2 deep dive |
| `nexus-dashboard.md` | Cat-18.4 deep dive |
| `cisco-ucs.md` | Cat-19.1 deep dive |
| `cisco-hyperflex.md` | Cat-19.2 deep dive |
| `azure-stack-hci.md` | Cat-19.3 deep dive |
| `intersight.md` | Cisco Intersight cloud-managed UCS |
| `compliance-business.md` | Cat-20 + 22 + 23 — compliance evidence pack |
| `splunk-itsi.md` | Cat-13.2 — service tree + KPI base searches |
| `splunk-platform-health.md` | Cat-13.1 — Splunk-itself audit trail |
| `application-monitoring.md` | Cat-7 + 8 + 12 + 13 + 16 — bridge to app reliability |
| `security-monitoring.md` | Cat-9 + 10 + 17 — bridge to security overlays |
| `cloud-monitoring.md` | Cat-3 + 4 + 20 — bridge to cloud / hybrid |
| `iot-ot.md` | Cat-14 — bridge to OT / industrial |

---

## References

### Standards and frameworks (with stable URLs)

- AICPA Trust Services Criteria — https://www.aicpa.org/
- ISO/IEC 27001:2022 — https://www.iso.org/standard/27001
- ISO/IEC 27017 (cloud) + 27018 (PII clouds)
- HIPAA Security Rule<sup class="ref">[<a href="#ref-12">12</a>]</sup> — https://www.hhs.gov/hipaa/
- PCI DSS 4.0 — https://www.pcisecuritystandards.org/
- GDPR — https://gdpr.eu/
- EU NIS2 Directive<sup class="ref">[<a href="#ref-3">3</a>]</sup> — https://eur-lex.europa.eu/eli/dir/2022/2555/oj
- EU DORA — https://eur-lex.europa.eu/eli/reg/2022/2554/oj
- NIST CSF 2.0 — https://www.nist.gov/cyberframework
- NIST SP 800-53 r5 — https://csrc.nist.gov/pubs/sp/800/53/r5/final
- NIST SP 800-92 (log management) + 800-184 (ransomware recovery) + 800-207 (ZTA)
- FedRAMP — https://www.fedramp.gov/
- DISA STIGs — https://public.cyber.mil/stigs/
- CIS Critical Security Controls v8 — https://www.cisecurity.org/
- CIS Foundations Benchmarks (per-platform)
- NERC CIP — https://www.nerc.com/pa/Stand/Pages/CIPStandards.aspx
- TSA Pipeline Security Directive — https://www.tsa.gov/
- MITRE ATT&CK Enterprise — https://attack.mitre.org/

### Vendor documentation

- Cisco Catalyst Center admin guide + REST API reference
- Cisco Catalyst SD-WAN (vManage) admin guide
- Cisco ACI APIC admin guide + REST API reference
- Cisco UCS Manager admin guide + Faults reference
- Cisco Intersight admin guide + REST API
- Cisco Nexus Dashboard admin guide
- Cisco IOS / IOS-XE / NX-OS configuration guides
- Cisco ThousandEyes admin (https://docs.thousandeyes.com/)
- VMware vSphere admin guide + esxtop reference
- VMware NSX admin guide
- VMware Aria Operations / vRealize Operations
- Microsoft Hyper-V admin guide
- Microsoft Windows Server documentation
- NetApp ONTAP admin guide + REST API reference
- Dell PowerStore / Unity / PowerScale admin guides
- Pure Storage Pure1 REST + Operations Guide
- Veeam Backup & Replication user guide + REST API
- Commvault user guide
- F5 BIG-IP admin guide
- Infoblox NIOS admin guide
- BlueCat Address Manager admin guide
- Citrix CVAD / DaaS admin guide

### Splunk documentation

- Splunk Enterprise Security 8 — User Manual, Use Case Library, RBA
- Splunk SOAR — Playbook authoring, REST API
- Splunk ITSI — Service tree + KPI base searches
- Splunk OpenTelemetry Collector for Network Devices
- Splunk Stream — wire data
- Splunk Connect for Syslog (SC4S)
- Splunk Connect for SNMP (SC4SNMP)
- Splunk Federated Search for Amazon S3 — long-term retention
- Splunk Edge Processor — field-level redaction at ingest
- Splunk Add-on for Unix and Linux (833)
- Splunk Add-on for Windows (742)
- Splunk Add-on for VMware
- Splunk Add-on for Cisco IOS (1352)
- Splunk Add-on for Cisco ACI (4022)
- Splunk Add-on for Cisco Meraki (5580)
- Cisco Catalyst Add-on for Splunk (7538)
- Cisco Enterprise Networking App for Splunk (7539)
- Cisco DC Networking App for Splunk (7777)
- Cisco ThousandEyes Add-on for Splunk (7719)
- Splunk Add-on for Cisco Catalyst SD-WAN (6656) + App (6657)

---

**Document maintenance.** Reviewed quarterly against vendor
release notes, regulatory updates, and Splunk product updates.
Last verified against:
- Splunk Enterprise Security 8.0
- Splunk SOAR 6.x
- Splunk ITSI (current)
- ESCU current quarterly drop
- Splunk_TA_nix 9.x + Splunk_TA_windows 9.x
- TA-cisco_ios 6.x
- Cisco Catalyst Add-on for Splunk 1.4+
- Splunk Add-on for Cisco Meraki 2.4+
- Cisco Catalyst Center 2.3.7+
- Cisco Catalyst SD-WAN Manager 25.x
- Cisco IOS-XE SD-WAN 17.13+
- VMware vSphere 7.0 / 8.0
- NetApp ONTAP 9.x
- Dell PowerStore / Unity / PowerScale current
- Pure Storage current
- Veeam Backup & Replication 12.x
- Commvault 11.x
- ISO/IEC 27001:2022 + 27017 + 27018
- NIST CSF 2.0 + 800-53 r5 + 800-92 + 800-184 + 800-207
- PCI DSS 4.0.1
- GDPR + UK GDPR<sup class="ref">[<a href="#ref-13">13</a>]</sup>
- NIS2 + DORA (EU)
- FedRAMP rev 5
- DISA STIGs (current)
- CIS Critical Security Controls v8

For corrections or additions, file an issue with `domain-infrastructure`,
`cat-1`, `cat-2`, `cat-5`, `cat-6`, `cat-15`, `cat-18`, or
`cat-19` labels.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Primary sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Splunk Infrastructure Monitoring Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/observability/en/infrastructure/intro-to-infrastructure.html

### Supporting sources

<a id="ref-2"></a>**[2]** Beyer, B., Jones, C., Petoff, J., & Murphy, N. R. (Eds.). (2016). *Site Reliability Engineering: How Google Runs Production Systems*. O'Reilly Media. ISBN 978-1491929124. https://sre.google/sre-book/table-of-contents/

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-4"></a>**[4]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-5"></a>**[5]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-6"></a>**[6]** Gregg, B. (2012). *The USE Method: Utilization, Saturation, and Errors*. brendangregg.com. https://www.brendangregg.com/usemethod.html

<a id="ref-7"></a>**[7]** Payment Card Industry Security Standards Council. (2018). *Payment Card Industry Data Security Standard v3.2.1* (v3.2.1). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-8"></a>**[8]** Payment Card Industry Security Standards Council. (2022). *Payment Card Industry Data Security Standard v4.0* (v4.0). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-9"></a>**[9]** Splunk Inc. (2026). *Splunk Distribution of the OpenTelemetry Collector*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/observability/en/gdi/opentelemetry/opentelemetry.html

<a id="ref-10"></a>**[10]** Splunk Inc. (2026). *Splunk Observability Cloud Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/observability/en/

<a id="ref-11"></a>**[11]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-12"></a>**[12]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<a id="ref-13"></a>**[13]** United Kingdom Parliament. (2018). *Data Protection Act 2018 (UK GDPR, retained EU law)*. The Stationery Office. 2018 c. 12. https://www.legislation.gov.uk/ukpga/2018/12/contents

<details>
<summary>Additional online sources cited in the document body (26)</summary>

<a id="ref-14"></a>**[14]** splunkbase.splunk.com. *Splunkbase app #833*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/833

<a id="ref-15"></a>**[15]** splunkbase.splunk.com. *Splunkbase app #742*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/742

<a id="ref-16"></a>**[16]** splunkbase.splunk.com. *Splunkbase app #1352*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/1352

<a id="ref-17"></a>**[17]** splunkbase.splunk.com. *Splunkbase app #3457*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/3457

<a id="ref-18"></a>**[18]** splunkbase.splunk.com. *Splunkbase app #4022*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/4022

<a id="ref-19"></a>**[19]** splunkbase.splunk.com. *Splunkbase app #5580*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/5580

<a id="ref-20"></a>**[20]** splunkbase.splunk.com. *Splunkbase app #6656*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/6656

<a id="ref-21"></a>**[21]** splunkbase.splunk.com. *Splunkbase app #6657*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/6657

<a id="ref-22"></a>**[22]** splunkbase.splunk.com. *Splunkbase app #7538*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/7538

<a id="ref-23"></a>**[23]** splunkbase.splunk.com. *Splunkbase app #7539*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/7539

<a id="ref-24"></a>**[24]** splunkbase.splunk.com. *Splunkbase app #7777*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/7777

<a id="ref-25"></a>**[25]** splunkbase.splunk.com. *Splunkbase app #7719*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/7719

<a id="ref-26"></a>**[26]** aicpa.org. *AICPA: standard*. Retrieved May 11, 2026, from https://www.aicpa.org/

<a id="ref-27"></a>**[27]** iso.org. *ISO/IEC 27001*. Retrieved May 11, 2026, from https://www.iso.org/standard/27001

<a id="ref-28"></a>**[28]** hhs.gov. *U.S. HHS: Hipaa*. Retrieved May 11, 2026, from https://www.hhs.gov/hipaa/

<a id="ref-29"></a>**[29]** pcisecuritystandards.org. *PCI SSC: document*. Retrieved May 11, 2026, from https://www.pcisecuritystandards.org/

<a id="ref-30"></a>**[30]** gdpr.eu. *gdpr.eu*. Retrieved May 11, 2026, from https://gdpr.eu/

<a id="ref-31"></a>**[31]** nist.gov. *NIST Cybersecurity Framework*. Retrieved May 11, 2026, from https://www.nist.gov/cyberframework

<a id="ref-32"></a>**[32]** csrc.nist.gov. *NIST: Final*. Retrieved May 11, 2026, from https://csrc.nist.gov/pubs/sp/800/53/r5/final

<a id="ref-33"></a>**[33]** fedramp.gov. *fedramp.gov*. Retrieved May 11, 2026, from https://www.fedramp.gov/

<a id="ref-34"></a>**[34]** public.cyber.mil. *public.cyber.mil: Stigs*. Retrieved May 11, 2026, from https://public.cyber.mil/stigs/

<a id="ref-35"></a>**[35]** cisecurity.org. *cisecurity.org*. Retrieved May 11, 2026, from https://www.cisecurity.org/

<a id="ref-36"></a>**[36]** nerc.com. *nerc.com: Cipstandards.Aspx*. Retrieved May 11, 2026, from https://www.nerc.com/pa/Stand/Pages/CIPStandards.aspx

<a id="ref-37"></a>**[37]** tsa.gov. *tsa.gov*. Retrieved May 11, 2026, from https://www.tsa.gov/

<a id="ref-38"></a>**[38]** attack.mitre.org. *MITRE ATT&CK Knowledge Base*. Retrieved May 11, 2026, from https://attack.mitre.org/

<a id="ref-39"></a>**[39]** docs.thousandeyes.com. *Cisco ThousandEyes*. Retrieved May 11, 2026, from https://docs.thousandeyes.com/

</details>

<!-- END-AUTOGENERATED-SOURCES -->
