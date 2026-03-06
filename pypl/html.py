#!/usr/bin/env python3
from enum import IntEnum
from typing import Optional, List, IO, Tuple

class NodeType(IntEnum):
    ErrorNode = 0
    TextNode = 1
    DocumentNode = 2
    ElementNode = 3
    DoctypeNode = 4

class Attribute:
    def __init__(self, key: str, val: str):
        self.Key = key
        self.Val = val

class Node:
    def __init__(self):
        self.Type: NodeType = NodeType.ErrorNode
        self.Data: str = ""
        self.Attr: List[Attribute] = []
        self.FirstChild: Optional[Node] = None
        self.NextSibling: Optional[Node] = None

def Parse(r: IO) -> Tuple[Optional[Node], Optional[Exception]]:
    pass