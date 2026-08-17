import asyncio

from app.workers.dm_worker import DMWorker
from app.workers.queue import DMQueue


class FakeDM:
    def __init__(self):
        self.id = 999
        self.retry_count = 5
        self.status = "accepted"
        self.pseudogram_dm_id = "dm_fake_c1"
        self.recipient_user_id = "usr_fake"
        self.comment_id = "cmt_fake"


class FakeRepository:
    def __init__(self, dm):
        self.dm = dm

    def get_by_id(self, dm_id):
        return self.dm

    def increment_retry(self, dm, next_attempt_at):
        dm.retry_count += 1
        dm.status = "queued"
        dm.next_attempt_at = next_attempt_at

    def update_delivery_status(self, dm, status):
        dm.status = status


class FakeSession:
    def close(self):
        pass


async def fake_get_dm_status(self, dm_id):
    class Result:
        status = "failed"

    return Result()


async def main():
    worker = DMWorker()

    dm = FakeDM()
    repository = FakeRepository(dm)

    import app.workers.dm_worker as worker_module

    original_session_local = worker_module.SessionLocal
    original_queue = worker_module.dm_queue
    original_repository = worker_module.DMRepository
    original_client = worker_module.PseudoGramClient

    fake_queue = DMQueue()

    class FakeClient:
        async def get_dm_status(self, dm_id):
            return await fake_get_dm_status(self, dm_id)

        async def close(self):
            pass

    worker_module.SessionLocal = lambda: FakeSession()
    worker_module.DMRepository = lambda db: repository
    worker_module.PseudoGramClient = FakeClient
    worker_module.dm_queue = fake_queue

    try:
        await worker.reconcile_dm(
            dm_id=dm.id,
            pseudogram_dm_id=dm.pseudogram_dm_id,
        )

        queued_id = await fake_queue.dequeue()

        print("Status:", dm.status)
        print("Retry count:", dm.retry_count)
        print("Queued DM ID:", queued_id)

    finally:
        worker_module.SessionLocal = original_session_local
        worker_module.dm_queue = original_queue
        worker_module.DMRepository = original_repository
        worker_module.PseudoGramClient = original_client


if __name__ == "__main__":
    asyncio.run(main())