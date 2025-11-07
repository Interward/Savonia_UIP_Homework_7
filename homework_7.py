import flet as ft
import os
from flet.security import encrypt, decrypt

class EncryptedChat:
    def __init__(self, page):
        self.page = page
        self.page.title = "Encrypted Chat"
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        
        self.secret_key = None
        self.username = None
        self.current_topic = "general"
        # logs
        self.topic_messages = {
            "general": [],
            "flet": [], 
            "fun stuff": []
        }
        
        self.entry_ui()

    # first UI
    def entry_ui(self):
        self.username_field = ft.TextField(label="Username", width=200)
        self.passphrase_field = ft.TextField(label="Passphrase", password=True, width=200)
        
        self.setup_view = ft.Column(
            [
                ft.Text("Encrypted Chat", size=20),
                self.username_field,
                self.passphrase_field,
                ft.ElevatedButton("Join Chat", on_click=self.entry),
            ], 
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.page.clean()
        self.page.add(self.setup_view)
    
    # chat UI
    def chat_ui(self):
        self.chat_log = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=300, width=400)
        self.message_field = ft.TextField(label="Message", expand=True)
        self.topics = ft.Dropdown(
            value="general",
            options=[
                ft.dropdown.Option("general"),
                ft.dropdown.Option("flet"),
                ft.dropdown.Option("fun stuff"),
            ],
            width=100,
            on_change=self.topic_changed
        )
        
        self.chat_view = ft.Column([
            ft.Row([
                ft.Text(f"User: {self.username}"),
                ft.Text(" | "),
                self.topics,
            ]),
            ft.Container(
                content=self.chat_log,
                border=ft.border.all(1),
                padding=10
            ),
            ft.Row([
                self.message_field,
                ft.ElevatedButton("Send", on_click=self.send_message),
            ]),
        ])
        self.page.clean()
        self.page.add(self.chat_view)
        
        # load messages for current topic
        self.retrieve_messages()
        
        # subscribe to a topic
        self.page.pubsub.subscribe(self.on_message)
    
    def entry(self, e):
        if not self.username_field.value or not self.passphrase_field.value:
            return
        
        self.username = self.username_field.value
        self.secret_key = self.passphrase_field.value
        self.chat_ui()
    
    # method to retrieve message logs for each topic
    def retrieve_messages(self):
        self.chat_log.controls.clear()
        
        for encrypted_data in self.topic_messages[self.current_topic]:
            decrypted_text = decrypt(encrypted_data, self.secret_key)
            message_data = eval(decrypted_text)
            
            self.chat_log.controls.append(
                ft.Text(f"{message_data['user']}: {message_data['text']}")
            )
        
        self.page.update()
    
    # when topic changes, load messages for that topic
    def topic_changed(self, e):
        self.current_topic = self.topics.value
        self.retrieve_messages()
    
    def send_message(self, e):
        # manage empty message
        if not self.message_field.value.strip():
            return
        
        # message data
        message_data = {
            "user": self.username,
            "text": self.message_field.value.strip(),
            "topic": self.current_topic
        }
        
        # encrypt message
        encrypted_data = encrypt(str(message_data), self.secret_key)
        
        # store the message in topic message history
        self.topic_messages[self.current_topic].append(encrypted_data)
        self.chat_log.controls.append(
            ft.Text(f"{message_data['user']}: {message_data['text']}")
        )

        # send encrypted message to all users
        self.page.pubsub.send_all({
            "encrypted": encrypted_data,
            "topic": self.current_topic
        })
        
        # clear typing field
        self.message_field.value = ""
        self.page.update()

    
    def on_message(self, message):
        # process messages for current topic
        if message["topic"] != self.current_topic:
            return
        
        if message["encrypted"] not in self.topic_messages[self.current_topic]:
            # store received message
            self.topic_messages[self.current_topic].append(message["encrypted"])
            
            # decrypt data
            decrypted_text = decrypt(message["encrypted"], self.secret_key)
            message_data = eval(decrypted_text)  # convert string back to dict
            
            # add message to chat log
            self.chat_log.controls.append(
                ft.Text(f"{message_data['user']}: {message_data['text']}")
            )
            
            self.page.update()

def main(page: ft.Page):
    EncryptedChat(page)

ft.app(target=main, view=ft.AppView.WEB_BROWSER)