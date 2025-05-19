import concurrent.futures
import kombu
from kombu.mixins import ConsumerProducerMixin

from h.pubsub import Sub
from h.realtime import get_connection
from h.subtask.api import knowledge_pushing


class PushKnowledge(Sub):
    def __init__(self, registry, connection, exchange, routing_key, out_exchange, out_routing_key, identifier):
        super().__init__(connection, exchange, routing_key, identifier)
        self.kn = registry['kn']
        self.publish = registry.publish
        self.send_exchange = out_exchange
        self.send_routing_key = out_routing_key

    def on_request(self, body, message):
        super().on_request(body, message)
        reply_message = knowledge_pushing(self.kn, body)

        self.publish(self.connection, self.send_exchange, self.send_routing_key, reply_message)


def push_messages(registry, subscribe_exchange, subscribe_routing_key, produce_exchange, produce_routing_key):
    settings = registry.settings

    connection = get_connection(settings, fail_fast=True)
    in_exchange = kombu.Exchange(
        subscribe_exchange, type="topic", durable=True, delivery_mode="persistent"
    )
    out_exchange = kombu.Exchange(
        produce_exchange, type="topic", durable=True, delivery_mode="persistent"
    )

    sub = PushKnowledge(
        registry,
        connection,
        in_exchange,
        subscribe_routing_key,
        out_exchange,
        produce_routing_key,
        "printout",
    )
    sub.run()
