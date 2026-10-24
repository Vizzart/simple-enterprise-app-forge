"""Weryfikacja access tokenów wydanych przez Keycloak (podpis RS256 z JWKS, iss, aud, exp)."""

import jwt
from flask import current_app

_jwks_clients: dict[str, jwt.PyJWKClient] = {}


class InvalidToken(Exception):
    """Token nieprawidłowy: zły podpis, wygasł, inny wystawca lub odbiorca."""


class KeycloakUnavailable(Exception):
    """Nie da się pobrać kluczy publicznych Keycloak (JWKS)."""


def _jwks_client(url: str) -> jwt.PyJWKClient:
    # klucze są cache'owane w kliencie; pobierane ponownie po zmianie `kid` (rotacja kluczy)
    client = _jwks_clients.get(url)
    if client is None:
        client = _jwks_clients[url] = jwt.PyJWKClient(url, cache_keys=True, lifespan=300)
    return client


def verify_token(token: str) -> dict:
    """Zwraca claims tokenu albo rzuca InvalidToken / KeycloakUnavailable."""
    config = current_app.config
    try:
        signing_key = _jwks_client(config["KEYCLOAK_JWKS_URL"]).get_signing_key_from_jwt(token)
    except jwt.PyJWKClientConnectionError as error:
        raise KeycloakUnavailable(str(error)) from error
    except (jwt.PyJWKClientError, jwt.InvalidTokenError) as error:
        raise InvalidToken(str(error)) from error

    try:
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=config["KEYCLOAK_ISSUER"],
            audience=config["KEYCLOAK_AUDIENCE"],
            leeway=30,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.InvalidTokenError as error:
        raise InvalidToken(str(error)) from error
