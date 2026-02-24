from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MangaBase(BaseModel):
    titulo: str
    imagen_portada: Optional[str] = None
    id_clan: Optional[int] = None


class MangaCreate(MangaBase):
    pass


class Manga(MangaBase):
    id: int
    creado_en: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChapterBase(BaseModel):
    id_manga: int
    numero_capitulo: float
    vistas: int = 0
    creado_en: Optional[datetime] = None


class ChapterCreate(ChapterBase):
    pass


class Chapter(ChapterBase):
    id: int

    class Config:
        from_attributes = True


class PageBase(BaseModel):
    chapter_id: int
    image_url: Optional[str] = None
    image_hash: Optional[str] = None
    page_number: Optional[int] = None


class PageCreate(PageBase):
    pass


class Page(PageBase):
    id: int

    class Config:
        from_attributes = True


class RatingBase(BaseModel):
    manga_id: int
    rating: float


class RatingCreate(RatingBase):
    pass


class Rating(RatingBase):
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MangaStats(BaseModel):
    id: int
    total_likes: int
    total_follows: int
    total_vistas: int
    avg_rating: float
    trending_score: float
    ultima_actividad: Optional[datetime]


class MangaCatalog(BaseModel):
    id: int
    titulo: str
    imagen_portada: Optional[str]
    nombre: Optional[str]
    member_count: Optional[int]
    total_likes: int
    total_follows: int
    total_vistas: int
    avg_rating: float
    trending_score: float
    total_capitulos: int


class MangaCatalogList(BaseModel):
    total: int
    pages: int
    current_page: int
    results: List[MangaCatalog]