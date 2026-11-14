"""Cookie session API. TLS is required; local HTTP is not an auth exception."""

import threading
import time
from collections import deque
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field, SecretStr

from rag_api.identity.service import AccessDenied, IdentityService

COOKIE = "__Host-rag_session"


class LoginInput(BaseModel):
    email: Annotated[str, Field(min_length=3, max_length=254)]
    password: Annotated[SecretStr, Field(min_length=12, max_length=256)]


class LoginLimiter:
    """Bounded process-wide budget, cannot be bypassed by rotating client addresses."""

    def __init__(self) -> None:
        self.attempts: deque[float] = deque()
        self.lock = threading.Lock()

    def check(self) -> None:
        with self.lock:
            current = time.monotonic()
            while self.attempts and self.attempts[0] <= current - 60:
                self.attempts.popleft()
            if len(self.attempts) >= 10:
                raise HTTPException(429, "Try again later", headers={"Retry-After": "60"})
            self.attempts.append(current)


def auth_router(service: IdentityService, origin: str) -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth", tags=["identity"])
    limiter = LoginLimiter()

    def require_origin(request: Request) -> None:
        if request.headers.get("origin") != origin:
            raise HTTPException(403, "Request denied")

    def token(request: Request) -> str:
        value = request.cookies.get(COOKIE, "")
        if not value or len(value) > 128:
            raise HTTPException(401, "Authentication required")
        return value

    @router.post("/login")
    def login(body: LoginInput, request: Request, response: Response) -> dict[str, str]:
        require_origin(request)
        limiter.check()
        try:
            tokens = service.login(body.email, body.password.get_secret_value())
        except AccessDenied:
            raise HTTPException(401, "Authentication failed") from None
        response.set_cookie(
            COOKIE,
            tokens.token,
            secure=True,
            httponly=True,
            samesite="strict",
            path="/",
            max_age=service.lifetime,
        )
        response.headers["Cache-Control"] = "no-store"
        return {"csrf_token": tokens.csrf}

    @router.get("/me")
    def me(request: Request, response: Response) -> dict[str, str]:
        try:
            principal = service.authenticate(token(request))
        except AccessDenied:
            raise HTTPException(401, "Authentication required") from None
        response.headers["Cache-Control"] = "no-store"
        return {
            "user_id": principal.user_id,
            "tenant_id": principal.tenant_id,
            "role": principal.role,
        }

    @router.post("/logout", status_code=204)
    def logout(request: Request, response: Response) -> None:
        require_origin(request)
        csrf = request.headers.get("x-csrf-token", "")
        if not csrf or len(csrf) > 128:
            raise HTTPException(403, "Request denied")
        try:
            service.logout(token(request), csrf)
        except AccessDenied:
            raise HTTPException(403, "Request denied") from None
        response.delete_cookie(COOKIE, secure=True, httponly=True, samesite="strict", path="/")
        response.headers["Cache-Control"] = "no-store"

    return router
