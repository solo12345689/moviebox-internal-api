import hashlib
import hmac
import base64
import time
import json
from typing import Union, Optional
from urllib.parse import urlparse, parse_qsl, urlencode, quote
import logging
logger = logging.getLogger(__name__)

GATEWAY_SECRET_ONLINE = "76iRl07s0xSN9jqmEWAt79EBJZulIQIsV64FZr2O"

def md5_hex(data: Union[str, bytes]) -> str:
    """Calculates MD5 hash of string or bytes and returns hex string."""
    if not data:
        return ""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.md5(data).hexdigest()

def sha256_hex(data: Union[str, bytes]) -> str:
    """Calculates SHA256 hash of string or bytes and returns hex string."""
    if not data:
        return ""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def generate_client_token() -> str:
    """
    Generates the X-Client-Token used for anonymous requests.
    Format: <timestamp>,<md5(reversed_timestamp)>
    """
    ts = str(int(time.time() * 1000))
    rev_ts = ts[::-1]
    return f"{ts},{md5_hex(rev_ts)}"

def generate_tr_signature(method: str, url: str, body_data: str = "", timestamp: int = None) -> str:
    """
    Generates the x-tr-signature for the MovieBox API Gateway.
    
    Canonical String Format:
    METHOD\nAccept\nContent-Type\nContent-Length\ntimestamp\nbodyMD5\npath?sorted_query
    """
    if timestamp is None:
        timestamp = int(time.time() * 1000)
    
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    # Extract and sort query parameters
    query_params = parse_qsl(parsed_url.query, keep_blank_values=True)
    if query_params:
        # GatewayInterceptor decodes keys/values and sorts by key
        query_params.sort(key=lambda x: x[0])
        # Manually join with '=' and '&' without encoding (app does this after decoding)
        query_string = "&".join([f"{k}={v}" for k, v in query_params])
        resource = f"{path}?{query_string}"
    else:
        resource = path
        
    # Smali truncates body at 0x19000 (102400) characters for MD5
    body_for_md5 = body_data[:0x19000] if body_data else ""
    body_md5 = md5_hex(body_for_md5) if body_data else ""
    
    # Standard headers for canonical string
    accept = "application/json"
    content_type = "application/json;charset=UTF-8"
    content_length = str(len(body_data)) if body_data else ""
    
    canonical_list = [
        method.upper(),
        accept,
        content_type,
        content_length,
        str(timestamp),
        body_md5,
        resource
    ]
    canonical_string = "\n".join(canonical_list)
    logger.info(f"CANONICAL STRING:\n{canonical_string}")
    
    # App base64 decodes the secret key (Online Secret)
    key = base64.b64decode(GATEWAY_SECRET_ONLINE)
    h = hmac.new(key, canonical_string.encode('utf-8'), hashlib.md5)
    
    # App base64 encodes the binary signature result
    signature_b64 = base64.b64encode(h.digest()).decode('utf-8')
    
    return f"{timestamp}|2|{signature_b64}"

def get_default_client_info() -> dict:
    """Returns randomized device metadata matching the official app's JSON structure."""
    import random
    
    # Realistic device id logic from app patterns
    device_id = "86820305" + "".join(random.choices("0123456789", k=7))
    
    return {
        "package_name": "com.movieboxpro.android",
        "version_name": "16.2.1",
        "version_code": 16210,
        "os": "android",
        "os_version": "12",
        "install_ch": "googleplay",
        "device_id": device_id,
        "install_store": "googleplay",
        "gaid": "",
        "brand": "google",
        "model": "Pixel 6",
        "system_language": "en",
        "net": "wifi",
        "region": "IN",
        "timezone": "Asia/Kolkata",
        "sp_code": "404"
    }

def generate_gslb_sign(package_name: str, device_id: str) -> str:
    """
    Generates the X-Gslb-Sign for the Global Server Load Balancer.
    Formula: sha256(packageName + sha256(deviceId))
    """
    key = sha256_hex(device_id)
    return sha256_hex(package_name + key)
