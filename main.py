from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

posts = [
    {"id": 1,"author":"Sally Rooney", "title": "Normal People", "content": "This book is wonderful", "date_posted": "2018"},
    {"id": 2,"author":"Jone Doe","title": "Python is Great", "content": "FastAPI makes it even better", "date_posted": "2025"},
]

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home_page.html",
        context={"posts":posts, "title":"Home"},
        )

@app.get("/api/posts/")
def get_all_authors():
    return posts

