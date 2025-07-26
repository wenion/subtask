import concurrent.futures
from kombu import Queue
from kombu.mixins import ConsumerProducerMixin

from h.realtime import get_connection
from h.subtask.api import (
    query,
    summarise_shareflow_view,
    shareflow_segmentation_view
)

rpc_queue = Queue('rpc_queue')


class Worker(ConsumerProducerMixin):
    def __init__(self, connection, registry):
        self.connection = connection
        self.kn = registry['kn']

    def get_consumers(self, Consumer, channel):
        return [Consumer(
            queues=[rpc_queue],
            on_message=self.on_request,
            accept={'application/json'},
            prefetch_count=1,
        )]

    def on_request(self, message):
        message.ack()
        print(message.payload)

        result = None
        func = message.payload.get('func', None)
        if func == "query" :
            result = query(self.kn, message.payload.get('q'))
            import time
        elif func == "segmentation":
            result = shareflow_segmentation_view(self.kn, message.payload)
        elif func == "summary":
            result = summarise_shareflow_view(self.kn, message.payload)

        self.producer.publish(
            {"result" : result},
            exchange='', routing_key=message.properties['reply_to'],
            correlation_id=message.properties['correlation_id'],
            serializer='json',
            retry=True,
        )

def recieve_rpc_request(registry):
    settings = registry.settings
    connection = get_connection(settings, fail_fast=True)
    worker = Worker(connection, registry)
    worker.run()
