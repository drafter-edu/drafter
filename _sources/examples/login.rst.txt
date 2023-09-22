.. _login:

Login Example
=============

Here is an application that allows you to login and logout. There is a very silly password checker that checks
if the username and password are correct based on literal values. This is just an example, and you should not
actually make a password checker like this! But it demonstrates how you can have a simple login system for your
application.


.. image:: ./login/login_index.png
    :width: 500

.. image:: ./login/login_ask.png
    :width: 500

.. image:: ./login/login_valid.png
    :width: 500

.. image:: ./login/login_reject.png
    :width: 500


.. literalinclude:: ./login/login.py
    :language: python

