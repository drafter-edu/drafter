"""
Shareable links functionality for encoding and decoding application state in URLs.

This module provides utilities to create shareable links that encode the application
state, allowing users to share their exact application state with others via a URL.
"""

import base64
import json
import zlib
from typing import Any, Dict, Optional
from dataclasses import asdict, is_dataclass
from urllib.parse import urlencode, parse_qs


def _serialize_state(state: Any) -> str:
    """
    Serialize state to a JSON string, handling dataclasses and common types.
    
    :param state: The state object to serialize
    :return: JSON string representation of the state
    """
    def default_serializer(obj):
        """Custom serializer for objects that aren't JSON serializable."""
        if is_dataclass(obj):
            return asdict(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            return list(obj)
        else:
            return str(obj)
    
    try:
        return json.dumps(state, default=default_serializer, separators=(',', ':'))
    except (TypeError, ValueError) as e:
        # Fallback: convert to string representation
        return json.dumps({'_raw': str(state), '_type': type(state).__name__})


def _deserialize_state(state_json: str) -> Any:
    """
    Deserialize state from a JSON string.
    
    :param state_json: JSON string to deserialize
    :return: Deserialized state object
    """
    try:
        return json.loads(state_json)
    except json.JSONDecodeError:
        return None


def encode_state_to_url_param(state: Any, compress: bool = True) -> str:
    """
    Encode application state into a URL-safe string parameter.
    
    The state is serialized to JSON, optionally compressed with zlib,
    and then base64url encoded for safe inclusion in URLs.
    
    :param state: The state object to encode
    :param compress: Whether to compress the state (default: True, recommended for large states)
    :return: URL-safe encoded state string
    
    Example:
        >>> state = {'count': 5, 'user': 'Alice'}
        >>> encoded = encode_state_to_url_param(state)
        >>> f"https://myapp.com/route?state={encoded}"
    """
    # Serialize to JSON
    state_json = _serialize_state(state)
    state_bytes = state_json.encode('utf-8')
    
    # Optionally compress
    if compress:
        state_bytes = zlib.compress(state_bytes, level=9)
    
    # Base64url encode (URL-safe)
    encoded = base64.urlsafe_b64encode(state_bytes).decode('ascii')
    
    # Remove padding (can be restored during decode)
    encoded = encoded.rstrip('=')
    
    return encoded


def decode_state_from_url_param(encoded_state: str, decompress: bool = True) -> Optional[Any]:
    """
    Decode application state from a URL parameter string.
    
    Reverses the encoding process: base64url decode, optionally decompress,
    and deserialize from JSON.
    
    :param encoded_state: The URL-safe encoded state string
    :param decompress: Whether the state was compressed (default: True)
    :return: Deserialized state object, or None if decoding fails
    
    Example:
        >>> encoded = "eJyrVkrLz8lMUbJSMjQyNTY1N1WqBQAjEgU2"
        >>> state = decode_state_from_url_param(encoded)
        >>> print(state)
        {'count': 5, 'user': 'Alice'}
    """
    try:
        # Restore padding
        padding = 4 - (len(encoded_state) % 4)
        if padding != 4:
            encoded_state += '=' * padding
        
        # Base64url decode
        state_bytes = base64.urlsafe_b64decode(encoded_state)
        
        # Optionally decompress
        if decompress:
            state_bytes = zlib.decompress(state_bytes)
        
        # Deserialize from JSON
        state_json = state_bytes.decode('utf-8')
        return _deserialize_state(state_json)
        
    except (base64.binascii.Error, zlib.error, UnicodeDecodeError, ValueError) as e:
        # Return None on any decoding error
        return None


def create_shareable_link(
    base_url: str,
    route: str,
    state: Any,
    additional_params: Optional[Dict[str, Any]] = None,
    state_param_name: str = 'shared_state'
) -> str:
    """
    Create a complete shareable link with encoded state.
    
    :param base_url: The base URL of the application (e.g., "https://myapp.com")
    :param route: The route path (e.g., "/dashboard")
    :param state: The state object to encode
    :param additional_params: Optional dictionary of additional URL parameters
    :param state_param_name: Name of the state parameter (default: 'shared_state')
    :return: Complete shareable URL
    
    Example:
        >>> state = {'count': 5, 'items': ['a', 'b', 'c']}
        >>> link = create_shareable_link(
        ...     "https://myapp.com",
        ...     "/dashboard",
        ...     state,
        ...     additional_params={'view': 'detailed'}
        ... )
        >>> print(link)
        https://myapp.com/dashboard?view=detailed&shared_state=eJyrVkrLz8...
    """
    # Encode the state
    encoded_state = encode_state_to_url_param(state)
    
    # Build parameters
    params = {state_param_name: encoded_state}
    if additional_params:
        params.update(additional_params)
    
    # Build URL
    base_url = base_url.rstrip('/')
    route = route if route.startswith('/') else f'/{route}'
    query_string = urlencode(params)
    
    return f"{base_url}{route}?{query_string}"


def extract_shared_state_from_params(
    params: Dict[str, Any],
    state_param_name: str = 'shared_state'
) -> Optional[Any]:
    """
    Extract and decode shared state from URL parameters.
    
    This function is typically called in a route handler to restore
    state from a shareable link.
    
    :param params: Dictionary of URL parameters (from request kwargs)
    :param state_param_name: Name of the state parameter (default: 'shared_state')
    :return: Decoded state object, or None if not present or invalid
    
    Example:
        >>> @route('dashboard')
        >>> def dashboard(**kwargs):
        ...     shared_state = extract_shared_state_from_params(kwargs)
        ...     if shared_state:
        ...         # Restore the shared state
        ...         get_state().update(shared_state)
        ...     return Page(...)
    """
    encoded_state = params.get(state_param_name)
    if encoded_state:
        return decode_state_from_url_param(encoded_state)
    return None


def get_current_shareable_link(
    request_url: str,
    state: Any,
    state_param_name: str = 'shared_state'
) -> str:
    """
    Generate a shareable link for the current page with current state.
    
    :param request_url: The current request URL
    :param state: The current state to encode
    :param state_param_name: Name of the state parameter (default: 'shared_state')
    :return: Updated URL with encoded state
    
    Example:
        >>> current_url = "https://myapp.com/page?user=alice"
        >>> current_state = get_state().current
        >>> shareable = get_current_shareable_link(current_url, current_state)
    """
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    
    # Parse the URL
    parsed = urlparse(request_url)
    
    # Get existing parameters
    params = parse_qs(parsed.query)
    # Convert lists to single values
    params = {k: v[0] if isinstance(v, list) and v else v for k, v in params.items()}
    
    # Encode and add state
    params[state_param_name] = encode_state_to_url_param(state)
    
    # Rebuild URL
    new_query = urlencode(params)
    new_parsed = parsed._replace(query=new_query)
    
    return urlunparse(new_parsed)
