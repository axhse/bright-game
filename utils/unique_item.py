import random


class UniqueItem:
    def __init__(self, uid=None):
        self._uid = UniqueItem.random_uid(length=64) if uid is None else uid

    @staticmethod
    def random_uid(length):
        return ''.join([random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for _ in range(length)])

    @property
    def uid(self) -> str:
        return self._uid
