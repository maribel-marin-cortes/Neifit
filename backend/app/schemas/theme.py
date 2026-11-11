from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


HexColor = str


class CompanyTheme(BaseModel):
    model_config = ConfigDict(extra='forbid')
    primary_color: HexColor = Field('#7A4E2D', pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: HexColor = Field('#5F8D4E', pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: HexColor = Field('#D98CA4', pattern=r'^#[0-9A-Fa-f]{6}$')
    background_color: HexColor = Field('#F6E7D8', pattern=r'^#[0-9A-Fa-f]{6}$')
    surface_color: HexColor = Field('#FFF8F2', pattern=r'^#[0-9A-Fa-f]{6}$')
    text_color: HexColor = Field('#4B2E1F', pattern=r'^#[0-9A-Fa-f]{6}$')
    logo_url: str | None = Field(None, max_length=2048)
    icon_url: str | None = Field(None, max_length=2048)
    cover_url: str | None = Field(None, max_length=2048)
    heading_font: Literal['Poppins','Montserrat','Inter','Lora','Roboto'] = 'Poppins'
    body_font: Literal['Inter','Roboto','Montserrat','Lora','Poppins'] = 'Inter'
    border_radius: int = Field(16, ge=0, le=32)
    button_style: Literal['solido','contorno','suave'] = 'solido'
    published: bool = True
