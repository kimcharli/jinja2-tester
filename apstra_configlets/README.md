# Configlets

<!-- markdownlint-disable-next-line MD013 -->
These configlets were originally located in <https://github.com/kimcharli/ck-apstra-api/tree/main/docs/configlets> and have been moved here for better coherency within this project.

<!-- markdownlint-disable-next-line MD013 -->
This project includes a collection of configlets to perform various network configurations. They are categorized as follows:

## Essential (Always)

These configlets are considered essential for basic operation.

- `core-isolation.j2`
- `no-rstp.j2`
- `system-base.j2`
- `re-protect.j2`
- `loop-detect.j2`

## Essential (In Certain Cases)

These configlets are essential under specific circumstances.

- `evpn-gw-bfd.j2`: Essential for EVPN GW deployments.

## Optional

These configlets provide optional functionality.

- `device-licenses.j2`
- `analyzer.j2`

## Miscellaneous

This category includes other configlets for various purposes.

- `sflow-snmpv3.j2`
- `all-irb-down.j2`
- `cos-common.j2`
- `cos-egress.j2`
- `cos-ingress.j2`
- `cut-end-systems.j2`
- `cut-right-spines.j2`
- `distributed-dr.j2`
- `evo-packet-forwarding-option.j2`
- `igmp-snooping.j2`
- `mac-move-limit.j2`
- `mgmt-leak-incomplete.j2`
- `mode-fec.j2`
- `no-arp-suppression.j2`
- `non-evo-sflow.j2`
- `ospf.j2`
- `port-mirroring.j2`
- `sn-to-resource-id.j2`
- `snmp-v2.j2`
- `snmp-v3.j2`
