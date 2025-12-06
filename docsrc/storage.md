# Drafter Storage API

A simple ORM (Object-Relational Mapping) for Drafter that enables saving and loading application state.

## Overview

The Drafter Storage API provides three different approaches for persisting state:

1. **Function-based API** - Simple functions like `save_state()` and `load_state()`
2. **Dictionary-based API** - A `Storage` class that works like a dictionary
3. **Dataclass-based API** - A `Storable` mixin that adds `.save()` and `.load()` methods to dataclasses

When running locally, state is saved to `~/.drafter_storage/` as JSON files. When deployed with Skulpt (in the browser), state can be saved to browser localStorage.

## Quick Start

### Function-based API

This approach is the simplest and most familiar to students learning basic file handling:

```python
from drafter import *
from dataclasses import dataclass

@dataclass
class State:
    message: str
    count: int

# Save state
state = State("Hello", 42)
save_state("my_app", state)

# Load state
loaded = load_state("my_app", State, State("Default", 0))
print(loaded.message)  # "Hello"
print(loaded.count)     # 42

# Delete state
delete_state("my_app")
```

### Dictionary-based API

This approach uses a dictionary-like interface:

```python
from drafter import *
from dataclasses import dataclass

@dataclass
class State:
    items: list[str]

# Create a storage instance
storage = Storage(prefix="my_app_")

# Save using dictionary syntax
state = State(["apple", "banana"])
storage["data"] = state

# Load using get() with type information
loaded = storage.get("data", State, State([]))
print(loaded.items)  # ["apple", "banana"]

# Check if key exists
if "data" in storage:
    storage.delete("data")
```

### Dataclass-based API

This approach adds storage methods directly to your dataclass:

```python
from drafter import *
from dataclasses import dataclass

@dataclass
class State(Storable):
    username: str
    score: int

# Save using the instance method
state = State("Player1", 100)
state.save("game_state")

# Load using the class method
loaded = State.load("game_state", State("Guest", 0))
print(loaded.username)  # "Player1"
print(loaded.score)     # 100
```

## Complete Examples

See the `examples/` directory for complete working applications:

- `examples/storage_functions.py` - Function-based API demo
- `examples/storage_dictionary.py` - Dictionary-based API with a todo list
- `examples/storage_dataclass.py` - Dataclass-based API with a user profile

## API Reference

### Function-based API

#### `save_state(key: str, state: Any) -> None`

Save state to storage.

**Parameters:**
- `key`: Storage key to identify the saved state
- `state`: The state object to save (must be serializable)

**Example:**
```python
save_state("my_data", my_state)
```

#### `load_state(key: str, state_type: Type[T], default: Optional[T] = None) -> Optional[T]`

Load state from storage.

**Parameters:**
- `key`: Storage key to identify the saved state
- `state_type`: The type to deserialize the state into
- `default`: Default value if no saved state exists

**Returns:** The loaded state, or default if not found

**Example:**
```python
loaded = load_state("my_data", State, State("default", 0))
```

#### `delete_state(key: str) -> None`

Delete saved state from storage.

**Parameters:**
- `key`: Storage key to identify the saved state to delete

**Example:**
```python
delete_state("my_data")
```

### Dictionary-based API

#### `Storage(prefix: str = "drafter_")`

Dictionary-like interface for storage.

**Parameters:**
- `prefix`: Prefix to add to all storage keys (default: "drafter_")

**Methods:**

- `storage[key] = value` - Save a value
- `storage.get(key, type, default)` - Load a value with type information
- `storage.delete(key)` - Delete a value
- `key in storage` - Check if key exists
- `storage.clear()` - Clear all keys with this storage's prefix (file mode only)

**Example:**
```python
storage = Storage(prefix="app1_")
storage["data"] = my_state
loaded = storage.get("data", State, default_state)
```

### Dataclass-based API

#### `Storable`

Mixin class for dataclasses to add save/load methods.

**Methods:**

- `instance.save(key: str)` - Save this instance to storage
- `ClassName.load(key: str, default: Optional[T] = None)` - Load an instance from storage
- `instance.delete_saved(key: str)` - Delete saved state

**Example:**
```python
@dataclass
class State(Storable):
    message: str
    count: int

state = State("Hello", 42)
state.save("my_state")
loaded = State.load("my_state", State("Default", 0))
```

## Storage Backends

### File Storage (Local Development)

When running locally, state is saved as JSON files in `~/.drafter_storage/`. Each key is sanitized to create a valid filename.

### Browser localStorage (Deployed)

When deployed with Skulpt, state would be saved to browser localStorage. 

**Note:** Full localStorage support in Skulpt requires additional JavaScript integration. The current implementation provides the Python API and file-based storage. Browser localStorage support is available through the provided `drafter-storage.js` module but requires integration with the Skulpt deployment process.

## Data Serialization

The storage API uses Drafter's existing `dehydrate_json()` and `rehydrate_json()` functions, which support:

- Primitive types: `int`, `str`, `float`, `bool`, `None`
- Collections: `list`, `dict`, `set`, `tuple`
- Dataclasses
- PIL Images (when Pillow is available)

Circular references are detected and will raise an error.

## Best Practices

1. **Use meaningful keys**: Choose descriptive keys that clearly identify what's being stored
   ```python
   save_state("user_preferences", prefs)  # Good
   save_state("data", prefs)              # Too generic
   ```

2. **Provide defaults**: Always provide a default value when loading to handle missing data
   ```python
   loaded = load_state("config", Config, Config.default())
   ```

3. **Use prefixes**: When using the Storage class, use prefixes to namespace your data
   ```python
   storage = Storage(prefix="myapp_v1_")
   ```

4. **Handle errors**: Storage operations may fail (disk full, permissions, etc.)
   ```python
   try:
       save_state("data", state)
   except Exception as e:
       print(f"Failed to save: {e}")
   ```

## Teaching with Storage

The Storage API is designed to teach CS1 concepts:

### File Handling Concepts
- Opening, reading, writing, and closing files (abstracted)
- Persistent storage vs. temporary variables
- Serialization (converting objects to storable formats)

### Data Structures
- Dictionary-based storage teaches key-value pairs
- Demonstrates the importance of data types
- Shows how complex objects can be broken down and reconstructed

### Object-Oriented Programming
- The Storable mixin demonstrates inheritance
- Shows how to add functionality to existing classes
- Introduces class methods vs. instance methods

## Troubleshooting

### Storage directory doesn't exist
The storage directory (`~/.drafter_storage/`) is created automatically. If you encounter permission errors, check your home directory permissions.

### State not loading correctly
Ensure the `state_type` parameter matches the type of the original saved state. Type mismatches will result in None being returned or errors during deserialization.

### localStorage not working in deployed app
Full localStorage support requires JavaScript integration. Check that `drafter-storage.js` is included in your deployment and that the browser supports localStorage.
