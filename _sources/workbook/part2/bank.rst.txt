============
Bank Account
============

A bank account let's you withdraw and deposit money.
We'll make a simple bank account application to support this.
Preview this website at |bank_preview|.

.. |bank_preview| raw:: html

    <a href="https://drafter-edu.github.io/examples/bank/" target="_blank">
        https://drafter-edu.github.io/examples/bank/</a>

.. image:: /workbook/part2/drafter_preview.png
    :width: 700
    :align: center
    :alt: Screenshot of the Bank Account application

**Step 1: Download** :download:`bank.py </workbook/part2/bank.py>` and put it into the same directory as the cookie clicker game.

The file contains the incomplete ``State``, five incomplete routes, six correct unit tests, and a call to ``start_server``.
You might be wondering why there are five routes when the image above only shows three pages.
The reason is because two of the routes (``finish_withdraw`` and ``finish_deposit``) are routes that modify
the state and then return the result of calling the ``index`` route.
The diagram below visualizes the relationships between the routes.

.. mermaid::

    flowchart
        start(("Start"))
        index["index"]
        start_withdraw["start_withdraw"]
        finish_withdraw[/"finish_withdraw"/]
        start_deposit["start_deposit"]
        finish_deposit[/"finish_deposit"/]
        start --> index
        index -- Withdraw --> start_withdraw
        start_withdraw -- "Withdraw(amount)" --> finish_withdraw
        start_withdraw -- Cancel --> index
        finish_withdraw -.-> index
        index -- Deposit --> start_deposit
        start_deposit -- "Deposit(amount)" --> finish_deposit
        start_deposit -- Cancel --> index
        finish_deposit -.-> index

To explain a little further:

* The ``index`` route has buttons to go to the ``start_withdraw`` and ``start_deposit`` routes.
* The ``start_withdraw`` and ``start_deposit`` have buttons to go to the ``finish_withdraw`` and ``finish_deposit`` routes, respectively,
  and also have a button to go back to the ``index`` route ("Cancel").
  The ``start_withdraw`` and ``start_deposit`` routes also have a ``TextBox`` to input the amount to withdraw or deposit,
  which is passed as a parameter to the ``finish_withdraw`` and ``finish_deposit`` routes.
* When the ``finish_withdraw`` and ``finish_deposit`` routes are called, they modify the state and
  then return the result of calling the ``index`` route.

**Step 2:** Inside the ``State`` class, add a ``balance`` field (an integer).

**Step 3:** You will need to create five routes:

1. The ``index`` route will consume a ``State`` object and return a ``Page`` (like most routes). The ``state`` in the
   returned ``Page`` will be unchanged. The content of the ``Page`` will be (in order):

    - The text ``"Your current balance is:: X"`` except instead of ``X`` it will be the ``balance`` of the ``State``
      object.
    - A ``Button`` with the text ``"Withdraw"`` that links to a ``start_withdraw`` route.
    - A ``Button`` with the text ``"Deposit"`` that links to a ``start_deposit`` route.

2. The ``start_withdraw`` route will consume a ``State`` object and return a ``Page``. The ``state`` in the returned
   ``Page`` will be unchanged. The content of the ``Page`` will be (in order):

    - The text ``"How much would you like to withdraw?"``.
    - A :py:func:`TextBox` that will be used to input the ``amount`` to withdraw, initially ``10``.
      Make sure you match the name for the ``TextBox`` to the name of the parameter in the ``finish_withdraw`` route.
    - A ``Button`` with the text ``"Withdraw"`` that links to a ``finish_withdraw`` route.
    - A ``Button`` with the text ``"Cancel"`` that links to the ``index`` route.

3. The ``finish_withdraw`` route will consume a ``State`` object and an ``amount`` (an ``int``).
   The ``balance`` of the ``state`` in the returned ``Page`` will be changed to reflect the withdrawal.
   The function should return the result of calling the ``index`` function with the modified ``state``.
   **Note**: Use the ``index`` function inside of this function to avoid code duplication.

4. The ``start_deposit`` route will consume a ``State`` object and return a ``Page``. The ``state`` in the returned
   ``Page`` will be unchanged. The content of the ``Page`` will be (in order):

    - The text ``"How much would you like to deposit?"``.
    - A :py:func:`TextBox` that will be used to input the ``amount`` to deposit, initially ``10``.
      Make sure you match the name for the ``TextBox`` to the name of the parameter in the ``finish_deposit`` route.
    - A ``Button`` with the text ``"Deposit"`` that links to a ``finish_deposit`` route.
    - A ``Button`` with the text ``"Cancel"`` that links to the ``index`` route.

5. The ``finish_deposit`` route will consume a ``State`` object and an ``amount`` (an ``int``).
   The ``balance`` of the ``state`` in the returned ``Page`` will be changed to reflect the deposit.
   The function should return the result of calling the ``index`` function with the modified ``state``.

**Step 4:** Run the application and check the tests to see if you have implemented the routes correctly.

This example has shown you how to have multiple pages that link together, with some routes that do not
modify the state and some routes that do modify the state.
You also have now seen a textbox, which is a way to get input from the user, and how that input can be passed
to another route as a parameter in order to update the state.
