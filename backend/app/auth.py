"""
Auth dependency stub — Module 1 (User Management) owns real
authentication (JWT / Supabase Auth per the project spec), which isn't
built yet.

Until Module 1 exists, get_current_user_id() just trusts a plain
X-User-Id header (or falls back to trusting the request body, which is
what the current routes do). This keeps Module 3 & 4 runnable and
testable standalone.

INTEGRATION POINT: once Module 1 issues real JWTs (or you're using
Supabase Auth), replace the body of get_current_user_id() with actual
token verification, e.g.:

    from jose import jwt, JWTError

    SECRET_KEY = os.getenv("JWT_SECRET")
    ALGORITHM = "HS256"

    def get_current_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> int:
        try:
            payload = jwt.decode(
                credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
            )
            return int(payload["sub"])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

Then swap `user_id: int` body/path fields for `user_id: int =
Depends(get_current_user_id)` in the route signatures in
routes/personalization.py and routes/learning_plan.py, and drop
user_id from the request schemas since it'll come from the token
instead of being caller-supplied (which is also a security fix — right
now nothing stops one user from generating a plan for another user_id).
"""

import os
from fastapi import Header, HTTPException


def get_current_user_id(x_user_id: int = Header(...)) -> int:
    """
    TEMPORARY dev-mode auth: trusts an X-User-Id header as-is.
    NOT SECURE — replace with real JWT verification before any real
    deployment. This exists only so routes can be wired against a
    consistent "current user" dependency now and swapped later without
    changing route logic.
    """
    if os.getenv("ENV", "development") != "development":
        raise HTTPException(
            status_code=501,
            detail="Real authentication (JWT/Supabase) is not yet "
            "configured. This stub only works in development.",
        )
    return x_user_id
