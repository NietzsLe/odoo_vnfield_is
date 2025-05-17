from kafka import KafkaConsumer
import threading
import json
import logging
import odoo
import uuid

random_uuid = uuid.uuid4()
_logger = logging.getLogger(__name__)


class KafkaConsumer(threading.Thread):
    def __init__(self, topic, model, kafka_servers):
        super().__init__()
        self.topic = topic
        self.kafka_servers = kafka_servers
        self.daemon = True  # Đảm bảo dừng cùng Odoo
        self.model = model
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=kafka_servers,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            group_id="odoo_consumer_" + random_uuid,
        )

    def run(self):
        _logger.info("Kafka consumer started for topic: %s", self.topic)
        with odoo.api.Environment.manage():
            registry = odoo.registry(odoo.tools.config["db_name"])
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                for msg in self.consumer:
                    self.handle_message(env, msg.value)

    def handle_message(self, env, message):
        _logger.info("Received message: %s", message)
        # Ví dụ: tạo một bản ghi mới trong Odoo
        env["vnfield."].create(
            {
                "name": message.get("name"),
                "description": message.get("desc"),
            }
        )


def start_kafka_consumers(cr, registry):
    # consumer = KafkaConsumer(
    #     topic="approval", model="", kafka_servers=["192.168.2.3:9092"]
    # )
    # consumer.start()
    pass
