# Full access for the Keycloak group `devops` (configure.sh maps that group to this policy).
path "*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# For every request Vault uses the MOST SPECIFIC path rule found in ALL policies of the token.
# `seaf-developer` has narrower rules for the two paths below. Without the copies here, a person who
# is in both Keycloak groups would only get read/list on seaf/metadata/* instead of full access.
# When you add a more specific path to another policy, repeat that path here with full capabilities.
path "seaf/data/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

path "seaf/metadata/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
