kkfrom typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.models.models import User, Drawing, Layer
from app.domain.repositories.interfaces import UserRepository, DrawingRepository
from app.infrastructure.db.models.models import User as DBUser, Drawing as DBDrawing, Layer as DBLayer, Like as DBLike, Follow as DBFollow
from app.infrastructure.mappers.mappers import UserMapper, DrawingMapper

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: int) -> Optional[User]:
        db_user = self.session.query(DBUser).filter(DBUser.id == user_id).first()
        return UserMapper.to_domain(db_user) if db_user else None

    def get_by_email(self, email: str) -> Optional[User]:
        db_user = self.session.query(DBUser).filter(DBUser.email == email).first()
        return UserMapper.to_domain(db_user) if db_user else None

    def get_by_nickname(self, nickname: str) -> Optional[User]:
        db_user = self.session.query(DBUser).filter(DBUser.nickname == nickname).first()
        return UserMapper.to_domain(db_user) if db_user else None

    def save(self, user: User) -> User:
        db_user = UserMapper.to_db(user)
        if db_user.id:
            self.session.merge(db_user)
        else:
            self.session.add(db_user)
        self.session.commit()
        return UserMapper.to_domain(db_user)

    def add_follow(self, follower_id: int, followed_id: int) -> None:
        follow = DBFollow(follower_id=follower_id, followed_id=followed_id)
        self.session.add(follow)
        self.session.commit()

    def remove_follow(self, follower_id: int, followed_id: int) -> None:
        self.session.query(DBFollow).filter_by(follower_id=follower_id, followed_id=followed_id).delete()
        self.session.commit()

class SQLAlchemyDrawingRepository(DrawingRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, drawing_id: int) -> Optional[Drawing]:
        db_drawing = self.session.query(DBDrawing).filter(DBDrawing.id == drawing_id).first()
        return DrawingMapper.to_domain(db_drawing) if db_drawing else None

    def save(self, drawing: Drawing) -> Drawing:
        db_drawing = DrawingMapper.to_db(drawing)
        if db_drawing.id:
            self.session.merge(db_drawing)
        else:
            self.session.add(db_drawing)
        
        # Save layers separately if they are new
        for layer in drawing.layers:
            db_layer = DBLayer(id=layer.id, drawing_id=db_drawing.id, creator_id=layer.creator_id, image_data=layer.image_data)
            self.session.merge(db_layer)
            
        self.session.commit()
        return DrawingMapper.to_domain(db_drawing)

    def delete(self, drawing_id: int) -> None:
        self.session.query(DBDrawing).filter(DBDrawing.id == drawing_id).delete()
        self.session.commit()
