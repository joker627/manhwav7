from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.dependencies.auth import get_current_user
from app.schemas.manga import MangaCatalog, RatingCreate, MangaCatalogList
from app.service.manga import (
    get_manga_catalog, get_manga_by_id, get_chapters_by_manga, get_chapter_by_id, get_pages_by_chapter,
    create_rating, get_user_rating, like_manga, follow_manga, increment_views
)

router = APIRouter()

@router.get("/catalog", response_model=MangaCatalogList)
def read_manga_catalog(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    format_type: Optional[str] = Query(None, alias="format"),
    sort_by: Optional[str] = "trending"
):
    return get_manga_catalog(
        page=page, 
        limit=limit, 
        search=search, 
        status=status, 
        format_type=format_type, 
        sort_by=sort_by
    )

@router.get("/{manga_id}")
def read_manga(manga_id: int):
    manga = get_manga_by_id(manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    return manga

@router.get("/{manga_id}/chapters")
def read_chapters(manga_id: int):
    return get_chapters_by_manga(manga_id)

@router.get("/chapters/{chapter_id}")
def read_chapter(chapter_id: int):
    chapter = get_chapter_by_id(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    increment_views(chapter_id)
    return chapter

@router.get("/chapters/{chapter_id}/pages")
def read_pages(chapter_id: int):
    return get_pages_by_chapter(chapter_id)

@router.post("/{manga_id}/rate")
def rate_manga(manga_id: int, rating: RatingCreate, current_user: dict = Depends(get_current_user)):
    rating.manga_id = manga_id
    return create_rating(current_user["id"], rating)

@router.get("/{manga_id}/my-rating")
def get_my_rating(manga_id: int, current_user: dict = Depends(get_current_user)):
    return get_user_rating(current_user["id"], manga_id)

@router.post("/{manga_id}/like")
def like(manga_id: int, current_user: dict = Depends(get_current_user)):
    return like_manga(current_user["id"], manga_id)

@router.post("/{manga_id}/follow")
def follow(manga_id: int, current_user: dict = Depends(get_current_user)):
    return follow_manga(current_user["id"], manga_id)