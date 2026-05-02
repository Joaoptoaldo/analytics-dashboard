from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base


class SyncState(Base):
    __tablename__ = "sync_state"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)