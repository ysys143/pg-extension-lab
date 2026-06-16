# Replica/bootstrap runbook: [extension]

## Cluster identity

- source system_identifier:
- source timeline:
- target system_identifier:
- target timeline:

## Extension artifacts

- In catalog:
- On disk:
- In sidecar/device cache:
- Rebuildable:

## Bootstrap steps

1. Install matching extension package.
2. Verify extension version and PostgreSQL major version.
3. Validate artifact ownership and cluster identity.
4. Rebuild non-portable artifacts.
5. Run smoke query and health check.

## Abort conditions

- system_identifier mismatch for non-rebuildable artifacts.
- extension version mismatch without an upgrade script.
- sidecar cache created against a different dataset hash.

