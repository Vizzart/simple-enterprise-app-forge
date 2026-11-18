# Policy for the Keycloak group `developers` (configure.sh maps that group to this policy).
# Engine: `seaf/` (KV v2). In KV v2 the API paths differ from what you see in the UI:
#   seaf/data/<path>      - secret values (read / write / delete a version)
#   seaf/metadata/<path>  - list keys, read versions and metadata

# Read, create, overwrite (new version) and soft-delete secret versions.
path "seaf/data/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Browse keys and read version history. Without `list` the UI shows an empty engine.
path "seaf/metadata/*" {
  capabilities = ["read", "list"]
}

# Deliberately NOT granted (admin only):
#   seaf/destroy/*    permanently destroy versions
#   seaf/undelete/*   restore soft-deleted versions
#   delete on seaf/metadata/*   remove a key with its whole history
