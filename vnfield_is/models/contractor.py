# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import logging

_logger = logging.getLogger(__name__)

class Contractor(models.Model):
    _inherit = "vnfield.contractor"
    
    # Thêm fields cần thiết cho Kafka integration
    external_id = fields.Integer(
        string="External ID",
        help="ID của contractor trên external systems",
        copy=False,
        readonly=True
    )
    
    is_default_contractor = fields.Boolean(
        string="Default Contractor",
        help="Đánh dấu contractor mặc định cho hệ thống IS",
        default=False,
        copy=False
    )
    
    is_leader = fields.Boolean(
        string="Leader Contractor",
        help="Đánh dấu contractor có quyền registry contractor mới",
        default=False,
        copy=False
    )
    
    # ─────────────── 🔐 PERMISSION METHODS ───────────────
    
    def _check_leader_permission(self):
        """
        🔒 Check xem contractor hiện tại có phải leader không
        """
        if not self.is_leader:
            raise exceptions.AccessError("❌ Chỉ leader contractor mới có quyền thực hiện hành động này")
        return True
    
    # ─────────────── 📝 CONTRACTOR REGISTRY METHODS ───────────────
    
    @api.model
    def registry_contractor(self, contractor_data, leader_contractor_id=None):
        """
        📋 Registry contractor mới - chỉ leader có quyền gọi
        Method này có thể được gọi qua Odoo JSON-RPC External API
        
        Cách gọi qua JSON-RPC:
        POST /jsonrpc
        {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    "database_name",
                    uid,
                    "password",
                    "vnfield.contractor",
                    "registry_contractor",
                    [{
                        "name": "ABC Construction",
                        "code": "ABC001",
                        "email": "contact@abc.com"
                    }],
                    {"leader_contractor_id": 1}
                ]
            },
            "id": 1
        }
        
        Args:
            contractor_data (dict): Dữ liệu contractor mới
                - name (str): Tên contractor (bắt buộc)
                - code (str): Mã contractor
                - email (str): Email
                - phone (str): Số điện thoại
                - address (str): Địa chỉ
                - ... (các fields khác)
            leader_contractor_id (int): ID của leader contractor thực hiện registration
        
        Returns:
            dict: Kết quả registration
                - success (bool): Thành công hay không
                - contractor_id (int): ID của contractor mới
                - message (str): Thông báo
                - error_details (str): Chi tiết lỗi nếu có
        """
        result = {
            'success': False,
            'contractor_id': None,
            'message': '',
            'error_details': None
        }
        
        try:
            # ─────────────── 🔒 CHECK LEADER PERMISSION ───────────────
            if leader_contractor_id:
                leader_contractor = self.browse(leader_contractor_id)
                if not leader_contractor.exists():
                    raise exceptions.AccessError("❌ Leader contractor không tồn tại")
                if not leader_contractor.is_leader:
                    raise exceptions.AccessError("❌ Chỉ leader contractor mới có quyền thực hiện hành động này")
            else:
                # Fallback: check xem có leader nào trong system không
                leader_contractors = self.search([('is_leader', '=', True)], limit=1)
                if not leader_contractors:
                    raise exceptions.AccessError("❌ Không có leader contractor nào trong hệ thống")
            
            # ─────────────── ✅ VALIDATE INPUT DATA ───────────────
            if not contractor_data or not isinstance(contractor_data, dict):
                raise ValueError("❌ Dữ liệu contractor không hợp lệ")
            
            if not contractor_data.get('name'):
                raise ValueError("❌ Tên contractor là bắt buộc")
            
            # ─────────────── 🏗️ CREATE NEW CONTRACTOR ───────────────
            new_contractor_vals = {
                'name': contractor_data.get('name'),
                'code': contractor_data.get('code', False),
                'email': contractor_data.get('email', False),
                'phone': contractor_data.get('phone', False),
                'address': contractor_data.get('address', False),
                'tax_code': contractor_data.get('tax_code', False),
                'license_number': contractor_data.get('license_number', False),
                'contact_person': contractor_data.get('contact_person', False),
                'bank_account': contractor_data.get('bank_account', False),
                'is_leader': False,  # Contractor mới không phải leader
                'is_default_contractor': False,  # Contractor mới không phải default
                'active': True
            }
            
            new_contractor = self.create(new_contractor_vals)
            
            # ─────────────── 📤 SEND KAFKA MESSAGE TO EXISTING CONTRACTORS ───────────────
            try:
                self._send_contractor_registry_notification(new_contractor)
            except Exception as kafka_error:
                _logger.warning(f"⚠️ Kafka notification failed but contractor created: {str(kafka_error)}")
            
            # ─────────────── ✅ SUCCESS RESPONSE ───────────────
            result.update({
                'success': True,
                'contractor_id': new_contractor.id,
                'message': f'✅ Contractor "{new_contractor.name}" đã được đăng ký thành công với ID: {new_contractor.id}',
            })
            
            _logger.info(f"🎉 New contractor registered: {new_contractor.name} (ID: {new_contractor.id})")
            
        except exceptions.AccessError as e:
            result.update({
                'message': str(e),
                'error_details': 'Access permission denied'
            })
            _logger.error(f"🔒 Permission denied for contractor registry: {str(e)}")
            
        except ValueError as e:
            result.update({
                'message': str(e),
                'error_details': 'Invalid input data'
            })
            _logger.error(f"❌ Invalid data for contractor registry: {str(e)}")
            
        except Exception as e:
            result.update({
                'message': f'❌ Lỗi không xác định: {str(e)}',
                'error_details': str(e)
            })
            _logger.error(f"❌ Unexpected error in contractor registry: {str(e)}")
            
        return result
    
    @api.model
    def check_leader_permission(self, contractor_id):
        """
        🔍 Check xem contractor có phải leader không
        Có thể gọi qua JSON-RPC External API
        
        Args:
            contractor_id (int): ID của contractor cần check
            
        Returns:
            dict: Permission check result
        """
        try:
            contractor = self.browse(contractor_id)
            
            result = {
                'success': True,
                'is_leader': contractor.is_leader if contractor.exists() else False,
                'contractor_name': contractor.name if contractor.exists() else '',
                'contractor_code': contractor.code if contractor.exists() else '',
                'message': f'✅ Permission check completed for contractor ID: {contractor_id}'
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'is_leader': False,
                'contractor_name': '',
                'contractor_code': '',
                'message': f'❌ Error checking leader permission: {str(e)}',
                'error_details': str(e)
            }
    
    @api.model
    def list_leader_contractors(self):
        """
        📋 Get list of leader contractors
        Có thể gọi qua JSON-RPC External API
        
        Returns:
            dict: List of leader contractors
        """
        try:
            leader_contractors = self.search([
                ('is_leader', '=', True),
                ('active', '=', True)
            ])
            
            leaders_data = []
            for leader in leader_contractors:
                leaders_data.append({
                    'id': leader.id,
                    'name': leader.name,
                    'code': leader.code or '',
                    'email': leader.email or '',
                    'external_id': leader.external_id or 0,
                    'is_default': leader.is_default_contractor
                })
            
            result = {
                'success': True,
                'leaders': leaders_data,
                'count': len(leaders_data),
                'message': f'✅ Found {len(leaders_data)} leader contractors'
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'leaders': [],
                'count': 0,
                'message': f'❌ Error listing leader contractors: {str(e)}',
                'error_details': str(e)
            }
    
    def _send_contractor_registry_notification(self, new_contractor):
        """
        📤 Send Kafka notification về contractor mới đến các contractor hiện có
        
        Args:
            new_contractor: Contractor record vừa được tạo
        """
        try:
            # ─────────────── 🔍 GET EXISTING CONTRACTORS ───────────────
            existing_contractors = self.search([
                ('id', '!=', new_contractor.id),
                ('active', '=', True),
                ('external_id', '!=', False)  # Chỉ gửi đến contractors có external_id
            ])
            
            if not existing_contractors:
                _logger.info("ℹ️ No existing contractors to notify")
                return
            
            # ─────────────── 📝 PREPARE MESSAGE PAYLOAD ───────────────
            message_payload = {
                'event_type': 'contractor_registry',
                'contractor_data': {
                    'id': new_contractor.id,
                    'name': new_contractor.name,
                    'code': new_contractor.code or '',
                    'email': new_contractor.email or '',
                    'phone': new_contractor.phone or '',
                    'address': new_contractor.address or '',
                    'tax_code': new_contractor.tax_code or '',
                    'license_number': new_contractor.license_number or '',
                    'contact_person': new_contractor.contact_person or '',
                    'bank_account': new_contractor.bank_account or '',
                    'created_date': new_contractor.create_date.isoformat() if new_contractor.create_date else '',
                    'is_active': new_contractor.active
                },
                'timestamp': fields.Datetime.now().isoformat(),
                'source_system': 'vnfield_is'
            }
            
            # ─────────────── 📡 GET KAFKA UTIL ───────────────
            kafka_util = self.env['vnfield.kafka.util']
            
            # ─────────────── 📤 SEND TO EACH EXISTING CONTRACTOR ───────────────
            success_count = 0
            for contractor in existing_contractors:
                try:
                    # Build topic name với contractor-specific naming
                    topic = kafka_util.build_topic_name('contractor_registry', include_contractor_id=False)
                    
                    # Prepare headers với destination
                    headers = {
                        'destination': str(contractor.external_id),
                        'event_type': 'contractor_registry',
                        'source_contractor_id': str(new_contractor.id),
                        'timestamp': fields.Datetime.now().isoformat()
                    }
                    
                    # Send message
                    success = kafka_util.produce(
                        topic=topic,
                        message=message_payload,
                        headers=headers
                    )
                    
                    if success:
                        success_count += 1
                        _logger.info(f"📤 Registry notification sent to contractor {contractor.name} (external_id: {contractor.external_id})")
                    else:
                        _logger.error(f"❌ Failed to send notification to contractor {contractor.name}")
                        
                except Exception as e:
                    _logger.error(f"❌ Error sending notification to contractor {contractor.name}: {str(e)}")
            
            _logger.info(f"📊 Registry notifications sent: {success_count}/{len(existing_contractors)} contractors")
            
        except Exception as e:
            _logger.error(f"❌ Error in contractor registry notification: {str(e)}")
            raise

# ═══════════════════════════════════════════════════════════
# ═           📋 ODOO JSON-RPC EXTERNAL API USAGE          ═
# ═══════════════════════════════════════════════════════════

"""
📋 CÁCH SỬ DỤNG ODOO JSON-RPC EXTERNAL API:

🔗 1. CONTRACTOR REGISTRY:
POST http://localhost:8069/jsonrpc
Content-Type: application/json

{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "object",
        "method": "execute_kw",
        "args": [
            "your_database_name",
            uid,
            "your_password",
            "vnfield.contractor",
            "registry_contractor",
            [{
                "name": "ABC Construction Company",
                "code": "ABC001",
                "email": "contact@abc-construction.com",
                "phone": "+84-123-456-789",
                "address": "123 Main St, Hanoi, Vietnam",
                "tax_code": "0123456789",
                "license_number": "LIC123456",
                "contact_person": "Mr. John Doe",
                "bank_account": "123456789"
            }],
            {"leader_contractor_id": 1}
        ]
    },
    "id": 1
}

🔗 2. CHECK LEADER PERMISSION:
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "object",
        "method": "execute_kw",
        "args": [
            "your_database_name",
            uid,
            "your_password",
            "vnfield.contractor",
            "check_leader_permission",
            [1]
        ]
    },
    "id": 2
}

🔗 3. LIST LEADER CONTRACTORS:
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "object",
        "method": "execute_kw",
        "args": [
            "your_database_name",
            uid,
            "your_password",
            "vnfield.contractor",
            "list_leader_contractors",
            []
        ]
    },
    "id": 3
}

📋 AUTHENTICATION STEPS:
1. First, authenticate to get uid:
POST http://localhost:8069/jsonrpc
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "common",
        "method": "authenticate",
        "args": ["your_database_name", "your_username", "your_password", {}]
    },
    "id": 1
}

2. Use returned uid in subsequent calls
"""