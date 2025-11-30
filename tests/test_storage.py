"""
Unit tests for the storage module.
"""
import pytest
import os
import tempfile
from dataclasses import dataclass
from drafter.storage import (
    save_state, load_state, delete_state,
    Storage, Storable,
    _save_to_file, _load_from_file, _delete_from_file,
    _get_storage_dir
)


@dataclass
class SimpleState:
    """Simple test state."""
    message: str
    count: int


@dataclass
class ComplexState:
    """More complex test state."""
    items: list[str]
    mapping: dict[str, int]
    nested: SimpleState


class TestFunctionBasedAPI:
    """Test the function-based save/load API."""
    
    def test_save_and_load_simple_state(self):
        """Test saving and loading a simple dataclass."""
        state = SimpleState("test", 42)
        save_state("test_simple", state)
        
        loaded = load_state("test_simple", SimpleState)
        assert loaded is not None
        assert loaded.message == "test"
        assert loaded.count == 42
    
    def test_load_nonexistent_returns_default(self):
        """Test that loading a nonexistent key returns the default."""
        default = SimpleState("default", 0)
        loaded = load_state("nonexistent_key_xyz", SimpleState, default)
        assert loaded == default
    
    def test_load_nonexistent_returns_none(self):
        """Test that loading a nonexistent key returns None if no default."""
        loaded = load_state("nonexistent_key_abc", SimpleState)
        assert loaded is None
    
    def test_save_and_load_complex_state(self):
        """Test saving and loading a complex nested dataclass."""
        nested = SimpleState("nested", 99)
        state = ComplexState(
            items=["a", "b", "c"],
            mapping={"x": 1, "y": 2},
            nested=nested
        )
        save_state("test_complex", state)
        
        loaded = load_state("test_complex", ComplexState)
        assert loaded is not None
        assert loaded.items == ["a", "b", "c"]
        assert loaded.mapping == {"x": 1, "y": 2}
        assert loaded.nested.message == "nested"
        assert loaded.nested.count == 99
    
    def test_delete_state(self):
        """Test deleting saved state."""
        state = SimpleState("to_delete", 123)
        save_state("test_delete", state)
        
        # Verify it exists
        loaded = load_state("test_delete", SimpleState)
        assert loaded is not None
        
        # Delete it
        delete_state("test_delete")
        
        # Verify it's gone
        loaded = load_state("test_delete", SimpleState)
        assert loaded is None


class TestDictionaryBasedAPI:
    """Test the dictionary-based Storage API."""
    
    def test_storage_setitem_and_get(self):
        """Test dictionary-style storage access."""
        storage = Storage(prefix="test_dict_")
        state = SimpleState("dict_test", 555)
        
        storage["my_key"] = state
        loaded = storage.get("my_key", SimpleState)
        
        assert loaded is not None
        assert loaded.message == "dict_test"
        assert loaded.count == 555
    
    def test_storage_get_with_default(self):
        """Test get with default value."""
        storage = Storage(prefix="test_default_")
        default = SimpleState("default", 0)
        
        loaded = storage.get("missing_key", SimpleState, default)
        assert loaded == default
    
    def test_storage_contains(self):
        """Test the 'in' operator."""
        storage = Storage(prefix="test_contains_")
        state = SimpleState("exists", 777)
        
        storage["exists_key"] = state
        assert "exists_key" in storage
        assert "missing_key" not in storage
    
    def test_storage_delete(self):
        """Test deleting from storage."""
        storage = Storage(prefix="test_del_")
        state = SimpleState("to_remove", 888)
        
        storage["remove_key"] = state
        assert "remove_key" in storage
        
        storage.delete("remove_key")
        assert "remove_key" not in storage
    
    def test_storage_prefix(self):
        """Test that prefix is correctly applied."""
        storage1 = Storage(prefix="app1_")
        storage2 = Storage(prefix="app2_")
        
        state1 = SimpleState("app1", 1)
        state2 = SimpleState("app2", 2)
        
        storage1["data"] = state1
        storage2["data"] = state2
        
        loaded1 = storage1.get("data", SimpleState)
        loaded2 = storage2.get("data", SimpleState)
        
        assert loaded1.message == "app1"
        assert loaded2.message == "app2"


class TestDataclassBasedAPI:
    """Test the dataclass-based Storable API."""
    
    def test_storable_save_and_load(self):
        """Test save() and load() methods on Storable dataclass."""
        @dataclass
        class MyState(Storable):
            value: str
            number: int
        
        state = MyState("storable", 999)
        state.save("test_storable")
        
        loaded = MyState.load("test_storable")
        assert loaded is not None
        assert loaded.value == "storable"
        assert loaded.number == 999
    
    def test_storable_load_with_default(self):
        """Test load() with default value."""
        @dataclass
        class MyState(Storable):
            value: str
        
        default = MyState("default_value")
        loaded = MyState.load("nonexistent_storable", default)
        assert loaded == default
    
    def test_storable_non_dataclass_raises(self):
        """Test that Storable raises error for non-dataclass."""
        class NotADataclass(Storable):
            pass
        
        obj = NotADataclass()
        with pytest.raises(TypeError):
            obj.save("test_key")


class TestFileBackend:
    """Test the file-based storage backend."""
    
    def test_storage_directory_creation(self):
        """Test that storage directory is created."""
        storage_dir = _get_storage_dir()
        assert os.path.exists(storage_dir)
        assert os.path.isdir(storage_dir)
    
    def test_file_save_and_load(self):
        """Test low-level file save/load."""
        test_data = '{"test": "data"}'
        _save_to_file("file_test", test_data)
        
        loaded = _load_from_file("file_test")
        assert loaded == test_data
    
    def test_file_delete(self):
        """Test low-level file deletion."""
        test_data = '{"delete": "me"}'
        _save_to_file("file_delete_test", test_data)
        
        # Verify it exists
        loaded = _load_from_file("file_delete_test")
        assert loaded is not None
        
        # Delete it
        _delete_from_file("file_delete_test")
        
        # Verify it's gone
        loaded = _load_from_file("file_delete_test")
        assert loaded is None
    
    def test_safe_key_sanitization(self):
        """Test that keys are sanitized for filenames."""
        # Keys with special characters should be sanitized
        state = SimpleState("safe", 42)
        save_state("test/key\\with:special*chars", state)
        
        # Should still be loadable
        loaded = load_state("test/key\\with:special*chars", SimpleState)
        assert loaded is not None
        assert loaded.message == "safe"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
