import asyncio
import discover, client

tv_info = discover.discover_lg_tv()
print(f"Here is the Tv Info - {tv_info}")

# Define menu categories and their methods
MENU = {
    "1": {
        "name": "🔊 Audio Control",
        "methods": {
            "1": ("Get Mute Status", "get_mute"),
            "2": ("Set Mute (ON)", lambda conn: conn.set_mute(True)),
            "3": ("Set Mute (OFF)", lambda conn: conn.set_mute(False)),
            "4": ("Get Volume", "get_volume"),
            "5": ("Set Volume", "set_volume_prompt"),
            "6": ("Volume Up", "volume_up"),
            "7": ("Volume Down", "volume_down"),
            "8": ("Get Audio Status", "get_audio_status"),
        }
    },
    "2": {
        "name": "📱 Applications",
        "methods": {
            "1": ("List Apps", "list_apps"),
            "2": ("List Launch Points", "list_launch_points"),
            "3": ("Get Foreground App", "get_foreground_app"),
            "4": ("Launch Netflix", "launch_netflix"),
            "5": ("Launch YouTube", "launch_youtube"),
            "6": ("Launch Prime Video", "launch_prime_video"),
            "7": ("Launch JioHotstar", "launch_jio_hotstar"),
            "8": ("Launch Custom App", "launch_app_prompt"),
        }
    },
    "3": {
        "name": "📺 Channels & Inputs",
        "methods": {
            "1": ("Get Channel List", "get_channel_list"),
            "2": ("Get Current Channel", "get_current_channel"),
            "3": ("Open Channel", "open_channel_prompt"),
            "4": ("Channel Up", "channel_up"),
            "5": ("Channel Down", "channel_down"),
            "6": ("Get External Inputs", "get_external_inputs"),
            "7": ("Switch Input", "switch_input_prompt"),
        }
    },
    "4": {
        "name": "▶️ Media Control",
        "methods": {
            "1": ("Play", "media_play"),
            "2": ("Pause", "media_pause"),
            "3": ("Stop", "media_stop"),
            "4": ("Rewind", "media_rewind"),
            "5": ("Fast Forward", "media_fast_forward"),
        }
    },
    "5": {
        "name": "⚡ System & Power",
        "methods": {
            "1": ("Get System Info", "get_system_info"),
            "2": ("Get Power State", "get_power_state"),
            "3": ("Turn Off Screen", "turn_off_screen"),
            "4": ("Turn On Screen", "turn_on_screen"),
            "5": ("Power Off TV", "power_off"),
        }
    },
}

def display_main_menu():
    """Display main menu categories"""
    print("\n" + "="*50)
    print("🎮 LG WebOS TV Remote Control System")
    print("="*50)
    for key, category in MENU.items():
        print(f"{key}. {category['name']}")
    print("0. Exit")
    print("="*50)

def display_category_menu(category_key):
    """Display methods in a category"""
    if category_key not in MENU:
        print("❌ Invalid category!")
        return None
    
    category = MENU[category_key]
    print(f"\n{'='*50}")
    print(f"{category['name']}")
    print("="*50)
    
    for key, (name, _) in category['methods'].items():
        print(f"{key}. {name}")
    print("0. Back to Main Menu")
    print("="*50)
    
    return category

async def execute_method(connector, category_key, method_key):
    """Execute the selected method"""
    category = MENU.get(category_key)
    if not category or method_key not in category['methods']:
        print("❌ Invalid selection!")
        return
    
    method_name, method = category['methods'][method_key]
    
    try:
        # Handle prompt-based methods
        if method == "set_volume_prompt":
            volume = input("Enter volume (0-100): ")
            result = await connector.set_volume(int(volume))
        elif method == "launch_app_prompt":
            app_id = input("Enter app ID: ")
            result = await connector.launch_app(app_id)
        elif method == "open_channel_prompt":
            channel_id = input("Enter channel ID: ")
            result = await connector.open_channel(channel_id)
        elif method == "switch_input_prompt":
            input_id = input("Enter input ID (e.g., HDMI1, AV1): ")
            result = await connector.switch_input(input_id)
        # Handle callable (lambda) methods
        elif callable(method):
            result = await method(connector)
        # Handle string method names
        else:
            result = await getattr(connector, method)()
        
        print(f"✅ {method_name} executed successfully!")
        if result:
            print(f"Response: {result}\n")
    except ValueError as e:
        print(f"❌ Invalid input: {e}\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")

async def console_menu(connector):
    """Main console menu loop"""
    while True:
        display_main_menu()
        category_choice = input("Select category (0 to exit): ").strip()
        
        if category_choice == "0":
            print("👋 Exiting...")
            break
        
        category = display_category_menu(category_choice)
        if not category:
            continue
        
        method_choice = input("Select method (0 to go back): ").strip()
        
        if method_choice == "0":
            continue
        
        await execute_method(connector, category_choice, method_choice)

async def main():
    if tv_info:
        print(f"✅ Found TV at {tv_info['ip']}: {tv_info['friendly_name']}")
        tv_ip = tv_info.get('ip')
        connector = client.WebOSClient(f"{tv_ip}")
        
        try:
            await connector.connect()
            print("🎯 Connected! Starting console menu...\n")
            await console_menu(connector)
        finally:
            await connector.close()
    else:
        print("❌ No LG TV found. Check network/TV is on.")

asyncio.run(main())