from constants import DATABASE_URL

from fastapi import Request, status
from fastapi_users import FastAPIUsers, models
from fastapi_users.db import (
    TortoiseBaseOAuthAccountModel,
    TortoiseBaseUserModel,
    TortoiseUserDatabase
)
from fastapi_users.authentication import CookieAuthentication
from tortoise import fields
from tortoise.models import Model
from tortoise.contrib.pydantic import PydanticModel, pydantic_model_creator

from gh import get_user_info

from httpx_oauth.clients.github import GitHubOAuth2

github_oauth_client = GitHubOAuth2(
    "", ""
)

SECRET = "SECRET"

class UserModel(TortoiseBaseUserModel):
    username = fields.CharField(null=False, max_length=255)
    avatar_url = fields.CharField(null=False, max_length=255)


class OAuthAccountModel(TortoiseBaseOAuthAccountModel):
    user = fields.ForeignKeyField("models.UserModel", related_name="oauth_accounts")


class User(models.BaseUser, models.BaseOAuthAccountMixin):
    username: str = ""
    avatar_url: str = ""

class UserCreate(models.BaseUserCreate):
    pass


class UserUpdate(User, models.BaseUserUpdate):
    pass


class UserDB(User, models.BaseUserDB, PydanticModel):
    class Config:
        orm_mode = True
        orig_model = UserModel


async def on_after_register(user: UserDB, request: Request):
    user_info = await get_user_info(user.oauth_accounts[0].access_token)

    user_model = await UserModel.get(id=user.id)
    user_model.username = user_info["login"]
    user_model.avatar_url = user_info["avatar_url"]
    await user_model.save()

    print(f"User {user_info['login']} has registered.")


class AutoRedirectCookieAuthentication(CookieAuthentication):
    async def get_login_response(self, user, response):
        await super().get_login_response(user, response)
        response.status_code = status.HTTP_302_FOUND
        response.headers["Location"] = "http://local.dev.com:3000"
        print(response.headers)
        return None


cookie_authentication = AutoRedirectCookieAuthentication(
    secret=SECRET,
    cookie_domain=".local.dev.com",
    lifetime_seconds=3600,
    cookie_httponly=False,
    cookie_secure=False,
    cookie_samesite="none",
)

user_db = TortoiseUserDatabase(UserDB, UserModel, OAuthAccountModel)
fastapi_users = FastAPIUsers(
    user_db,
    [cookie_authentication],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)
github_oauth_router = fastapi_users.get_oauth_router(
    github_oauth_client, SECRET, after_register=on_after_register
)


class Repository(Model):
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField("models.UserModel", related_name="repositories")

    owner = fields.TextField()
    name = fields.TextField()

    meta = fields.JSONField(default={})
    stats = fields.JSONField(default={})

    class Meta:
        table = "repository"
        unique_together = ("owner", "name")

    def __str__(self):
        return f"Repo: {self.owner}/{self.name}"


Repostitory_Pydantic = pydantic_model_creator(Repository, name="Repository")
RepostitoryIn_Pydantic = pydantic_model_creator(
    Repository, name="RepositoryIn", exclude_readonly=True, include=["owner", "name"]
)


# async def init_db():
#     await Tortoise.init(db_url=DATABASE_URL, modules={"models": ["__main__"]})
#     await Tortoise.generate_schemas()
