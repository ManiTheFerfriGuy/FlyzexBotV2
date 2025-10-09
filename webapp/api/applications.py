"""Application management endpoints."""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Query, status

from flyzexbot.services.storage import Application, ApplicationHistoryEntry

from ..dependencies import StorageDependency, require_admin_api_key
from ..models import (
    ApplicationDetailResponse,
    ApplicationHistoryModel,
    ApplicationInsightsResponse,
    ApplicationModel,
    ApplicationResponseModel,
    DashboardMetricsResponse,
    PendingApplicationsResponse,
)

router = APIRouter(prefix="/api/applications", tags=["applications"])

SortParam = Query(
    "recent",
    pattern="^(recent|oldest|name)$",
    description="Ordering strategy: recent (default), oldest or name.",
)
LimitParam = Query(
    default=None,
    ge=1,
    le=200,
    description="Maximum number of records to return after filtering.",
)
OffsetParam = Query(0, ge=0, description="Number of filtered items to skip before returning results.")
SearchParam = Query(
    default=None,
    min_length=2,
    max_length=64,
    description="Substring matched against applicant metadata and answers.",
)
LanguageParam = Query(
    default=None,
    alias="language",
    description="One or more language codes to filter by (case-insensitive).",
)


def _to_application_model(application: Application) -> ApplicationModel:
    return ApplicationModel(
        user_id=application.user_id,
        full_name=application.full_name,
        username=application.username,
        answer=application.answer,
        created_at=application.created_at,
        language_code=application.language_code,
        responses=[
            ApplicationResponseModel(
                question_id=response.question_id,
                question=response.question,
                answer=response.answer,
            )
            for response in getattr(application, "responses", [])
        ],
    )


def _to_history_model(entry: ApplicationHistoryEntry | None) -> ApplicationHistoryModel | None:
    if not entry:
        return None
    return ApplicationHistoryModel(
        status=entry.status,
        updated_at=entry.updated_at,
        note=getattr(entry, "note", None),
        language_code=getattr(entry, "language_code", None),
    )


def _normalize_languages(values: Iterable[str] | None) -> set[str]:
    if not values:
        return set()
    return {value.strip().lower() for value in values if value and value.strip()}


def _matches_query(application: Application, query: str) -> bool:
    lowered = query.lower()
    haystacks = [
        application.full_name,
        application.username,
        application.answer,
        application.language_code,
    ]
    for response in getattr(application, "responses", []) or []:
        haystacks.extend([response.question, response.answer])
    for haystack in haystacks:
        if haystack and lowered in haystack.lower():
            return True
    return False


def _sort_applications(applications: list[Application], strategy: str) -> list[Application]:
    if strategy == "name":
        return sorted(
            applications,
            key=lambda app: (app.full_name or app.username or "").lower(),
        )
    reverse = strategy != "oldest"
    return sorted(applications, key=lambda app: app.created_at or "", reverse=reverse)


def _build_pending_language_histogram(applications: Iterable[Application]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for application in applications:
        language = (application.language_code or "unknown").lower()
        counter[language] += 1
    return dict(counter)


@router.get(
    "/pending",
    response_model=PendingApplicationsResponse,
    dependencies=[Depends(require_admin_api_key)],
)
async def pending_applications(
    storage: StorageDependency,
    *,
    sort: str = SortParam,
    limit: int | None = LimitParam,
    offset: int = OffsetParam,
    search: str | None = SearchParam,
    language: list[str] | None = LanguageParam,
) -> PendingApplicationsResponse:
    pending_items = list(storage.get_pending_applications())
    languages = _normalize_languages(language)
    if languages:
        pending_items = [
            application
            for application in pending_items
            if (application.language_code or "unknown").lower() in languages
        ]

    if search:
        pending_items = [
            application
            for application in pending_items
            if _matches_query(application, search)
        ]

    ordered_items = _sort_applications(pending_items, sort)

    total_filtered = len(ordered_items)
    if offset:
        ordered_items = ordered_items[offset:]
    if limit is not None:
        ordered_items = ordered_items[:limit]

    return PendingApplicationsResponse(
        total=total_filtered,
        applications=[_to_application_model(app) for app in ordered_items],
    )


@router.get(
    "/insights",
    response_model=ApplicationInsightsResponse,
    dependencies=[Depends(require_admin_api_key)],
)
async def application_insights(storage: StorageDependency) -> ApplicationInsightsResponse:
    stats_getter = getattr(storage, "get_application_statistics", None)
    if callable(stats_getter):
        payload = stats_getter()
        return ApplicationInsightsResponse(**payload)
    return ApplicationInsightsResponse(
        pending=0,
        status_counts={},
        languages={},
        total=0,
        average_pending_answer_length=0.0,
        recent_updates=[],
    )


@router.get(
    "/dashboard",
    response_model=DashboardMetricsResponse,
    dependencies=[Depends(require_admin_api_key)],
)
async def application_dashboard(storage: StorageDependency) -> DashboardMetricsResponse:
    stats = storage.get_application_statistics()
    status_counts = {str(k): int(v) for k, v in stats.get("status_counts", {}).items()}
    approved = status_counts.get("approved", 0)
    denied = status_counts.get("denied", 0)
    withdrawn = status_counts.get("withdrawn", 0)
    completed = approved + denied + withdrawn
    approval_rate = (approved / completed) if completed else 0.0

    pending_applications = list(storage.get_pending_applications())
    pending_by_language = _build_pending_language_histogram(pending_applications)

    return DashboardMetricsResponse(
        total=int(stats.get("total", 0)),
        pending=int(stats.get("pending", 0)),
        approved=approved,
        denied=denied,
        withdrawn=withdrawn,
        status_counts=status_counts,
        approval_rate=approval_rate,
        languages={str(k): int(v) for k, v in stats.get("languages", {}).items()},
        pending_by_language=pending_by_language,
        average_pending_answer_length=float(stats.get("average_pending_answer_length", 0.0)),
        recent_updates=list(stats.get("recent_updates", [])),
    )


@router.get(
    "/{user_id}",
    response_model=ApplicationDetailResponse,
    dependencies=[Depends(require_admin_api_key)],
)
async def get_application_detail(
    user_id: int,
    storage: StorageDependency,
) -> ApplicationDetailResponse:
    application = storage.get_application(user_id)
    history = storage.get_application_status(user_id)
    if not application and not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="درخواست متقاضی یافت نشد.",
        )
    return ApplicationDetailResponse(
        application=_to_application_model(application) if application else None,
        history=_to_history_model(history),
    )
