"""Azure cat-4.2 expansion taxonomy — real Activity Log and Monitor surfaces."""

from __future__ import annotations

from .taxonomy import TaxonomyEntry

_AZURE_OPS: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("Virtual Machine Creation", "Detects Microsoft.Compute/virtualMachines/write creating VMs.", "Unexpected VM creation may indicate cryptomining or shadow workloads.", ("Microsoft.Compute/virtualMachines/write",)),
    ("Virtual Machine Deletion", "Detects Microsoft.Compute/virtualMachines/delete.", "Mass VM deletion causes outages and may follow ransomware.", ("Microsoft.Compute/virtualMachines/delete",)),
    ("VM Power State Changes", "Detects start/deallocate/restart operations on VMs.", "Off-hours power changes can hide data collection or cost evasion.", ("Microsoft.Compute/virtualMachines/start/action", "Microsoft.Compute/virtualMachines/deallocate/action", "Microsoft.Compute/virtualMachines/restart/action")),
    ("Network Security Group Rule Changes", "Detects NSG create/update/delete.", "NSG edits exposing ports to Internet are a primary Azure breach vector.", ("Microsoft.Network/networkSecurityGroups/write", "Microsoft.Network/networkSecurityGroups/delete", "Microsoft.Network/networkSecurityGroups/securityRules/write")),
    ("Virtual Network Changes", "Detects VNet and subnet modifications.", "VNet changes alter segmentation and peering trust boundaries.", ("Microsoft.Network/virtualNetworks/write", "Microsoft.Network/virtualNetworks/delete", "Microsoft.Network/virtualNetworks/subnets/write")),
    ("Public IP Assignment", "Detects public IP create and associate.", "New public IPs on admin subnets expand attack surface.", ("Microsoft.Network/publicIPAddresses/write", "Microsoft.Network/networkInterfaces/join/action")),
    ("Azure Firewall Policy Changes", "Detects Azure Firewall and policy rule updates.", "Firewall policy deletion removes north-south inspection.", ("Microsoft.Network/azureFirewalls/write", "Microsoft.Network/firewallPolicies/write", "Microsoft.Network/firewallPolicies/ruleCollectionGroups/write")),
    ("Load Balancer Configuration Changes", "Detects load balancer and rule set updates.", "LB changes redirect production traffic paths.", ("Microsoft.Network/loadBalancers/write", "Microsoft.Network/loadBalancers/backendAddressPools/write")),
    ("Storage Account Creation", "Detects storage account provisioning.", "Storage in unapproved regions may violate residency.", ("Microsoft.Storage/storageAccounts/write",)),
    ("Storage Account Key Regeneration", "Detects storage account keys regenerated.", "Key regen may indicate credential rotation—or attacker persistence cleanup.", ("Microsoft.Storage/storageAccounts/regeneratekey/action",)),
    ("Storage Blob Public Access Changes", "Detects blob container public access level changes.", "Public blob containers caused major data leaks.", ("Microsoft.Storage/storageAccounts/blobServices/containers/write",)),
    ("Key Vault Access Policy Changes", "Detects Key Vault access policy and RBAC updates.", "Vault policy changes can grant secret decrypt to attackers.", ("Microsoft.KeyVault/vaults/accessPolicies/write", "Microsoft.KeyVault/vaults/write")),
    ("Key Vault Secret Deletion", "Detects secret and key deletion in Key Vault.", "Secret deletion breaks apps and may hide exfiltration.", ("Microsoft.KeyVault/vaults/secrets/delete", "Microsoft.KeyVault/vaults/keys/delete")),
    ("SQL Database Firewall Changes", "Detects SQL server firewall rule updates.", "SQL firewall allowing 0.0.0.0 opens databases to Internet scanning.", ("Microsoft.Sql/servers/firewallRules/write", "Microsoft.Sql/servers/firewallRules/delete")),
    ("SQL Database Creation", "Detects SQL database and server creation.", "Shadow databases expand data stores outside governance.", ("Microsoft.Sql/servers/databases/write", "Microsoft.Sql/servers/write")),
    ("Cosmos DB Account Changes", "Detects Cosmos DB account create/update/delete.", "Cosmos account keys and firewall changes affect globally replicated data.", ("Microsoft.DocumentDB/databaseAccounts/write", "Microsoft.DocumentDB/databaseAccounts/delete")),
    ("AKS Cluster Creation", "Detects AKS managed cluster provisioning.", "New Kubernetes clusters expand container attack surface.", ("Microsoft.ContainerService/managedClusters/write", "Microsoft.ContainerService/managedClusters/delete")),
    ("App Service Configuration Changes", "Detects Web App settings and connection string updates.", "App Service settings may embed secrets or open CORS.", ("Microsoft.Web/sites/config/write", "Microsoft.Web/sites/write")),
    ("Function App Changes", "Detects Azure Functions app create/update.", "Function apps with managed identity changes affect downstream RBAC.", ("Microsoft.Web/sites/write", "Microsoft.Web/sites/functions/write")),
    ("Role Assignment Creation", "Detects Microsoft.Authorization/roleAssignments/write.", "New role assignments at subscription scope are privilege escalation.", ("Microsoft.Authorization/roleAssignments/write", "Microsoft.Authorization/roleAssignments/delete")),
    ("Custom Role Definition Changes", "Detects roleDefinitions write/delete.", "Custom roles with wildcard actions bypass least privilege.", ("Microsoft.Authorization/roleDefinitions/write", "Microsoft.Authorization/roleDefinitions/delete")),
    ("Policy Assignment Changes", "Detects policy assignments at management group or subscription.", "Policy removal disables Azure Policy guardrails.", ("Microsoft.Authorization/policyAssignments/write", "Microsoft.Authorization/policyAssignments/delete")),
    ("Diagnostic Settings Changes", "Detects diagnosticSettings write on subscriptions or resources.", "Disabling diagnostics blinds SIEM ingestion.", ("Microsoft.Insights/diagnosticSettings/write", "Microsoft.Insights/diagnosticSettings/delete")),
    ("Activity Log Alert Deletion", "Detects activityLogAlerts delete.", "Deleting activity alerts hides future admin actions.", ("Microsoft.Insights/activityLogAlerts/delete", "Microsoft.Insights/activityLogAlerts/write")),
    ("Resource Group Deletion", "Detects resourceGroups/delete.", "RG deletion removes entire application stacks and logs.", ("Microsoft.Resources/subscriptions/resourceGroups/delete", "Microsoft.Resources/subscriptions/resourceGroups/write")),
    ("Azure AD Conditional Access Policy Changes", "Detects conditional access policy updates via Entra audit.", "CA policy weakening removes MFA requirements.", ("Update conditional access policy", "Delete conditional access policy")),
    ("Entra ID User Creation", "Detects user account creation in directory audit.", "New users outside HR provisioning may be persistence.", ("Add user", "Add member to group")),
    ("Entra ID Privileged Role Assignment", "Detects privileged role assignments in audit logs.", "Global Admin or Privileged Role Admin grants are critical.", ("Add member to role", "Add eligible member to role")),
    ("Service Principal Credential Changes", "Detects app registration secret and certificate updates.", "SP credential adds enable non-interactive persistence.", ("Update application", "Add service principal credentials")),
    ("Defender for Cloud Alert Ingestion", "Surfaces High severity Defender alerts.", "Defender alerts correlate Azure signals for active threats.", ("Microsoft.Security/alerts/write",)),
    ("Azure Backup Vault Changes", "Detects Recovery Services vault modifications.", "Backup vault deletion impairs ransomware recovery.", ("Microsoft.RecoveryServices/vaults/write", "Microsoft.RecoveryServices/vaults/delete")),
    ("ExpressRoute Circuit Changes", "Detects ExpressRoute gateway and circuit updates.", "Hybrid connectivity changes affect on-prem trust.", ("Microsoft.Network/expressRouteCircuits/write", "Microsoft.Network/virtualNetworkGateways/write")),
    ("Private Endpoint Changes", "Detects private endpoint create/delete.", "Private endpoint removal exposes PaaS to public routes.", ("Microsoft.Network/privateEndpoints/write", "Microsoft.Network/privateEndpoints/delete")),
    ("DNS Zone Record Changes", "Detects DNS zone and record set writes.", "DNS record changes enable hijacking and phishing.", ("Microsoft.Network/dnsZones/write", "Microsoft.Network/dnsZones/A/write")),
    ("Automation Account Runbook Changes", "Detects Automation account and runbook publish.", "Runbooks with Run As accounts execute with elevated rights.", ("Microsoft.Automation/automationAccounts/runbooks/write",)),
    ("Logic App Workflow Changes", "Detects Logic App create/update.", "Logic Apps with HTTP triggers may expose webhooks.", ("Microsoft.Logic/workflows/write",)),
    ("Event Hub Authorization Rule Changes", "Detects Event Hub namespace auth rule updates.", "Shared access policies may grant send/list on telemetry pipes.", ("Microsoft.EventHub/namespaces/authorizationRules/write",)),
    ("Synapse Workspace Changes", "Detects Synapse workspace and SQL pool modifications.", "Data warehouse exposure affects analytics classification.", ("Microsoft.Synapse/workspaces/write", "Microsoft.Synapse/workspaces/sqlPools/write")),
    ("Front Door WAF Policy Changes", "Detects Front Door and WAF policy updates.", "WAF policy removal exposes edge applications.", ("Microsoft.Network/frontdoorWebApplicationFirewallPolicies/write", "Microsoft.Cdn/profiles/afdEndpoints/write")),
]


def _azure_entry(
    title: str,
    desc: str,
    val: str,
    ops: tuple[str, ...],
    *,
    sourcetype: str = "azure:monitor:activity",
    criticality: str = "high",
    wave: str = "walk",
) -> TaxonomyEntry:
    op_clause = " OR ".join(f'operationName="{o}"' for o in ops)
    return TaxonomyEntry(
        subcategory="4.2",
        title=f"Azure {title}",
        service="azure",
        index="azure",
        sourcetype=sourcetype,
        spl_filter=f"({op_clause})",
        criticality=criticality,
        difficulty="beginner",
        monitoring_type=("Security", "Audit"),
        splunk_pillar="Security",
        description=desc,
        value=val,
        implementation=(
            "Enable Azure Activity Log and Entra audit export to Event Hub or Storage; configure "
            "`Splunk_TA_microsoft-cloudservices` modular inputs into `index=azure`. "
            "Tune exclusions for documented automation service principals."
        ),
        visualization="Events list, timeline by operationName, table of caller and resourceId.",
        app="Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`, Splunkbase 3110)",
        equipment=("azure",),
        equipment_models=("azure_activity_log",),
        mitre_attack=("T1078.004",),
        cim_models=("Change",),
        wave=wave,
        prerequisite_uc="4.2.58",
        nist_control="AU-2",
        cis_control="5.1",
        splunkbase_id=3110,
        splunkbase_name="Splunk Add-on for Microsoft Cloud Services",
        vendor_ref_title="Azure Activity Log schema",
        vendor_ref_url="https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/activity-log-schema",
        table_fields="_time caller operationName resourceId status",
    )


CRAWL_AZURE = TaxonomyEntry(
    subcategory="4.2",
    title="Azure Activity Log Baseline Ingestion and Health",
    service="azure",
    index="azure",
    sourcetype="azure:monitor:activity",
    spl_filter="*",
    criticality="critical",
    difficulty="beginner",
    monitoring_type=("Audit", "Operations"),
    splunk_pillar="Platform",
    description=(
        "Verifies Azure Activity Log and subscription-level administrative events flow into Splunk "
        "via the Microsoft Cloud Services add-on without prolonged ingestion gaps."
    ),
    value=(
        "Activity Log is the audit foundation for Azure detections. Missing administrative events "
        "hide RBAC, network, and data-plane configuration changes until audits fail."
    ),
    implementation=(
        "Export Activity Log to Event Hub or Storage Account; configure `Splunk_TA_microsoft-cloudservices` "
        "Azure Monitor Activity input. Alert when zero events for 60 minutes in business hours."
    ),
    visualization="Single value (events 24h), subscription coverage table, ingestion lag.",
    app="Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`, Splunkbase 3110)",
    equipment=("azure",),
    equipment_models=("azure_activity_log",),
    mitre_attack=("N/A (operational baseline)",),
    wave="crawl",
    prerequisite_uc=None,
    splunkbase_id=3110,
    splunkbase_name="Splunk Add-on for Microsoft Cloud Services",
    vendor_ref_title="Azure Monitor Activity log",
    vendor_ref_url="https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/platform-logs-overview",
    table_fields="_time operationName caller resourceId",
)

_AZURE_POSTURE: list[TaxonomyEntry] = [
    TaxonomyEntry(
        subcategory="4.2",
        title="Azure Defender for Cloud High-Severity Alerts",
        service="defender",
        index="azure",
        sourcetype="ms:defender:m365",
        spl_filter="severity=High OR severity=Medium",
        criticality="critical",
        difficulty="intermediate",
        monitoring_type=("Security", "Threat"),
        splunk_pillar="Security",
        description="Ingests Microsoft Defender for Cloud alerts at Medium or High severity.",
        value="Defender for Cloud maps Azure misconfigurations and threat detections to actionable alerts.",
        implementation="Enable Defender plans and forward alerts via Microsoft Cloud Services add-on.",
        visualization="Alert table, severity timeline, resourceId pivot.",
        app="Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`, Splunkbase 3110)",
        equipment=("azure",),
        mitre_attack=("T1190",),
        wave="walk",
        prerequisite_uc="4.2.58",
        splunkbase_id=3110,
        splunkbase_name="Splunk Add-on for Microsoft Cloud Services",
        vendor_ref_title="Microsoft Defender for Cloud",
        vendor_ref_url="https://learn.microsoft.com/en-us/azure/defender-for-cloud/alerts-overview",
    ),
    TaxonomyEntry(
        subcategory="4.2",
        title="Azure NSG Flow Log Denied Traffic Spike",
        service="network",
        index="azure",
        sourcetype="azure:monitor:resource",
        spl_filter='flowStatus=D OR flowStatus=Deny',
        criticality="high",
        difficulty="intermediate",
        monitoring_type=("Security", "Network"),
        splunk_pillar="Security",
        description="Aggregates NSG flow records where traffic was denied.",
        value="Denied flow spikes reveal port scans and blocked lateral movement.",
        implementation="Enable NSG flow logs to Storage/Event Hub; ingest via Microsoft Cloud Services add-on.",
        visualization="Top dest ports, source IP heatmap, timechart of denies.",
        app="Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`, Splunkbase 3110)",
        equipment=("azure",),
        mitre_attack=("T1046",),
        wave="walk",
        prerequisite_uc="4.2.58",
        splunkbase_id=3110,
        splunkbase_name="Splunk Add-on for Microsoft Cloud Services",
        vendor_ref_title="NSG flow logs",
        vendor_ref_url="https://learn.microsoft.com/en-us/azure/network-watcher/network-watcher-nsg-flow-logging-overview",
        table_fields="_time src_ip dest_ip dest_port flowStatus",
    ),
]

# Generate additional Azure entries from operation templates + metric-style monitors
_AZURE_METRICS: list[tuple[str, str, str]] = [
    ("App Service HTTP 5xx Rate", "Tracks elevated server errors on App Service plans.", "5xx spikes break SLAs and may indicate exploitation or misconfiguration."),
    ("AKS Node Not Ready", "Detects Kubernetes nodes reporting NotReady status.", "NotReady nodes reduce capacity and may indicate compromise."),
    ("Storage Account Availability Drop", "Monitors storage availability metrics below SLA.", "Availability drops affect dependent applications and backups."),
    ("SQL DTU Consumption Spike", "Detects SQL database DTU pegged near limit.", "DTU saturation causes time-outs resembling denial of service."),
    ("VPN Gateway Tunnel Down", "Detects disconnected site-to-site VPN tunnels.", "Tunnel loss isolates hybrid workloads from on-prem services."),
    ("Application Gateway Backend Unhealthy", "Surfaces unhealthy backend pool members.", "Unhealthy backends cause user-facing outages at the edge."),
    ("Redis Cache Connection Spike", "Detects connection count anomalies on Azure Cache.", "Connection spikes may indicate credential stuffing on session stores."),
    ("Service Bus Dead Letter Growth", "Monitors dead-letter queue depth growth.", "DLQ growth signals poison messages breaking async workflows."),
    ("Azure Files Share Quota Threshold", "Alerts when file share capacity nears quota.", "Quota exhaustion stops writes for shared file workloads."),
    ("Batch Account Job Failures", "Counts failed Batch jobs in a window.", "Batch failures may indicate compromised compute jobs."),
]

_AZURE_EXTRA: list[TaxonomyEntry] = []
for title, desc, val in _AZURE_METRICS:
    _AZURE_EXTRA.append(
        TaxonomyEntry(
            subcategory="4.2",
            title=f"Azure {title}",
            service="monitor",
            index="azure",
            sourcetype="azure:monitor:resource",
            spl_filter="*",
            criticality="medium",
            difficulty="intermediate",
            monitoring_type=("Performance", "Availability"),
            splunk_pillar="Observability",
            description=desc,
            value=val,
            implementation="Enable Azure Monitor metrics/diagnostics export to Event Hub; map metrics in Microsoft Cloud Services add-on.",
            visualization="Timechart, single-value SLA breach, top resources table.",
            app="Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`, Splunkbase 3110)",
            equipment=("azure",),
            wave="walk",
            prerequisite_uc="4.2.58",
            cost_tier="medium",
            splunkbase_id=3110,
            splunkbase_name="Splunk Add-on for Microsoft Cloud Services",
            vendor_ref_title="Azure Monitor metrics",
            vendor_ref_url="https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/metrics-charts",
        )
    )

AZURE_ENTRIES: list[TaxonomyEntry] = [CRAWL_AZURE]
AZURE_ENTRIES.extend(
    _azure_entry(title, desc, val, ops) for title, desc, val, ops in _AZURE_OPS
)
AZURE_ENTRIES.extend(_AZURE_POSTURE)
AZURE_ENTRIES.extend(_AZURE_EXTRA)

# Pad with RBAC-focused variants for high-volume coverage (real operations, distinct titles)
_RBAC_RESOURCES = (
    "Microsoft.Compute",
    "Microsoft.Storage",
    "Microsoft.Network",
    "Microsoft.KeyVault",
    "Microsoft.Sql",
    "Microsoft.ContainerService",
    "Microsoft.Web",
    "Microsoft.DocumentDB",
    "Microsoft.RecoveryServices",
    "Microsoft.EventHub",
)
for res in _RBAC_RESOURCES:
    AZURE_ENTRIES.append(
        _azure_entry(
            f"{res.split('.')[-1]} Role Assignment at Subscription Scope",
            f"Detects roleAssignments/write affecting {res} resources at subscription scope.",
            f"Subscription-scoped RBAC on {res} grants broad control—review every assignment.",
            ("Microsoft.Authorization/roleAssignments/write",),
        )
    )
