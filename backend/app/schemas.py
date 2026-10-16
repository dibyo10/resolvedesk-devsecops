from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

Status = Literal["OPEN", "IN_PROGRESS", "RESOLVED"]
Priority = Literal["LOW", "MEDIUM", "HIGH", "URGENT"]


class TicketCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    requester_email: EmailStr = Field(max_length=254)
    priority: Priority = "MEDIUM"
    status: Status = "OPEN"
    assignee: str = Field(default="Unassigned", min_length=1, max_length=120)


class TicketUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    subject: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    requester_email: EmailStr | None = Field(default=None, max_length=254)
    priority: Priority | None = None
    status: Status | None = None
    assignee: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def reject_null_fields(self):
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Ticket fields cannot be null")
        return self


class TicketOut(TicketCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class StatsOut(BaseModel):
    total: int
    open: int
    inProgress: int
    resolved: int
    urgent: int
