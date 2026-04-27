from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.infrastructure.repositories.sql_repositories import SQLAlchemyDrawingRepository, SQLAlchemyUserRepository
from app.domain.factories.factories import DomainFactory
from app.application.commands.handlers import (
    CreateDrawingCommand, CreateDrawingHandler,
    AddLayerCommand, AddLayerHandler,
    ToggleLikeCommand, ToggleLikeHandler,
    DeleteDrawingCommand, DeleteDrawingHandler,
    FollowUserCommand, FollowUserHandler,
    UnfollowUserCommand, UnfollowUserHandler
)
from app.application.queries.handlers import (
    GetDrawingQuery, GetDrawingHandler,
    GetFeedQuery, GetFeedHandler,
    SearchQuery, SearchHandler,
    GetUserDrawingsQuery, GetUserDrawingsHandler,
    GetUserContributedDrawingsQuery, GetUserContributedDrawingsHandler,
    IsFollowingQuery, IsFollowingHandler,
    GetFollowersQuery, GetFollowersHandler
)
from app.presentation.schemas.schemas import DrawingCreate, DrawingResponse, LayerCreate, LayerResponse, UserResponse
from app.core.security import get_current_user
from app.domain.exceptions.exceptions import DomainException, EntityNotFoundError, EmailAlreadyExistsError
from app.infrastructure.db.models.models import User as DBUser

router = APIRouter(prefix="/drawings", tags=["drawings"])

# Dependency injectors
def get_create_drawing_handler(db: Session = Depends(get_db)) -> CreateDrawingHandler:
    user_repo = SQLAlchemyUserRepository(db)
    drawing_repo = SQLAlchemyDrawingRepository(db)
    factory = DomainFactory(user_repo)
    return CreateDrawingHandler(drawing_repo, factory)

def get_drawing_query_handler(db: Session = Depends(get_db)) -> GetDrawingHandler:
    drawing_repo = SQLAlchemyDrawingRepository(db)
    return GetDrawingHandler(drawing_repo)

def get_feed_query_handler(db: Session = Depends(get_db)) -> GetFeedHandler:
    drawing_repo = SQLAlchemyDrawingRepository(db)
    return GetFeedHandler(drawing_repo)

def get_search_query_handler(db: Session = Depends(get_db)) -> SearchHandler:
    drawing_repo = SQLAlchemyDrawingRepository(db)
    return SearchHandler(drawing_repo)

def get_user_drawings_query_handler(db: Session = Depends(get_db)) -> GetUserDrawingsHandler:
    drawing_repo = SQLAlchemyDrawingRepository(db)
    return GetUserDrawingsHandler(drawing_repo)

def get_user_contributed_drawings_query_handler(db: Session = Depends(get_db)) -> GetUserContributedDrawingsHandler:
    drawing_repo = SQLAlchemyDrawingRepository(db)
    return GetUserContributedDrawingsHandler(drawing_repo)

def get_is_following_query_handler(db: Session = Depends(get_db)) -> IsFollowingHandler:
    drawing_repo = SQLAlchemyDrawingRepository(db)
    return IsFollowingHandler(drawing_repo)

def get_followers_query_handler(db: Session = Depends(get_db)) -> GetFollowersHandler:
    user_repo = SQLAlchemyUserRepository(db)
    return GetFollowersHandler(user_repo)

def get_delete_drawing_handler(db: Session = Depends(get_db)) -> DeleteDrawingHandler:
    drawing_repo = SQLAlchemyDrawingRepository(db)
    return DeleteDrawingHandler(drawing_repo)

def get_add_layer_handler(db: Session = Depends(get_db)) -> AddLayerHandler:
    drawing_repo = SQLAlchemyDrawingRepository(db)
    return AddLayerHandler(drawing_repo)

def get_toggle_like_handler(db: Session = Depends(get_db)) -> ToggleLikeHandler:
    drawing_repo = SQLAlchemyDrawingRepository(db)
    return ToggleLikeHandler(drawing_repo)

def get_follow_user_handler(db: Session = Depends(get_db)) -> FollowUserHandler:
    user_repo = SQLAlchemyUserRepository(db)
    return FollowUserHandler(user_repo)

def get_unfollow_user_handler(db: Session = Depends(get_db)) -> UnfollowUserHandler:
    user_repo = SQLAlchemyUserRepository(db)
    return UnfollowUserHandler(user_repo)

@router.post("/", response_model=DrawingResponse, status_code=status.HTTP_201_CREATED)
def create_drawing(
    drawing_in: DrawingCreate,
    handler: CreateDrawingHandler = Depends(get_create_drawing_handler),
    query_handler: GetDrawingHandler = Depends(get_drawing_query_handler),
    current_user: DBUser = Depends(get_current_user)
):
    try:
        drawing_id = handler.handle(CreateDrawingCommand(
            owner_id=current_user.id,
            title=drawing_in.title,
            first_layer_data=drawing_in.first_layer_data
        ))
        return query_handler.handle(GetDrawingQuery(drawing_id))
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/feed", response_model=List[DrawingResponse])
def get_feed(
    q: Optional[str] = None,
    feed_handler: GetFeedHandler = Depends(get_feed_query_handler),
    search_handler: SearchHandler = Depends(get_search_query_handler),
    current_user: DBUser = Depends(get_current_user)
):
    if q:
        results = search_handler.handle(SearchQuery(q))
        return results["drawings"]
    return feed_handler.handle(GetFeedQuery(current_user.id))

@router.get("/search")
def search(
    q: str,
    handler: SearchHandler = Depends(get_search_query_handler)
):
    return handler.handle(SearchQuery(q))

@router.get("/users/{user_id}/drawings", response_model=List[DrawingResponse])
def get_user_drawings(
    user_id: int,
    handler: GetUserDrawingsHandler = Depends(get_user_drawings_query_handler)
):
    return handler.handle(GetUserDrawingsQuery(user_id))

@router.get("/users/{user_id}/contributed", response_model=List[DrawingResponse])
def get_user_contributed_drawings(
    user_id: int,
    handler: GetUserContributedDrawingsHandler = Depends(get_user_contributed_drawings_query_handler)
):
    return handler.handle(GetUserContributedDrawingsQuery(user_id))

@router.get("/users/{user_id}/is_following")
def is_following(
    user_id: int,
    handler: IsFollowingHandler = Depends(get_is_following_query_handler),
    current_user: DBUser = Depends(get_current_user)
):
    following = handler.handle(IsFollowingQuery(current_user.id, user_id))
    return {"is_following": following}

@router.get("/users/{user_id}/followers", response_model=List[UserResponse])
def get_followers(
    user_id: int,
    handler: GetFollowersHandler = Depends(get_followers_query_handler)
):
    return handler.handle(GetFollowersQuery(user_id))

@router.get("/{drawing_id}", response_model=DrawingResponse)
def get_drawing(
    drawing_id: int,
    handler: GetDrawingHandler = Depends(get_drawing_query_handler)
):
    try:
        return handler.handle(GetDrawingQuery(drawing_id))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{drawing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_drawing(
    drawing_id: int,
    handler: DeleteDrawingHandler = Depends(get_delete_drawing_handler),
    current_user: DBUser = Depends(get_current_user)
):
    try:
        handler.handle(DeleteDrawingCommand(drawing_id, current_user.id))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainException as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/{drawing_id}/layers", response_model=LayerResponse, status_code=status.HTTP_201_CREATED)
def add_layer(
    drawing_id: int,
    layer_in: LayerCreate,
    handler: AddLayerHandler = Depends(get_add_layer_handler),
    query_handler: GetDrawingHandler = Depends(get_drawing_query_handler),
    current_user: DBUser = Depends(get_current_user)
):
    try:
        layer_id = handler.handle(AddLayerCommand(drawing_id, current_user.id, layer_in.image_data))
        # Re-fetch drawing to get the layer details properly formatted if needed, 
        # but here we can just return the layer if our repo returns a domain Layer that maps to LayerResponse.
        # However, for simplicity and ensuring full data:
        drawing = query_handler.handle(GetDrawingQuery(drawing_id))
        for layer in drawing.layers:
            if layer.id == layer_id:
                return layer
        return None # Should not happen
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{drawing_id}/like")
def like_drawing(
    drawing_id: int,
    handler: ToggleLikeHandler = Depends(get_toggle_like_handler),
    current_user: DBUser = Depends(get_current_user)
):
    try:
        handler.handle(ToggleLikeCommand(drawing_id, current_user.id))
        return {"message": "Toggled like"}
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/users/{user_id}/follow")
def follow_user(
    user_id: int,
    handler: FollowUserHandler = Depends(get_follow_user_handler),
    current_user: DBUser = Depends(get_current_user)
):
    try:
        handler.handle(FollowUserCommand(current_user.id, user_id))
        return {"message": "Followed"}
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{user_id}/unfollow")
def unfollow_user(
    user_id: int,
    handler: UnfollowUserHandler = Depends(get_unfollow_user_handler),
    current_user: DBUser = Depends(get_current_user)
):
    try:
        handler.handle(UnfollowUserCommand(current_user.id, user_id))
        return {"message": "Unfollowed"}
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[DrawingResponse])
def get_all(
    q: Optional[str] = None,
    handler: SearchHandler = Depends(get_search_query_handler)
):
    if q:
        results = handler.handle(SearchQuery(q))
        return results["drawings"]
    return []
