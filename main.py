import asyncio
from remote.client import WebOSClient

async def main():
    client = WebOSClient("192.168.0.5")  # Your IP
    await client.connect()

    # Test get volume
    volume = await client.send_command("ssap://audio/getVolume",subscribe=True)
    print("Current Volume:", volume)

    # Set volume
    await client.send_command("ssap://audio/setVolume", {"volume": 20})

    # Power off (careful!)
    # await client.send_command("ssap://system/turnOff")

    await client.close()

asyncio.run(main())