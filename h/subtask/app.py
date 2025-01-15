import pyramid

from h.config import configure
from h.security import StreamerPolicy
from h.sentry_filters import SENTRY_FILTERS
from nosql.process_model import fetch_all_process_model, delete_process_model
from nosql.user_event_record import fetch_user_event_record_by_session_id
import logging
from logging.handlers import RotatingFileHandler
from pm4py.objects.petri_net.importer import importer as pnml_importer
from datetime import datetime
import pytz

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


def load_all_process_models():
    process_models = fetch_all_process_model()
    if process_models:
        for pm in process_models:
            record = fetch_user_event_record_by_session_id(session_id=pm.session_id, userid=pm.creator)
            if not record:
                # if Shareflow doesn't exist, delete the PM
                delete_process_model(pm.pk)
                print(f"{pm.pm_name} {pm.session_id} {pm.creator} NOT FOUND UPON CHECKING AND DELETED")
                continue
            pm_string = pm.pm_content
            net, im, fm = pnml_importer.deserialize(pm_string, parameters={"auto_guess_final_marking": False, "encoding": DEFAULT_ENCODING})
            all_process_models[f"{pm.pm_name}_[SEP]_{pm.session_id}"] = (net, im, fm)
            logger.info(f"Process Model for {pm.pm_name}_{pm.session_id} loaded.")


def create_app(_global_config, **settings):
    config = configure(settings=settings)

    config.include("pyramid_services")

    config.include("h.security")
    # Override the default authentication policy.
    config.set_security_policy(StreamerPolicy())

    config.include("h.db")
    config.include("h.session")
    config.include("h.services")
    # include redis nosql codes -- Steve
    config.include("h.subtask.nosql")

    # We include links in order to set up the alternative link registrations
    # for annotations.
    config.include("h.links")

    # And finally we add routes. Static routes are not resolvable by HTTP
    # clients, but can be used for URL generation within the websocket server.
    # config.add_route("ws", "/ws")
    # config.add_route("annotation", "/a/{id}", static=True)
    # config.add_route("api.annotation", "/api/annotations/{id}", static=True)

    # Health check
    config.scan("h.views.status")
    config.add_route("status", "/_status")

    # config.scan("h.subtask.views")
    config.scan("h.subtask.streamer")
    config.add_tween(
        "h.streamer.tweens.close_db_session_tween_factory",
        over=["pyramid_exclog.exclog_tween_factory", pyramid.tweens.EXCVIEW],
    )

    # Configure sentry
    config.add_settings(
        {
            "h_pyramid_sentry.filters": SENTRY_FILTERS,
            "h_pyramid_sentry.celery_support": True,
        }
    )

    config.include("h_pyramid_sentry")

    # Add support for logging exceptions whenever they arise
    config.include("pyramid_exclog")
    config.add_settings({"exclog.extra_info": True})
    logger.info("Loading Process Models...")
    load_all_process_models()
    logger.info("Service Started!!")
    return config.make_wsgi_app()
