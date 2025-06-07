from datetime import datetime, timezone
import math
import pytz
from redis_om import Migrator
from redis_om import Field, JsonModel, EmbeddedJsonModel
from urllib.parse import urlparse
from typing import Optional


class UserEventRecord(JsonModel):
    class Meta:
        global_key_prefix = 'h'
        model_key_prefix = 'UserEventRecord'
    startstamp: int = Field(index=True)
    endstamp: int = Field(index=True)
    session_id: str = Field(full_text_search=True, sortable=True)
    task_name: Optional[str] = Field(full_text_search=True, sortable=True)
    description: str = Field(full_text_search=True, sortable=True)
    target_uri: Optional[str]
    start: Optional[int]
    backdate: Optional[int] = 0
    completed: int = Field(index=True)
    userid: str = Field(index=True)
    groupid: str = Field(index=True)
    groups: Optional[str] = Field(index=True, default=None)
    shared: int = Field(index=True)



def fetch_all_user_event_record():
    query = UserEventRecord.find()
    total = query.all()
    return total if len(total) > 0 else None


def fetch_user_event_record_by_session_id(session_id, userid):
    query = UserEventRecord.find(
        (UserEventRecord.session_id == session_id) &
        (UserEventRecord.userid == userid)
        )
    total = query.all()
    return total[0] if len(total) > 0 else None


def fetch_user_event_record_by_pk(pk):
    query = UserEventRecord.find(UserEventRecord.pk == pk)
    total = query.all()
    return total[0] if len(total) > 0 else None


def fetch_user_event_record_by_session(session_id):
    query = UserEventRecord.find(UserEventRecord.session_id == session_id)
    total = query.all()
    return total[0] if len(total) > 0 else None

