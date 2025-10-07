"""
Simple ORM for Drafter that provides local storage support.

This module provides three different APIs for saving and loading state:
1. Function-based API (save_state, load_state)
2. Dictionary-based API (Storage class)
3. Dataclass-based API (Storable mixin)

All approaches use browser local storage when deployed with Skulpt,
or file-based storage when running locally.
"""

import json
import os
from typing import Any, Optional, TypeVar, Type
from dataclasses import is_dataclass, asdict

from drafter.history import dehydrate_json, rehydrate_json

# Type variable for generic state
T = TypeVar('T')


def _get_storage_backend():
    """
    Determine which storage backend to use.
    Returns 'skulpt' when running in browser, 'file' when running locally.
    """
    try:
        # Check if we're running in Skulpt environment
        import sys
        if hasattr(sys, 'platform') and sys.platform == 'skulpt':
            return 'skulpt'
    except:
        pass
    return 'file'


# =============================================================================
# Function-based API
# =============================================================================

def save_state(key: str, state: Any) -> None:
    """
    Save state to local storage using a simple function-based API.
    
    Example usage:
        save_state("my_app_data", my_state)
    
    :param key: Storage key to identify the saved state
    :param state: The state object to save (must be serializable)
    """
    backend = _get_storage_backend()
    serialized = json.dumps(dehydrate_json(state))
    
    if backend == 'skulpt':
        # Use localStorage in the browser
        _save_to_localstorage(key, serialized)
    else:
        # Use file storage locally
        _save_to_file(key, serialized)


def load_state(key: str, state_type: Type[T], default: Optional[T] = None) -> Optional[T]:
    """
    Load state from local storage using a simple function-based API.
    
    Example usage:
        loaded_state = load_state("my_app_data", State, State("default", 0))
    
    :param key: Storage key to identify the saved state
    :param state_type: The type to deserialize the state into
    :param default: Default value if no saved state exists
    :return: The loaded state, or default if not found
    """
    backend = _get_storage_backend()
    
    if backend == 'skulpt':
        serialized = _load_from_localstorage(key)
    else:
        serialized = _load_from_file(key)
    
    if serialized is None:
        return default
    
    try:
        data = json.loads(serialized)
        return rehydrate_json(data, state_type)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error loading state from key '{key}': {e}")
        return default


def delete_state(key: str) -> None:
    """
    Delete saved state from local storage.
    
    :param key: Storage key to identify the saved state to delete
    """
    backend = _get_storage_backend()
    
    if backend == 'skulpt':
        _delete_from_localstorage(key)
    else:
        _delete_from_file(key)


# =============================================================================
# Dictionary-based API
# =============================================================================

class Storage:
    """
    Dictionary-like interface for local storage.
    
    Example usage:
        storage = Storage()
        storage["my_key"] = my_state
        loaded = storage.get("my_key", State, default_state)
    """
    
    def __init__(self, prefix: str = "drafter_"):
        """
        Initialize storage with an optional key prefix.
        
        :param prefix: Prefix to add to all storage keys
        """
        self.prefix = prefix
        self.backend = _get_storage_backend()
    
    def __setitem__(self, key: str, value: Any) -> None:
        """
        Save a value to storage using dictionary syntax.
        
        :param key: Storage key
        :param value: Value to save
        """
        full_key = self.prefix + key
        save_state(full_key, value)
    
    def __getitem__(self, key: str) -> Any:
        """
        Load a value from storage using dictionary syntax.
        Note: This requires the value to be JSON-compatible.
        
        :param key: Storage key
        :return: The stored value
        :raises KeyError: If key doesn't exist
        """
        full_key = self.prefix + key
        result = load_state(full_key, dict)
        if result is None:
            raise KeyError(f"Key '{key}' not found in storage")
        return result
    
    def get(self, key: str, state_type: Type[T], default: Optional[T] = None) -> Optional[T]:
        """
        Load a value from storage with type information.
        
        :param key: Storage key
        :param state_type: Expected type of the stored value
        :param default: Default value if key doesn't exist
        :return: The stored value or default
        """
        full_key = self.prefix + key
        return load_state(full_key, state_type, default)
    
    def delete(self, key: str) -> None:
        """
        Delete a key from storage.
        
        :param key: Storage key to delete
        """
        full_key = self.prefix + key
        delete_state(full_key)
    
    def __contains__(self, key: str) -> bool:
        """
        Check if a key exists in storage.
        
        :param key: Storage key to check
        :return: True if key exists, False otherwise
        """
        full_key = self.prefix + key
        result = load_state(full_key, dict)
        return result is not None
    
    def clear(self) -> None:
        """
        Clear all keys with this storage's prefix.
        Note: This only works reliably in file mode.
        """
        if self.backend == 'file':
            storage_dir = _get_storage_dir()
            if os.path.exists(storage_dir):
                for filename in os.listdir(storage_dir):
                    if filename.startswith(self.prefix):
                        filepath = os.path.join(storage_dir, filename)
                        try:
                            os.remove(filepath)
                        except OSError:
                            pass


# =============================================================================
# Dataclass-based API
# =============================================================================

class Storable:
    """
    Mixin class for dataclasses to add save/load methods.
    
    Example usage:
        @dataclass
        class State(Storable):
            message: str
            count: int
        
        state = State("Hello", 42)
        state.save("my_state")
        
        loaded = State.load("my_state", State("Default", 0))
    """
    
    def save(self, key: str) -> None:
        """
        Save this instance to local storage.
        
        :param key: Storage key to save under
        """
        if not is_dataclass(self):
            raise TypeError("Storable can only be used with dataclasses")
        save_state(key, self)
    
    @classmethod
    def load(cls: Type[T], key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Load an instance from local storage.
        
        :param key: Storage key to load from
        :param default: Default instance if key doesn't exist
        :return: The loaded instance or default
        """
        return load_state(key, cls, default)
    
    def delete_saved(self, key: str) -> None:
        """
        Delete saved state from local storage.
        
        :param key: Storage key to delete
        """
        delete_state(key)


# =============================================================================
# Internal storage backend implementations
# =============================================================================

def _get_storage_dir() -> str:
    """Get the directory for file-based storage."""
    storage_dir = os.path.join(os.path.expanduser("~"), ".drafter_storage")
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir


def _save_to_file(key: str, data: str) -> None:
    """Save data to a file."""
    storage_dir = _get_storage_dir()
    # Sanitize key to create valid filename
    safe_key = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in key)
    filepath = os.path.join(storage_dir, f"{safe_key}.json")
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(data)
    except IOError as e:
        print(f"Error saving to file: {e}")


def _load_from_file(key: str) -> Optional[str]:
    """Load data from a file."""
    storage_dir = _get_storage_dir()
    safe_key = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in key)
    filepath = os.path.join(storage_dir, f"{safe_key}.json")
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError as e:
        print(f"Error loading from file: {e}")
        return None


def _delete_from_file(key: str) -> None:
    """Delete a file."""
    storage_dir = _get_storage_dir()
    safe_key = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in key)
    filepath = os.path.join(storage_dir, f"{safe_key}.json")
    
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except OSError as e:
            print(f"Error deleting file: {e}")


# Skulpt implementations - these will be intercepted by JavaScript
def _save_to_localstorage(key: str, data: str) -> None:
    """Save data to browser localStorage (Skulpt only)."""
    # This is a stub that will be replaced by Skulpt module
    print(f"localStorage.setItem('{key}', {data!r})")


def _load_from_localstorage(key: str) -> Optional[str]:
    """Load data from browser localStorage (Skulpt only)."""
    # This is a stub that will be replaced by Skulpt module
    print(f"localStorage.getItem('{key}')")
    return None


def _delete_from_localstorage(key: str) -> None:
    """Delete data from browser localStorage (Skulpt only)."""
    # This is a stub that will be replaced by Skulpt module
    print(f"localStorage.removeItem('{key}')")
