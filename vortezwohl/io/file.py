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


def size_of(path: str) -> int:  # bytes
    def size_of_dir(dir_path: str) -> int:
        total_size = 0
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            return 0
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            if os.path.isfile(item_path):
                total_size += os.path.getsize(item_path)
            elif os.path.isdir(item_path):
                total_size += size_of_dir(item_path)
        return total_size

    if not os.path.exists(path):
        return 0
    if os.path.isfile(path):
        return os.path.getsize(path)
    elif os.path.isdir(path):
        return size_of_dir(path)
    else:
        raise TypeError(f'The path "{path}" is not a file or directory.')
