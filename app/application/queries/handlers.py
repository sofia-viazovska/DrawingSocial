from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.domain.exceptions.exceptions import EntityNotFoundError
from app.application.dtos.read_models import UserReadModel, DrawingReadModel, LayerReadModel
from app.infrastructure.db.models.models import User as DBUser, Drawing as DBDrawing, Follow as DBFollow

@dataclass(frozen=True)
class GetUserQuery:
    user_id: int

class GetUserHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, query: GetUserQuery) -> UserReadModel:
        user = self.session.query(DBUser).filter(DBUser.id == query.user_id).first()
        if not user:
            raise EntityNotFoundError(f"User with id {query.user_id} not found")
        return UserReadModel(id=user.id, email=user.email, nickname=user.nickname)

@dataclass(frozen=True)
class GetDrawingQuery:
    drawing_id: int

class GetDrawingHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, query: GetDrawingQuery) -> DrawingReadModel:
        d = self.session.query(DBDrawing).filter(DBDrawing.id == query.drawing_id).first()
        if not d:
            raise EntityNotFoundError(f"Drawing with id {query.drawing_id} not found")
        
        return DrawingReadModel(
            id=d.id,
            title=d.title,
            owner_id=d.owner_id,
            owner_email=d.owner.email,
            created_at=d.created_at,
            likes_count=len(d.likes),
            layers=[LayerReadModel(id=l.id, creator_id=l.creator_id, creator_nickname=l.creator.nickname, image_data=l.image_data, created_at=l.created_at) for l in d.layers]
        )

@dataclass(frozen=True)
class GetFeedQuery:
    user_id: int

class GetFeedHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, query: GetFeedQuery) -> List[DrawingReadModel]:
        followed_ids = self.session.query(DBFollow.followed_id).filter(DBFollow.follower_id == query.user_id).all()
        ids = [i[0] for i in followed_ids]
        
        results = self.session.query(DBDrawing).filter(DBDrawing.owner_id.in_(ids)).order_by(DBDrawing.created_at.desc()).all()
        
        return [DrawingReadModel(
            id=d.id, title=d.title, owner_id=d.owner_id, owner_email=d.owner.email,
            created_at=d.created_at, likes_count=len(d.likes), layers=[]
        ) for d in results]

@dataclass(frozen=True)
class SearchQuery:
    query: str

class SearchHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, query: SearchQuery) -> dict:
        drawings = self.session.query(DBDrawing).filter(DBDrawing.title.contains(query.query)).all()
        users = self.session.query(DBUser).filter(or_(DBUser.nickname.contains(query.query), DBUser.email.contains(query.query))).all()
        
        return {
            "drawings": [DrawingReadModel(id=d.id, title=d.title, owner_id=d.owner_id, owner_email=d.owner.email, created_at=d.created_at, likes_count=len(d.likes), layers=[]) for d in drawings],
            "users": [UserReadModel(id=u.id, email=u.email, nickname=u.nickname) for u in users]
        }

@dataclass(frozen=True)
class GetUserDrawingsQuery:
    user_id: int

class GetUserDrawingsHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, query: GetUserDrawingsQuery) -> List[DrawingReadModel]:
        drawings = self.session.query(DBDrawing).filter(DBDrawing.owner_id == query.user_id).all()
        return [DrawingReadModel(id=d.id, title=d.title, owner_id=d.owner_id, owner_email=d.owner.email, created_at=d.created_at, likes_count=len(d.likes), layers=[]) for d in drawings]

@dataclass(frozen=True)
class GetUserContributedDrawingsQuery:
    user_id: int

class GetUserContributedDrawingsHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, query: GetUserContributedDrawingsQuery) -> List[DrawingReadModel]:
        # Вибираємо малюнки, де користувач створив хоча б один шар, але не є власником
        drawings = self.session.query(DBDrawing).join(DBDrawing.layers).filter(DBDrawing.owner_id != query.user_id).filter(DBUser.id == query.user_id).all()
        return [DrawingReadModel(id=d.id, title=d.title, owner_id=d.owner_id, owner_email=d.owner.email, created_at=d.created_at, likes_count=len(d.likes), layers=[]) for d in drawings]

@dataclass(frozen=True)
class IsFollowingQuery:
    follower_id: int
    followed_id: int

class IsFollowingHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, query: IsFollowingQuery) -> bool:
        follow = self.session.query(DBFollow).filter_by(follower_id=query.follower_id, followed_id=query.followed_id).first()
        return follow is not None

@dataclass(frozen=True)
class GetFollowersQuery:
    user_id: int

class GetFollowersHandler:
    def __init__(self, session: Session):
        self.session = session

    def handle(self, query: GetFollowersQuery) -> List[UserReadModel]:
        followers = self.session.query(DBUser).join(DBFollow, DBUser.id == DBFollow.follower_id).filter(DBFollow.followed_id == query.user_id).all()
        return [UserReadModel(id=u.id, email=u.email, nickname=u.nickname) for u in followers]
