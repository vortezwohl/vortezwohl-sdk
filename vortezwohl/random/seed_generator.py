import os
import threading
import random

SEED_LOCK = threading.RLock()
SEED_INCREMENT = None
SEED_MULTIPLIER = None
MOD = int(1e64)


def next_seed() -> int:
    global SEED_INCREMENT, SEED_MULTIPLIER
    SEED_INCREMENT = int(os.getenv('INITIAL_SEED', 0)) if SEED_INCREMENT is None else SEED_INCREMENT
    SEED_MULTIPLIER = int(os.getenv('SEED_MULTIPLIER', 1)) if SEED_MULTIPLIER is None else SEED_MULTIPLIER
    SEED_LOCK.acquire(blocking=True)
    SEED_INCREMENT = ((SEED_INCREMENT + 1) * SEED_MULTIPLIER * max((SEED_INCREMENT // MOD), 1)) % MOD
    SEED_MULTIPLIER += 1
    SEED_LOCK.release()
    random.seed(SEED_INCREMENT)
    return SEED_INCREMENT
