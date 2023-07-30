import time
from contextlib import contextmanager

from celery.utils.log import get_task_logger
from django.core.cache import cache

logger = get_task_logger(__name__)

class CeleryTaskLocker:
    def __init__(self, lock_id: str, oid: str, lock_expire: int= 10 * 60):
        self._oid = oid
        self._lock_expire = lock_expire
        self._lock_id = lock_id
        self._status = None
        self._timeout_at = None

    def __enter__(self):
        # cache.add fails if the key already exists
        self._timeout_at = time.monotonic() + self._lock_expire - 3
        self._status = cache.add(self._lock_id, self._oid, self._lock_expire)
        return self._status

    def __exit__(self, exc_type, exc_val, exc_tb):
        timeout_at = time.monotonic() + self._lock_expire - 3
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if time.monotonic() < timeout_at and self._status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            cache.delete(self._lock_id)






@contextmanager
def memcache_lock(lock_id, oid, expire: int=60 * 10):
    """
    Default exire 10 minutes
    """
    timeout_at = time.monotonic() + expire - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, oid, expire)
    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if time.monotonic() < timeout_at and status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            cache.delete(lock_id)