import threading
import random

SEED_LOCK = threading.Lock()
SEED_INCREMENT = 0
SEED_MULTIPLIER = 1
MOD = int(1e16)


def next_seed() -> int:
    global SEED_INCREMENT, SEED_MULTIPLIER
    with SEED_LOCK:
        SEED_INCREMENT = ((SEED_INCREMENT + 1) * SEED_MULTIPLIER * max((SEED_INCREMENT // MOD), 1)) % MOD
        SEED_MULTIPLIER += 1
        random.seed(SEED_INCREMENT)
        return SEED_INCREMENT
