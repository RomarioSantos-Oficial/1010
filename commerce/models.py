from pydantic import BaseModel, Field


class Product(BaseModel):
    sku: str = Field(pattern=r"^[A-Z0-9-]+$")
    name: str
    category: str
    description: str
    price: float = Field(ge=0)
    stock: dict[str, int]
    image: str | None = None
    usage_guidance: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    adults_only: bool = False
    active: bool = True

    @property
    def available(self) -> bool:
        return any(quantity > 0 for quantity in self.stock.values())
