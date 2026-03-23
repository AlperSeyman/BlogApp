from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import PostCreate, PostResponse, PostUpdate, PaginatedPostResponse

from auth import CurrentUser

router = APIRouter()

# api process

# get all posts
@router.get("", response_model=PaginatedPostResponse)
async def get_Allpost_api(db: Annotated[AsyncSession, Depends(get_db)], skip: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = 10):

    count_result = await db.execute(select(func.count()).select_from(models.Post))
    total = count_result.scalar() or 0

    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).order_by(models.Post.date_posted.desc()).offset(skip).limit(limit))
    posts = result.scalars().all()

    has_more = skip + len(posts) < total

    return PaginatedPostResponse(
        posts = [PostResponse.model_validate(post) for post in posts],
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more,
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post_api(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


# update a post (put)
@router.put("/{post_id}", response_model=PostResponse)
async def updateFull_post_api(post_id: int, current_user: CurrentUser, post_data: PostUpdate, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.user_id != current_user.id :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")

    post.title = post_data.title
    post.content = post_data.content

    await db.commit()
    await db.refresh(post, attribute_names=["author"])

    return post


# update a post (patch)
@router.patch("/{post_id}", response_model=PostResponse)
async def updatePartial_post_api(post_id: int, current_user: CurrentUser, post_data: PostUpdate, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    update_post_dict = post_data.model_dump(exclude_unset=True)

    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")

    for field, value in update_post_dict.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])

    return post


# create a post
@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post_api(post: PostCreate, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):

    new_post = models.Post(title=post.title, content=post.content, user_id=current_user.id)
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])

    return new_post


# delete a post
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post_api(post_id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")

    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")

    await db.delete(post)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)