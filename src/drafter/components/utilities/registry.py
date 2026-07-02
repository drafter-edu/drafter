from typing import Optional, Any
from drafter.components.utilities.contracts import ComponentContract
from drafter.data.converter import ConverterFn, ConversionContext, ConversionResult


class ComponentContractRegistry:
    def register(self, contract: ComponentContract) -> None: ...
    def get(self, component_name: str) -> Optional[ComponentContract]: ...
    def all(self) -> tuple[ComponentContract, ...]: ...


class ConverterRegistry:
    def register(
        self, target_type: Any, converter: ConverterFn, *, priority: int = 100
    ) -> None: ...
    def convert(self, ctx: ConversionContext) -> ConversionResult: ...


COMPONENT_CONTRACT_REGISTRY = ComponentContractRegistry()
CONVERTER_REGISTRY = ConverterRegistry()
