import logging

from h.pubsub import Sub, Pub

log = logging.getLogger(__name__)

PULL_EXCHANGE = "pull"
PUSH_EXCHANGE = "push"
PULL_TOPIC = "pull.user.tab"
PUSH_TOPIC = "push.user.tab"


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
                    'title': 'Join our Cloud HD Video Meeting',-
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
        response = kn.knowledge_pushing(payload, "")
        summary = response[0]["output_text"]
        json_data =response[1]
        context = []

        for index, item in enumerate(json_data):
            result = {
                "id": "dsi-"+ str(index),
                "page_content": "",
                "metadata": {
                    "id": "dsi-"+ str(index),
                    "title": item["title"],
                    "url": item["url"],
                    "score": str(0.99 - index*0.01),
                    "summary": item["summary"],
                    "highlights": "",
                    "repository": item["repository"],
                },
                "is_bookmark": False
            }
            context.append(result)

        reply_message = {
            "client_id": payload['client_id'],
            "type": "knowledge-push",
            "payload": {
                "summary": summary,
                "context": [context]
            }
        }

        pub.publish(reply_message, produce_routing_key)

    sub = Sub(
        settings,
        PUSH_EXCHANGE,
        routing_key=subscribe_routing_key,
        identifier="printout",
        callback=callback,
    )
    sub.run()
