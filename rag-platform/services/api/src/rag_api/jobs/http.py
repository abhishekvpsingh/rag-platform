"""Authenticated, owner-scoped job APIs with no source payloads or exception text."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from rag_api.identity.http import COOKIE
from rag_api.identity.service import AccessDenied, IdentityService
from rag_api.jobs.service import JobConflict, JobService


class JobView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    kind: str
    state: str
    attempts: int
    max_attempts: int
    progress: int
    created_at: datetime
    updated_at: datetime
    error_code: str | None


class CheckInput(BaseModel):
    duration_seconds: Annotated[int, Field(ge=0, le=60)] = 0


def jobs_router(identity: IdentityService, origin: str) -> APIRouter:
    router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])
    service = JobService(identity.engine)

    def authenticate(request: Request, response: Response, mutation: bool = False) -> str:
        response.headers["Cache-Control"] = "no-store"
        token = request.cookies.get(COOKIE, "")
        if len(token) > 128:
            raise HTTPException(401, "Authentication required")
        csrf: str | None = None
        if mutation:
            csrf = request.headers.get("x-csrf-token", "")
            if request.headers.get("origin") != origin or not csrf or len(csrf) > 128:
                raise HTTPException(403, "Request denied")
        try:
            identity.authenticate(token, csrf)
        except AccessDenied:
            raise HTTPException(401, "Authentication required") from None
        return token

    @router.get("")
    def listing(request: Request, response: Response) -> list[JobView]:
        token = authenticate(request, response)
        return [JobView.model_validate(job) for job in service.list_jobs(token)]

    @router.post("/checks", status_code=202)
    def submit(body: CheckInput, request: Request, response: Response) -> JobView:
        token = authenticate(request, response, True)
        key = request.headers.get("idempotency-key", "")
        if not 1 <= len(key) <= 128:
            raise HTTPException(422, "Idempotency-Key is required (1–128 characters)")
        try:
            job = service.submit_check(token, key, body.duration_seconds)
        except AccessDenied:
            raise HTTPException(403, "Request denied") from None
        except JobConflict:
            raise HTTPException(409, "Job request conflicts or active-job limit reached") from None
        return JobView.model_validate(job)

    @router.post("/{job_id}/cancel", status_code=204)
    def cancel(job_id: str, request: Request, response: Response) -> None:
        token = authenticate(request, response, True)
        try:
            service.cancel(token, job_id)
        except AccessDenied:
            raise HTTPException(404, "Job unavailable") from None

    @router.post("/{job_id}/replay", status_code=204)
    def replay(job_id: str, request: Request, response: Response) -> None:
        token = authenticate(request, response, True)
        try:
            service.replay(token, job_id)
        except AccessDenied:
            raise HTTPException(404, "Job unavailable") from None
        except JobConflict:
            raise HTTPException(409, "Job cannot be replayed") from None

    return router
