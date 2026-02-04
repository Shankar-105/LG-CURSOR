import asyncio
import discover,client

tv_info = discover.discover_lg_tv()
print(f"Here is the Tv Info - {tv_info}")
async def main():
    if tv_info:
        print(f"Found TV at {tv_info['ip']}: {tv_info['friendly_name']}")
        tv_ip = tv_info.get('ip')
        connector = client.WebOSClient(f"{tv_ip}")  # Your IP
        await connector.connect()
        await connector.list_apps()
        await connector.close()
    else:
        print("No LG TV found. Check network/TV is on.")

asyncio.run(main())