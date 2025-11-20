import json
import time
from uuid import uuid4

class Message:
    def __init__(self, msg_type, sender, content, recipient=None, group_id=None):
        self.id = str(uuid4())
        self.timestamp = time.time()
        self.msg_type = msg_type
        self.sender = sender
        self.content = content
        self.recipient = recipient
        self.group_id = group_id
    
    def to_json(self):
        return json.dumps({
            'id': self.id,
            'timestamp': self.timestamp,
            'type': self.msg_type,
            'sender': self.sender,
            'content': self.content,
            'recipient': self.recipient,
            'group_id': self.group_id
        })
    
    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        msg = cls(
            data['type'],
            data['sender'],
            data['content'],
            data.get('recipient'),
            data.get('group_id')
        )
        msg.id = data['id']
        msg.timestamp = data['timestamp']
        return msg