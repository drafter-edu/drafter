"""
Registries for component-declared metadata.

Components define what they emit; these registries aggregate that metadata
at startup so the router can reason globally (binding, aliases, docs
generation, and consistency checks).

The converter registry itself lives in the router layer
(:mod:`drafter.router.parameters.conversion`), since the router owns
conversion policy; it is re-exported here so components have a natural place
to import it from when registering component-specific converters.
"""

from typing import Optional

from drafter.components.utilities.contracts import ComponentContract


def __getattr__(name: str):
    # Lazy re-export: components import the converter registry from here, but
    # the router layer must not load while component modules are still
    # initializing (it would recreate a circular import through drafter.data).
    if name in ("CONVERTER_REGISTRY", "ConverterRegistry"):
        from drafter.router.parameters import conversion

        return getattr(conversion, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class ComponentContractRegistry:
    """Central collection of every component's declared contract."""

    def __init__(self) -> None:
        self._contracts: dict[str, ComponentContract] = {}

    def register(self, contract: ComponentContract) -> None:
        self._contracts[contract.component_name] = contract

    def get(self, component_name: str) -> Optional[ComponentContract]:
        return self._contracts.get(component_name)

    def all(self) -> tuple[ComponentContract, ...]:
        return tuple(self._contracts.values())

    def alias_map(self) -> dict[str, str]:
        """Aggregate event-field aliases across all contracts.

        Returns:
            Mapping of alias name -> canonical field name, used by the
            router's normalize stage.
        """
        aliases: dict[str, str] = {}
        for contract in self._contracts.values():
            for event in contract.emitted_events:
                for canonical, alternates in event.aliases.items():
                    for alternate in alternates:
                        aliases[alternate] = canonical
        return aliases

    def synthetic_fields(self) -> frozenset[str]:
        """Every non-form field any component contributes to the payload."""
        return frozenset(
            name
            for contract in self._contracts.values()
            for name in contract.synthetic_fields
        )


COMPONENT_CONTRACT_REGISTRY = ComponentContractRegistry()
