# Vault server config (dev infra). Real server mode, NOT `-dev`:
# after every start Vault is sealed -> `make vault-init` once, then `make vault-unseal`.
ui = true

storage "file" {
  path = "/vault/file"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true # local dev only, no TLS
}

api_addr      = "http://localhost:8200"
disable_mlock = true
