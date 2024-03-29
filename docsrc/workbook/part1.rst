.. _workbook:

---------------
Workbook Part 1
---------------


Modern application development is focused on web development.

==============
Cookie Clicker
==============

Preview this website: https://drafter-edu.github.io/examples/cookie-clicker/

Cookie Clicker is a simple game where you click a cookie to get more cookies.

First, download the following file full of unit tests: :download:`workbook_part_1_tests.py`.

You will need to create a ``State`` class that has a ``cookies`` field (an integer).

Then, you will need to create two routes:

1. The ``index`` route will consume a ``State`` object and return a ``Page``. The ``state`` in the
   returned ``Page`` will be unchanged. The content of the ``Page`` will be (in order):

    - The text ``"You have X cookies"`` except instead of ``X`` it will be the ``cookies`` of the ``State``
      object.
    - A ``Button`` with the text ``"🍪"`` that links to a ``cookie`` route.

2. The ``cookie`` route will consume a ``State`` object and return a ``Page``.
   The ``cookies`` of the ``state`` in the returned ``Page`` will be increased by 1.
   The function should return the result of calling the ``index`` function with the modified ``state``.

Finally, call ``start_server``, passing in a ``State`` object with ``cookies`` set to ``0``.

============
Bank Account
============

Preview this website: https://drafter-edu.github.io/examples/bank-account/

A bank account let's you withdraw and deposit money.

You will need to create a ``State`` class that has a ``balance`` field (an integer).

Then, you will need to create five routes:

1. The ``index`` route will consume a ``State`` object and return a ``Page`` (like most routes). The ``state`` in the
   returned ``Page`` will be unchanged. The content of the ``Page`` will be (in order):

    - The text ``"Your balance is: X"`` except instead of ``X`` it will be the ``balance`` of the ``State``
      object.
    - A ``Button`` with the text ``"Withdraw"`` that links to a ``start_withdraw`` route.
    - A ``Button`` with the text ``"Deposit"`` that links to a ``start_deposit`` route.

2. The ``start_withdraw`` route will consume a ``State`` object and return a ``Page``. The ``state`` in the returned
   ``Page`` will be unchanged. The content of the ``Page`` will be (in order):

    - The text ``"How much would you like to withdraw?"``.
    - A ``TextBox`` that will be used to input the ``amount`` to withdraw, initially ``10``.
    - A ``Button`` with the text ``"Withdraw"`` that links to a ``finish_withdraw`` route.
    - A ``Button`` with the text ``"Cancel"`` that links to the ``index`` route.

3. The ``finish_withdraw`` route will consume a ``State`` object and an ``amount`` (an ``int``).
   The ``balance`` of the ``state`` in the returned ``Page`` will be changed to reflect the withdrawal.
   The function should return the result of calling the ``index`` function with the modified ``state``.
   **Note**: Use the ``index`` function inside of this function to avoid code duplication.

4. The ``start_deposit`` route will consume a ``State`` object and return a ``Page``. The ``state`` in the returned
   ``Page`` will be unchanged. The content of the ``Page`` will be (in order):

    - The text ``"How much would you like to deposit?"``.
    - A ``TextBox`` that will be used to input the ``amount`` to deposit, initially ``10``.
    - A ``Button`` with the text ``"Deposit"`` that links to a ``finish_deposit`` route.
    - A ``Button`` with the text ``"Cancel"`` that links to the ``index`` route.

5. The ``finish_deposit`` route will consume a ``State`` object and an ``amount`` (an ``int``).
   The ``balance`` of the ``state`` in the returned ``Page`` will be changed to reflect the deposit.
   The function should return the result of calling the ``index`` function with the modified ``state``.

Finally, call ``start_server``, passing in a ``State`` object with ``balance`` set to ``100``.

=====================
Simple Adventure Game
=====================

