"""
helpers.py

This module provides helper functions for interacting with external services and databases.

1. `get_public_ip`: Fetches the public IP address of the machine using the ipify API.

Dependencies:
    - requests: Used for making HTTP requests to external APIs.

Usage:
    - Use `get_public_ip` to retrieve the machine's public IP address.
"""

import json
import socket
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from pulumi import log
import requests


def get_public_ip():
    """
    Retrieves the public IP address of the machine using the ipify API.

    This function makes a request to the ipify API (https://api.ipify.org) to fetch the public
    IP address of the machine. If the request is successful, it returns the IP address as a string.
    In case of an error (such as a timeout or failed request), it logs the error and returns None.

    Returns:
        str: The public IP address of the machine, or None if an error occurred.
    """
    try:
        # Use ipify API to get the public IP address
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return data["ip"]
    except requests.exceptions.Timeout as e:
        print(f"Error timeout fetching public IP: {e}")
        return None
    except requests.RequestException as e:
        print(f"Error retrieving public IP: {e}")
        return None


def load_vector_index_spec(path: Path) -> Mapping[str, Any]:
    """Load the vector index spec shared with the application to keep definitions in sync."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        msg = (
            "Vector index spec not found at "
            f"{path}. Ensure application assets exist before running Pulumi."
        )
        raise RuntimeError(msg) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Vector index spec at {path} is not valid JSON.") from exc


def extract_standard_srv(conn: Any) -> str:
    """Tolerantly extract the standard SRV string from the provider output."""
    if isinstance(conn, dict):
        value = conn.get("standard_srv") or conn.get("standardSrv") or conn.get("STANDARD_SRV")
        if value:
            return value
    if isinstance(conn, list) and conn:
        entry = conn[0]
        if isinstance(entry, dict):
            value = (
                entry.get("standard_srv")
                or entry.get("standardSrv")
                or entry.get("STANDARD_SRV")
            )
            if value:
                return value
    raise ValueError("Unable to extract standard SRV connection string from cluster output.")


def resolve_ip_from_url(url: str) -> str | None:
    """Resolve a hostname in a URL to an IPv4 address."""
    try:
        host = urlparse(url).hostname
        if not host:
            return None
        return socket.gethostbyname(host)
    except (socket.gaierror, OSError) as exc:
        log.warn(f"Unable to resolve IP for {url}: {exc}")
        return None


__all__ = [
    "extract_standard_srv",
    "get_public_ip",
    "load_vector_index_spec",
    "resolve_ip_from_url",
]
