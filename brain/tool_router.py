import re
import unicodedata
from dataclasses import dataclass

from adult_commerce.age_gate import AgeGate
from adult_commerce.policy import AdultCommercePolicy
from commerce.catalog import CatalogService
from commerce.inventory import InventoryService
from commerce.recommendation import RecommendationService

from .action_router import ActionRequest, ActionResult, ActionRouter


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in text if not unicodedata.combining(char))


@dataclass
class Intent:
    action: str | None = None
    args: dict | None = None


class CommerceIntentRouter:
    categories = {
        "moda praia": "moda_praia", "maio": "moda_praia", "biquini": "moda_praia",
        "calcado": "calcados", "sandalia": "calcados", "sapato": "calcados",
        "moda": "moda", "roupa": "moda", "vestido": "moda", "blazer": "moda",
        "lingerie": "lingerie", "roupa intima": "lingerie",
        "eletronico": "eletronicos", "fone": "eletronicos", "microfone": "eletronicos", "ring light": "eletronicos",
        "sex shop": "bem_estar_adulto", "adulto": "bem_estar_adulto", "massageador": "bem_estar_adulto",
    }

    def classify(self, text: str) -> Intent:
        clean = normalize(text)
        sku_match = re.search(r"\b(?:MODA|PRAIA|CALC|LING|ELEC|ADULT)-\d{3}\b", clean.upper())
        sku = sku_match.group(0) if sku_match else None
        size_match = re.search(r"\b(?:tamanho\s+)?(PP|P|M|G|GG|XG|UNICO|3[4-9]|4[0-4])\b", clean.upper())
        size = size_match.group(1) if size_match else None
        category = next((value for term, value in self.categories.items() if term in clean), None)
        if sku and any(term in clean for term in ("como usa", "como usar", "instrucoes", "modo de uso")):
            return Intent("get_product_guide", {"sku": sku})
        if sku and any(term in clean for term in ("estoque", "tem", "disponivel", "tamanho")):
            return Intent("get_stock", {"sku": sku, "size": size})
        if sku and any(term in clean for term in ("preco", "custa", "valor")):
            return Intent("get_product", {"sku": sku})
        if sku:
            return Intent("get_product", {"sku": sku})
        if any(term in clean for term in ("recomenda", "indica", "sugere", "opcao")):
            return Intent("recommend_products", {"category": category})
        if category and any(term in clean for term in ("produto", "mostra", "catalogo", "tem")):
            return Intent("search_products", {"category": category})
        return Intent()


class CommerceToolRouter:
    def __init__(self, catalog: CatalogService, age_gate: AgeGate):
        self.catalog = catalog
        self.inventory = InventoryService(catalog)
        self.recommendation = RecommendationService(catalog)
        self.age_gate = age_gate
        self.policy = AdultCommercePolicy()
        self.actions = ActionRouter()
        self.actions.register("get_product", self._get_product)
        self.actions.register("get_stock", self._get_stock)
        self.actions.register("get_product_guide", self._get_product_guide)
        self.actions.register("search_products", self._search_products)
        self.actions.register("recommend_products", self._recommend_products)

    def execute(self, user_id: str, text: str, intent: Intent) -> ActionResult | None:
        if not intent.action:
            return None
        allowed, message = self.policy.validate_request(text)
        if not allowed:
            return ActionResult(action=intent.action, success=False, spoken_text=message or "Solicitação recusada.")
        args = {**(intent.args or {}), "include_adult": self.age_gate.is_verified(user_id)}
        if args.get("category") == "bem_estar_adulto" and not self.age_gate.is_verified(user_id):
            return ActionResult(action=intent.action, success=False, spoken_text="Para consultar produtos adultos, confirme primeiro que você tem 18 anos ou mais.")
        return self.actions.execute(ActionRequest(action=intent.action, action_args=args))

    def execute_requested(self, user_id: str, text: str, request: ActionRequest) -> ActionResult:
        allowed, message = self.policy.validate_request(text)
        if not allowed:
            return ActionResult(action=request.action, success=False, spoken_text=message or "Solicitação recusada.")
        args = {**request.action_args, "include_adult": self.age_gate.is_verified(user_id)}
        if args.get("category") == "bem_estar_adulto" and not self.age_gate.is_verified(user_id):
            return ActionResult(action=request.action, success=False, spoken_text="Para consultar produtos adultos, confirme primeiro que você tem 18 anos ou mais.")
        return self.actions.execute(ActionRequest(action=request.action, action_args=args))

    def _get_product(self, sku: str, include_adult: bool = False) -> ActionResult:
        product = self.catalog.get(sku, include_adult)
        if not product:
            return ActionResult(action="get_product", success=False, spoken_text="Não encontrei esse produto no catálogo disponível.")
        stock = sum(product.stock.values())
        return ActionResult(action="get_product", success=True, data=product.model_dump(), spoken_text=f"{product.name} ({product.sku}) custa R$ {product.price:.2f} e possui {stock} unidade(s) em estoque.")

    def _get_stock(self, sku: str, size: str | None = None, include_adult: bool = False) -> ActionResult:
        product = self.catalog.get(sku, include_adult)
        if not product:
            return ActionResult(action="get_stock", success=False, spoken_text="Não encontrei esse produto no catálogo disponível.")
        quantity = self.inventory.stock(sku, size, include_adult)
        if size and quantity is None:
            return ActionResult(action="get_stock", success=False, spoken_text=f"O tamanho {size} não existe para {product.name}.")
        if size:
            text = f"{product.name} tem {quantity} unidade(s) no tamanho {size}." if quantity else f"{product.name} está sem estoque no tamanho {size}."
        else:
            text = f"Estoque de {product.name}: " + ", ".join(f"{key}: {value}" for key, value in product.stock.items()) + "."
        return ActionResult(action="get_stock", success=True, data={"sku": sku, "size": size, "stock": quantity}, spoken_text=text)

    def _get_product_guide(self, sku: str, include_adult: bool = False) -> ActionResult:
        product = self.catalog.get(sku, include_adult)
        if not product:
            return ActionResult(action="get_product_guide", success=False, spoken_text="Não encontrei esse produto no catálogo disponível ou o acesso 18+ ainda não foi confirmado.")
        if not product.usage_guidance:
            return ActionResult(action="get_product_guide", success=False, spoken_text=f"Ainda não há instruções verificadas cadastradas para {product.name}. Consulte o manual do fabricante.")
        guidance = " ".join(f"{index}. {item}" for index, item in enumerate(product.usage_guidance, 1))
        safety = " ".join(product.safety_notes)
        return ActionResult(
            action="get_product_guide", success=True,
            data={"sku": sku, "usage_guidance": product.usage_guidance, "safety_notes": product.safety_notes},
            spoken_text=f"Orientação segura para {product.name}: {guidance} Cuidados: {safety}",
        )

    def _search_products(self, category: str | None = None, include_adult: bool = False) -> ActionResult:
        products = self.catalog.search(category=category, include_adult=include_adult)
        if not products:
            return ActionResult(action="search_products", success=False, spoken_text="Não encontrei produtos nessa categoria.")
        text = "Encontrei: " + "; ".join(f"{item.name} ({item.sku}) — R$ {item.price:.2f}" for item in products[:5]) + "."
        return ActionResult(action="search_products", success=True, data={"products": [item.model_dump() for item in products]}, spoken_text=text)

    def _recommend_products(self, category: str | None = None, include_adult: bool = False) -> ActionResult:
        products = self.recommendation.recommend(category, include_adult)
        if not products:
            return ActionResult(action="recommend_products", success=False, spoken_text="Não tenho uma recomendação disponível nessa categoria.")
        text = "Posso recomendar: " + "; ".join(f"{item.name} ({item.sku}) — R$ {item.price:.2f}" for item in products) + "."
        return ActionResult(action="recommend_products", success=True, data={"products": [item.model_dump() for item in products]}, spoken_text=text)
