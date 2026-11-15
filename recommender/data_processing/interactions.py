"""Load normalized interactions for offline evaluation."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from recommender.models import ItemKey
SQL_PATH = Path(__file__).with_name("interactions.sql")
@dataclass(frozen=True)
class UserInteraction:
    user_id: str
    item_id: str
    item_type: str
    event_type: str
    rating_value: int | None
    is_completed: bool | None
    event_at: datetime | None
    @property
    def item_key(self) -> ItemKey:
        return (self.item_type.casefold(), self.item_id)
def load_interactions(connection: Any) -> list[UserInteraction]:
    query = SQL_PATH.read_text(encoding="utf-8")
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        names = [column.name for column in cursor.description]
    return [UserInteraction(**dict(zip(names, row))) for row in rows]
