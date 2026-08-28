from commerce.catalog import CatalogService
from commerce.inventory import InventoryService


def test_stock_states_and_sizes(tmp_path):
    inventory = InventoryService(CatalogService(tmp_path / "catalog.db"))
    assert inventory.stock("LING-001", "G") == 4
    assert inventory.stock("LING-002", "P") == 0
    assert inventory.stock("LING-001", "XG") is None
    assert inventory.stock("NAO-EXISTE", "G") is None

