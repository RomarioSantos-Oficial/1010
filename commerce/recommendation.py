from .catalog import CatalogService
from .models import Product


class RecommendationService:
    def __init__(self, catalog: CatalogService):
        self.catalog = catalog

    def recommend(self, category: str | None = None, include_adult: bool = False, limit: int = 3) -> list[Product]:
        products = self.catalog.search(category=category, include_adult=include_adult, limit=20)
        return sorted((item for item in products if item.available), key=lambda item: (-sum(item.stock.values()), item.price))[:limit]
