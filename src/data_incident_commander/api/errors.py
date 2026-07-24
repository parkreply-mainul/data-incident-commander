"""Stable, public-safe API error translation."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from data_incident_commander.application.errors import (
    ConcurrentUpdateConflict,
    DependencyUnavailable,
    IncidentConflict,
    IncidentNotFound,
    InvalidWorkflowTransition,
    ProviderOutputMismatch,
)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unavailable")


def error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    response = JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "retryable": retryable,
                "request_id": request_id,
                "details": details or {},
            }
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _: RequestValidationError) -> JSONResponse:
        return error_response(
            request,
            status_code=422,
            code="VALIDATION_ERROR",
            message="The request is invalid.",
        )

    @app.exception_handler(IncidentNotFound)
    async def not_found(request: Request, _: IncidentNotFound) -> JSONResponse:
        return error_response(
            request,
            status_code=404,
            code="INCIDENT_NOT_FOUND",
            message="The requested incident does not exist.",
        )

    @app.exception_handler(InvalidWorkflowTransition)
    async def invalid_state(request: Request, error: InvalidWorkflowTransition) -> JSONResponse:
        return error_response(
            request,
            status_code=409,
            code="INVALID_STATE_TRANSITION",
            message=str(error),
        )

    @app.exception_handler(DependencyUnavailable)
    async def dependency_unavailable(
        request: Request, _: DependencyUnavailable
    ) -> JSONResponse:
        return error_response(
            request,
            status_code=503,
            code="DEPENDENCY_UNAVAILABLE",
            message="A required investigation dependency is unavailable.",
            retryable=True,
        )

    @app.exception_handler(ProviderOutputMismatch)
    async def provider_output_mismatch(
        request: Request, _: ProviderOutputMismatch
    ) -> JSONResponse:
        return error_response(
            request,
            status_code=502,
            code="PROVIDER_OUTPUT_MISMATCH",
            message="The investigation provider returned a report that does not match the request.",
            retryable=False,
        )

    @app.exception_handler(IncidentConflict)
    async def conflict(request: Request, error: IncidentConflict) -> JSONResponse:
        return error_response(
            request,
            status_code=409,
            code="CONFLICT",
            message=str(error),
        )

    @app.exception_handler(ConcurrentUpdateConflict)
    async def concurrent_conflict(
        request: Request, _: ConcurrentUpdateConflict
    ) -> JSONResponse:
        return error_response(
            request,
            status_code=409,
            code="INCIDENT_CONFLICT",
            message="The incident changed after it was read. Retrieve it and try again.",
            retryable=True,
        )

    @app.exception_handler(Exception)
    async def internal_error(request: Request, _: Exception) -> JSONResponse:
        return error_response(
            request,
            status_code=500,
            code="INTERNAL_ERROR",
            message="An unexpected internal error occurred.",
            retryable=False,
        )
