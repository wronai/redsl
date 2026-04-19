"""Secret handling models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

if TYPE_CHECKING:
    from .core import _utcnow
else:
    from datetime import UTC, datetime as _dt

    def _utcnow() -> _dt:
        return _dt.now(UTC)


class SecretRotation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    last_rotated: datetime | None = None
    rotate_every_days: int | None = Field(default=None, ge=1, le=3650)
    next_rotation_due: datetime | None = None

    @model_validator(mode="after")
    def _check_rotation_order(self) -> SecretRotation:
        if (
            self.last_rotated
            and self.next_rotation_due
            and self.next_rotation_due < self.last_rotated
        ):
            raise ValueError("next_rotation_due cannot be earlier than last_rotated")
        return self


class SecretSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref: str = Field(..., min_length=1)
    required: bool = True
    rotation: SecretRotation = Field(default_factory=SecretRotation)

    @field_validator("ref")
    @classmethod
    def _validate_ref(cls, value: str) -> str:
        if not value.startswith(("file:", "env:", "vault:", "doppler:")):
            raise ValueError("Secret ref must start with file:, env:, vault:, or doppler:")
        return value


__all__ = ["SecretRotation", "SecretSpec"]
