import random


class UniqueItem:
    def __init__(self, uid_length: int = 64):
        self._uid = ''.join([random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for _ in range(uid_length)])

    @property
    def uid(self) -> str:
        return self._uid
