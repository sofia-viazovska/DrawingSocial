from app.domain.models.models import User as DomainUser, Drawing as DomainDrawing, Layer as DomainLayer
from app.infrastructure.db.models.models import User as DBUser, Drawing as DBDrawing, Layer as DBLayer, Like as DBLike, Follow as DBFollow

class UserMapper:
    @staticmethod
    def to_domain(db_user: DBUser) -> DomainUser:
        if db_user is None:
            return None
        return DomainUser(
            id=db_user.id,
            email=db_user.email,
            nickname=db_user.nickname,
            hashed_password=db_user.hashed_password,
            following=[f.following_id for f in db_user.following],
            followers=[f.follower_id for f in db_user.followers]
        )

    @staticmethod
    def to_db(domain_user: DomainUser) -> DBUser:
        if domain_user is None:
            return None
        return DBUser(
            id=domain_user.id,
            email=domain_user.email,
            nickname=domain_user.nickname,
            hashed_password=domain_user.hashed_password
        )

class DrawingMapper:
    @staticmethod
    def to_domain(db_drawing: DBDrawing) -> DomainDrawing:
        if db_drawing is None:
            return None
        return DomainDrawing(
            id=db_drawing.id,
            owner_id=db_drawing.owner_id,
            title=db_drawing.title,
            owner_nickname=db_drawing.owner.nickname if db_drawing.owner else None,
            owner_email=db_drawing.owner.email if db_drawing.owner else None,
            created_at=db_drawing.created_at,
            layers=[LayerMapper.to_domain(l) for l in db_drawing.layers],
            likes=[l.user_id for l in db_drawing.likes]
        )

    @staticmethod
    def to_db(domain_drawing: DomainDrawing) -> DBDrawing:
        if domain_drawing is None:
            return None
        return DBDrawing(
            id=domain_drawing.id,
            owner_id=domain_drawing.owner_id,
            title=domain_drawing.title,
            created_at=domain_drawing.created_at
        )

class LayerMapper:
    @staticmethod
    def to_domain(db_layer: DBLayer) -> DomainLayer:
        if db_layer is None:
            return None
        return DomainLayer(
            id=db_layer.id,
            drawing_id=db_layer.drawing_id,
            author_id=db_layer.author_id,
            image_data=db_layer.image_data,
            author_nickname=db_layer.author.nickname if db_layer.author else None,
            created_at=db_layer.created_at
        )

    @staticmethod
    def to_db(domain_layer: DomainLayer) -> DBLayer:
        if domain_layer is None:
            return None
        return DBLayer(
            id=domain_layer.id,
            drawing_id=domain_layer.drawing_id,
            author_id=domain_layer.author_id,
            image_data=domain_layer.image_data,
            created_at=domain_layer.created_at
        )
