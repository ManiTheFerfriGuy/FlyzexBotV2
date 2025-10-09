"""Pydantic models describing the WebApp API schema."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ApplicationResponseModel(BaseModel):
    question_id: str = Field(..., description="Identifier of the application question.")
    question: str = Field(..., description="Localized question text.")
    answer: str = Field(..., description="Applicant response text.")


class ApplicationModel(BaseModel):
    user_id: int = Field(..., description="Telegram user identifier.")
    full_name: Optional[str] = Field(None, description="Full display name of the applicant.")
    username: Optional[str] = Field(None, description="Public username without the @ prefix.")
    answer: Optional[str] = Field(None, description="Legacy short answer field.")
    created_at: str = Field(..., description="Formatted creation timestamp.")
    language_code: Optional[str] = Field(None, description="Telegram language code.")
    responses: List[ApplicationResponseModel] = Field(default_factory=list)


class PendingApplicationsResponse(BaseModel):
    total: int = Field(..., description="Total number of pending applications.")
    applications: List[ApplicationModel] = Field(default_factory=list)


class AdminModel(BaseModel):
    user_id: int = Field(..., description="Telegram user identifier.")
    username: Optional[str] = Field(None, description="Public username without the @ prefix.")
    full_name: Optional[str] = Field(None, description="Display name of the admin.")


class AdminListResponse(BaseModel):
    total: int = Field(..., description="Total admins in the database.")
    admins: List[AdminModel] = Field(default_factory=list)


class AdminDetailResponse(BaseModel):
    admin: AdminModel


class AdminMutationResponse(BaseModel):
    status: str = Field(..., description="Outcome of the mutation (created/updated).")


class XPEntryModel(BaseModel):
    rank: int
    user_id: int | str
    username: Optional[str]
    full_name: Optional[str]
    xp: int


class CupsEntryModel(BaseModel):
    rank: int
    user_id: int | str
    username: Optional[str]
    full_name: Optional[str]
    cups: int


class XPLeaderboardResponse(BaseModel):
    total: int
    leaderboard: List[XPEntryModel]


class CupsLeaderboardResponse(BaseModel):
    total: int
    leaderboard: List[CupsEntryModel]


class SimpleLeaderboardResponse(BaseModel):
    chat_id: int
    limit: int
    leaderboard: List[dict]


class CupsHistoryResponse(BaseModel):
    chat_id: int
    limit: int
    cups: List[dict]


class ProfileResponse(BaseModel):
    user_id: int
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]


class ApplicationInsightsResponse(BaseModel):
    pending: int
    status_counts: dict
    languages: dict
    total: int
    average_pending_answer_length: float
    recent_updates: List[dict]


class HealthResponse(BaseModel):
    status: str = Field(..., description="Static health indicator.")
    storage_loaded: bool = Field(..., description="Whether the storage backend is initialised.")
    uses_ephemeral_secret: bool = Field(..., description="Indicates if data persistence is disabled.")
