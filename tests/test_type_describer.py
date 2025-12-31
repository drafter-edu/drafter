from drafter.monitor.events.recursive_type_describer import analyze_type
from dataclasses import dataclass


@dataclass
class Animal:
    name: str

@dataclass
class Dog(Animal):
    age: int
    is_fuzzy: bool
    
@dataclass
class Cat(Animal):
    lives_left: int
    
@dataclass
class Item:
    name: str
    price: int
    stock: int

@dataclass
class State:
    items: list[Item]
    bought: list[str]
    money: int


def test_primitive_representation():
    assert analyze_type(42) == {
        "type": "int",
        "kind": "primitive",
        "value": 42,
        "id": id(42),
        "complexity": 1,
    }
    assert analyze_type("hello") == {
        "type": "str",
        "kind": "primitive",
        "value": "hello",
        "id": id("hello"),
        "complexity": 1,
    }
    assert analyze_type(3.14) == {
        "type": "float",
        "kind": "primitive",
        "value": 3.14,
        "id": id(3.14),
        "complexity": 1,
    }
    assert analyze_type(True) == {
        "type": "bool",
        "kind": "primitive",
        "value": True,
        "id": id(True),
        "complexity": 1,
    }
    
def test_primitive_lists_representation():
    value = [1, 2, 3]
    assert analyze_type(value) == {
        "type": "list",
        "kind": "homogenous_linear_collection",
        "elementType": "int",
        "fullType": "list[int]",
        "id": id(value),
        "elements": [
            {"type": "int", "kind": "primitive", "value": 1, "id": id(1), "complexity": 1},
            {"type": "int", "kind": "primitive", "value": 2, "id": id(2), "complexity": 1},
            {"type": "int", "kind": "primitive", "value": 3, "id": id(3), "complexity": 1},
        ],
        "complexity": 11,
    }
    
    values = ["a", "b", "c"]
    assert analyze_type(values) == {
        "type": "list",
        "kind": "homogenous_linear_collection",
        "elementType": "str",
        "fullType": "list[str]",
        "id": id(values),
        "elements": [
            {"type": "str", "kind": "primitive", "value": "a", "id": id("a"), "complexity": 1},
            {"type": "str", "kind": "primitive", "value": "b", "id": id("b"), "complexity": 1},
            {"type": "str", "kind": "primitive", "value": "c", "id": id("c"), "complexity": 1},
        ],
        "complexity": 11,
    }
    
def test_empty_list_representation():
    value = []
    assert analyze_type(value) == {
        "type": "list",
        "kind": "empty_linear_collection",
        "id": id(value),
        "complexity": 10,
    }
    
def test_dataclass_representation():
    dog = Dog(name="Buddy", age=5, is_fuzzy=True)
    assert analyze_type(dog) == {
        "type": "Dog",
        "kind": "dataclass",
        "id": id(dog),
        "fields": [
            {"name": "name", "value": {"type": "str", "kind": "primitive", "value": "Buddy", "id": id("Buddy"), "complexity": 1}},
            {"name": "age", "value": {"type": "int", "kind": "primitive", "value": 5, "id": id(5), "complexity": 1}},
            {"name": "is_fuzzy", "value": {"type": "bool", "kind": "primitive", "value": True, "id": id(True), "complexity": 1}},
        ],
        "complexity": 13,
    }
    
    cat = Cat(name="Whiskers", lives_left=9)
    assert analyze_type(cat) == {
        "type": "Cat",
        "kind": "dataclass",
        "id": id(cat),
        "fields": [
            {"name": "name", "value": {"type": "str", "kind": "primitive", "value": "Whiskers", "id": id("Whiskers"), "complexity": 1}},
            {"name": "lives_left", "value": {"type": "int", "kind": "primitive", "value": 9, "id": id(9), "complexity": 1}},
        ],
        "complexity": 12,
    }
    
def test_list_of_dataclasses_representation():
    dogs = [
        Dog(name="Buddy", age=5, is_fuzzy=True),
        Dog(name="Max", age=3, is_fuzzy=False),
    ]
    assert analyze_type(dogs) == {
        "type": "list",
        "kind": "homogenous_linear_collection",
        "elementType": "Dog",
        "fullType": "list[Dog]",
        "id": id(dogs),
        "elements": [
            {
                "type": "Dog",
                "kind": "dataclass",
                "id": id(dogs[0]),
                "fields": [
                    {"name": "name", "value": {"type": "str", "kind": "primitive", "value": "Buddy", "id": id("Buddy"), "complexity": 1}},
                    {"name": "age", "value": {"type": "int", "kind": "primitive", "value": 5, "id": id(5), "complexity": 1}},
                    {"name": "is_fuzzy", "value": {"type": "bool", "kind": "primitive", "value": True, "id": id(True), "complexity": 1}},
                ],
                "complexity": 13,
            },
            {
                "type": "Dog",
                "kind": "dataclass",
                "id": id(dogs[1]),
                "fields": [
                    {"name": "name", "value": {"type": "str", "kind": "primitive", "value": "Max", "id": id("Max"), "complexity": 1}},
                    {"name": "age", "value": {"type": "int", "kind": "primitive", "value": 3, "id": id(3), "complexity": 1}},
                    {"name": "is_fuzzy", "value": {"type": "bool", "kind": "primitive", "value": False, "id": id(False), "complexity": 1}},
                ],
                "complexity": 13,
            },
        ],
        "complexity": 23,
    }

def test_mixed_list_representation():
    value = [1, "two", 3.0]
    assert analyze_type(value) == {
        "type": "list",
        "kind": "linear_collection",
        "fullType": "list[float | int | str]",
        "elementType": "float | int | str",
        "id": id(value),
        "elements": [
            {"type": "int", "kind": "primitive", "value": 1, "id": id(1), "complexity": 1},
            {"type": "str", "kind": "primitive", "value": "two", "id": id("two"), "complexity": 1},
            {"type": "float", "kind": "primitive", "value": 3.0, "id": id(3.0), "complexity": 1},
        ],
        "complexity": 11,
    }
    
def test_2d_list_representation():
    values = [[1,2,3], [4,4,4], [7,8,9]]
    assert analyze_type(values) == {
        "type": "list",
        "kind": "homogenous_grid",
        "elementType": "list[int]",
        "fullType": "list[list[int]]",
        "id": id(values),
        "rows": [
            {"type": "list", "kind": "homogenous_linear_collection", "elementType": "int", "fullType": "list[int]", "id": id(values[0]), "elements": [
                {"type": "int", "kind": "primitive", "value": 1, "id": id(1), "complexity": 1},
                {"type": "int", "kind": "primitive", "value": 2, "id": id(2), "complexity": 1},
                {"type": "int", "kind": "primitive", "value": 3, "id": id(3), "complexity": 1},
            ], "complexity": 11},
            {"type": "list", "kind": "homogenous_linear_collection", "elementType": "int", "fullType": "list[int]", "id": id(values[1]), "elements": [
                {"type": "int", "kind": "primitive", "value": 4, "id": id(4), "complexity": 1},
                {"type": "int", "kind": "primitive", "value": 4, "id": id(4), "complexity": 1},
                {"type": "int", "kind": "primitive", "value": 4, "id": id(4), "complexity": 1},
            ], "complexity": 11},
            {"type": "list", "kind": "homogenous_linear_collection", "elementType": "int", "fullType": "list[int]", "id": id(values[2]), "elements": [
                {"type": "int", "kind": "primitive", "value": 7, "id": id(7), "complexity": 1},
                {"type": "int", "kind": "primitive", "value": 8, "id": id(8), "complexity": 1},
                {"type": "int", "kind": "primitive", "value": 9, "id": id(9), "complexity": 1},
            ], "complexity": 11},
        ],
        "complexity": 31,
    }
    
def test_shop_state_representation():
    state = State(
        items=[
            Item(name="Sword", price=100, stock=5),
            Item(name="Shield", price=150, stock=2),
        ],
        bought=["Potion"],
        money=250,
    )
    assert analyze_type(state) == {
        "type": "State",
        "kind": "dataclass",
        "id": id(state),
        "fields": [
            {
                "name": "items",
                "value": {
                    "type": "list",
                    "kind": "homogenous_linear_collection",
                    "elementType": "Item",
                    "fullType": "list[Item]",
                    "id": id(state.items),
                    "elements": [
                        {
                            "type": "Item",
                            "kind": "dataclass",
                            "id": id(state.items[0]),
                            "fields": [
                                {"name": "name", "value": {"type": "str", "kind": "primitive", "value": "Sword", "id": id("Sword"), "complexity": 1}},
                                {"name": "price", "value": {"type": "int", "kind": "primitive", "value": 100, "id": id(100), "complexity": 1}},
                                {"name": "stock", "value": {"type": "int", "kind": "primitive", "value": 5, "id": id(5), "complexity": 1}},
                            ],
                            "complexity": 13,
                        },
                        {
                            "type": "Item",
                            "kind": "dataclass",
                            "id": id(state.items[1]),
                            "fields": [
                                {"name": "name", "value": {"type": "str", "kind": "primitive", "value": "Shield", "id": id("Shield"), "complexity": 1}},
                                {"name": "price", "value": {"type": "int", "kind": "primitive", "value": 150, "id": id(150), "complexity": 1}},
                                {"name": "stock", "value": {"type": "int", "kind": "primitive", "value": 2, "id": id(2), "complexity": 1}},
                            ],
                            "complexity": 13,
                        },
                    ],
                    "complexity": 23,
                },
            },
            {
                "name": "bought",
                "value": {
                    "type": "list",
                    "kind": "homogenous_linear_collection",
                    "elementType": "str",
                    "fullType": "list[str]",
                    "id": id(state.bought),
                    "elements": [
                        {"type": "str", "kind": "primitive", "value": "Potion", "id": id("Potion"), "complexity": 1},
                    ],
                    "complexity": 11,
                },
            },
            {
                "name": "money",
                "value": {
                    "type": "int",
                    "kind": "primitive",
                    "value": 250,
                    "id": id(250),
                    "complexity": 1,
                },
            },
        ],
        "complexity": 45,
    }
    
def test_unknown_type_representation():
    value = object()
    assert analyze_type(value) == {
        "type": "object",
        "kind": "unknown",
        "id": id(value),
        "value": repr(value),
        "complexity": 1,
    }
    
def test_simple_dictionary_representation():
    value = {"a": 1, "b": 2}
    assert analyze_type(value) == {
        "type": "dict",
        "kind": "dict",
        "areKeysHomogenous": True,
        "areValuesHomogenous": True,
        "keyType": "str",
        "valueType": "int",
        "fullType": "dict[str, int]",
        "id": id(value),
        "entries": [
            { "key": {"type": "str", "kind": "primitive", "value": "a", "id": id("a"), "complexity": 1},
              "value": {"type": "int", "kind": "primitive", "value": 1, "id": id(1), "complexity": 1} },
            { "key": {"type": "str", "kind": "primitive", "value": "b", "id": id("b"), "complexity": 1},
              "value": {"type": "int", "kind": "primitive", "value": 2, "id": id(2), "complexity": 1} },
        ],
        "complexity": 21,
    }
    
def test_cycle_detection_representation():
    value = []
    value.append(value)  # Create a cycle
    assert analyze_type(value) == {
        "type": "list",
        "kind": "homogenous_linear_collection",
        "elementType": "list",
        "fullType": "list[list]",
        "id": id(value),
        "elements": [
            {
                "type": "list",
                "kind": "cycle_reference",
                "targetId": id(value),
                "complexity": 100,
            }
        ],
        "complexity": 110,
    }
    
def test_max_depth_representation():
    value = ((((("deep",),),),),)
    assert analyze_type(value, max_depth=2) == {
        "type": "tuple",
        "kind": "tuple",
        "id": id(value),
        "fullType": "tuple[tuple[tuple[tuple]]]",
        "elements": [
            {
                "type": "tuple",
                "kind": "tuple",
                "id": id(value[0]),
                "fullType": "tuple[tuple[tuple]]",
                "elements": [
                    {
                        "type": "tuple",
                        "kind": "tuple",
                        "id": id(value[0][0]),
                        "fullType": "tuple[tuple]",
                        "elements": [
                            {
                                "type": "tuple",
                                "id": id(value[0][0][0]),
                                "kind": "max_depth_reached",
                                "complexity": 1,
                            }
                        ],
                        "complexity": 11,
                    }
                ],
                "complexity": 21,
            }
        ],
        "complexity": 31,
    }
    
    
def test_simple_error_representation():
    # TODO: Create a scenario that triggers an error during analysis
    pass
    
def test_major_error_representation():
    class BadClass:
        def __repr__(self):
            raise ValueError("Bad repr!")
    
    value = BadClass()
    assert analyze_type(value) == {
        "type": "?",
        "kind": "complete_failure",
        "id": id(value),
        "error_message": "Bad repr!",
        "new_error_message": "Bad repr!",
        "complexity": 0,
    }