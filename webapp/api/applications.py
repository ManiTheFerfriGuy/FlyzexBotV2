"""Application management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from flyzexbot.services.storage import Application

from ..dependencies import StorageDependency, require_admin_api_key
from ..models import (
    ApplicationInsightsResponse,
    ApplicationModel,
    ApplicationResponseModel,
    PendingApplicationsResponse,
)

router = APIRouter(prefix="/api/applications", tags=["applications"])


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


@router.get("/pending", response_model=PendingApplicationsResponse, dependencies=[Depends(require_admin_api_key)])
async def pending_applications(storage: StorageDependency) -> PendingApplicationsResponse:
    applications = [_to_application_model(app) for app in storage.get_pending_applications()]
    return PendingApplicationsResponse(total=len(applications), applications=applications)


@router.get("/insights", response_model=ApplicationInsightsResponse, dependencies=[Depends(require_admin_api_key)])
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
