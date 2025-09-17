from typing_extensions import Iterable


def batch_iter(_iterable: Iterable, batch_size: int = 1) -> list:
    step = 0
    tmp_iter = []
    for item in _iterable:
        step += 1
        tmp_iter.append(item)
        if step % batch_size == 0:
            yield tmp_iter.copy()
            tmp_iter.clear()
    yield tmp_iter
