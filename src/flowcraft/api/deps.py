"""API dependencies — authentication and shared utilities."""

import os
from typing import Optional
from fastapi import Header, HTTPException, status
from dotenv import load_dotenv

load_dotenv()

EXPECTED_API_KEY = os.getenv("API_KEY", "flowcraft-dev-key-change-in-production")


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> str:
    """Validate X-API-Key header against configured API key.

    Returns the verified key if valid, raises 401 otherwise.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header. Set API_KEY in .env and include it in requests.",
        )
    if x_api_key != EXPECTED_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )
    return x_api_key
