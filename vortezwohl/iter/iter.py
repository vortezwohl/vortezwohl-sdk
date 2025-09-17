from typing_extensions import Iterable, Any


def batch_iter(_iterable: Iterable, batch_size: int = 1, fill_value: Any = None) -> list:
    step = 0
    tmp_iter = []
    for item in _iterable:
        step += 1
        tmp_iter.append(item)
        if step % batch_size == 0:
            yield tmp_iter.copy()
            tmp_iter.clear()
    if len(tmp_iter) > 0:
        while len(tmp_iter) < batch_size:
            tmp_iter.append(fill_value)
        yield tmp_iter


def sliding_window_iter(_iterable: Iterable, window_size: int, stride: int, fill_value: Any = None) -> Iterable:
    _list_iterable = list(_iterable)
    outer_step = 0
    for _ in _list_iterable:
        if outer_step % stride == 0:
            tmp_iter = []
            inner_step = 0
            for item in _list_iterable[outer_step:]:
                inner_step += 1
                tmp_iter.append(item)
                if inner_step % window_size == 0 and inner_step > 0:
                    yield tmp_iter.copy()
                    tmp_iter.clear()
                    break
            if len(tmp_iter) > 0:
                while len(tmp_iter) < window_size:
                    tmp_iter.append(fill_value)
                yield tmp_iter.copy()
        outer_step += 1
