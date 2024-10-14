import logging
import os
import sys

import gevent
from pyramid.events import ApplicationCreated, subscriber

from h.subtask import db
from h.subtask.metrics import metrics_process
from h.subtask.task import process_messages

log = logging.getLogger(__name__)


# Message queues that the streamer processes messages from
TRACE_TOPIC = "request.user.event"
TASK_TOPIC = "response.user.event"


@subscriber(ApplicationCreated)
def start(event):  # pragma: no cover
    """
    Start some greenlets to process the incoming data from the message queue.

    This subscriber is called when the application is booted, and kicks off
    greenlets running `process_queue` for each message queue we subscribe to.
    The function does not block.
    """
    registry = event.app.registry
    settings = registry.settings

    greenlets = [
        gevent.spawn(process_messages, settings, TRACE_TOPIC, TASK_TOPIC),
    ]

    # Start a "greenlet of last resort" to monitor the worker greenlets and
    # bail if any unexpected errors occur.
    gevent.spawn(supervise, greenlets)


def supervise(greenlets):  # pragma: no cover
    try:
        gevent.joinall(greenlets, raise_error=True)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:  # pylint:disable=bare-except
        log.critical("Unexpected exception in streamer greenlet:", exc_info=True)
    else:
        log.critical("Unexpected early exit of streamer greenlets. Aborting!")
    # If the worker greenlets exit early, our best option is to kill the worker
    # process and let the app server take care of restarting it.
    sys.exit(1)
