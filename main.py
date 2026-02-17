from typing import Annotated

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import engine, Base, get_db

from schemas import PostCreate, PostResponse, UserCreate, UserResponse, PostUpdate

Base.metadata.create_all(bind=engine)

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")


#############################################################################################

# TEMPLATE PROCESS

# home page and show all posts
@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.Post))
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name='home.html',
        context={"posts":posts, "title":"Home"}
    )

@app.get("/posts/{post_id}", include_in_schema=False)
def get_post(request: Request, post_id: int, db:Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request=request,
            name="post.html",
            context={"post":post, "title":title}
        )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found")

@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
def get_user_posts(request: Request,user_id: int, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="user_posts.html",
        context={"posts": posts, "user": user, "title":f"{user.username}' Posts"},
    )


#############################################################################################

# API PROCESS

# get all posts
@app.get("/api/post", response_model=list[PostResponse])
def get_Allpost_api(db: Annotated[Session, Depends(get_db)]):

    posts = db.execute(select(models.Post)).scalars().all()
    return posts

# get specific post
@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post_api(post_id: int, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

# update a post (put)
@app.put("/api/posts/{post_id}", response_model=PostResponse)
def updateFull_post_api(post_id: int, post_data: PostCreate, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post_data.user_id != post.user_id:
        result = db.execute(select(models.User).where(models.User.id == post_data.user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    db.commit()
    db.refresh(post)

    return post

# update a post (patch)
@app.patch("/api/posts/{post_id}", response_model=PostResponse)
def updatePartial_post_api(post_id: int, post_data: PostUpdate, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    update_post_dict = post_data.model_dump(exclude_unset=True)

    for field, value in update_post_dict.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)

    return post

# create a post
@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post_api(post: PostCreate, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_post = models.Post(title=post.title, content=post.content, user_id=post.user_id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post

# get all users
@app.get("/api/users", response_model=list[UserResponse])
def get_all_users_api(db: Annotated[Session, Depends(get_db)]):

    users = db.execute(select(models.User)).scalars().all()

    return users

# get specific user
@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(
        select(models.User).where(models.User.id == user_id),
    )
    user = result.scalars().first()
    if  user:
        return user

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

# get specific user's posts
@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
def get_user_posts_api(user_id: int, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts

# create a user
@app.post("/api/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_api(user: UserCreate, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(
        select(models.User).where(models.User.username == user.username)
    )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists.")

    result = db.execute(
        select(models.User).where(models.User.email == user.email)
    )
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists.")

    new_user = models.User(username=user.username, email=user.email)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):

    msg =  ( exception.detail if exception.detail else "An error occured. Please check your request and try again." ) # ternary operators
    # if exception:
    #     message = exception.detail
    # else:
    #     message = "An error occured. Please check your request and try again."

    if request.url.path.startswith('/api'):
        return JSONResponse(status_code=exception.status_code, content={'detail':msg})

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"status_code": exception.status_code, "title":exception.status_code, "message":msg},
        status_code=exception.status_code,
    )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):

    if request.url.path.startswith('/api'):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={'detail': exception.errors()}
        )

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={'status_code': status.HTTP_422_UNPROCESSABLE_CONTENT, 'title': status.HTTP_422_UNPROCESSABLE_CONTENT, "message":"Invalid request. Please check your input and try again."},
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )