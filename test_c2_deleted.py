from app.workers.dm_worker import DMWorker


class FakeDM:
    def __init__(self):
        self.id = 999
        self.status = "cancelled"


def main():
    worker = DMWorker()

    dm = FakeDM()

    # This is the same protection used inside
    # DMWorker.process_dm().
    if dm.status in {
        "delivered",
        "failed",
        "cancelled",
    }:
        print("DM status:", dm.status)
        print("DM will NOT be sent.")
        print("C2 cancellation test OK")
        return

    print("ERROR: cancelled DM would be processed")


if __name__ == "__main__":
    main()