from enum import StrEnum
from typing import List
from pydantic import BaseModel, Field


class NivelCriticidad(StrEnum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class ResponseSchema(BaseModel):
    tecnologias: List[str] = Field(min_length=1)
    nivel_de_criticidad: NivelCriticidad
    resumen_tecnico: str = Field(min_length=1)