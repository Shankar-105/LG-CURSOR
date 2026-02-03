from remote.client import WebOSClient
class Buttons():
    def __init__(self):
        pass
    async def getVolume():
          return await WebOSClient.send_command("ssap://audio/getVolume")

    async def setVolume():
        return await WebOSClient.send_command("ssap://audio/setVolume", {"volume": 20})