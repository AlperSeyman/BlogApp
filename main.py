from typing import Annotated

from contextlib import asynccontextmanager
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler

from fastapi import FastAPI, Request, HTTPException, status, Depends, Response
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import engine, Base, get_db
from routers import posts, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)


app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")

# api
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])


#############################################################################################

# home page and show all posts
@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name='home.html',
        context={"posts":posts, "title":"Home"}
    )

@app.get("/posts/{post_id}", include_in_schema=False)
async def get_post(request: Request, post_id: int, db:Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))
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
async def get_user_posts(request: Request,user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id))
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="user_posts.html",
        context={"posts": posts, "user": user, "title":f"{user.username}' Posts"},
    )


@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):

    # msg =  ( exception.detail if exception.detail else "An error occured. Please check your request and try again." ) # ternary operators
    # if exception:
    #     message = exception.detail
    # else:
    #     message = "An error occured. Please check your request and try again."

    if request.url.path.startswith('/api'):
        return await http_exception_handler(request=request, exc=exception)

    msg =  ( exception.detail if exception.detail else "An error occured. Please check your request and try again." )

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"status_code": exception.status_code, "title":exception.status_code, "message":msg},
        status_code=exception.status_code,
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):

    if request.url.path.startswith('/api'):
        return await request_validation_exception_handler(request=request, exc=exception)

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={'status_code': status.HTTP_422_UNPROCESSABLE_CONTENT, 'title': status.HTTP_422_UNPROCESSABLE_CONTENT, "message":"Invalid request. Please check your input and try again."},
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )