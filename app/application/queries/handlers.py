from dataclasses import dataclass
from typing import List, Optional
from app.domain.repositories.interfaces import UserRepository, DrawingRepository
from app.domain.exceptions.exceptions import EntityNotFoundError
from app.application.dtos.read_models import UserReadModel, DrawingReadModel, LayerReadModel

@dataclass(frozen=True)
class GetUserQuery:
    user_id: int

class GetUserHandler:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def handle(self, query: GetUserQuery) -> UserReadModel:
        user = self.user_repo.get_by_id(query.user_id)
        if not user:
            raise EntityNotFoundError(f"User with id {query.user_id} not found")
        return UserReadModel(
            id=user.id,
            email=user.email,
            nickname=user.nickname
        )

@dataclass(frozen=True)
class GetDrawingQuery:
    drawing_id: int

class GetDrawingHandler:
    def __init__(self, drawing_repo: DrawingRepository):
        self.drawing_repo = drawing_repo

    def handle(self, query: GetDrawingQuery) -> DrawingReadModel:
        drawing = self.drawing_repo.get_by_id(query.drawing_id)
        if not drawing:
            raise EntityNotFoundError(f"Drawing with id {query.drawing_id} not found")
        
        return DrawingReadModel(
            id=drawing.id,
            owner_id=drawing.owner_id,
            owner_email=drawing.owner_email,
            owner_nickname=drawing.owner_nickname,
            title=drawing.title,
            created_at=drawing.created_at,
            layers=[
                LayerReadModel(
                    id=l.id,
                    drawing_id=l.drawing_id,
                    author_id=l.author_id,
                    author_nickname=l.author_nickname,
                    image_data=l.image_data,
                    created_at=l.created_at
                ) for l in drawing.layers
            ],
            likes_count=len(drawing.likes)
        )

@dataclass(frozen=True)
class GetFeedQuery:
    user_id: int

class GetFeedHandler:
    def __init__(self, drawing_repo: DrawingRepository):
        self.drawing_repo = drawing_repo

    def handle(self, query: GetFeedQuery) -> List[DrawingReadModel]:
        drawings = self.drawing_repo.list_feed(query.user_id)
        return [
            DrawingReadModel(
                id=d.id,
                owner_id=d.owner_id,
                owner_email=d.owner_email,
                owner_nickname=d.owner_nickname,
                title=d.title,
                created_at=d.created_at,
                layers=[
                    LayerReadModel(
                        id=l.id,
                        drawing_id=l.drawing_id,
                        author_id=l.author_id,
                        author_nickname=l.author_nickname,
                        image_data=l.image_data,
                        created_at=l.created_at
                    ) for l in d.layers
                ],
                likes_count=len(d.likes)
            ) for d in drawings
        ]

@dataclass(frozen=True)
class SearchQuery:
    query_text: str

class SearchHandler:
    def __init__(self, drawing_repo: DrawingRepository):
        self.drawing_repo = drawing_repo

    def handle(self, query: SearchQuery) -> dict:
        results = self.drawing_repo.search(query.query_text)
        users = results.get("users", [])
        drawings = results.get("drawings", [])
        
        return {
            "users": [
                UserReadModel(
                    id=u.id,
                    email=u.email,
                    nickname=u.nickname
                ) for u in users
            ],
            "drawings": [
                DrawingReadModel(
                    id=d.id,
                    owner_id=d.owner_id,
                    owner_email=d.owner_email,
                    owner_nickname=d.owner_nickname,
                    title=d.title,
                    created_at=d.created_at,
                    layers=[
                        LayerReadModel(
                            id=l.id,
                            drawing_id=l.drawing_id,
                            author_id=l.author_id,
                            author_nickname=l.author_nickname,
                            image_data=l.image_data,
                            created_at=l.created_at
                        ) for l in d.layers
                    ],
                    likes_count=len(d.likes)
                ) for d in drawings
            ]
        }

@dataclass(frozen=True)
class GetUserDrawingsQuery:
    user_id: int

class GetUserDrawingsHandler:
    def __init__(self, drawing_repo: DrawingRepository):
        self.drawing_repo = drawing_repo

    def handle(self, query: GetUserDrawingsQuery) -> List[DrawingReadModel]:
        drawings = self.drawing_repo.get_user_drawings(query.user_id)
        return [
            DrawingReadModel(
                id=d.id,
                owner_id=d.owner_id,
                owner_email=d.owner_email,
                owner_nickname=d.owner_nickname,
                title=d.title,
                created_at=d.created_at,
                layers=[
                    LayerReadModel(
                        id=l.id,
                        drawing_id=l.drawing_id,
                        author_id=l.author_id,
                        author_nickname=l.author_nickname,
                        image_data=l.image_data,
                        created_at=l.created_at
                    ) for l in d.layers
                ],
                likes_count=len(d.likes)
            ) for d in drawings
        ]

@dataclass(frozen=True)
class GetUserContributedDrawingsQuery:
    user_id: int

class GetUserContributedDrawingsHandler:
    def __init__(self, drawing_repo: DrawingRepository):
        self.drawing_repo = drawing_repo

    def handle(self, query: GetUserContributedDrawingsQuery) -> List[DrawingReadModel]:
        drawings = self.drawing_repo.get_user_contributed_drawings(query.user_id)
        return [
            DrawingReadModel(
                id=d.id,
                owner_id=d.owner_id,
                owner_email=d.owner_email,
                owner_nickname=d.owner_nickname,
                title=d.title,
                created_at=d.created_at,
                layers=[
                    LayerReadModel(
                        id=l.id,
                        drawing_id=l.drawing_id,
                        author_id=l.author_id,
                        author_nickname=l.author_nickname,
                        image_data=l.image_data,
                        created_at=l.created_at
                    ) for l in d.layers
                ],
                likes_count=len(d.likes)
            ) for d in drawings
        ]

@dataclass(frozen=True)
class GetFollowersQuery:
    user_id: int

class GetFollowersHandler:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def handle(self, query: GetFollowersQuery) -> List[UserReadModel]:
        followers = self.user_repo.get_followers(query.user_id)
        return [
            UserReadModel(
                id=f.id,
                email=f.email,
                nickname=f.nickname
            ) for f in followers
        ]

@dataclass(frozen=True)
class IsFollowingQuery:
    follower_id: int
    following_id: int

class IsFollowingHandler:
    def __init__(self, drawing_repo: DrawingRepository):
        self.drawing_repo = drawing_repo

    def handle(self, query: IsFollowingQuery) -> bool:
        return self.drawing_repo.is_following(query.follower_id, query.following_id)
