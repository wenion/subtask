import logging
import os
import sys

import gevent
from pyramid.events import ApplicationCreated, subscriber

from h.subtask import db
from h.subtask.metrics import metrics_process
from h.pubsub import Sub, Pub

log = logging.getLogger(__name__)


TRACE_EXCHANGE = "trace"
TASK_EXCHANGE = "process.task"


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
        # ------- remove -------
        # Implementation

        reply_message = {
            "client_id": payload['client_id'],
            "state": "xxx",
            "content": payload['type'],
        }

        # Implementation
        # ------- remove -------

        pub.publish(reply_message, produce_routing_key)

    sub = Sub(
        settings,
        TRACE_EXCHANGE,
        routing_key=subscribe_routing_key,
        identifier="printout",
        callback=callback,
    )
    sub.run()
