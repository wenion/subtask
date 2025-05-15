import jsonschema
import logging

from h.pubsub import Sub, Pub
from jsonschema import validate, ValidationError, SchemaError

log = logging.getLogger(__name__)

PULL_EXCHANGE = "pull"
PUSH_EXCHANGE = "push"
PULL_TOPIC = "pull.user.tab"
PUSH_TOPIC = "push.user.tab"


request_schema = {
    "type": "object",
    "properties": {
        "messageType": {"type": "string"},
        "textContent": {"type": "string"},
        "url": {"type": "string"},
        "userid": {"type": "string"},
        "title": {"type": "string"},
        "client_id": {"type": "string"},
        "tabId": {"type": ["string", "null"]},  # Optional and can be null
        "windowId": {"type": ["string", "null"]},  # Optional and can be null
        "timestamp": {"type": ["integer", "null"]},  # Optional and can be null
    },
    "required": ["messageType", "textContent", "url", "userid", "title", "client_id"],  # These are required fields
    "additionalProperties": False  # Disallow extra properties
}

response_schema = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "object",
            "properties": {
                "output_text": {"type": "string"}
            },
            "required": ["output_text"],
            "additionalProperties": True
        },
        "response_list": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                        "repository": {"type": "string"},
                        "summary": {"type": "string"}
                    },
                    "required": ["title", "url", "repository", "summary"],
                    "additionalProperties": True
                }
            }
        }
    },
    "required": ["summary", "response_list"],
    "additionalProperties": True
}

def validate_payload(payload: dict, schema) -> bool:
    try:
        # Validate the payload against the schema
        validate(instance=payload, schema=schema)
        return True
    except ValidationError as ve:
        # Handle the validation error
        log.error(f"Validation error: {ve.message}")
        return False
    except SchemaError as se:
        # Handle the validation error
        log.error(f"SchemaError error: {se.message}")
        return False

def push_messages(registry, subscribe_routing_key, produce_routing_key):
    """
    Processes incoming messages by subscribing to a RabbitMQ topic, consuming
    messages, and responding via a RabbitMQ producer.

    params:
        registry:
            settings (dict): Configuration settings. Example: {'broker_url': 'amqp://guest:guest@localhost:5672//'}
            "kn": Knowledge_Nuggest
        routing_key (str): The routing key used to subscribe to the topic.
    """
    settings = registry.settings
    kn = registry['kn']
    pub = Pub(settings, PULL_EXCHANGE)

    def callback(payload, attribute):
        """
        This is a nested function that is called whenever a message is received.

        params:
            payload (dict): The content of the received message.
                -

            attribute (object): The message metadata containing delivery information such as:
                - state (str): The state of the message (e.g., 'RECEIVED').
                - content_type (str): Type of content in the message (e.g., 'application/json').
                - delivery_tag (int): A unique tag to track the delivery.
                - body_length (int): The length of the message body.
                - properties (dict): Additional properties of the message.
                - delivery_info (dict): Information about message routing, exchange, and routing key.

            Example payload:
                {
                    'messageType': 'PageData',
                    'textContent': 'Click Open Zoom Workplace app on the dialog',
                    'url': 'https://patterns.hypothes.is/',
                    'userid': 'acct:admin@localhost',
                    'title': 'Join our Cloud HD Video Meeting',
                    'client_id': 'c03bbbf6af3775bc803063f550e3be4c'
                    -'tabId': 1566284858,
                    -'windowId': 1566283865,
                    -'timestamp': 1728880697193,
                }

            Example reply_message:
                {
                    "client_id": "c03bbbf6af3775bc803063f550e3be4c", # required
                    "content": "custom",
                }
        """
        reply_message = {}
        message_type = payload.get("messageType", None)
        if message_type == "PageData":
            reply_message = handle_knowledge_push(payload)
        elif message_type == "Query":
            pass


        pub.publish(reply_message, produce_routing_key)

    sub = Sub(
        settings,
        PUSH_EXCHANGE,
        routing_key=subscribe_routing_key,
        identifier="printout",
        callback=callback,
    )
    sub.run()

def handle_knowledge_push(payload):
    is_valid = validate_payload(payload, request_schema)
    if not is_valid:
        log.error('request error')
        return

    content = payload["textContent"]
    response = kn.knowledge_pushing(content)

    summary = response[0]
    response_list = response[1]
    topics = []
    for topic in response_list:
        results = []
        for i, (doc, score) in enumerate(topic):
            m = doc.metadata
            if isinstance(m.get("summary", {}), dict):
                m["summary"] = m["summary"].get("output_text", m.get("title", ""))
            results.append({'id': i, 'page_content': doc.page_content, 'metadata': m, 'score': score})
        topics.append(results)
        top5 = topics[0][:5] if topics else []

    return {
        "client_id": payload['client_id'],
        "type": "knowledge-push",
        "payload": {
            "summary": summary,
            "context": [top5]
        }
    }
