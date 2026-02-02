from fastapi import FastAPI

app = FastAPI()

posts: list[dict] = [
    {
        "id": 1,
        "author": "Sally Rooney",
        "title": "Normal People",
        "content": "This book is wonderful and classic",
        "data_poster": "2018",
    },
      {
        "id": 2,
        "author": "Jane Doe",
        "title": "Python is Great for Web Development",
        "content": "Python is a great language for web development, and FastAPI makes it even better",
        "data_poster": "2025",
    },
]

@app.get("/")
def home():
    return {"message":"Hello World!"}

@app.get("/api/posts/")
def get_all_authors():
    return posts

@app.get("/api/posts/{post_id}")
def get_author(post_id:int):

    for post in posts:
        if post["id"] == post_id:
            return post

    return {"Message":"Post not found"}