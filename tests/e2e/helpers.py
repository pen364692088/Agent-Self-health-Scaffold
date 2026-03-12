# helpers.py - Utility functions for E2E tests

def assert_status(response, expected=200):
    """Simple assertion helper for HTTP-like responses.
    Args:
        response: object with a 'status' attribute or key.
        expected (int): expected status code.
    """
    status = getattr(response, "status", response.get("status", None))
    assert status == expected, f"Expected status {expected}, got {status}"

def build_url(base_url, *parts):
    """Join base URL with path components ensuring proper slashes."""
    return "/".join([base_url.rstrip("/"), *[p.strip("/") for p in parts]])
