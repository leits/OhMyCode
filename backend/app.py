from datetime import datetime, timedelta
from typing import List

from db import Repository, Repostitory_Pydantic, RepostitoryIn_Pydantic, UserDB, UserModel, OAuthAccountModel
from constants import DATABASE_URL
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise, HTTPNotFoundError
from fastapi_users.db import TortoiseUserDatabase
from pydantic import BaseModel
from db import fastapi_users, github_oauth_router, User

user_db = TortoiseUserDatabase(UserDB, UserModel, OAuthAccountModel)
app = FastAPI()
register_tortoise(
    app,
    db_url=DATABASE_URL,
    modules={"models": ["db"]},
    generate_schemas=True,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://local.dev.com:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Status(BaseModel):
    message: str


CurrentUserDepends = Depends(fastapi_users.current_user())

app.include_router(fastapi_users.get_users_router(), prefix="/users", tags=["users"])

app.include_router(github_oauth_router, prefix="/auth/github", tags=["auth"])

@app.get(
    "/repos", response_model=List[Repostitory_Pydantic], tags=["repos"]
)
async def get_repos(user: User = CurrentUserDepends):
    repos = Repository.filter(user__id=user.id).all()
    return await Repostitory_Pydantic.from_queryset(repos)


@app.post("/repos", response_model=Repostitory_Pydantic, tags=["repos"])
async def add_repo(
    repo: RepostitoryIn_Pydantic, user: User = CurrentUserDepends
):
    data = repo.dict(exclude_unset=True)
    data["user_id"] = user.id
    data["next_report_at"] = datetime.today() + timedelta(days=1, hours=6)
    repo_obj = await Repository.create(**data)
    return await Repostitory_Pydantic.from_tortoise_orm(repo_obj)


@app.get(
    "/repos/{repo_id}",
    response_model=Repostitory_Pydantic,
    responses={404: {"model": HTTPNotFoundError}},
    tags=["repos"],
)
async def get_repo(repo_id: str, user: User = CurrentUserDepends):
    return await Repostitory_Pydantic.from_queryset_single(Repository.get(id=repo_id))


@app.patch(
    "/repos/{repo_id}",
    response_model=Repostitory_Pydantic,
    responses={404: {"model": HTTPNotFoundError}},
    tags=["repos"],
)
async def update_repo(
    repo_id: str,
    repo: RepostitoryIn_Pydantic,
    user: User = CurrentUserDepends,
):
    await Repository.filter(id=repo_id).update(**repo.dict(exclude_unset=True))
    return await Repostitory_Pydantic.from_queryset_single(Repository.get(id=repo_id))


@app.delete(
    "/repos/{repo_id}",
    response_model=Status,
    responses={404: {"model": HTTPNotFoundError}},
    tags=["repos"],
)
async def delete_repo(repo_id: str, user: User = CurrentUserDepends):
    deleted_count = await Repository.filter(id=repo_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"repo {repo_id} not found")
    return Status(message=f"Deleted repo {repo_id}")
