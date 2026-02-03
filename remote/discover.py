import socket
import time
import requests
import xml.etree.ElementTree as ET
from typing import Optional, Dict, List
from urllib.parse import unquote  # For decoding DLNA header if needed

def discover_lg_tv(timeout: int = 10) -> Optional[Dict[str, str]]:
    """
    Discover LG webOS TV on the local network via SSDP/UPnP.
    
    Returns a dict with 'ip', 'friendly_name', 'model_name' if found, else None.
    Prints debug info for troubleshooting.
    """
    multicast_group = '239.255.255.250'
    port = 1900
    MSEARCH_MSG = (
        'M-SEARCH * HTTP/1.1\r\n'
        'HOST: 239.255.255.250:1900\r\n'
        'MAN: "ssdp:discover"\r\n'
        'MX: 5\r\n'
        'ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n'  # LG TVs respond to this
        'USER-AGENT: UDAP/2.0\r\n'  # Required for LG UDAP/UPnP
        '\r\n'
    ).encode('utf-8')
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.settimeout(1)  # Per-loop timeout for control
    
    # Send the M-SEARCH
    sock.sendto(MSEARCH_MSG, (multicast_group, port))
    print("Sent M-SEARCH broadcast. Listening for responses...")
    
    potential_devices: List[Dict[str, str]] = []
    seen_locations: set = set()  # Deduplicate by location to avoid repeats
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            data, addr = sock.recvfrom(1024)
            response = data.decode('utf-8', errors='ignore')
            print(f"\nReceived response from {addr}:\n{response}")
            
            # Parse LOCATION from response
            location = None
            for line in response.splitlines():
                if line.lower().startswith('location:'):
                    location = line.split(':', 1)[1].strip()
                    break
            
            if location and location not in seen_locations:
                seen_locations.add(location)
                print(f"Location found: {location}")
                # Fetch and parse XML
                try:
                    xml_response = requests.get(location, timeout=5)
                    xml_response.raise_for_status()
                    xml_text = xml_response.text
                    print(f"XML content (full):\n{xml_text}")  # Print full for debug
                    
                    tree = ET.ElementTree(ET.fromstring(xml_text))
                    root = tree.getroot()
                    
                    # Use iter with full namespaced tag to extract reliably
                    upnp_ns = '{urn:schemas-upnp-org:device-1-0}'
                    manuf_text = ''
                    model_text = ''
                    friendly_text = 'Unknown'
                    desc_text = ''
                    
                    for el in root.iter():
                        if el.tag == upnp_ns + 'manufacturer':
                            manuf_text = (el.text or '').lower().strip()
                        elif el.tag == upnp_ns + 'modelName':
                            model_text = (el.text or '').lower().strip()
                        elif el.tag == upnp_ns + 'friendlyName':
                            friendly_text = (el.text or 'Unknown').strip()
                        elif el.tag == upnp_ns + 'modelDescription':
                            desc_text = (el.text or '').lower().strip()
                    
                    print(f"Parsed: Manufacturer='{manuf_text}', Model='{model_text}', Friendly='{friendly_text}', Description='{desc_text}'")
                    
                    # Robust LG webOS check (case insensitive, check multiple fields)
                    if ('lg' in manuf_text or 'lge' in manuf_text) and ('webos' in model_text or 'webos' in desc_text or 'webos' in friendly_text.lower()):
                        ip = addr[0]
                        device_info = {
                            'ip': ip,
                            'friendly_name': friendly_text,
                            'model_name': model_text.capitalize() or desc_text.capitalize() or "webOS TV"
                        }
                        potential_devices.append(device_info)
                        print(f"Matched LG webOS TV: {device_info}")
                    else:
                        print("Not detected as LG webOS - skipping.")
                except Exception as e:
                    print(f"Error fetching/parsing XML from {location}: {e}")
        except socket.timeout:
            continue  # Loop until timeout
    
    sock.close()
    
    if potential_devices:
        print(f"Found {len(potential_devices)} potential LG TVs. Returning first one.")
        return potential_devices[0]
    else:
        print("No LG webOS TV found after timeout.")
        return None