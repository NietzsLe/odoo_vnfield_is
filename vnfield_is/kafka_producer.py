from kafka import KafkaProducer
import json


def produce(env, value, headers):
    """
    Gửi một message tới Kafka topic.

    :param topic: Tên Kafka topic
    :param value: Dữ liệu gửi (dict hoặc chuỗi)
    :param key: Khóa phân phối (string), optional
    :param headers: Dictionary headers (key: str, value: str), optional
    :param bootstrap_servers: Địa chỉ Kafka server
    """

    # Tạo KafkaProducer (kết nối Kafka)
    print([env["ir.config_parameter"].sudo().get_param("vnfield_cs.kafka_server")])
    producer = KafkaProducer(
        bootstrap_servers=[
            env["ir.config_parameter"].sudo().get_param("vnfield_cs.kafka_server")
        ],
        value_serializer=lambda v: (
            json.dumps(v).encode("utf-8")
            if isinstance(v, dict)
            else str(v).encode("utf-8")
        ),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )

# producer = KafkaProducer(
#     bootstrap_servers=[
#         "192.168.56.117:9092"
#     ],
#     value_serializer=lambda v: (
#         json.dumps(v).encode("utf-8")
#         if isinstance(v, dict)
#         else str(v).encode("utf-8")
#     ),
# )

    # Chuyển headers dict -> list of tuples (bytes)
    print([(k, v) for k, v in (headers or {}).items()])
    header_list = [(k, v) for k, v in (headers or {}).items()]
    # Gửi message
    producer.send("odoo-integration", value=value, headers=header_list)
    producer.flush()  # Đảm bảo message được gửi đi
    producer.close()  # Đóng kết nối sau khi gửi (nếu chỉ dùng 1 lần)
