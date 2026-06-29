"""
A Drafter example with many complex state types.
"""

from drafter import *
from PIL import Image as PILImage
import pandas as pd


@dataclass
class Person:
    first_name: str
    last_name: str
    age: int


@dataclass
class Address:
    street: str
    city: str
    zip_code: str


@dataclass
class Company:
    name: str
    address: Address
    employees: list[Person]


@dataclass
class State:
    pokemon: pd.DataFrame
    count: int
    grade: float
    name: str
    is_active: bool
    tags: list[str]
    flags: list[bool]
    metadata: dict[str, str]
    options: dict[str, bool]
    nested: dict[str, dict[str, int]]
    company: Company
    companies: list[Company]
    owner: Person
    addresses: list[Address]
    main_image: PILImage.Image
    all_images: list[PILImage.Image]


PEOPLE = [
    Person(first_name="John", last_name="Doe", age=30),
    Person(first_name="Jane", last_name="Smith", age=25),
    Person(first_name="Alice", last_name="Johnson", age=28),
    Person(first_name="Bob", last_name="Brown", age=32),
    Person(first_name="Charlie", last_name="Davis", age=29),
    Person(first_name="Dave", last_name="Evans", age=31),
    Person(first_name="Eve", last_name="Foster", age=27),
    Person(first_name="Frank", last_name="Green", age=26),
    Person(first_name="Grace", last_name="Harris", age=24),
    Person(first_name="Hank", last_name="Iverson", age=33),
    Person(first_name="Ivy", last_name="Jackson", age=30),
]
ADDRESSES = [
    Address(street="123 Main St", city="Anytown", zip_code="12345"),
    Address(street="456 Elm St", city="Othertown", zip_code="67890"),
    Address(street="789 Oak St", city="Sometown", zip_code="11223"),
    Address(street="101 Pine St", city="Newtown", zip_code="33445"),
    Address(street="202 Maple St", city="Oldtown", zip_code="55667"),
    Address(street="303 Birch St", city="Smalltown", zip_code="77889"),
    Address(street="404 Cedar St", city="Middletown", zip_code="99001"),
]

STARTING_DATA = State(
    pokemon=pd.read_csv("files/pokemon.csv"),
    count=33,
    grade=49.5,
    name="Lelouch Lamperouge",
    is_active=False,
    tags=["red", "blue", "green"],
    flags=[True, False, False, True, False],
    metadata={"creator": "admin", "version": "1.0"},
    options={"enable_feature_x": True, "enable_feature_y": False},
    nested={
        "level1": {"level2": 42, "level3": 84},
        "level4": {"level5": 168},
        "level6": {"level7": 336, "level8": 672},
    },
    company=Company(name="Acme Corp", address=ADDRESSES[0], employees=PEOPLE[:2]),
    companies=[
        Company(name="Python Co", address=ADDRESSES[1], employees=PEOPLE[2:4]),
        Company(name="Another Co", address=ADDRESSES[2], employees=PEOPLE[4:6]),
        Company(name="Yet Another Co", address=ADDRESSES[3], employees=PEOPLE[6:8]),
        Company(name="Final Co", address=ADDRESSES[4], employees=PEOPLE[8:10]),
    ],
    owner=Person(first_name="Guido", last_name="van Rossum", age=65),
    addresses=ADDRESSES[5:],
    main_image=PILImage.open(("images/soon-128.png")),
    all_images=[
        PILImage.open(("images/car_blockpy.gif")),
        PILImage.open(("images/soon-128.png")),
    ],
)


@route
def index(state: State):
    return Page(
        state,
        ["Nothing to see here... Check the debug dashboard!", Image(state.main_image)],
    )


start_server(STARTING_DATA)
