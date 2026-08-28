from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class IdentityConfig(BaseModel):
    type: str = "virtual_ai_character"
    disclosure: bool = True


class StyleConfig(BaseModel):
    warmth: float = Field(0.85, ge=0, le=1)
    humor: float = Field(0.55, ge=0, le=1)
    formality: float = Field(0.30, ge=0, le=1)
    detail: float = Field(0.55, ge=0, le=1)
    affection: float = Field(0.75, ge=0, le=1)


class SalesConfig(BaseModel):
    enabled: bool = True
    consult_catalog_before_price: bool = True
    never_invent_stock: bool = True
    never_invent_product_specs: bool = True


class MemoryConfig(BaseModel):
    remember_interaction_preferences: bool = True
    remember_product_interests: bool = True
    remember_sensitive_personal_data: bool = False


class AdultCommerceConfig(BaseModel):
    enabled: bool = True
    adults_only: bool = True


class PersonaConfig(BaseModel):
    name: str
    language: str = "pt-BR"
    identity: IdentityConfig = IdentityConfig()
    style: StyleConfig = StyleConfig()
    sales: SalesConfig = SalesConfig()
    memory: MemoryConfig = MemoryConfig()
    adult_commerce: AdultCommerceConfig = AdultCommerceConfig()


def load_persona(path: Path | str) -> PersonaConfig:
    with Path(path).open(encoding="utf-8") as stream:
        return PersonaConfig.model_validate(yaml.safe_load(stream))

