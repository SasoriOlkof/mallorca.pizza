"""Runtime state shared by FastAPI routes."""

from dataclasses import dataclass

from mallorca_pizza.config.catalog import RestaurantCatalog


@dataclass(slots=True)
class RuntimeState:
    catalog: RestaurantCatalog | None = None

    @property
    def ready(self) -> bool:
        return self.catalog is not None
