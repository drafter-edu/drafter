from dataclasses import dataclass


@dataclass
class DrafterBinaryFile:
    filename: str
    content: bytes
    content_type: str
    size: int
    
@dataclass
class DrafterTextFile:
    filename: str
    content: str
    content_type: str
    size: int