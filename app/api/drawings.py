from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.db.database import get_db
from app.models.models import Drawing, Layer, User, Like, Follow
from app.schemas.schemas import DrawingCreate, DrawingResponse, LayerCreate, LayerResponse, FeedDrawing, UserResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/drawings", tags=["drawings"])

@router.post("/", response_model=DrawingResponse, status_code=status.HTTP_201_CREATED)
def create_drawing(
    drawing_in: DrawingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not drawing_in.first_layer_data.strip():
        raise HTTPException(status_code=400, detail="Layer cannot be empty")
        
    new_drawing = Drawing(
        title=drawing_in.title,
        owner_id=current_user.id
    )
    db.add(new_drawing)
    db.commit()
    db.refresh(new_drawing)
    
    # Pre-populate owner details for response
    new_drawing.owner_email = current_user.email
    new_drawing.owner_nickname = current_user.nickname
    
    first_layer = Layer(
        drawing_id=new_drawing.id,
        author_id=current_user.id,
        image_data=drawing_in.first_layer_data
    )
    db.add(first_layer)
    db.commit()
    db.refresh(new_drawing)
    
    return new_drawing

@router.get("/feed", response_model=List[FeedDrawing])
def get_feed(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if q:
        # Search by keywords among authors nickname/emails and paintings names
        search_query = f"%{q}%"
        drawings = db.query(Drawing).join(User, Drawing.owner_id == User.id).filter(
            (Drawing.title.ilike(search_query)) |
            (User.nickname.ilike(search_query)) |
            (User.email.ilike(search_query))
        ).order_by(Drawing.created_at.desc()).all()
    else:
        # Get IDs of users current user is following
        following_ids = db.query(Follow.following_id).filter(Follow.follower_id == current_user.id).all()
        following_ids = [f[0] for f in following_ids]
        
        # Also include own drawings in feed
        following_ids.append(current_user.id)
        
        # Get drawings from these users
        drawings = db.query(Drawing).filter(Drawing.owner_id.in_(following_ids)).order_by(Drawing.created_at.desc()).all()
    
    feed = []
    for d in drawings:
        likes_count = db.query(func.count(Like.id)).filter(Like.drawing_id == d.id).scalar()
        owner_email = d.owner.email if d.owner else None
        owner_nickname = d.owner.nickname if d.owner else None
        feed.append(FeedDrawing(
            id=d.id,
            owner_id=d.owner_id,
            owner_email=owner_email,
            owner_nickname=owner_nickname,
            title=d.title,
            created_at=d.created_at,
            likes_count=likes_count
        ))
    
    return feed

@router.get("/search", response_model=dict)
def search(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    search_query = f"%{q}%"
    
    # Search users
    users = db.query(User).filter(
        (User.nickname.ilike(search_query)) |
        (User.email.ilike(search_query))
    ).all()
    
    # Search drawings
    drawings = db.query(Drawing).join(User, Drawing.owner_id == User.id).filter(
        (Drawing.title.ilike(search_query)) |
        (User.nickname.ilike(search_query)) |
        (User.email.ilike(search_query))
    ).order_by(Drawing.created_at.desc()).all()
    
    user_results = [
        {"id": u.id, "nickname": u.nickname, "email": u.email}
        for u in users
    ]
    
    drawing_results = []
    for d in drawings:
        likes_count = db.query(func.count(Like.id)).filter(Like.drawing_id == d.id).scalar()
        drawing_results.append({
            "id": d.id,
            "owner_id": d.owner_id,
            "owner_email": d.owner.email,
            "owner_nickname": d.owner.nickname,
            "title": d.title,
            "created_at": d.created_at,
            "likes_count": likes_count
        })
        
    return {
        "users": user_results,
        "drawings": drawing_results
    }

def _populate_drawing_response(drawing: Drawing, db: Session) -> DrawingResponse:
    likes_count = db.query(func.count(Like.id)).filter(Like.drawing_id == drawing.id).scalar()
    
    # Sort layers by created_at
    drawing.layers = sorted(drawing.layers, key=lambda x: x.created_at)
    
    response = DrawingResponse.model_validate(drawing)
    
    # Manually map author nicknames for each layer
    for i, layer in enumerate(drawing.layers):
        response.layers[i].author_nickname = layer.author.nickname if layer.author else None

    response.likes_count = likes_count
    response.owner_email = drawing.owner.email if drawing.owner else None
    response.owner_nickname = drawing.owner.nickname if drawing.owner else None
    return response

@router.get("/{drawing_id}", response_model=DrawingResponse)
def get_drawing(drawing_id: int, db: Session = Depends(get_db)):
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    return _populate_drawing_response(drawing, db)

@router.delete("/{drawing_id}", status_code=status.HTTP_200_OK)
def delete_drawing(
    drawing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    if drawing.owner_id != current_user.id:
        raise HTTPException(status_code=401, detail="Only the owner can delete the drawing")
        
    db.delete(drawing)
    db.commit()
    return {"detail": "Drawing deleted"}

@router.post("/{drawing_id}/layers", response_model=LayerResponse, status_code=status.HTTP_201_CREATED)
def add_layer(
    drawing_id: int,
    layer_in: LayerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not layer_in.image_data.strip():
        raise HTTPException(status_code=400, detail="Layer cannot be empty")
        
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
        
    new_layer = Layer(
        drawing_id=drawing_id,
        author_id=current_user.id,
        image_data=layer_in.image_data
    )
    db.add(new_layer)
    db.commit()
    db.refresh(new_layer)
    return new_layer

@router.post("/{drawing_id}/like", status_code=status.HTTP_200_OK)
def like_drawing(
    drawing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
        
    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.drawing_id == drawing_id
    ).first()
    
    if existing_like:
        raise HTTPException(status_code=409, detail="Drawing already liked")
        
    new_like = Like(user_id=current_user.id, drawing_id=drawing_id)
    db.add(new_like)
    db.commit()
    return {"detail": "Drawing liked"}

@router.get("/users/{user_id}/drawings", response_model=List[DrawingResponse])
def get_user_drawings(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    drawings = db.query(Drawing).filter(Drawing.owner_id == user_id).order_by(Drawing.created_at.desc()).all()
    return [_populate_drawing_response(d, db) for d in drawings]

@router.get("/users/{user_id}/contributed", response_model=List[DrawingResponse])
def get_user_contributed_drawings(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find drawings where the user has a layer but is NOT the owner
    drawings = db.query(Drawing).join(Layer).filter(
        Layer.author_id == user_id,
        Drawing.owner_id != user_id
    ).distinct().order_by(Drawing.created_at.desc()).all()
    
    return [_populate_drawing_response(d, db) for d in drawings]

@router.post("/users/{user_id}/follow", status_code=status.HTTP_200_OK)
def follow_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")
        
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    existing_follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()
    
    if existing_follow:
        raise HTTPException(status_code=409, detail="Already following this user")
        
    new_follow = Follow(follower_id=current_user.id, following_id=user_id)
    db.add(new_follow)
    db.commit()
    return {"detail": "User followed"}

@router.delete("/users/{user_id}/unfollow", status_code=status.HTTP_200_OK)
def unfollow_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()
    
    if not follow:
        raise HTTPException(status_code=404, detail="You are not following this user")
        
    db.delete(follow)
    db.commit()
    return {"detail": "User unfollowed"}

@router.get("/users/{user_id}/is_following", response_model=dict)
def is_following(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()
    
    return {"is_following": follow is not None}

@router.get("/users/{user_id}/followers", response_model=List[UserResponse])
def get_followers(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    followers = db.query(User).join(Follow, Follow.follower_id == User.id).filter(
        Follow.following_id == user_id
    ).all()
    return followers

@router.get("/users/{user_id}/following", response_model=List[UserResponse])
def get_following(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    following = db.query(User).join(Follow, Follow.following_id == User.id).filter(
        Follow.follower_id == user_id
    ).all()
    return following
