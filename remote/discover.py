import socket
import time
import urllib.request  # Or use requests if you prefer (import requests)
import xml.etree.ElementTree as ET
from typing import Optional, Dict  # For type hints, keep it pro

def discover_lg_tv(timeout: int = 10) -> Optional[Dict[str, str]]:
    """
    Discover LG webOS TV on the local network via SSDP/UPnP.
    
    Returns a dict with 'ip', 'friendly_name', 'model_name' if found, else None.
    """
    multicast_group = '239.255.255.250'
    port = 1900
    MSEARCH_MSG = (
    'M-SEARCH * HTTP/1.1\r\n'
    'HOST: 239.255.255.250:1900\r\n'
    'MAN: "ssdp:discover"\r\n'
    'MX: 5\r\n'  # Max wait time for responses
    'ST: upnp:rootdevice\r\n'  # Or 'urn:schemas-upnp-org:device:MediaRenderer:1' for media devices like TVs
    '\r\n'
     ).encode('utf-8')
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)  # TTL for multicast
    sock.settimeout(timeout)
    
    # Send the M-SEARCH
    sock.sendto(MSEARCH_MSG, (multicast_group, port))
    
    devices = []
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            data, addr = sock.recvfrom(1024)
            response = data.decode('utf-8')
            
            # Parse LOCATION from response (it's like HTTP headers)
            location = None
            for line in response.splitlines():
                if line.lower().startswith('location:'):
                    location = line.split(':', 1)[1].strip()
                    break
            
            if location:
                # Fetch and parse XML
                try:
                    with urllib.request.urlopen(location) as xml_file:
                        tree = ET.parse(xml_file)
                        root = tree.getroot()
                        
                        # Find relevant tags (namespaces might vary, so use find with .//)
                        namespace = {'upnp': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
                        
                        manufacturer = root.find('.//upnp:manufacturer', namespace)
                        model_name = root.find('.//upnp:modelName', namespace)
                        friendly_name = root.find('.//upnp:friendlyName', namespace)
                        
                        # Check if it's LG webOS
                        if (manufacturer and 'LG' in manufacturer.text) and \
                           (model_name and 'webOS' in model_name.text):
                            ip = addr[0]  # addr is (ip, port)
                            return {
                                'ip': ip,
                                'friendly_name': friendly_name.text if friendly_name else 'Unknown',
                                'model_name': model_name.text if model_name else 'Unknown'
                            }
                except Exception as e:
                    print(f"Error fetching/parsing XML: {e}")
                    continue  # Skip bad responses
        except socket.timeout:
            break  # Timeout done
    
    sock.close()
    return None  # No LG TV found