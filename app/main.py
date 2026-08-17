import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.rules import router as rules_router
from app.api.webhook import router as webhook_router
from app.api.stats import router as stats_router

from app.database import init_db, SessionLocal
from app.repositories.dm_repository import DMRepository

from app.workers.dm_worker import dm_worker
from app.workers.queue import dm_queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.
    """

    init_db()

    # Recover queued DM jobs from the database.
    db = SessionLocal()

    try:
        dm_repository = DMRepository(db)

        queued_dms = dm_repository.get_queued()

        for dm in queued_dms:
            # Store only the DM ID in the in-memory queue.
            await dm_queue.enqueue(dm.id)

    finally:
        db.close()

    # Start the background DM worker.
    worker_task = asyncio.create_task(
        dm_worker.run_forever()
    )

    try:
        yield

    finally:
        # Stop the worker cleanly when the application shuts down.
        worker_task.cancel()

        try:
            await worker_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="LinkPlease API",
    description="Reliable Instagram automation backend.",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(rules_router)
app.include_router(webhook_router)
app.include_router(stats_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
    }