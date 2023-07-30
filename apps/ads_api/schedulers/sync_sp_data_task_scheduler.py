from celery.schedules import crontab

from apps.ads_api.constants import ServerLocation
from apps.ads_api.interfaces.schedulers.scheduler_interface import SchedulerInterface


class SyncSpDataTaskScheduler(SchedulerInterface):
    def __init__(self, sender):
        self._sender = sender
        self._task = self._save_task_import()

    def setup_with_delay_by_location(self):
        self._sender.add_periodic_task(
            crontab(hour=0, minute=0),
            self._task.s(
                server_locations=[ServerLocation.EUROPE, ServerLocation.FAR_EAST]
            ),
        )
        self._sender.add_periodic_task(
            crontab(hour=8, minute=0),
            self._task.s(server_locations=[ServerLocation.NORTH_AMERICA]),
        )

    @staticmethod
    def _save_task_import():
        from apps.ads_api.tasks import sync_sp_data

        return sync_sp_data
