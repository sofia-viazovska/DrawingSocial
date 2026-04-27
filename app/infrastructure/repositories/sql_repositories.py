from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.models.models import User, Drawing, Layer
from app.domain.repositories.interfaces import UserRepository, DrawingRepository
from app.infrastructure.db.models.models import User as DBUser, Drawing as DBDrawing, Layer as DBLayer, Like as DBLike, Follow as DBFollow
from app.infrastructure.mappers.mappers import UserMapper, DrawingMapper, LayerMapper

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        db_user = self.db.query(DBUser).filter(DBUser.id == user_id).first()
        return UserMapper.to_domain(db_user)

    def get_by_email(self, email: str) -> Optional[User]:
        db_user = self.db.query(DBUser).filter(DBUser.email == email).first()
        return UserMapper.to_domain(db_user)

    def get_by_nickname(self, nickname: str) -> Optional[User]:
        db_user = self.db.query(DBUser).filter(DBUser.nickname == nickname).first()
        return UserMapper.to_domain(db_user)

    def save(self, user: User) -> User:
        db_user = UserMapper.to_db(user)
        if db_user.id:
            # Update existing - simplified for now
            existing = self.db.query(DBUser).filter(DBUser.id == db_user.id).first()
            if existing:
                existing.email = db_user.email
                existing.nickname = db_user.nickname
                existing.hashed_password = db_user.hashed_password
                db_user = existing
        else:
            self.db.add(db_user)
        
        self.db.commit()
        self.db.refresh(db_user)
        return UserMapper.to_domain(db_user)

    def add_follow(self, follower_id: int, following_id: int):
        follow = DBFollow(follower_id=follower_id, following_id=following_id)
        self.db.add(follow)
        self.db.commit()

    def remove_follow(self, follower_id: int, following_id: int):
        self.db.query(DBFollow).filter(
            DBFollow.follower_id == follower_id,
            DBFollow.following_id == following_id
        ).delete()
        self.db.commit()

    def get_followers(self, user_id: int) -> List[User]:
        db_users = self.db.query(DBUser).join(
            DBFollow, DBUser.id == DBFollow.follower_id
        ).filter(DBFollow.following_id == user_id).all()
        return [UserMapper.to_domain(u) for u in db_users]

class SQLAlchemyDrawingRepository(DrawingRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, drawing_id: int) -> Optional[Drawing]:
        db_drawing = self.db.query(DBDrawing).filter(DBDrawing.id == drawing_id).first()
        return DrawingMapper.to_domain(db_drawing)

    def list_feed(self, user_id: int) -> List[Drawing]:
        # Drawings from followed users
        following_ids = self.db.query(DBFollow.following_id).filter(DBFollow.follower_id == user_id).all()
        following_ids = [f[0] for f in following_ids]
        db_drawings = self.db.query(DBDrawing).filter(DBDrawing.owner_id.in_(following_ids)).all()
        return [DrawingMapper.to_domain(d) for d in db_drawings]

    def search(self, q: str) -> dict:
        q_search = f"%{q}%"
        db_users = self.db.query(DBUser).filter(
            (DBUser.nickname.contains(q)) | (DBUser.email.contains(q))
        ).all()
        
        # Search drawings by title or by author nickname/email
        db_drawings = self.db.query(DBDrawing).join(DBUser).filter(
            (DBDrawing.title.contains(q)) | 
            (DBUser.nickname.contains(q)) | 
            (DBUser.email.contains(q))
        ).all()
        
        return {
            "users": [UserMapper.to_domain(u) for u in db_users],
            "drawings": [DrawingMapper.to_domain(d) for d in db_drawings]
        }

    def get_user_drawings(self, user_id: int) -> List[Drawing]:
        db_drawings = self.db.query(DBDrawing).filter(DBDrawing.owner_id == user_id).all()
        return [DrawingMapper.to_domain(d) for d in db_drawings]

    def get_user_contributed_drawings(self, user_id: int) -> List[Drawing]:
        db_drawings = self.db.query(DBDrawing).join(DBLayer).filter(
            DBLayer.author_id == user_id,
            DBDrawing.owner_id != user_id
        ).distinct().all()
        return [DrawingMapper.to_domain(d) for d in db_drawings]

    def is_following(self, follower_id: int, following_id: int) -> bool:
        follow = self.db.query(DBFollow).filter(
            DBFollow.follower_id == follower_id,
            DBFollow.following_id == following_id
        ).first()
        return follow is not None

    def save(self, drawing: Drawing) -> Drawing:
        db_drawing = DrawingMapper.to_db(drawing)
        if db_drawing.id:
            existing = self.db.query(DBDrawing).filter(DBDrawing.id == db_drawing.id).first()
            if existing:
                existing.title = db_drawing.title
                db_drawing = existing
        else:
            self.db.add(db_drawing)
        
        self.db.commit()
        self.db.refresh(db_drawing)
        return DrawingMapper.to_domain(db_drawing)

    def delete(self, drawing_id: int):
        self.db.query(DBDrawing).filter(DBDrawing.id == drawing_id).delete()
        self.db.commit()

    def add_layer(self, layer: Layer) -> Layer:
        db_layer = LayerMapper.to_db(layer)
        self.db.add(db_layer)
        self.db.commit()
        self.db.refresh(db_layer)
        return LayerMapper.to_domain(db_layer)

    def toggle_like(self, drawing_id: int, user_id: int):
        like = self.db.query(DBLike).filter(
            DBLike.drawing_id == drawing_id,
            DBLike.user_id == user_id
        ).first()
        if like:
            self.db.delete(like)
        else:
            self.db.add(DBLike(drawing_id=drawing_id, user_id=user_id))
        self.db.commit()
