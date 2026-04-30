# Customer-provided lookup tables

The **splunk-uc-nis2** app references CSV lookups from `default/savedsearches.conf` via `inputlookup`. Those files are **not** shipped with the app. Operators must create them (under this `lookups/` directory, or wherever your `transforms.conf` definitions point) and populate them with org-specific data **before** enabling the corresponding saved searches.

## Required CSV files

Place the following files where Splunk can resolve them as lookup tables (typically `lookups/` in this app, with matching definitions in `default/transforms.conf` if needed):

- `business_units.csv`
- `emergency_comm_channels.csv`
- `incident_register.csv`
- `ir_playbooks.csv`
- `nis2_annual_assessment_register.csv`
- `nis2_asset_hygiene_expectations.csv`
- `nis2_bcp_test_register.csv`
- `nis2_board_report_schedule.csv`
- `nis2_control_matrix.csv`
- `nis2_cooperation_group_register.csv`
- `nis2_cross_border_incident_register.csv`
- `nis2_entity_classification.csv`
- `nis2_evidence_report_catalog.csv`
- `nis2_governance_evidence.csv`
- `nis2_management_roster.csv`
- `nis2_privileged_role_roster.csv`
- `nis2_scada_maintenance_windows.csv`
- `nis2_segment_coverage_expectations.csv`
- `nis2_supplier_assessment_register.csv`
- `nis2_training_completion.csv`
- `terminated_employees.csv`
- `vendor_sbom.csv`
- `vrm_attestations.csv`

Column schemas must match what each saved search expects (filters, joins, and field names in the SPL). Use the individual searches in `default/savedsearches.conf` as the source of truth for required fields.
