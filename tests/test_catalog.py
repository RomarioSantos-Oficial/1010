from commerce.catalog import CatalogService


def test_catalog_product_price_stock_and_image(tmp_path):
    catalog = CatalogService(tmp_path / "catalog.db")
    product = catalog.get("LING-001")
    assert product.name == "Conjunto Aurora"
    assert product.price == 149.90
    assert product.stock["G"] == 4
    assert product.image


def test_product_not_found_and_missing_image(tmp_path):
    catalog = CatalogService(tmp_path / "catalog.db")
    assert catalog.get("NAO-EXISTE") is None
    assert catalog.get("ELEC-003").image is None


def test_category_and_adult_products_are_filtered(tmp_path):
    catalog = CatalogService(tmp_path / "catalog.db")
    assert len(catalog.search(category="categoria_inexistente")) == 0
    assert not any(product.adults_only for product in catalog.search())
    assert len(catalog.search(category="bem_estar_adulto", include_adult=True)) == 3

