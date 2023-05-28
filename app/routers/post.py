from typing import List, Optional
from fastapi import Response, status, HTTPException, Depends, APIRouter
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlalchemy.orm import Session
from .. import schemas, models, oauth2
from ..database import get_db

router = APIRouter(prefix="/posts",
                   tags=["Posts"])



# @app.get("/posts")
# async def posts():
#     cursor.execute("""SELECT * FROM posts""")
#     posts = cursor.fetchall()
#     return {"message":posts}
#@router.get("/", response_model=List[schemas.PostOut])

@router.get("/", response_model=List[schemas.PostOut])
async def get_posts(db:Session = Depends(get_db), 
                current_user: int = Depends(oauth2.get_current_user), limit:int = 10, skip = 0,
                search: Optional[str] = ""):
    # posts = db.query(models.Posts).filter(models.Posts.owner_id == current_user.id).all()
    # posts = db.query(models.Posts).filter(models.Posts.title.contains(search)).limit(limit).offset(skip).all()
    
    posts = db.query(models.Posts, func.count(models.Vote.post_id).label("votes")).join(models.Vote, models.Vote.post_id == models.Posts.id, isouter=True).group_by(models.Posts.id).filter(models.Posts.title.contains(search)).limit(limit).offset(skip).all()  

    return posts


# @app.post("/post", status_code= status.HTTP_201_CREATED)
# async def create_post(post: Post):
#     cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING * """,
#                     (post.title, post.content, post.published))
#     new_post = cursor.fetchone()
#     conn.commit()
#     return {"data": new_post}
@router.post("/", status_code= status.HTTP_201_CREATED, response_model=schemas.Post)
async def create_post(post: schemas.PostCreate, db:Session = Depends(get_db), 
                      current_user: int = Depends(oauth2.get_current_user)):
    
    new_post = models.Posts(owner_id = current_user.id, **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

# @app.get("/posts/{id}")
# async def get_post(id:int):
#     cursor.execute("SELECT * FROM posts WHERE id = %s", (str(id),))
#     post = cursor.fetchone()
#     if not post:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail= f"post with id {id} not found")
#     return {"post_detail":post}
@router.get("/{id}", response_model=schemas.PostOut)
async def get_post(id:int, db:Session = Depends(get_db), 
                   current_user: int = Depends(oauth2.get_current_user)):
    post = db.query(models.Posts, func.count(models.Vote.post_id).label("votes")).join(
                    models.Vote, models.Vote.post_id == models.Posts.id, isouter=True).group_by(
                    models.Posts.id).filter(models.Posts.id == id).first()  
        
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail= f"post with id {id} not found")
    # if post.owner_id != current_user.id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
    #                         detail="Not authorized to perform requested action")
    return post

# @app.delete("/posts/{id}")
# async def delete_post(id:int):
#     cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING * """, (str(id),))
#     deleted_post = cursor.fetchone()
#     conn.commit()
#     if deleted_post == None:
#         raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
#                             detail= f"post with id {id} does not exist")    
#     return  Response(status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/{id}")
async def delete_post(id:int, db:Session = Depends(get_db), 
                      current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Posts).filter(models.Posts.id == id)
    post = post_query.first()
    if post == None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
                            detail= f"post with id {id} does not exist")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Not authorized to perform requested action")
    post_query.delete(synchronize_session=False)
    db.commit()  
    return  Response(status_code=status.HTTP_204_NO_CONTENT)

# @app.put("/posts/{id}")
# def update_post(id: int, post:Post):
#     cursor.execute("""UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING * """, 
#                     (post.title, post.content, post.published, str(id),))
#     updated_post = cursor.fetchone()
#     conn.commit()
#     if updated_post == None:
#         raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
#                             detail= f"post with id {id} does not exist")  
#     return {"data": updated_post}
@router.put("/{id}", response_model=schemas.Post)
async def update_post(id: int, updated_post:schemas.PostCreate, db:Session = Depends(get_db), 
                      current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Posts).filter(models.Posts.id == id)
    post = post_query.first()
    if post == None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND,
                            detail= f"post with id {id} does not exist")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Not authorized to perform requested action")
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()
    return post_query.first()

