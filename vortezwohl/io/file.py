import os


def read_file(path: str, encoding: str = 'utf-8') -> str:
    try:
        with open(path, mode='r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(path, mode='r', encoding='gbk') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(path, mode='r', encoding=encoding, errors='replace') as f:
                return f.read()


def write_file(content: str | bytes, path: str, encoding: str = 'utf-8') -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(content, bytes):
        with open(path, mode='wb') as f:
            f.write(content)
        return path
    with open(path, mode='w', encoding=encoding) as f:
        f.write(content)
    return os.path.abspath(path)


def get_files(path: str) -> list:
    path = os.path.abspath(path)
    if os.path.exists(path):
        entries = os.listdir(path)
        return [os.path.join(path, entry) for entry in entries if os.path.isfile(os.path.join(path, entry))]
    else:
        return []
