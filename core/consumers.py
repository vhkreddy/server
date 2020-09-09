from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = 'event'
        self.room_group_name = self.room_name + "_notification"
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        print("#######CONNECTED############")

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        print("DISCONNECED CODE: ",code)

    def receive(self, text_data=None, bytes_data=None):
        print(" MESSAGE RECEIVED")
        data = json.loads(text_data)
        message = data['message']
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": 'send_message_to_frontend',
                "message": message
            }
        )
        
    def send_message_to_frontend(self,event):
        print("EVENT TRIGERED")
        message = event['message']
        command = event['command']
        self.send(text_data=json.dumps({
            'message': message,
            'command': command
        })) 




