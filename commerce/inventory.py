from .catalog import CatalogService


class InventoryService:
    def __init__(self, catalog: CatalogService):
        self.catalog = catalog

    def stock(self, sku: str, size: str | None = None, include_adult: bool = False) -> int | dict[str, int] | None:
        product = self.catalog.get(sku, include_adult)
        if not product:
            return None
        if size:
            return product.stock.get(size.upper())
        return product.stock

