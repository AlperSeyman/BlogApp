from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas import PostCreate, PostRespone

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

posts = [
    {"id": 1,"author":"Sally Rooney", "title": "Normal People", "content": "This book is wonderful", "date_posted": "2018"},
    {"id": 2,"author":"Jone Doe","title": "Python is Great", "content": "FastAPI makes it even better", "date_posted": "2025"},
]

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"posts":posts, "title":"Home"},
        )

@app.get("/posts/{post_id}", include_in_schema=False)
def get_post(request: Request, post_id: int):

    for post in posts:
        if post.get("id") == post_id:
            title = post["title"][:50]
            return templates.TemplateResponse(
                request=request,
                name="post.html",
                context={"post":post, "title":title}
            )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found")

@app.get("/api/post", response_model=list[PostRespone])
def get_Allpost():
    return posts

@app.get("/api/posts/{post_id}", response_model=PostRespone)
def get_post(post_id: int):

    for post in posts:
        if post_id == post.get("id"): # post["id"]
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

@app.post("/api/posts", response_model=PostRespone, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate):

    new_id = max([post["id"] for post in posts]) + 1 if posts else 1

    # current_id = 0
    # if posts:
    #     for post in posts:
    #         if current_id < post["id"]:
    #             current_id = post["id"]
    #     new_id = current_id + 1
    # else:
    #     new_id = 1

    new_post = {
        "id": new_id,
        "title":post.title,
        "author": post.author,
        "content": post.content,
        "date_posted": "February 7, 2026"
    }

    posts.append(new_post)
    return new_post



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