from datetime import datetime, timedelta
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from constants import DATABASE_URL
from db import Repository, Repostitory_Pydantic, RepostitoryIn_Pydantic
from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel
from send_report import save_yesterday_stats, send_report
from tortoise.contrib.fastapi import HTTPNotFoundError, register_tortoise

app = FastAPI()

Schedule = AsyncIOScheduler()


register_tortoise(
    app,
    db_url=DATABASE_URL,
    modules={"models": ["db"]},
    generate_schemas=True,
    add_exception_handlers=True,
)


class Status(BaseModel):
    message: str


@app.get("/repos", response_model=List[Repostitory_Pydantic])
async def get_repos():
    return await Repostitory_Pydantic.from_queryset(Repository.all())


@app.post("/repos", response_model=Repostitory_Pydantic)
async def create_repo(repo: RepostitoryIn_Pydantic):
    data = repo.dict(exclude_unset=True)
    data["id"] = f"{repo.owner}_{repo.name}"
    data["next_report_at"] = datetime.today() + timedelta(days=1, hours=6)
    repo_obj = await Repository.create(**data)
    return await Repostitory_Pydantic.from_tortoise_orm(repo_obj)


@app.get(
    "/repos/{repo_id}",
    response_model=Repostitory_Pydantic,
    responses={404: {"model": HTTPNotFoundError}},
)
async def get_repo(repo_id: str):
    return await Repostitory_Pydantic.from_queryset_single(Repository.get(id=repo_id))


@app.post(
    "/repos/{repo_id}/send_report",
    response_model=Status,
    responses={404: {"model": HTTPNotFoundError}},
)
async def send_repo_report(repo_id: str):
    await send_report(repo_id)
    return Status(message=f"Sent report for repo {repo_id}")


@app.put(
    "/repos/{repo_id}",
    response_model=Repostitory_Pydantic,
    responses={404: {"model": HTTPNotFoundError}},
)
async def update_repo(repo_id: str, repo: RepostitoryIn_Pydantic):
    await Repository.filter(id=repo_id).update(**repo.dict(exclude_unset=True))
    return await Repostitory_Pydantic.from_queryset_single(Repository.get(id=repo_id))


@app.delete(
    "/repos/{repo_id}",
    response_model=Status,
    responses={404: {"model": HTTPNotFoundError}},
)
async def delete_repo(repo_id: str):
    deleted_count = await Repository.filter(id=repo_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"repo {repo_id} not found")
    return Status(message=f"Deleted repo {repo_id}")


async def save_all_yesterday_stats():
    logger.info("Check repos to send report")
    repos = await Repository.filter(next_report_at__lt=datetime.now()).all()
    if not repos:
        logger.info("No repos to update")
    for repo in repos:
        await save_yesterday_stats(repo.id)


async def send_reports():
    logger.info("Check repos to send report")
    repos = await Repository.filter(next_report_at__lt=datetime.now()).all()
    if not repos:
        logger.info("No repos to update")
    for repo in repos:
        await send_report(repo.id)


@app.on_event("startup")
async def setup_scheduler():
    Schedule.start()
    Schedule.add_job(send_reports, trigger="interval", seconds=60 * 10)
    Schedule.add_job(save_all_yesterday_stats, trigger="cron", hour="00", minute="00")


@app.on_event("shutdown")
async def stop_scheduler():
    Schedule.shutdown()
