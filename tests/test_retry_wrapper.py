"""
Test wrapper with retry logic for handling intermittent network errors
mentioned in the GitHub issue.
"""
import time
import functools
from selenium.common.exceptions import WebDriverException


def retry_on_network_error(max_retries=3, delay=1.0):
    """
    Decorator to retry test functions on network errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (WebDriverException, ConnectionError, OSError) as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Check if it's a network-related error
                    if any(keyword in error_msg for keyword in [
                        'network', 'connection', 'timeout', 'unreachable',
                        'refused', 'reset', 'could not connect'
                    ]):
                        if attempt < max_retries:
                            print(f"Network error on attempt {attempt + 1}, retrying in {delay}s: {e}")
                            time.sleep(delay)
                            continue
                    
                    # If it's not a network error or we're out of retries, re-raise
                    raise
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator