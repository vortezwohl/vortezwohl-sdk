# vortezwohl-sdk

> Useful Python SDKs

## Installation

```
pip install -U git+https://github.com/vortezwohl/vortezwohl-sdk.git
```

## Quick Start

- ### Thread Pool

    - Import SDKs

        ```python
        import random
        import time

        from vortezwohl.concurrent import ThreadPool
        ```

    - Create callables

        ```python
        def job1(x: int, y: int) -> int:
            res = x + y
            time.sleep(res / 2)
            return res


        def job2() -> int:
            _delay = random.randint(1, 4)
            time.sleep(_delay / 2)
            return _delay


        def job3(x) -> int:
            time.sleep(x / 2)
            return x
        ```

    - Gather jobs (tasks)

        ```python
        with ThreadPool() as t:
            for fn, param, result in t.gather(jobs=[job1, job1, job1, job2, job2, job3], 
                                            arguments=[(1, 2), (2, 3), {'x': 3, 'y': 4}, None, None, 5]):
                print('fn={}, param={}, result={}'.format(fn, param, result))
        ```

        stdout:

        ```
        fn=<function job2 at 0x00000183016C0180>, param=None, result=1
        fn=<function job1 at 0x00000183013B63E0>, param=(1, 2), result=3
        fn=<function job2 at 0x00000183016C0180>, param=None, result=3
        fn=<function job1 at 0x00000183013B63E0>, param=(2, 3), result=5
        fn=<function job3 at 0x00000183016C0220>, param=5, result=5
        fn=<function job1 at 0x00000183013B63E0>, param={'x': 3, 'y': 4}, result=7
        ```

    - Submit jobs respectively


        ```python
        with ThreadPool() as t:
            t.submit(job1, 1, 2)
            t.submit(job1, 2, 3)
            t.submit(job1, x=3, y=4)
            t.submit(job2)
            t.submit(job2)
            t.submit(job3, 5)
            for fn, param, result in t.next_result:
                print('fn={}, param={}, result={}'.format(fn, param, result))
        ```

        stdout:

        ```
        fn=<function job2 at 0x000001B82B61C0E0>, param=None, result=2
        fn=<function job1 at 0x000001B82B31A480>, param=(1, 2), result=3
        fn=<function job2 at 0x000001B82B61C0E0>, param=None, result=4
        fn=<function job1 at 0x000001B82B31A480>, param=(2, 3), result=5
        fn=<function job3 at 0x000001B82B61C180>, param=(5,), result=5
        fn=<function job1 at 0x000001B82B31A480>, param={'x': 3, 'y': 4}, result=7
        ```

- ### Seed Generator

    - Import SDKs

        ```python
        import random

        from vortezwohl.random import next_seed
        ```
    
    - Do random stuff

        ```python
        for _ in range(10):
            next_seed()
            print(random.randint(1, 10))
        ```

        stdout:

        ```
        3
        4
        4
        8
        9
        6
        8
        7
        1
        10
        ```