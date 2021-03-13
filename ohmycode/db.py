from constants import DATABASE_URL
from tortoise import Tortoise, fields
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.models import Model


class Repository(Model):
    id = fields.TextField(pk=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    reported_at = fields.DatetimeField(null=True)
    next_report_at = fields.DatetimeField(null=True)

    owner = fields.TextField()
    name = fields.TextField()
    stats = fields.JSONField(default={})

    class Meta:
        table = "repository"
        unique_together = ("owner", "name")

    def __str__(self):
        return f"Repo: {self.owner}/{self.name}"


Repostitory_Pydantic = pydantic_model_creator(Repository, name="Repository")
RepostitoryIn_Pydantic = pydantic_model_creator(
    Repository, name="RepositoryIn", exclude_readonly=True, exclude=["reported_at"]
)


async def init_db():
    await Tortoise.init(db_url=DATABASE_URL, modules={"models": ["__main__"]})
    await Tortoise.generate_schemas()
