# -*- coding: utf-8 -*-
#############################################################################
#
#    VN Field Integration System 
#    Kafka Utility Class để produce và consume messages
#
#############################################################################

import json
import logging
from confluent_kafka import Producer, Consumer, KafkaError
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# ═             📡 KAFKA UTILITY CLASS                     ═
# ═══════════════════════════════════════════════════════════

class KafkaUtil(models.TransientModel):
    _name = 'vnfield.kafka.util'
    _description = 'Kafka Utility for Producer and Consumer Operations'

    @api.model
    def get_bootstrap_servers(self):
        """
        📊 Get Bootstrap Server từ system parameters
        """
        return self.env['ir.config_parameter'].sudo().get_param(
            'vnfield.kafka.bootstrap_servers', 
            default='localhost:9092'
        )
    
    @api.model
    def get_consumer_group_id(self):
        """
        🎯 Get Consumer Group ID từ external_id của default contractor
        """
        try:
            # ─────────────── 🔍 FIND DEFAULT CONTRACTOR ───────────────
            default_contractor = self.env['vnfield.contractor'].search([
                ('is_default_contractor', '=', True)
            ], limit=1)
            
            if default_contractor and default_contractor.external_id:
                # ─────────────── 🏗️ BUILD GROUP ID WITH EXTERNAL_ID ───────────────
                base_group = self.env['ir.config_parameter'].sudo().get_param(
                    'vnfield.kafka.consumer_group_id', 
                    default='vnfield_is_consumer'
                )
                return f"{base_group}_{default_contractor.external_id}"
            else:
                # ─────────────── ⚠️ FALLBACK TO SYSTEM PARAMETER ───────────────
                _logger.warning('⚠️ No default contractor with external_id found, using system parameter')
                return self.env['ir.config_parameter'].sudo().get_param(
                    'vnfield.kafka.consumer_group_id', 
                    default='vnfield_is_consumer'
                )
                
        except Exception as e:
            _logger.error(f'❌ Error getting consumer group ID: {str(e)}')
            # ─────────────── 🛡️ SAFE FALLBACK ───────────────
            return self.env['ir.config_parameter'].sudo().get_param(
                'vnfield.kafka.consumer_group_id', 
                default='vnfield_is_consumer'
            )
    
    @api.model
    def get_default_contractor_external_id(self):
        """
        🏢 Get external_id của default contractor
        
        Returns:
            int|None: External ID của default contractor hoặc None nếu không tìm thấy
        """
        try:
            default_contractor = self.env['vnfield.contractor'].search([
                ('is_default_contractor', '=', True)
            ], limit=1)
            
            if default_contractor and default_contractor.external_id:
                return default_contractor.external_id
            else:
                _logger.warning('⚠️ No default contractor with external_id found')
                return None
                
        except Exception as e:
            _logger.error(f'❌ Error getting default contractor external_id: {str(e)}')
            return None
    
    @api.model
    def get_consumer_timeout(self):
        """
        ⏱️ Get Consumer Timeout từ system parameters
        """
        return float(self.env['ir.config_parameter'].sudo().get_param(
            'vnfield.kafka.consumer_timeout', 
            default='5.0'
        ))
    
    @api.model
    def get_max_messages(self):
        """
        📊 Get Max Messages Per Consumption từ system parameters
        """
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'vnfield.kafka.max_messages', 
            default='10'
        ))
    
    @api.model
    def get_producer_retries(self):
        """
        🔄 Get Producer Retries từ system parameters
        """
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'vnfield.kafka.producer_retries', 
            default='3'
        ))
    
    @api.model
    def get_topic_prefix(self):
        """
        📡 Get Topic Prefix từ system parameters
        """
        return self.env['ir.config_parameter'].sudo().get_param(
            'vnfield.kafka.topic_prefix', 
            default='vnfield_is'
        )
    
    @api.model
    def build_topic_name(self, base_name, include_contractor_id=False):
        """
        🏗️ Build topic name với prefix từ system parameters
        
        Args:
            base_name (str): Base topic name
            include_contractor_id (bool): Có include contractor external_id trong topic name không
            
        Returns:
            str: Formatted topic name với prefix (và contractor ID nếu được yêu cầu)
        """
        prefix = self.get_topic_prefix()
        
        if include_contractor_id:
            contractor_external_id = self.get_default_contractor_external_id()
            if contractor_external_id:
                return f"{prefix}.{contractor_external_id}.{base_name}"
            else:
                _logger.warning('⚠️ No contractor external_id available, using prefix only')
                return f"{prefix}.{base_name}"
        else:
            return f"{prefix}.{base_name}"
    
    @api.model
    def validate_topics(self, topics):
        """
        ✅ Validate topic names và ensure chúng là list
        
        Args:
            topics (str|list): Topic name hoặc list của topic names
            
        Returns:
            list: Validated list của topic names
        """
        if isinstance(topics, str):
            return [topics]
        elif isinstance(topics, list):
            return topics
        else:
            raise ValueError("Topics phải là string hoặc list of strings")
    
    @api.model
    def produce(self, topic, message, headers=None):
        """
        📤 Produce message đến Kafka topic
        
        Args:
            topic (str): Kafka topic name
            message (dict): Message payload  
            headers (dict): Optional message headers
        
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            # ─────────────── 🔧 PRODUCER CONFIGURATION ───────────────
            contractor_external_id = self.get_default_contractor_external_id()
            client_id = f'{self.get_topic_prefix()}_producer'
            if contractor_external_id:
                client_id = f'{self.get_topic_prefix()}_{contractor_external_id}_producer'
            
            producer_config = {
                'bootstrap.servers': self.get_bootstrap_servers(),
                'client.id': client_id,
                'acks': 'all',
                'retries': self.get_producer_retries(),
                'retry.backoff.ms': 100,
                'delivery.timeout.ms': 30000,
                'request.timeout.ms': 25000
            }
            
            producer = Producer(producer_config)
            
            # ─────────────── 📝 MESSAGE PREPARATION ───────────────
            message_value = json.dumps(message, ensure_ascii=False, default=str)
            
            # Convert headers to list of tuples với UTF-8 encoding
            kafka_headers = []
            if headers:
                for key, value in headers.items():
                    kafka_headers.append((key, str(value).encode('utf-8')))
            
            # ─────────────── 📡 SEND MESSAGE ───────────────
            def delivery_report(err, msg):
                """📋 Callback for delivery reports"""
                if err is not None:
                    _logger.error(f'❌ Message delivery failed: {err}')
                else:
                    _logger.info(f'✅ Message delivered to {msg.topic()} [{msg.partition()}]')
            
            producer.produce(
                topic=topic,
                value=message_value.encode('utf-8'),
                headers=kafka_headers,
                callback=delivery_report
            )
            
            # ─────────────── ⏳ WAIT FOR DELIVERY ───────────────
            producer.flush(timeout=10)
            
            _logger.info(f'🚀 Message sent to topic: {topic}')
            return True
            
        except Exception as e:
            _logger.error(f'❌ Kafka produce error: {str(e)}')
            return False
    
    @api.model 
    def consume(self, topics, group_id=None, timeout=None, max_messages=None):
        """
        📥 Consume messages từ Kafka topics
        
        Args:
            topics (list): List của topic names để consume
            group_id (str): Consumer group ID (optional, sử dụng system parameter nếu None)
            timeout (float): Timeout seconds cho polling (optional, sử dụng system parameter nếu None)
            max_messages (int): Maximum số messages để consume (optional, sử dụng system parameter nếu None)
        
        Returns:
            list: List của consumed messages
        """
        messages = []
        
        # ─────────────── 🔧 PARAMETER RESOLUTION ───────────────
        if group_id is None:
            group_id = self.get_consumer_group_id()
        if timeout is None:
            timeout = self.get_consumer_timeout()
        if max_messages is None:
            max_messages = self.get_max_messages()
        
        try:
            # ─────────────── 🔧 CONSUMER CONFIGURATION ───────────────
            contractor_external_id = self.get_default_contractor_external_id()
            client_id = f'{self.get_topic_prefix()}_consumer'
            if contractor_external_id:
                client_id = f'{self.get_topic_prefix()}_{contractor_external_id}_consumer'
            
            consumer_config = {
                'bootstrap.servers': self.get_bootstrap_servers(),
                'group.id': group_id,
                'client.id': client_id,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': True,
                'auto.commit.interval.ms': 1000,
                'session.timeout.ms': 30000,
                'heartbeat.interval.ms': 10000
            }
            
            consumer = Consumer(consumer_config)
            
            # ─────────────── 📡 SUBSCRIBE TO TOPICS ───────────────
            consumer.subscribe(topics)
            _logger.info(f'🎯 Subscribed to topics: {topics} with group_id: {group_id}')
            _logger.info(f'🏢 Using contractor external_id: {contractor_external_id}' if contractor_external_id else '⚠️ No contractor external_id found')
            
            # ─────────────── 📥 CONSUME MESSAGES ───────────────
            message_count = 0
            while message_count < max_messages:
                msg = consumer.poll(timeout=timeout)
                
                if msg is None:
                    _logger.info('⏱️ No more messages, timeout reached')
                    break
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        _logger.info(f'📄 End of partition reached: {msg.topic()} [{msg.partition()}]')
                        continue
                    else:
                        _logger.error(f'❌ Consumer error: {msg.error()}')
                        break
                
                # ─────────────── 🔄 PROCESS MESSAGE ───────────────
                try:
                    message_data = json.loads(msg.value().decode('utf-8'))
                    
                    # Extract headers
                    headers = {}
                    if msg.headers():
                        for key, value in msg.headers():
                            headers[key] = value.decode('utf-8') if value else None
                    
                    processed_message = {
                        'topic': msg.topic(),
                        'partition': msg.partition(),
                        'offset': msg.offset(),
                        'timestamp': msg.timestamp(),
                        'headers': headers,
                        'payload': message_data
                    }
                    
                    messages.append(processed_message)
                    message_count += 1
                    
                    _logger.info(f'📨 Consumed message from {msg.topic()}: {message_data}')
                    
                except json.JSONDecodeError as e:
                    _logger.error(f'❌ JSON decode error: {str(e)}')
                    continue
                    
        except Exception as e:
            _logger.error(f'❌ Kafka consume error: {str(e)}')
        
        finally:
            # ─────────────── 🔚 CLEANUP ───────────────
            try:
                consumer.close()
                _logger.info('🔚 Consumer closed successfully')
            except:
                pass
        
        _logger.info(f'📊 Total consumed messages: {len(messages)}')
        return messages
    
    @api.model
    def test_connection(self):
        """
        🔍 Test Kafka connection để kiểm tra server availability
        
        Returns:
            dict: Connection test results
        """
        result = {
            'success': False,
            'message': '',
            'bootstrap_servers': self.get_bootstrap_servers(),
            'error_details': None
        }
        
        try:
            # ─────────────── 🧪 TEST PRODUCER CONNECTION ───────────────
            contractor_external_id = self.get_default_contractor_external_id()
            client_id = f'{self.get_topic_prefix()}_test_producer'
            if contractor_external_id:
                client_id = f'{self.get_topic_prefix()}_{contractor_external_id}_test_producer'
            
            producer_config = {
                'bootstrap.servers': self.get_bootstrap_servers(),
                'client.id': client_id,
                'socket.timeout.ms': 5000,
                'api.version.request.timeout.ms': 5000
            }
            
            producer = Producer(producer_config)
            
            # Test bằng cách request metadata
            metadata = producer.list_topics(timeout=5)
            
            if metadata and metadata.topics:
                result['success'] = True
                result['message'] = f'✅ Kết nối thành công đến Kafka server: {self.get_bootstrap_servers()}'
                result['available_topics'] = list(metadata.topics.keys())
                _logger.info(f"🎯 Kafka connection test successful: {len(metadata.topics)} topics available")
            else:
                result['message'] = '⚠️ Kết nối thành công nhưng không có topics nào'
                
        except Exception as e:
            result['message'] = f'❌ Không thể kết nối đến Kafka server: {str(e)}'
            result['error_details'] = str(e)
            _logger.error(f"❌ Kafka connection test failed: {str(e)}")
            
        return result

# ═══════════════════════════════════════════════════════════
# ═           🏗️ SYMBOL DEPENDENCIES ANALYSIS              ═
# ═══════════════════════════════════════════════════════════

"""
📋 DEPENDENCIES ĐƯỢC SỬ DỤNG TRONG FILE NÀY:

🔗 PYTHON DEPENDENCIES:
- json: JSON serialization/deserialization cho message payload
- logging: Error và info logging cho debugging và monitoring
- confluent_kafka.Producer: Kafka message producer với delivery reports
- confluent_kafka.Consumer: Kafka message consumer với auto-commit
- confluent_kafka.KafkaError: Error handling cho connection và message errors

🔗 ODOO DEPENDENCIES:
- odoo.models.TransientModel: Base class cho utility model không lưu vào database
- odoo.fields: Field definitions (reserved cho future enhancements)
- odoo.api: API decorators (@api.model) cho static method calls
- self.env['ir.config_parameter']: System parameters access cho configuration

🔗 KAFKA INTEGRATION DEPENDENCIES:
- Bootstrap servers: Connection configuration đến Kafka cluster từ system parameters
- Producer configuration: Message delivery settings với acks=all và retries
- Consumer configuration: Message consumption settings với auto-commit
- Topic management: Subscribe và produce to topics với naming conventions
- Message formatting: JSON payload với UTF-8 encoding và custom headers
- Connection testing: Metadata requests để validate server availability

🔗 SYSTEM PARAMETERS DEPENDENCIES:
- vnfield.kafka.bootstrap_servers: Kafka cluster connection string
- vnfield.kafka.consumer_group_id: Consumer group identifier cho parallel processing
- vnfield.kafka.consumer_timeout: Polling timeout configuration
- vnfield.kafka.max_messages: Batch size control cho consumption
- vnfield.kafka.producer_retries: Error recovery configuration
- vnfield.kafka.topic_prefix: Topic naming convention để organize messages

🔗 VNFIELD BASE DEPENDENCIES:
- vnfield.contractor: Default contractor model với is_default_contractor field
- external_id: External system mapping field cho contractor identification
- is_default_contractor: Boolean field để identify default contractor cho site này

🔗 BUSINESS LOGIC DEPENDENCIES:
- IS-CS communication: Message exchange giữa Integration và Contractor Systems
- Contractor isolation: Consumer groups isolated by contractor external_id
- Change propagation: Kafka messages để sync data changes across sites
- Multi-site architecture: Distributed contractor management coordination với unique IDs
- Error resilience: Robust error management với retry mechanisms và logging
- Configuration flexibility: System parameter driven configuration management
- Connection validation: Health check capabilities cho Kafka infrastructure
- Topic organization: Contractor-specific topic naming cho message routing
"""
