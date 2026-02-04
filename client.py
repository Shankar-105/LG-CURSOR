import asyncio
import websockets
import json
import ssl
import os
from dotenv import set_key, find_dotenv
from config import settings

class WebOSClient:

    def __init__(self, tv_ip, client_key_file=settings.client_key):
        self.tv_ip = tv_ip
        self.uri = f"wss://{tv_ip}:3001"
        self.client_key = client_key_file
        self.ws = None
        self.request_id = 0  # Counter for unique IDs
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def save_client_key(self,new_key: str):
        """Update or add CLIENT_KEY to .env using python-dotenv"""
        dotenv_path = find_dotenv(usecwd=True)  # Finds .env in current dir or parents
        if not dotenv_path:
            dotenv_path = os.path.join(os.getcwd(), ".env")
            # Create empty .env if missing
            open(dotenv_path, 'a').close()

        # set_key returns (success, key, old_value)
        success, key, old = set_key(
            dotenv_path=dotenv_path,
            key_to_set="CLIENT_KEY",
            value_to_set=new_key,
            quote_mode="always",   
            export=False
        )

        if success:
            print(f"🎉 Updated CLIENT_KEY in .env → {new_key}")
            self.client_key = new_key
            settings.client_key = new_key  # if you want settings obj updated
        else:
            print("Failed to update .env – check permissions or path")

    async def connect(self):
        self.ws = await websockets.connect(self.uri, ping_interval=20, ping_timeout=20, ssl=self.ssl_context)
        print(f"Connected to {self.uri}!")

        # Register (with key if we have it)
        register_msg = {
                    "type": "register",
                    "id": "register_0",
                    "payload": {
                    "forcePairing": False,
                    "pairingType": "PROMPT",
                    "manifest": {
                        "manifestVersion": 1,
                        "appVersion": "1.1",
                        "signed": {
                            "created": "20140509",
                            "appId": "com.lge.test",
                            "vendorId": "com.lge",
                            "localizedAppNames": {
                                "": "LG Remote App",
                                "ko-KR": "LG 리모컨 앱",
                                "zxx-XX": "LG Rэмотэ Aпп"
                            },
                            "localizedVendorNames": {"": "LG Electronics"},
                            "permissions": [
                                "TEST_SECURE",
                                "CONTROL_INPUT_TEXT",
                                "CONTROL_MOUSE_AND_KEYBOARD",
                                "READ_INSTALLED_APPS",
                                "READ_LGE_SDX",
                                "READ_NOTIFICATIONS",
                                "SEARCH",
                                "WRITE_SETTINGS",
                                "WRITE_NOTIFICATION_ALERT",
                                "CONTROL_POWER",
                                "READ_CURRENT_CHANNEL",
                                "READ_RUNNING_APPS",
                                "READ_UPDATE_INFO",
                                "UPDATE_FROM_REMOTE_APP",
                                "READ_LGE_TV_INPUT_EVENTS",
                                "READ_TV_CURRENT_TIME",
                                "CONTROL_AUDIO"  # ← Add here if missing!
                            ],
                            "serial": "2f930e2d2cfe083771f68e4fe7bb07"
                        },
                        "permissions": [
                            "LAUNCH",
                            "LAUNCH_WEBAPP",
                            "APP_TO_APP",
                            "CLOSE",
                            "TEST_OPEN",
                            "TEST_PROTECTED",
                            "CONTROL_AUDIO",  # ← Must be here for volume read/set
                            "CONTROL_DISPLAY",
                            "CONTROL_INPUT_JOYSTICK",
                            "CONTROL_INPUT_MEDIA_RECORDING",
                            "CONTROL_INPUT_MEDIA_PLAYBACK",
                            "CONTROL_INPUT_TV",
                            "CONTROL_POWER",
                            "READ_APP_STATUS",
                            "READ_CURRENT_CHANNEL",
                            "READ_INPUT_DEVICE_LIST",
                            "READ_NETWORK_STATE",
                            "READ_RUNNING_APPS",
                            "READ_TV_CHANNEL_LIST",
                            "WRITE_NOTIFICATION_TOAST",
                            "READ_POWER_STATE",
                            "READ_COUNTRY_INFO"
                        ],
                        "signatures": [
                            {
                                "signatureVersion": 1,
                                "signature": "eyJhbGdvcml0aG0iOiJSU0EtU0hBMjU2Iiwia2V5SWQiOiJ0ZXN0LXNpZ25pbmctY2VydCIsInNpZ25hdHVyZVZlcnNpb24iOjF9.hrVRgjCwXVvE2OOSpDZ58hR+59aFNwYDyjQgKk3auukd7pcegmE2CzPCa0bJ0ZsRAcKkCTJrWo5iDzNhMBWRyaMOv5zWSrthlf7G128qvIlpMT0YNY+n/FaOHE73uLrS/g7swl3/qH/BGFG2Hu4RlL48eb3lLKqTt2xKHdCs6Cd4RMfJPYnzgvI4BNrFUKsjkcu+WD4OO2A27Pq1n50cMchmcaXadJhGrOqH5YmHdOCj5NSHzJYrsW0HPlpuAx/ECMeIZYDh6RMqaFM2DXzdKX9NmmyqzJ3o/0lkk/N97gfVRLW5hA29yeAwaCViZNCP8iC9aO0q9fQojoa7NQnAtw=="
                            }
                        ]
                    }
                        }
        }
        if self.client_key:
            register_msg["payload"]["client-key"] = self.client_key
            print("Using saved client-key – no prompt!")

        await self.ws.send(json.dumps(register_msg))
        print("Sent register!")

        # Handle responses until registered
        while True:
            resp = await self.ws.recv()
            resp_dict = json.loads(resp)
            print("TV:", resp)
            if resp_dict.get("type") == "registered":
                client_key=resp_dict["payload"].get("client-key")
                if client_key and self.client_key != client_key:  # Save new key
                    new_key=client_key
                    self.save_client_key(new_key=new_key)
                break
            elif resp_dict.get("type") == "error":
                print("Error:", resp_dict)
                raise Exception("Register failed")

    async def send_command(self,uri,payload=None):
        self.request_id += 1
        msg_type = "request"
        msg = {
            "type": msg_type,
            "id": f"cmd_{self.request_id}",
            "uri": uri,
            "payload": payload or {}
        }
        await self.ws.send(json.dumps(msg))
        print(f"Sent {msg_type} to {uri}")

        # Wait for response
        resp = await self.ws.recv()
        resp_dict = json.loads(resp)
        if resp_dict.get("id") != msg["id"]:
            print("ID mismatch!")
            return None
        if resp_dict.get("type") == "error":
            print("That's an Error:",resp_dict)
            return None
        print(f"PayLoad of the Above Response From TV {resp_dict.get("payload",resp_dict)}")
        return resp_dict.get("payload",resp_dict)  # Return data
    #  AUDIO RELATED ENDPOINTS
    async def get_mute(self):
        return await self.send_command("ssap://audio/getMute")

    async def set_mute(self, mute: bool = True):
        return await self.send_command("ssap://audio/setMute", {"mute": mute})

    async def get_volume(self):
        return await self.send_command("ssap://audio/getVolume")

    async def set_volume(self, volume: int = 20):  # 0-100 typically
        if not 0 <= volume <= 100:
            raise ValueError("Volume must be 0-100")
        return await self.send_command("ssap://audio/setVolume", {"volume": volume})

    async def volume_up(self):
        return await self.send_command("ssap://audio/volumeUp")

    async def volume_down(self):
        return await self.send_command("ssap://audio/volumeDown")

    async def get_audio_status(self):
        return await self.send_command("ssap://audio/getStatus")
    
    async def list_apps(self):
        return await self.send_command("ssap://com.webos.applicationManager/listApps")

    async def list_launch_points(self):
        return await self.send_command("ssap://com.webos.applicationManager/listLaunchPoints")

    async def get_foreground_app(self):
        return await self.send_command("ssap://com.webos.applicationManager/getForegroundAppInfo")

    async def launch_app(self, app_id: str, params: dict = None):
        payload = {"id": app_id}
        if params:
            payload["params"] = params
        return await self.send_command("ssap://system.launcher/launch", payload)

    # Convenience shortcuts (these are what the real remote buttons do)
    async def launch_netflix(self):     return await self.launch_app("netflix")
    async def launch_youtube(self):     return await self.launch_app("youtube.leanback.v4")
    async def launch_prime_video(self): return await self.launch_app("amazon")
    async def launch_disney_plus(self): return await self.launch_app("disneyplus")
    async def launch_hulu(self):        return await self.launch_app("hulu")

    async def close(self):
        if self.ws:
            print("Bye byee Socket Closing")
            await self.ws.close()