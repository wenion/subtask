import logging
import os
import sys

import gevent
from pyramid.events import ApplicationCreated, subscriber

from h.subtask import db
#from h.subtask.metrics import metrics_process
from h.pubsub import Sub, Pub

from logging.handlers import RotatingFileHandler
import pytz
from datetime import datetime, timedelta
import string
from h.subtask.nosql import fetch_user_event, fetch_all_user_event, fetch_all_events_by_task_name, \
    fetch_all_user_events_by_session, fetch_all_user_event_within_time, create_process_model, \
    delete_process_model_by_session_creator, fetch_all_process_model, same_as_previous
from h.subtask.nosql import add_task_page, delete_task_page, delete_task_page_name_id, delete_process_model, fetch_all_user_event_record, fetch_user_event_record_by_session, fetch_all_task_pages
from h.subtask.nosql import add_push_record, delete_push_record, fetch_push_record, fetch_all_push_record, clean_old_record_from_user, get_last_within_past_minute_in_task_page
from h.subtask.nosql import is_task_page, stop_pushing, fetch_all_events_by_tn_sid, get_next_expert_step, update_expert_step, set_related_pms, get_process_model
from h.subtask.nosql import fetch_all_process_model, delete_process_model, get_step_pk_timestamp, fetch_process_model_by_session_creator, fetch_process_model_by_session_name
from h.subtask.nosql import fetch_user_event_record_by_session_id, fetch_user_event_record_by_pk, set_expert_step, share_group_info, unshare_group_info
import pandas as pd
import numpy as np
import urllib.parse
from urllib.parse import urlparse, parse_qs
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.conformance.tokenreplay.variants import token_replay
from pm4py.objects.petri_net.importer import importer as pnml_importer
from pm4py.util.constants import DEFAULT_ENCODING
from pm4py.visualization.petri_net import visualizer
import random
import pm4py
import json
import networkx as nx
import time
import urllib.request


TRACE_EXCHANGE = "trace"
TASK_EXCHANGE = "process.task"

user_status = {}
idle_status = {}
translation_table = str.maketrans(string.punctuation, '_'*len(string.punctuation))

logger = logging.getLogger("TAD")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("task_classification.log", maxBytes=5120000, backupCount=5000)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.Formatter.converter = lambda *args: datetime.now(tz=pytz.timezone('Australia/Melbourne')).timetuple()
#formatter.converter = time.localtime
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info("Service Starting...")

all_process_models = {}

def check_server(url="https://www.google.com", timeout=5):
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return "Nectar"
    except:
        return "Local"

global_time_delta = 0
if check_server() == "Local":
    global_time_delta = 22
    logger.info(f"Local server detected. Time delta set to {global_time_delta}")
elif check_server() == "Nectar":
    global_time_delta = 14
    logger.info(f"Nectar server detected. Time delta set to {global_time_delta}")

def load_all_process_models():
    process_models = fetch_all_process_model()
    if process_models:
        for pm in process_models:
            record = fetch_user_event_record_by_pk(pk=pm.session_id)
            if not record:
                # if Shareflow doesn't exist, delete the PM
                delete_process_model(pm.pk)
                logger.error(f"{pm.pm_name} {pm.session_id} {pm.creator} NOT FOUND UPON CHECKING AND DELETED")
                continue
            pm_string = pm.pm_content
            net, im, fm = pnml_importer.deserialize(pm_string, parameters={"auto_guess_final_marking": False, "encoding": DEFAULT_ENCODING})
            all_process_models[f"{pm.pm_name}_[SEP]_{pm.session_id}"] = (net, im, fm, pm.groups)
            logger.info(f"Process Model for {pm.pm_name}_{pm.session_id} loaded. {pm.pk}")


def convert_log_to_formatted(event_log):
    activity = []
    event_log.sort_values(by=["timestamp"], ascending=[True], inplace=True)
    event_log["time"] = pd.to_datetime(event_log["timestamp"], unit="ms")
    event_log = event_log.reset_index()
    for index, row in event_log.iterrows():
        text_content = ""
        if not pd.isna(row["text_content"]) and row["event_type"] == "click" and row["tag_name"].lower() in ["button", "a", "span"]:
            text_content = " " + str(row["text_content"])
        url = ""
        if type(row["base_url"]) == str:
            url = row["base_url"]
            if "#" in url:
                url, _ = url.split("#") # remove the fragment
            if "?" in url:
                url, _ = url.split("?") # exclude the query for now
            prefix = "https://"
            if "https://" in url:
                _, url = url.split("https://", 1)
                if url.count("/") > 1:
                    # remove the last parts (if there are multiple levels in the URL) that likely are too context specific
                    url, last_part = url.rsplit("/", 1)

                url = prefix + url

            if "?" in row["base_url"]:
                parsed_url = urlparse(row["base_url"])
                params = parse_qs(parsed_url.query)
                new_params = "?"
                for key, value in params.items():
                    nondigit_values = []
                    for val in value:
                        if not val.isdigit():
                            nondigit_values.append(val.translate(translation_table))
                    new_params += f"{key.translate(translation_table)}_{','.join(nondigit_values)}&"
                    # if key in ["id", "course", "update", "courseid"]:
                    #     new_params += f"{key.translate(translation_table)}&"
                    # else:
                    #     new_params += f"{key.translate(translation_table)}_{value[0].translate(translation_table)}&"
                # if parsed_url.fragment:
                #     fragment = parsed_url.fragment
                #     fragment = fragment.translate(translation_table)
                #     new_params += fragment
                if new_params != "?":
                    if new_params[-1] == "&":
                        new_params = new_params[:-1]
                    url = url + new_params
                url = " in " + url
            else:
                url = " in " + url
        # previous_event = "N/A"
        # if index-1 >= 0 and event_log.at[index-1, "tag_name"]:
        #     previous_event = event_log.at[index-1, "tag_name"]
        act = f"{row['event_type']}: {row['tag_name']}{text_content}{url}"
        activity.append(act)
    event_log["activity"] = activity
    # if event_log["time"].dtype == "O":
    #     event_log["time"] = event_log["time"].str.replace(r"\s+(AEDT|ASDT)", "", regex=True)
    #     event_log["time"] = pd.to_datetime(event_log["time"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    if "case_id" not in event_log.columns:
        case_session = {}
        for cid, sid in enumerate(event_log["session_id"].unique()):
            case_session[sid] = cid + 1
        case_ids = []
        for index, row in event_log.iterrows():
            case_ids.append(case_session[row["session_id"]])
        event_log["case_id"] = case_ids
    formatted_event_log = pm4py.format_dataframe(event_log, case_id="case_id", activity_key="activity", timestamp_key="time")
    return formatted_event_log


def create_process_model_from_log(event_log):
    if event_log is None or event_log.empty:
        logger.warning("Empty or invalid event log")
        return None, None, None
    formatted_event_log = convert_log_to_formatted(event_log)
    net, im, fm = pm4py.discover_petri_net_heuristics(formatted_event_log, activity_key="concept:name", case_id_key="case:concept:name", timestamp_key="time:timestamp")
    return net, im, fm, formatted_event_log


def expert_steps(new_trace, new_pm, threshold=0.7, include_self=True):
    # if mutual fitness pass the pre-determined threshold, the two PMs are considered similar
    conforming_trace = []
    conforming_pm = []
    for k, v in all_process_models.items():
        net, im, fm, _ = v
        replay_result = pm4py.conformance.conformance_diagnostics_token_based_replay(new_trace, net, im, fm,
                                                                                     activity_key="concept:name",
                                                                                     case_id_key="case:concept:name",
                                                                                     timestamp_key="time:timestamp")[0]
        fitness = replay_result["trace_fitness"]
        print(f"new pm TO {k}: {fitness}")
        if fitness >= threshold:
            pm_name, session_id = k.split("_[SEP]_")
            result = fetch_all_events_by_tn_sid(pm_name, session_id)
            trace = pd.DataFrame(result["table_result"])
            trace = trace[(trace["tag_name"] != "RECORD") & (~trace["tag_name"].str.startswith("HYPOTHESIS"))]  # filter out RECORD events and extension events
            formatted_trace = convert_log_to_formatted(trace)
            net, im, fm = new_pm
            replay_result = pm4py.conformance.conformance_diagnostics_token_based_replay(formatted_trace, net, im, fm,
                                                                                         activity_key="concept:name",
                                                                                         case_id_key="case:concept:name",
                                                                                         timestamp_key="time:timestamp")[0]
            fitness = replay_result["trace_fitness"]
            print(f"{k} TO new pm: {fitness}")
            if fitness >= threshold:
                formatted_trace["case_id"] = [len(conforming_trace)] * formatted_trace.shape[0]
                conforming_trace.append(formatted_trace)
                conforming_pm.append(k)
    print("point 1")
    if len(conforming_trace) == 0:
        return {}
    if include_self:
        new_trace["case_id"] = [len(conforming_trace)] * new_trace.shape[0]
        conforming_trace.append(new_trace)
    print("point 2")
    total_trace = pd.concat(conforming_trace)
    dfg = pm4py.discover_dfg(total_trace)[0]
    G = nx.DiGraph()
    print("point 3")
    for (act_from, act_to), freq in dfg.items():
        G.add_edge(act_from, act_to, weight=freq)
    print("point 4")
    b_centrality = nx.betweenness_centrality(G, normalized=True, endpoints=False)
    b_centrality = dict(sorted(b_centrality.items(), key=lambda x: x[1], reverse=True))
    print("point 5")
    new_pm_places = [val.name for val in new_pm[0].transitions]
    key_steps = [k for k, v in b_centrality.items() if k in new_pm_places and v > 0.1]
    related_pms = []
    print("point 6")
    for pm in conforming_pm:
        pm_name, session_id = pm.split("_[SEP]_")
        related_pm = fetch_process_model_by_session_name(session_id, pm_name)
        related_pms.append(related_pm.pk)
        outcome = update_expert_step(pm_name, session_id, key_steps)
        if not outcome[0]:
            logger.error(outcome[1])
    return key_steps, related_pms


def load_expert_steps_for_pm(pm_name, session_id, pm):
    trace = fetch_all_events_by_tn_sid(pm_name, session_id)["table_result"]
    formatted_trace = convert_log_to_formatted(pd.DataFrame(trace))
    exp_steps, related_pms = expert_steps(formatted_trace, new_pm=pm, threshold=0.7, include_self=False)
    exp_steps_timed = []
    for index, row in formatted_trace.iterrows():
        if row["concept:name"] in exp_steps:
            exp_steps_timed.append((row["pk"], row["timestamp"]))
    outcome_1 = set_expert_step(pm_name, session_id, exp_steps_timed)
    outcome_2 = set_related_pms(pm_name, session_id, related_pms)
    if not outcome_1[0] or not outcome_2[0]:
        logger.error(outcome_1[1] + ";" + outcome_2[1])
    else:
        logger.info(outcome_1[1] + ";" + outcome_2[1])



logger.info("Loading Process Models...")
load_all_process_models()
for k, v in all_process_models.items():
    tn, sid = k.split("_[SEP]_")
    pm = (v[0], v[1], v[2])
    load_expert_steps_for_pm(tn, sid, pm)
logger.info("Service Started!!")


def create_pm(user_id, shareflow_name, session_id, group_id=""):
    user_id = user_id
    shareflow_name = shareflow_name
    session_id = session_id
    group_id = group_id
    result = fetch_all_user_events_by_session(user_id, session_id)
    if not result or not result["table_result"] or result["total"] == 0:
        return {
            "message": "Invalid User ID or ShareFlow name. Cannot create process model",
            "created": False
        }
    trace = pd.DataFrame(result["table_result"])
    trace = trace[(trace["tag_name"] != "RECORD") & (~trace["tag_name"].str.startswith("HYPOTHESIS"))] # filter out RECORD events and extension events
    net, im, fm, formatted_trace = create_process_model_from_log(trace)
    new_pm = (net, im, fm)
    exp_steps, related_pms = expert_steps(new_trace=formatted_trace, new_pm=new_pm, threshold=0.7)
    exp_steps_timed = []
    if not net:
        return {
            "message": "Fail to create process model",
            "created": False
        }
    sf_name = shareflow_name.translate(translation_table)
    current_timestamp = int(datetime.now().timestamp() * 1000)
    if not os.path.exists("process_models"):
        os.makedirs("process_models")
    file_path = f"process_models/{sf_name}_{current_timestamp}.pnml"
    pm4py.write_pnml(net, im, fm, file_path)
    try:
        with open(file_path, 'r') as file:
            pnml_data = file.read()
            print(user_id, current_timestamp, group_id, shareflow_name, session_id)
            pk_concept_mapping = {}
            for index, row in formatted_trace.iterrows():
                if row["concept:name"] not in pk_concept_mapping:
                    pk_concept_mapping[row["concept:name"]] = []
                pk_concept_mapping[row["concept:name"]].append((row["pk"], row["timestamp"]))
                if row["concept:name"] in exp_steps:
                    exp_steps_timed.append((row["pk"], row["timestamp"]))
            status = create_process_model(creator=user_id,
                                          create_time=current_timestamp,
                                          group=group_id,
                                          pm_name=shareflow_name,
                                          pm_content=pnml_data,
                                          session_id=session_id,
                                          pk_concept_mapping=pk_concept_mapping,
                                          expert_steps=sorted(exp_steps_timed, key=lambda x: x[1]),
                                          groups=[],
                                          related_pms=related_pms)
            if not status:
                logger.error("Error occurred during the creation of process model.")
                return {
                    "message": "Error occurred during the creation of process model.",
                    "created": False
                }
    except FileNotFoundError:
        logger.error("File not found. Please check the file path.")
        return {
            "message": "File not found during creation of process model. Please retry!",
            "created": False
        }
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return {
            "message": f"An error occurred: {e}",
            "created": False
        }
    os.remove(file_path)
    all_process_models[f"{shareflow_name}_[SEP]_{session_id}"] = (net, im, fm, [])
    parameters = {"format": "png"}
    gviz = visualizer.apply(net, im, fm, parameters=parameters)
    visualizer.save(gviz, f"process_models/{sf_name}_{current_timestamp}.png")
    logger.info(f"PM {shareflow_name}_{session_id} created by {user_id}")
    # store all task pages
    all_urls = set(trace["base_url"].unique().tolist())
    all_domains = set()
    for url in all_urls:
        parsed_url = urlparse(url)
        if parsed_url:
            domain = parsed_url.netloc
            if domain:
                all_domains.add(domain)
    for domain in all_domains:
        add_task_page(url=domain, pm_name=shareflow_name, session_id=session_id)
        logger.info(f"{domain} added as task page.")
    return {
        "message": "Process model created",
        "created": True
    }


def update_pm(user_id, shareflow_name, session_id, shareflow_df, group_id=""):
    trace = shareflow_df
    trace = trace[(trace["tag_name"] != "RECORD") & (~trace["tag_name"].str.startswith("HYPOTHESIS"))] # filter out RECORD events and extension events
    net, im, fm, formatted_trace = create_process_model_from_log(trace)
    new_pm = (net, im, fm)
    exp_steps, related_pms = expert_steps(new_trace=formatted_trace, new_pm=new_pm, threshold=0.7)
    exp_steps_timed = []
    if not net:
        return {
            "message": "Fail to update process model",
            "updated": False
        }
    sf_name = shareflow_name.translate(translation_table)
    current_timestamp = int(datetime.now().timestamp() * 1000)
    if not os.path.exists("process_models"):
        os.makedirs("process_models")
    file_path = f"process_models/{sf_name}_{current_timestamp}.pnml"
    pm4py.write_pnml(net, im, fm, file_path)
    try:
        with open(file_path, 'r') as file:
            pnml_data = file.read()
            print(user_id, current_timestamp, group_id, shareflow_name, session_id)
            pk_concept_mapping = {}
            for index, row in formatted_trace.iterrows():
                if row["concept:name"] not in pk_concept_mapping:
                    pk_concept_mapping[row["concept:name"]] = []
                pk_concept_mapping[row["concept:name"]].append((row["pk"], row["timestamp"]))
                if row["concept:name"] in exp_steps:
                    exp_steps_timed.append((row["pk"], row["timestamp"]))
            status = create_process_model(creator=user_id,
                                          create_time=current_timestamp,
                                          group=group_id,
                                          pm_name=shareflow_name,
                                          pm_content=pnml_data,
                                          session_id=session_id,
                                          pk_concept_mapping=pk_concept_mapping,
                                          expert_steps=sorted(exp_steps_timed, key=lambda x: x[1]),
                                          groups=[],
                                          related_pms=related_pms)
            if not status:
                logger.error("Error occurred during the update of process model.")
                return {
                    "message": "Error occurred during the update of process model.",
                    "updated": False
                }
    except FileNotFoundError:
        logger.error("File not found. Please check the file path.")
        return {
            "message": "File not found during update of process model. Please retry!",
            "updated": False
        }
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return {
            "message": f"An error occurred: {e}",
            "updated": False
        }
    os.remove(file_path)
    all_process_models[f"{shareflow_name}_[SEP]_{session_id}"] = (net, im, fm, [])
    parameters = {"format": "png"}
    gviz = visualizer.apply(net, im, fm, parameters=parameters)
    visualizer.save(gviz, f"process_models/{sf_name}_{current_timestamp}.png")
    logger.info(f"PM {shareflow_name}_{session_id} updated by {user_id}")
    # store all task pages
    all_urls = set(trace["base_url"].unique().tolist())
    all_domains = set()
    for url in all_urls:
        parsed_url = urlparse(url)
        if parsed_url:
            domain = parsed_url.netloc
            if domain:
                all_domains.add(domain)
    for domain in all_domains:
        add_task_page(url=domain, pm_name=shareflow_name, session_id=session_id)
        logger.info(f"{domain} added as task page.")
    return {
        "message": "Process model updated",
        "updated": True
    }


def delete_pm(user_id, session_id, shareflow_name):
    user_id = user_id
    session_id = session_id
    shareflow_name = shareflow_name
    result = fetch_all_user_events_by_session(user_id, session_id)
    if not result or not result["table_result"] or result["total"] == 0:
        return {
            "message": "Invalid User ID or Session ID. Cannot delete process model",
            "removed": False
        }
    if f"{shareflow_name}_[SEP]_{session_id}" in all_process_models:
        del all_process_models[f"{shareflow_name}_[SEP]_{session_id}"]
    else:
        logger.warning(f"Process model not found in session, {user_id}, {session_id}")
    pm = fetch_process_model_by_session_name(user_id, session_id)
    related_pms = pm.related_pms
    status = delete_process_model_by_session_creator(session_id, user_id)
    if not status:
        logger.error(f"Error deleting process model from database, {user_id}, {session_id}")
        return {
            "message": "Error deleting process model from database",
            "removed": False
        }
    deleted = delete_task_page_name_id(shareflow_name, session_id)
    if not deleted:
        logger.error(f"Error deleting task page info from database, {user_id}, {session_id}")
    logger.info(f"PM {shareflow_name}_{session_id} deleted by {user_id}")
    # update all related_pms to revise the expert steps and their related_pms (which should theoretically exclude the deleted pm)
    for ppk in related_pms:
        cur_pm = get_process_model(ppk)
        loaded_pm = all_process_models[f"{cur_pm.pm_name}_[SEP]_{cur_pm.session_id}"]
        pm = (loaded_pm[0], loaded_pm[1], loaded_pm[2])
        load_expert_steps_for_pm(cur_pm.pm_name, cur_pm.session_id, pm)
    return {
        "message": "Process model deleted",
        "removed": True
    }


def task_classification(url, user_id, interval=5000, user_groups=[]):
    invalid_result = {"task_name": "", "certainty": 0, "message": "", "interval": -1, "task_ids": [], "task_details": [], "show_flag": False}
    next_request_result = {"task_name": "", "certainty": 0, "message": "", "interval": 5000, "task_ids": [], "task_details": [], "show_flag": False}
    current_time = datetime.now()
    url = url
    if not is_task_page(url):
        # if url information is not provided or if the provided url is not a task page
        logger.warning("Invalid URL information!")
        return invalid_result
    user_id = user_id
    if interval:
        interval = int(interval)
    if interval == 0:
        logger.warning(user_id + ": Invalid interval" + " " + current_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
        return next_request_result

    time_threshold = current_time - timedelta(minutes=6)
    time_threshold = int(time_threshold.timestamp())
    clean_old_record_from_user(time_threshold, user_id)

    if stop_pushing(url, user_id):
        logger.info(user_id + ": Stop pushing criteria matched")
        return {"task_name": "", "certainty": 0, "message": "", "interval": 60000, "task_ids": [], "task_details": [], "show_flag": False}

    time_delta = global_time_delta
    interval_in_second = interval / 1000
    if interval_in_second > time_delta:
        time_delta = interval_in_second

    time_ago = current_time - timedelta(seconds=time_delta)
    time_ago = int(time_ago.timestamp() * 1000)

    result = fetch_all_user_event_within_time(user_id, time_ago)
    previous_push = get_last_within_past_minute_in_task_page(user_id, url)
    trace = pd.DataFrame(result["table_result"])

    if trace is None or len(trace) < 1:
        if len(trace) == 0:
            if user_id not in idle_status:
                idle_status[user_id] = 0
            idle_status[user_id] += 1
        logger.warning(f"{user_id}: Not enough trace found - {len(trace)}" + " " + current_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
        if user_id in idle_status:
            # if an user is idle for more than 5 minutes, gradually increase the request interval
            idle_result = next_request_result.copy()
            multiplier = 1
            if int(idle_status[user_id]/12) >= 5:
                multiplier += int(idle_status[user_id]/12)
                logger.warning(f"{user_id} is detected to be inactive for more than 5 minutes")
            idle_result["interval"] = idle_result["interval"] * multiplier
            return idle_result
        if not previous_push:
            return next_request_result
    if len(trace) > 0 and user_id in idle_status and idle_status[user_id] > 0:
        del idle_status[user_id]
    trace = trace[(~trace["tag_name"].str.startswith("EXPERT")) & (~trace["tag_name"].str.startswith("HYPOTHESIS")) & (~trace["base_url"].str.startswith("https://goldmind.monash.edu/"))]
    if trace is None or len(trace) == 0:
        logger.warning(f"{user_id}: User is interacting with GoldMind" + " " + current_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
        return next_request_result
    formatted_trace = convert_log_to_formatted(trace)

    match_scores = {}
    match_steps = {}
    for k, v in all_process_models.items():
        net, im, fm, groups = v
        if len(groups) == 0 or not set(groups) & set(user_groups):
            # if the PM is private or the PM is not related to this user (no overlap of the PM groups and user groups)
            continue
        replay_result = pm4py.conformance.conformance_diagnostics_token_based_replay(formatted_trace, net, im, fm, activity_key="concept:name", case_id_key="case:concept:name", timestamp_key="time:timestamp")[0]

        fitness = replay_result["trace_fitness"]
        cur_progress = list(replay_result["enabled_transitions_in_marking"]) # or "enabled_transitions_in_marking" "reached_marking"
        progress = []
        pm_name, session_id = k.split("_[SEP]_")
        for p in cur_progress:
            results = get_step_pk_timestamp(pm_name, session_id, p.name)
            if results and len(results) == 1:
                # if there are multiple occurrence of this concept step, ignore for now, which will likely fall back to a previous step (having minimal impact on the task identification)
                progress += results
        progress = sorted(progress, key=lambda item: item[1], reverse=True)
        match_scores[k] = fitness
        match_steps[k] = progress

    match_scores = dict(sorted(match_scores.items(), key=lambda item: item[1], reverse=True))
    #print("****************************************")
    #print("Matched scores", match_scores)
    #print("++++++++++++++++++++++++++++++++++++++++")
    if len(match_scores.keys()) == 0:
        logger.warning("No PM for matching yet...")
        return next_request_result

    task = list(match_scores.keys())[0] # highest matched task
    match_score = match_scores[task]
    # not pushing if all match scores below threshold
    if match_score < 0.25:
        logger.warning(user_id + ": No task matching")
        if not previous_push:
            return next_request_result

    # in the process model dictionary storing all PMs in the current session, the keys are <PM_name>_[SEP]_<session_id>
    # "_[SEP]_" is added as a separator, when displaying, it is important to exclude the session ID
    count = 0
    matched_tasks = []
    task_details = []
    tids = []
    if match_score <= 0.9:
        # if match score <= 0.9, get top n (max 3) whose score <= 0.9 but >= 0.25
        for key, value in match_scores.items():
            if count == 3 or value < 0.25: # TODO: may need to tune the threshold again
                break
            t_name, t_id = key.split("_[SEP]_") # t_id has been updated to pk of shareflow
            shareflow = fetch_user_event_record_by_pk(t_id)
            if shareflow:
                if shareflow.userid == user_id:
                    logger.warning(f"{user_id} was matched with own PM {key} (fitness: {value})")
                    continue
                current_steps = [val[0] for val in match_steps[key]]
                exp_step = get_next_expert_step(t_name, t_id, match_steps[key][0][1]) if len(match_steps[key]) > 0 else None
                task_details.append({"user_id": shareflow.userid,
                                     "session_id": shareflow.pk,
                                     "task_name": shareflow.task_name,
                                     "current_step": current_steps,
                                     "expert_step": exp_step,
                                     "match_score": value})
                tids.append(shareflow.pk)
                matched_tasks.append(t_name)
                count += 1
    else:
        for key, value in match_scores.items():
            if value == match_score:
                t_name, t_id = key.split("_[SEP]_")  # t_id has been updated to pk of shareflow
                shareflow = fetch_user_event_record_by_pk(t_id)
                if shareflow:
                    if shareflow.userid == user_id:
                        # if the PM creator is the current user, don't append it to the list
                        logger.warning(f"{user_id} was matched with own PM {key} (fitness: {value})")
                        continue
                    current_steps = [val[0] for val in match_steps[key]]
                    exp_step = get_next_expert_step(t_name, t_id, match_steps[key][0][1]) if len(match_steps[key]) > 0 else None
                    task_details.append({"user_id": shareflow.userid,
                                         "session_id": shareflow.pk,
                                         "task_name": shareflow.task_name,
                                         "current_step": current_steps,
                                         "expert_step": exp_step,
                                         "match_score": value})
                    tids.append(shareflow.pk)
                    matched_tasks.append(t_name)
                    count += 1
        # randomly select one highest Shareflow if there are multiple matching
        matched_task_idx = random.choice(list(range(len(matched_tasks))))
        logger.info(f"Tasks identified for {user_id}: {matched_tasks[matched_task_idx]} with score {match_score}")
        matched_tasks = [matched_tasks[matched_task_idx]]
        task_details = [task_details[matched_task_idx]]
        tids = [tids[matched_task_idx]]

    #print(task_details)

    if len(matched_tasks) == 0 or len(task_details) == 0 or len(tids) == 0:
        logger.warning(user_id + ": No task matching")
        if not previous_push:
            return next_request_result
        else:
            task_details = previous_push

    # has pinned shareflow and the pinned one is within the identified tasks -> no action
    if user_status[user_id]["pinnedSF"] and user_status[user_id]["pinnedSF"][0] in tids and user_status[user_id]["pinnedSF"][1] in matched_tasks:
        logger.info(user_id + "has pinned SF, which is one of the identified tasks; no push")
        return next_request_result

    push_message = "The following ShareFlows from your colleagues might be useful: "
    same = same_as_previous(user_id=user_id,
                            url=url,
                            push_type="SF",
                            push_content=push_message,
                            additional_info=json.dumps(task_details))
    # TODO: confirm if users should receive new push if they were identified to be in a different step
    if same:
        logger.info(user_id + ": Same task identified as in previous Shareflow Push; the current one won't be pushed")
        return next_request_result

    pr = add_push_record(timestamp=int(datetime.now().timestamp()),
                         push_type="SF",
                         push_to=user_id,
                         push_content=push_message,
                         url=url,
                         additional_info=json.dumps(task_details))
    #pr.expire(360) # the push records are stored for 6 minutes, then expire

    logger.info(f"Tasks identified for {user_id}: {'; '.join(matched_tasks)} with score {match_score}")

    return {
        "task_name": "; ".join(matched_tasks),
        "certainty": match_score,
        "message": push_message,
        "interval": interval * 2.5,
        "task_ids": tids,
        "task_details": task_details,
        "show_flag": True
    }


def send_push(settings, produce_routing_key):
    global user_status
    pub = Pub(settings, TASK_EXCHANGE)
    logger.info("Task matching loop started...")
    try:
        while True:
            current_time = datetime.now().timestamp() * 1000
            to_del = []
            for user in list(user_status.keys()):
                status = None
                if user in user_status:
                    status = user_status[user]
                interval = status["interval"]
                if interval < 0:
                    continue
                elif interval >= 900000:
                    to_del.append(user)
                    continue
                gevent.sleep(0.1)
                if interval and status["last_active"] and status["last_match"] and current_time - status["last_active"] >= user_status[user]["interval"] and current_time - status["last_match"] >= user_status[user]["interval"]:
                    logger.info(f"Matching for user {user} triggered...")
                    url = status["url"]
                    response = task_classification(url, user, user_status[user]["interval"], user_status[user]["groups"])
                    if response["interval"] >= 900000:
                        to_del.append(user)
                        continue
                    user_status[user]["interval"] = response["interval"]
                    client_id = status["client_id"]
                    #print(user_status)
                    if response["show_flag"]:
                        gevent.sleep(0.1)
                        reply_message = {
                            "client_id": user_status[user]["client_id"],
                            "type": "ShareFlow Notification",
                            "title": "Need help with this task?",
                            "message": "message",
                            "timestamp": current_time,
                            "extra": response["task_details"],
                            "url": url,
                            "content": response["message"]
                        }
                        pub.publish(reply_message, produce_routing_key)
                    user_status[user]["last_match"] = current_time
            for user in to_del:
                if user in user_status:
                    del user_status[user]
                    logger.info(f"Matching stopped for user {user} due to inactivity for 15 minutes")
                if user in idle_status:
                    del idle_status[user]
            gevent.sleep(0.1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down task matching loop...")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
    finally:
        logger.info("Loop has stopped")


def process_messages(settings, subscribe_routing_key, produce_routing_key):
    """
    Processes incoming messages by subscribing to a RabbitMQ topic, consuming
    messages, and responding via a RabbitMQ producer.

    params:
        settings (dict): Configuration settings. Example: {'broker_url': 'amqp://guest:guest@localhost:5672//'}
        routing_key (str): The routing key used to subscribe to the topic.
    """
    pub = Pub(settings, TASK_EXCHANGE)

    def callback(payload, attribute):
        """
        This is a nested function that is called whenever a message is received.

        params:
            payload (dict): The content of the received message.
                - messageType (str): Type of message, e.g., 'TraceData'.
                - type (str): The type of event (e.g., 'click').
                - clientX (int): X-coordinate of the event on the screen.
                - clientY (int): Y-coordinate of the event on the screen.
                - tagName (str): The HTML tag involved in the interaction.
                - textContent (str): The text content of the HTML element.
                - interactionContext (str): JSON string containing additional context for the interaction.
                - xpath (str): The XPath of the HTML element involved in the interaction.
                - eventSource (str): The source of the event (e.g., 'MOUSE').
                - width (int): The width of the client browser window.
                - height (int): The height of the client browser window.
                - enableCapture (bool): A flag indicating whether to enable capture (True/False).
                - url (str): The URL of the page where the event occurred.
                - tabId (int): Unique identifier of the browser tab.
                - windowId (int): Unique identifier of the browser window.
                - userid (str): Identifier for the user triggering the event.
                - timestamp (int): Timestamp of the event in milliseconds.
                - title (str): The title of the web page where the event occurred.
                - region (str): The region information (if applicable).
                - session_id (str): Session identifier (if applicable).
                - task_name (str): Name of the task related to the event (if applicable).
                - ip_address (str): The IP address of the client (if available).
                - client_id (str): Unique identifier for the client application.

            attribute (object): The message metadata containing delivery information such as:
                - state (str): The state of the message (e.g., 'RECEIVED').
                - content_type (str): Type of content in the message (e.g., 'application/json').
                - delivery_tag (int): A unique tag to track the delivery.
                - body_length (int): The length of the message body.
                - properties (dict): Additional properties of the message.
                - delivery_info (dict): Information about message routing, exchange, and routing key.

            Example payload:
                {
                    'messageType': 'TraceData',
                    'type': 'click',
                    'clientX': 1216,
                    'clientY': 271,
                    'tagName': 'H1',
                    'textContent': 'Click Open Zoom Workplace app on the dialog',
                    'interactionContext': '{"name":"Click Open Zoom Workplace app","value":"Click Open Zoom Workplace app"}',
                    'xpath': '//*[@id="zoom-ui-frame"]/div[2]/div/div[1]/h1',
                    'eventSource': 'MOUSE',
                    'width': 1920,
                    'height': 945,
                    'enableCapture': False,
                    'url': 'https://zoom.us/j/87028072235?pwd=WWlyL2hVYUc2RVoydmRUWWMxRGRodz09#success',
                    'tabId': 1566284858,
                    'windowId': 1566283865,
                    'userid': 'acct:admin@localhost',
                    'timestamp': 1728880697193,
                    'title': 'Join our Cloud HD Video Meeting',
                    'region': '',
                    'session_id': '',
                    'task_name': '',
                    'ip_address': '',
                    'client_id': 'c03bbbf6af3775bc803063f550e3be4c'
                }

            Example reply_message:
                {
                    "client_id": "c03bbbf6af3775bc803063f550e3be4c", # required
                    "state": "SUCCESS",
                    "content": "custom",
                }
        """

        # TODO: change implementation to use windowId and TabId, ClientId will not work properly
        print("payload", payload["messageType"])
        global user_status
        current_time = datetime.now().timestamp() * 1000
        message = ""
        if "userid" in payload and payload["userid"] not in user_status:
            user_status[payload["userid"]] = {"last_active": None, "interval": 5000, "last_match": None, "url": payload["url"], "pinnedSF": None, "groups": ["__world__"] + payload["groups"]}
            logger.info(f"Task matching for user {payload['userid']} has started...")

        if payload["messageType"] == "TraceData" and payload["tagName"] == "RECORD" and payload["textContent"] == "finish":
            # stop recording --> create ShareFlow
            user_status[payload["userid"]]["last_active"] = current_time
            if not user_status[payload["userid"]]["last_match"]:
                user_status[payload["userid"]]["last_match"] = current_time
            user_id = payload["userid"]
            shareflow_name = payload["taskName"]
            session_id = payload["sessionId"] # has changed to the shareflow_pk
            group_id = ""
            outcome = create_pm(user_id, shareflow_name, session_id, group_id)
            if not outcome["created"]:
                logger.error(outcome["message"])
            else:
                message = outcome["message"]
            logger.info(message)

        elif payload["messageType"] == "TraceData" and payload["tagName"] == "RECORD" and payload["textContent"] == "delete":
            user_id = payload["userid"]
            session_id = payload["sessionId"]
            shareflow_name = payload["taskName"]
            result = fetch_user_event_record_by_pk(session_id)
            if not result:
                logger.error("ShareFlow not found somehow, incorrect Session ID. Please check the issue!")
            if f"{shareflow_name}_[SEP]_{session_id}" in all_process_models:
                del all_process_models[f"{shareflow_name}_[SEP]_{session_id}"]
            else:
                logger.warning(f"Process model not found in session, {user_id}, {session_id}")
            status = delete_process_model_by_session_creator(session_id, user_id)
            if not status:
                logger.error(f"Error deleting process model from database, {user_id}, {session_id}")
                return False
            deleted = delete_task_page_name_id(shareflow_name, session_id)
            if not deleted:
                logger.error(f"Error deleting task page info from database, {user_id}, {session_id}")
            logger.info(f"PM {shareflow_name}_{session_id} deleted by {user_id}")
            return True

        elif payload["messageType"] == "UpdateShareflow":
            meta = payload["shareflowMeta"]
            session_id = meta["sessionId"]
            task_name = meta["taskName"]
            creator = meta["userid"]
            group_id = meta["groupid"]
            trace_df = pd.DataFrame(payload["update"])
            trace_df = trace_df.rename(columns={"textContent": "text_content", "type": "event_type", "tagName": "tag_name", "url": "base_url", "sessionId": "session_id"})
            delete_outcome = delete_pm(creator, session_id, task_name)
            if not delete_outcome["removed"]:
                logger.error(f"Error deleting process model for update, {creator}, {session_id}, {task_name}; due to {delete_outcome['message']}")
            else:
                logger.info(f"PM {task_name}_{session_id} deleted for update by {creator}")
            update_outcome = update_pm(creator, task_name, session_id, group_id, trace_df)
            if not update_outcome["updated"]:
                logger.error(f"Error updating process model, {creator}, {session_id}, {task_name}; due to {update_outcome['message']}")
            else:
                logger.info(f"PM {task_name}_{session_id} updated by {creator}")

        elif payload["messageType"] == "PinShareflow":
            status = payload["status"]
            meta = payload["shareflowMeta"]
            session_id = meta["session_id"]
            task_name = meta["task_name"]
            if status == "pin":
                user_status[payload["userid"]]["pinnedSF"] = (session_id, task_name)
            elif status == "unpin":
                user_status[payload["userid"]]["pinnedSF"] = None

        elif payload["messageType"] == "ShareShareFlow":
            status = payload["status"]
            meta = payload["shareflowMeta"]
            target_group = payload["groupid"]
            outcome = None
            if status == "share":
                outcome = share_group_info(meta["task_name"], meta["session_id"], target_group)
            elif status == "unshare":
                outcome = unshare_group_info(meta["task_name"], meta["session_id"], target_group)
            if not outcome or not outcome[0]:
                logger.error(f"Error sharing/unsharing process model, {meta['session_id']}, {meta['task_name']}; due to {outcome[1]}")
            elif outcome[0]:
                logger.info(f"PM {meta['session_id']}, {meta['task_name']} shared / unshared to {target_group}")
                all_process_models[f"{meta['task_name']}_[SEP]_{meta['session_id']}"][3] = outcome[1]

        #{"messageType": "ShareShareFlow", "status": "share", "shareflowMeta": {"session_id": "xxx", "task_name": "xxx", "creator": "xxx"}, "groupid": "__world__"}
        #{"messageType": "ShareShareFlow", "status": "unshare", "shareflowMeta": {"session_id": "xxx", "task_name": "xxx", "creator": "xxx"}, "groupid": "__world__"}
        elif payload["messageType"] == "TraceData":
            # task classification info
            user_status[payload["userid"]]["last_active"] = current_time
            if not user_status[payload["userid"]]["last_match"]:
                user_status[payload["userid"]]["last_match"] = current_time
            if payload["userid"] in idle_status and int(idle_status[payload["userid"]] / 12) >= 5:
                # if user becomes active again, reactivate task matching
                idle_status[payload["userid"]] = 0
                user_status[payload["userid"]]["interval"] = 5000
            user_status[payload["userid"]]["url"] = payload["url"]
            user_status[payload["userid"]]["client_id"] = payload["client_id"]
            # if any update to the user's groups
            if set(payload["groups"] + ["__world__"]) != set(user_status[payload["userid"]]["groups"]):
                user_status[payload["userid"]]["groups"] = set(payload["groups"] + ["__world__"])

            if user_status[payload["userid"]]["interval"] < 0 and is_task_page(payload["url"]):
                # if user switches from a non task page to a task page, reactivate task matching
                user_status[payload["userid"]]["interval"] = 5000
            if payload["url"] != user_status[payload["userid"]]["url"]:
                # if user goes to a new page, the interval should be reset
                user_status[payload["userid"]]["url"] = payload["url"]
                user_status[payload["userid"]]["interval"] = 5000
            print("triggered Client_ID", payload["client_id"])
        #    url = payload["url"]
        #    user_id = payload["userid"]
        #    task_classification(url, user_id, interval=None)

        # ------- remove -------
        # Implementation


    sub = Sub(
        settings,
        TRACE_EXCHANGE,
        routing_key=subscribe_routing_key,
        identifier="printout",
        callback=callback,
    )
    sub.run()
