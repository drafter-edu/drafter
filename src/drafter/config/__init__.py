"""Configuration package for Drafter.

Groups the configuration dataclasses for each core component of the system:
bootstrapping (`bootstrap`), the development app server (`app_server`), the
static site builder (`app_builder`), settings shared by the server and builder
(`app_common`), and the client-side page renderer (`client_server`). All of
these inherit from `BaseConfiguration` (`base`), which layers defaults,
environment variables, and command line arguments, and they are aggregated
into the `SystemConfiguration` singleton (`system`). Supporting modules define
the execution engine type (`engines`), student-facing site metadata
(`site_information`), and reserved internal URL routes (`urls`).
"""
