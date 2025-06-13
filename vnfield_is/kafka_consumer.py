# my_module/kafka_consumer.py
import threading
from kafka import KafkaConsumer
import json
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def start_kafka_consumer(env):
    def approval_step_worker():
        _logger.info("⚡ Kafka consumer đang chạy...")
        consumer = KafkaConsumer(
            "odoo-integration",
            bootstrap_servers=[
                env["ir.config_parameter"].sudo().get_param("vnfield_cs.kafka_server")
            ],
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            key_deserializer=lambda m: json.loads(m.decode("utf-8")),
            group_id="odoo-consumer-"
            + env["ir.config_parameter"]
            .sudo()
            .get_param("vnfield_cs.organization_name"),
        )

        for msg in consumer:
            data = msg.value
            _logger.info("🧾 Nhận message từ Kafka: %s", data)

            try:
                with env.cr.savepoint():  # đảm bảo rollback riêng lẻ nếu lỗi
                    # Ví dụ tạo contact
                    print(msg)
                    if msg.headers["org_names"] == env.sudo().get_param(
                        "vnfield_cs.organization_name"
                    ):
                        if msg.headers["entity"] == "approval.step":
                            if msg.headers["method"] == "update":
                                approval_step = env["vnfield.approval.step"].search(
                                    [("external_id", "=", msg.headers["id"])], limit=1
                                )
                                if approval_step:
                                    print(approval_step)
                                    approval_step.write(msg.value)
            except Exception as e:
                _logger.error("❌ Lỗi xử lý Kafka message: %s", e)

    thread = threading.Thread(target=approval_step_worker, daemon=True)
    thread.start()
