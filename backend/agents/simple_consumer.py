from datetime import timezone

"""
Simple WebSocket Consumer for testing connections
"""

import json
import uuid
from datetime import datetime

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

# Get the custom user model
User = get_user_model()

class SimpleSessionConsumer(AsyncWebsocketConsumer):
    """Simple WebSocket consumer for testing session connections"""
    
    async def connect(self):
        try:
            self.session_id = self.scope['url_route']['kwargs']['session_id']
            self.session_group_name = f'session_{self.session_id}'
            
            print(f"DEBUG: WebSocket connection attempt for session: {self.session_id}")
            print(f"DEBUG: Group name: {self.session_group_name}")
            print(f"DEBUG: Channel name: {self.channel_name}")
            print(f"DEBUG: Scope keys: {list(self.scope.keys())}")
            
            # Join session group
            await self.channel_layer.group_add(
                self.session_group_name,
                self.channel_name
            )
            
            await self.accept()
            print(f"DEBUG: WebSocket connection accepted for session: {self.session_id}")
            
            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'session_id': self.session_id,
                'message': 'Connected to session (Simple Consumer)',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: Failed to connect WebSocket: {e}")
            import traceback
            traceback.print_exc()
            await self.close(code=1011)  # Internal server error
    
    async def disconnect(self, close_code):
        print(f"DEBUG: WebSocket disconnection for session: {self.session_id}, code: {close_code}")
        
        # Leave session group
        await self.channel_layer.group_discard(
            self.session_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            print(f"DEBUG: Received WebSocket message: {data}")
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
                print("DEBUG: Sent pong response")
            else:
                await self.send_error(f'Unknown message type: {message_type}')
                
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON format')
        except Exception as e:  # noqa: BLE001
            print(f"DEBUG: Error in WebSocket receive: {e}")
            await self.send_error(f'Processing error: {e!s}')
    
    async def handle_chat_message(self, data):
        """Handle incoming chat message"""
        content = data.get('content', '')
        message_type = data.get('message_type', 'text')
        
        print(f"DEBUG: Processing chat message: '{content}'")
        
        if not content and message_type == 'text':
            await self.send_error('Message content is required')
            return
        
        # Echo the message back to the group
        message_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message_id,
                    'content': content,
                    'message_type': message_type,
                    'sender': 'Anonymous',
                    'timestamp': timestamp
                }
            }
        )
        
        print(f"DEBUG: Message echoed to group: {self.session_group_name}")
        
        # Send a simple agent response after a brief delay
        response_content = f"Hello! I received your message: '{content}'. This is a test response from the simple consumer."
        
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'agent_response',
                'response': {
                    'content': response_content,
                    'orchestrator': 'Test Agent',
                    'agent_id': 'test-agent-123'
                },
                'original_message_id': message_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
        
        print(f"DEBUG: Agent response sent to group: {self.session_group_name}")
    
    # WebSocket message handlers
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        print(f"DEBUG: Sending chat message to WebSocket: {event['message']}")
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def agent_response(self, event):
        """Send agent response to WebSocket"""
        print(f"DEBUG: Sending agent response to WebSocket: {event['response']}")
        await self.send(text_data=json.dumps({
            'type': 'agent_response',
            'response': event['response'],
            'original_message_id': event.get('original_message_id'),
            'timestamp': event.get('timestamp')
        }))
    
    async def send_error(self, error_message):
        """Send error message"""
        print(f"DEBUG: Sending error: {error_message}")
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message
        }))