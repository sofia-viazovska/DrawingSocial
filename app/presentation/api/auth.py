from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.database import get_db
from app.infrastructure.repositories.sql_repositories import SQLAlchemyUserRepository
from app.domain.factories.factories import DomainFactory
from app.application.commands.handlers import RegisterUserCommand, RegisterUserHandler
from app.application.queries.handlers import GetUserQuery, GetUserHandler
from app.presentation.schemas.schemas import UserCreate, UserResponse, Token
from app.core.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from app.domain.exceptions.exceptions import DomainException, EmailAlreadyExistsError, NicknameAlreadyExistsError, EntityNotFoundError

router = APIRouter(prefix="/auth", tags=["auth"])

def get_register_handler(db: Session = Depends(get_db)) -> RegisterUserHandler:
    user_repo = SQLAlchemyUserRepository(db)
    factory = DomainFactory(user_repo)
    return RegisterUserHandler(user_repo, factory)

def get_user_query_handler(db: Session = Depends(get_db)) -> GetUserHandler:
    user_repo = SQLAlchemyUserRepository(db)
    return GetUserHandler(user_repo)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate, 
    handler: RegisterUserHandler = Depends(get_register_handler),
    query_handler: GetUserHandler = Depends(get_user_query_handler)
):
    try:
        user_id = handler.handle(RegisterUserCommand(
            email=user_in.email,
            nickname=user_in.nickname,
            hashed_password=get_password_hash(user_in.password)
        ))
        return query_handler.handle(GetUserQuery(user_id))
    except (EmailAlreadyExistsError, NicknameAlreadyExistsError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=Token)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user_repo = SQLAlchemyUserRepository(db)
    # Finding user for login - we can keep it here or move to a separate use case
    from app.infrastructure.db.models.models import User as DBUser
    db_user = db.query(DBUser).filter(
        (DBUser.email == form_data.username) | (DBUser.nickname == form_data.username)
    ).first()
    
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/nickname or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int, 
    handler: GetUserHandler = Depends(get_user_query_handler)
):
    try:
        return handler.handle(GetUserQuery(user_id))
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/me", response_model=UserResponse)
def get_me(db: Session = Depends(get_db), current_user_db = Depends(get_current_user)):
    # current_user from security usually returns DB model, we might need to map it
    from app.infrastructure.mappers.mappers import UserMapper
    return UserMapper.to_domain(current_user_db)
