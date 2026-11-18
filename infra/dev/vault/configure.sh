#!/usr/bin/env bash
# Configure Vault for login through Keycloak (realm `infra`). Safe to run again. Run: make vault-config
#
#   1. policies      every policies/*.hcl is written as a policy named like the file
#   2. auth method   `oidc`, connected to Keycloak (client `vault`)
#   3. role          one OIDC role `keycloak` (roles/keycloak.json); who may log in = members of the
#                    groups listed in GROUP_POLICIES below (the script adds them as bound_claims)
#   4. groups        per Keycloak group one Vault *external* group with its policy and an alias
#                    (alias name = group name as it appears in the token claim `groups`)
#
# Needs: `vault` CLI on the host, Vault unsealed, Keycloak up with realm `infra` imported.
# Env:   VAULT_ADDR (default http://localhost:8200)
#        VAULT_TOKEN (default: root token from .envs/.vault-init.json)

# Keycloak group -> Vault policy. To add a group: create it in Keycloak (infra-realm.json),
# add a pair here, add policies/<policy>.hcl if the policy is new, run `make vault-config`.
GROUP_POLICIES=${GROUP_POLICIES:-"devops:seaf-admin developers:seaf-developer"}

set -euo pipefail
cd "$(dirname "$0")"
ROOT=../../..
export VAULT_ADDR=${VAULT_ADDR:-http://localhost:8200}
if [ -z "${VAULT_TOKEN:-}" ]; then
  VAULT_TOKEN=$(python3 -c "import json;print(json.load(open('$ROOT/.envs/.vault-init.json'))['root_token'])")
  export VAULT_TOKEN
fi
SECRET=$(grep '^VAULT_OIDC_CLIENT_SECRET=' "$ROOT/.envs/.keycloak" | cut -d= -f2)
[ -n "$SECRET" ] || { echo "VAULT_OIDC_CLIENT_SECRET is missing in .envs/.keycloak" >&2; exit 1; }

echo "1/4 policies"
for file in policies/*.hcl; do
  vault policy write "$(basename "$file" .hcl)" "$file"
done

echo "2/4 auth method oidc"
AUTH_LIST=$(vault auth list -format=json)
case "$AUTH_LIST" in
  *'"oidc/"'*) echo "already enabled" ;;
  *) vault auth enable oidc ;;
esac
vault write auth/oidc/config oidc_discovery_url=http://localhost:8080/realms/infra \
  oidc_client_id=vault oidc_client_secret="$SECRET" default_role=keycloak

echo "3/4 role keycloak"
python3 - "$GROUP_POLICIES" <<'PY' | vault write auth/oidc/role/keycloak -
import json, sys
role = json.load(open("roles/keycloak.json"))
role["bound_claims"] = {"groups": [pair.split(":")[0] for pair in sys.argv[1].split()]}
print(json.dumps(role))
PY

echo "4/4 groups and aliases"
ACCESSOR=$(vault auth list -format=json | python3 -c 'import json,sys;print(json.load(sys.stdin)["oidc/"]["accessor"])')
for pair in $GROUP_POLICIES; do
  group=${pair%%:*}
  policy=${pair##*:}
  vault write identity/group name="$group" type=external policies="$policy" >/dev/null
  id=$(vault read -field=id identity/group/name/"$group")
  [ -n "$id" ] || { echo "no id for group $group" >&2; exit 1; }
  alias_name=$(vault read -format=json identity/group/name/"$group" |
    python3 -c 'import json,sys;print(json.load(sys.stdin)["data"].get("alias",{}).get("name",""))')
  if [ -z "$alias_name" ]; then
    vault write identity/group-alias name="$group" mount_accessor="$ACCESSOR" canonical_id="$id" >/dev/null
  fi
  echo "  $group -> $policy"
done
echo "Vault configured. Log in: $VAULT_ADDR/ui (method OIDC)."
