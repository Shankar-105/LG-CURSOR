import asyncio
from remote import client,discover

# async def main():
#     client = WebOSClient("192.168.0.5")  # Your IP
#     await client.connect()

#     # Test get volume
#     volume = await client.send_command("ssap://audio/getVolume",subscribe=True)
#     print("Current Volume:", volume)

#     # Set volume
#     await client.send_command("ssap://audio/setVolume", {"volume": 20})

#     # Power off (careful!)
#     # await client.send_command("ssap://system/turnOff")

#     await client.close()

# asyncio.run(main())
tv_info = discover.discover_lg_tv()
if tv_info:
    print(f"Found TV at {tv_info['ip']}: {tv_info['friendly_name']}")
    # Now use tv_info['ip'] for your pairing/connect logic
else:
    print("No LG TV found. Check network/TV is on.")