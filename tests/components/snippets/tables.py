from tests.components.snippets._base import TestableComponentSet
from drafter import *


tests = TestableComponentSet("tables")

# Simple table tests
tests.table_basic = Table(
    [["Alice", "30"], ["Bob", "25"], ["Charlie", "35"]], id="table1"
)
tests.table_basic = """
<table id="table1">
  <tbody>
    <tr>
      <td>
        Alice
      </td>
      <td>
        30
      </td>
    </tr>
    <tr>
      <td>
        Bob
      </td>
      <td>
        25
      </td>
    </tr>
    <tr>
      <td>
        Charlie
      </td>
      <td>
        35
      </td>
    </tr>
  </tbody>
</table>
"""

tests.table_with_header = Table(
    [["Alice", "30"], ["Bob", "25"]], header=["Name", "Age"]
)
tests.table_with_header = """
<table>
  <thead>
    <tr>
      <th>
        Name
      </th>
      <th>
        Age
      </th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        Alice
      </td>
      <td>
        30
      </td>
    </tr>
    <tr>
      <td>
        Bob
      </td>
      <td>
        25
      </td>
    </tr>
  </tbody>
</table>
"""

tests.table_numeric = Table(
    [
        ["Product", "Price", "Quantity"],
        ["Widget", "9.99", "5"],
        ["Gadget", "19.99", "3"],
    ],
    header=["Item", "Cost", "Count"],
)
tests.table_numeric = """
<table>
  <thead>
    <tr>
      <th>
        Item
      </th>
      <th>
        Cost
      </th>
      <th>
        Count
      </th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        Product
      </td>
      <td>
        Price
      </td>
      <td>
        Quantity
      </td>
    </tr>
    <tr>
      <td>
        Widget
      </td>
      <td>
        9.99
      </td>
      <td>
        5
      </td>
    </tr>
    <tr>
      <td>
        Gadget
      </td>
      <td>
        19.99
      </td>
      <td>
        3
      </td>
    </tr>
  </tbody>
</table>
"""

tests.table_with_class = Table(
    [["Red", "#FF0000"], ["Green", "#00FF00"]],
    header=["Color", "Hex"],
    classes="color-table",
    id="table1",
)
tests.table_with_class = """
<table class="color-table" id="table1">
  <thead>
    <tr>
      <th>
        Color
      </th>
      <th>
        Hex
      </th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        Red
      </td>
      <td>
        #FF0000
      </td>
    </tr>
    <tr>
      <td>
        Green
      </td>
      <td>
        #00FF00
      </td>
    </tr>
  </tbody>
</table>
"""

tests.table_single_row = Table(
    [["Single", "Row"]], header=["Col1", "Col2"], id="table2"
)
tests.table_single_row = """
<table id="table2">
  <thead>
    <tr>
      <th>
        Col1
      </th>
      <th>
        Col2
      </th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        Single
      </td>
      <td>
        Row
      </td>
    </tr>
  </tbody>
</table>
"""
