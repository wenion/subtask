from datetime import datetime, timezone
import math
import pytz
from redis_om import Migrator
from redis_om import Field, JsonModel, EmbeddedJsonModel
from urllib.parse import urlparse
from typing import Optional


class ProcessModel(JsonModel):
    class Meta:
        global_key_prefix = 'h'
        model_key_prefix = 'ProcessModel'
    creator: str = Field(index=True) #userid in UserRole
    create_time: int = Field(index=True) # the time process model is created
    group: str = Field(index=False) #the permitted groups for the ShareFlow public_id
    pm_name: str = Field(index=True)#process model name
    pm_content: str = Field(index=True)# process model content
    session_id: str = Field(index=True) # session_id is actually the pk of ShareFlow (user_event_record)
    pk_concept_mapping: dict = Field(index=False)
    expert_steps: Optional[list] = Field(index=False, default=[])
    related_pms: Optional[list] = Field(index=False, default=[])
    groups: Optional[list] = Field(index=False, default=[])


def fetch_all_process_model():
    query = ProcessModel.find()
    all_models = query.all()
    return all_models if len(all_models) > 0 else None


def fetch_process_model_by_session_creator(session_id, creator):
    query = ProcessModel.find((ProcessModel.session_id == session_id) & (ProcessModel.creator == creator))
    total = query.all()
    return total[0] if len(total) > 0 else None


def fetch_process_model_by_session_name(session_id, pm_name):
    query = ProcessModel.find((ProcessModel.session_id == session_id) & (ProcessModel.pm_name == pm_name))
    total = query.all()
    return total[0] if len(total) > 0 else None


def get_process_model(pk):
    process_model = ProcessModel.get(pk)
    process_model_dict = process_model.dict()
    return process_model_dict


def create_process_model(
        creator,
        create_time,
        group,
        pm_name,
        pm_content,
        session_id,
        pk_concept_mapping,
        expert_steps,
        groups,
        related_pms):
    exist = fetch_process_model_by_session_creator(session_id, creator)
    if exist:
        return exist
    process_model = ProcessModel(
        creator = creator,
        create_time = create_time,
        group = group,
        pm_name = pm_name,
        pm_content = pm_content,
        session_id = session_id,
        pk_concept_mapping = pk_concept_mapping,
        expert_steps = expert_steps,
        groups = groups,
        related_pms = related_pms
    )
    process_model.save()
    return process_model


def update_process_model(session_id, creator, update):
    process_model = fetch_process_model_by_session_creator(session_id=session_id, creator=creator)
    if process_model:
        # process_model.creator = update.get('creator')
        # process_model.group = update.get('group')
        # process_model.pm_name = update.get('pm_name')
        process_model.pm_content = update.get('pm_content')

        process_model.save()
        return process_model
    else:
        return None


def delete_process_model_by_session_creator(session_id, creator):
    try:
        pm = fetch_process_model_by_session_creator(session_id, creator)
        if pm:
            ProcessModel.delete(pm.pk)
        else:
            return False
    except:
        return False
    else:
        return True


def delete_process_model(pk):
    try:
        ProcessModel.delete(pk)
    except:
        return False


def get_step_pk_timestamp(pm_name, session_id, concept):
    query = ProcessModel.find((ProcessModel.session_id == session_id) & (ProcessModel.pm_name == pm_name))
    total = query.all()
    if len(total) > 0:
        pm = total[0]
        if concept in pm.pk_concept_mapping:
            return pm.pk_concept_mapping[concept]
    return None


def get_next_expert_step(pm_name, session_id, cur_timestamp):
    query = ProcessModel.find((ProcessModel.session_id == session_id) & (ProcessModel.pm_name == pm_name))
    total = query.all()
    if len(total) > 0:
        pm = total[0]
        for step in pm.expert_steps:
            if step[1] > cur_timestamp:
                return step[0]
        return pm.expert_steps[0][0] if len(pm.expert_steps) > 0 else None
    return None


def update_expert_step(pm_name, session_id, expert_steps):
    query = ProcessModel.find((ProcessModel.pm_name == pm_name) & (ProcessModel.session_id == session_id))
    total = query.all()
    if len(total) > 0:
        pm = total[0]
        cur_expert_steps = pm.expert_steps if pm.expert_steps else []
        cur_expert_step_pks = [val[0] for val in cur_expert_steps]
        pk_concept_mapping = pm.pk_concept_mapping
        for step in expert_steps:
            if step in pk_concept_mapping:
                step_pk_timestamp = pk_concept_mapping[step]
                for s in step_pk_timestamp:
                    if s[0] not in cur_expert_step_pks:
                        cur_expert_steps.append(s)
        cur_expert_steps = list(sorted(cur_expert_steps, key=lambda item: item[1]))
        pm.expert_steps = cur_expert_steps
        try:
            pm.save()
            return True, "Expert steps updated"
        except Exception as e:
            return False, str(e)
    return False, "Process Model not found"


def set_expert_step(pm_name, session_id, expert_steps):
    query = ProcessModel.find((ProcessModel.session_id == session_id) & (ProcessModel.pm_name == pm_name))
    total = query.all()
    if len(total) > 0:
        pm = total[0]
        pm.expert_steps = expert_steps
        try:
            pm.save()
            return True, "Expert steps set"
        except Exception as e:
            return False, str(e)
    return False, "Process Model not found"


def set_related_pms(pm_name, session_id, related_pms):
    query = ProcessModel.find((ProcessModel.session_id == session_id) & (ProcessModel.pm_name == pm_name))
    total = query.all()
    if len(total) > 0:
        pm = total[0]
        pm.related_pms = related_pms
        try:
            pm.save()
            return True, "Related PMs set"
        except Exception as e:
            return False, str(e)
    return False, "Process Model not found"


def share_group_info(pm_name, session_id, groupid):
    query = ProcessModel.find((ProcessModel.session_id == session_id) & (ProcessModel.pm_name == pm_name))
    total = query.all()
    if len(total) > 0:
        pm = total[0]
        if not pm.groups:
            pm.groups = []
        pm.groups.append(groupid)
        try:
            pm.save()
            return True, pm.groups
        except Exception as e:
            return False, str(e)
    return False, "Group cannot be added"


def unshare_group_info(pm_name, session_id, groupid):
    query = ProcessModel.find((ProcessModel.session_id == session_id) & (ProcessModel.pm_name == pm_name))
    total = query.all()
    if len(total) > 0:
        pm = total[0]
        if not pm.groups or len(pm.groups) == 0:
            return False, "No group info to delete"
        pm.groups.remove(groupid)
        try:
            pm.save()
            return True, pm.groups
        except Exception as e:
            return False, str(e)
    return False, "Group cannot be deleted"