import json
import sqlite3
from pathlib import Path

from .models import Product

SEED_PRODUCTS = [
    Product(sku="MODA-001", name="Vestido Aurora", category="moda", price=189.90, stock={"P": 2, "M": 5, "G": 3}, description="Vestido midi elegante em tecido leve.", image="assets/products/MODA-001.jpg"),
    Product(sku="MODA-002", name="Blazer Serena", category="moda", price=249.90, stock={"P": 1, "M": 4, "G": 2}, description="Blazer feminino de corte clássico.", image="assets/products/MODA-002.jpg"),
    Product(sku="PRAIA-001", name="Maiô Oceano", category="moda_praia", price=179.90, stock={"P": 2, "M": 5, "G": 3}, description="Maiô de corpo inteiro com proteção UV.", image="assets/products/PRAIA-001.jpg"),
    Product(sku="PRAIA-002", name="Saída Solar", category="moda_praia", price=129.90, stock={"P": 2, "M": 4, "G": 2}, description="Saída de praia leve para sobreposição.", image="assets/products/PRAIA-002.jpg"),
    Product(sku="CALC-001", name="Sandália Brisa", category="calcados", price=159.90, stock={"35": 2, "36": 4, "37": 5, "38": 2}, description="Sandália de tiras para looks de verão.", image="assets/products/CALC-001.jpg"),
    Product(sku="LING-001", name="Conjunto Aurora", category="lingerie", price=149.90, stock={"P": 3, "M": 8, "G": 4}, description="Conjunto em renda com acabamento delicado.", image="assets/products/LING-001.jpg"),
    Product(sku="LING-002", name="Body Serena", category="lingerie", price=169.90, stock={"P": 0, "M": 3, "G": 2}, description="Body em renda de estilo discreto.", image="assets/products/LING-002.jpg"),
    Product(sku="ELEC-001", name="Fone Luna Air", category="eletronicos", price=299.90, stock={"UNICO": 12}, description="Fone Bluetooth com estojo de carregamento.", image="assets/products/ELEC-001.jpg"),
    Product(sku="ELEC-002", name="Ring Light Studio", category="eletronicos", price=219.90, stock={"UNICO": 6}, description="Iluminação LED ajustável para conteúdo e lives.", image="assets/products/ELEC-002.jpg"),
    Product(sku="ELEC-003", name="Microfone Live USB", category="eletronicos", price=389.90, stock={"UNICO": 0}, description="Microfone condensador USB para transmissões.", image=None),
    Product(sku="ADULT-001", name="Massageador Íris", category="bem_estar_adulto", price=199.90, stock={"UNICO": 7}, description="Massageador adulto de uso pessoal em silicone compatível.", image="assets/products/ADULT-001.jpg", adults_only=True, usage_guidance=["Leia o manual e carregue o produto antes do primeiro uso.", "Comece na menor intensidade e ajuste apenas conforme o conforto.", "Higienize antes e depois do uso conforme o manual."], safety_notes=["Uso exclusivo de adultos e sempre consensual.", "Interrompa o uso se houver dor, irritação ou dano no produto."]),
    Product(sku="ADULT-002", name="Kit Bem-Estar Luna", category="bem_estar_adulto", price=129.90, stock={"UNICO": 5}, description="Kit adulto de cuidados íntimos.", image="assets/products/ADULT-002.jpg", adults_only=True, usage_guidance=["Confira no manual a finalidade de cada item.", "Higienize os itens antes e depois do uso.", "Guarde cada item seco e separado."], safety_notes=["Uso exclusivo de adultos e sempre consensual.", "Não compartilhe itens sem a higienização indicada pelo fabricante."]),
    Product(sku="ADULT-003", name="Óleo de Massagem Noite", category="bem_estar_adulto", price=69.90, stock={"UNICO": 9}, description="Óleo corporal para massagem, uso externo.", image="assets/products/ADULT-003.jpg", adults_only=True, usage_guidance=["Aplique pequena quantidade na pele externa e massageie.", "Faça um teste em pequena área antes do uso amplo."], safety_notes=["Somente para uso externo.", "Evite olhos, mucosas e pele irritada; suspenda em caso de reação."]),
]


class CatalogService:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def initialize(self) -> None:
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS products (
                    sku TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
                    description TEXT NOT NULL, price REAL NOT NULL CHECK(price >= 0),
                    stock_json TEXT NOT NULL, image TEXT,
                    usage_json TEXT NOT NULL DEFAULT '[]', safety_json TEXT NOT NULL DEFAULT '[]',
                    adults_only INTEGER NOT NULL DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS ix_products_category ON products(category,active);
            """)
            columns = {row[1] for row in db.execute("PRAGMA table_info(products)")}
            if "usage_json" not in columns:
                db.execute("ALTER TABLE products ADD COLUMN usage_json TEXT NOT NULL DEFAULT '[]'")
            if "safety_json" not in columns:
                db.execute("ALTER TABLE products ADD COLUMN safety_json TEXT NOT NULL DEFAULT '[]'")
            for product in SEED_PRODUCTS:
                db.execute(
                    "INSERT OR IGNORE INTO products(sku,name,category,description,price,stock_json,image,usage_json,safety_json,adults_only,active) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (product.sku, product.name, product.category, product.description, product.price, json.dumps(product.stock), product.image, json.dumps(product.usage_guidance), json.dumps(product.safety_notes), product.adults_only, product.active),
                )
                if product.usage_guidance:
                    db.execute(
                        "UPDATE products SET usage_json=?, safety_json=? WHERE sku=? AND usage_json='[]'",
                        (json.dumps(product.usage_guidance), json.dumps(product.safety_notes), product.sku),
                    )

    @staticmethod
    def _product(row: sqlite3.Row | None) -> Product | None:
        if row is None:
            return None
        data = dict(row)
        data["stock"] = json.loads(data.pop("stock_json"))
        data["usage_guidance"] = json.loads(data.pop("usage_json", "[]"))
        data["safety_notes"] = json.loads(data.pop("safety_json", "[]"))
        data["adults_only"] = bool(data["adults_only"])
        data["active"] = bool(data["active"])
        data.pop("updated_at", None)
        return Product.model_validate(data)

    def get(self, sku: str, include_adult: bool = False) -> Product | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM products WHERE sku=? AND active=1", (sku.upper(),)).fetchone()
        product = self._product(row)
        return None if product and product.adults_only and not include_adult else product

    def search(self, query: str = "", category: str | None = None, include_adult: bool = False, limit: int = 10) -> list[Product]:
        clauses, params = ["active=1"], []
        if not include_adult:
            clauses.append("adults_only=0")
        if category:
            clauses.append("category=?")
            params.append(category)
        if query:
            clauses.append("(lower(name) LIKE ? OR lower(description) LIKE ? OR lower(category) LIKE ?)")
            term = f"%{query.casefold()}%"
            params.extend([term, term, term])
        params.append(limit)
        with self.connect() as db:
            rows = db.execute(f"SELECT * FROM products WHERE {' AND '.join(clauses)} ORDER BY name LIMIT ?", params).fetchall()
        return [self._product(row) for row in rows]

    def categories(self, include_adult: bool = False) -> list[str]:
        clause = "" if include_adult else "AND adults_only=0"
        with self.connect() as db:
            return [row[0] for row in db.execute(f"SELECT DISTINCT category FROM products WHERE active=1 {clause} ORDER BY category")]

    def health(self) -> bool:
        with self.connect() as db:
            return db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
