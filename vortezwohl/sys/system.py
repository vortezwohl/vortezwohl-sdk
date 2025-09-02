import re
import os
import sys
import subprocess

from vortezwohl.io.file import get_files, size_of
from vortezwohl.nlp.levenshtein_distance import LevenshteinDistance

lev_distance = LevenshteinDistance(ignore_case=True)


class System:
    def __init__(self):
        self._python = sys.executable
        self._venv_executable = os.path.dirname(self._python)
        self._workdir = os.getcwd()
        self.shell(f'{self._python} -m ensurepip --upgrade', force_check=True)
        __pip_name = lev_distance.rank('pip', [os.path.basename(_) for _ in get_files(self._venv_executable)])[0]
        self._pip = os.path.join(self._venv_executable, __pip_name)

    def shell(self, cmd: str, workdir: str | None = None, timeout: int | None = None,
              force_check: bool = False) -> tuple[str, int, str]:
        if workdir is None:
            workdir = self._workdir
        res = subprocess.run(cmd, cwd=workdir, shell=True, capture_output=True, text=True,
                             timeout=timeout, check=force_check)
        return res.stdout, res.returncode, res.stderr

    def script(self, script: str, argument: str):
        return self.shell(f'{os.path.join(self._venv_executable, script)} {argument}')

    def interpret(self, script: str, is_module: bool = False):
        if is_module:
            return self.shell(f'{self._python} -m {script}', force_check=False)
        return self.shell(f'{self._python} {script}', force_check=False)

    def list_packages(self):
        tmp_res = self.shell(f'{self._pip} list', force_check=True)[0].splitlines(keepends=False)[2:]
        res = []
        blank_pattern = re.compile(r'(\s+)')
        for line in tmp_res:
            if len(line.strip()) < 1:
                break
            res.append(line)
        for i, line in enumerate(res):
            _tmp_line = re.split(pattern=blank_pattern, string=line)
            res[i] = f'{_tmp_line[0]}=={_tmp_line[2]}'
        return res

    def show_package(self, package: str) -> list[str]:
        try:
            return self.shell(f'{self._pip} show {package}', force_check=True)[0].splitlines(keepends=False)
        except subprocess.CalledProcessError:
            return []

    def package_size(self, package: str) -> int:
        location = [line for line in self.show_package(package) if line.lower().__contains__('location:')]
        if len(location) > 0:
            location = location[0]
            location = location[location.find(':') + 1:].strip()
            return size_of(location)
        else:
            return 0

    def package_version(self, package: str) -> str:
        version = [line for line in self.show_package(package) if line.lower().__contains__('version:')]
        if len(version) > 0:
            version = version[0]
            return version[version.find(':') + 1:].strip()
        else:
            return 'Unknown'

    def install_package(self, package: str, version: str | None = None) -> str | bool:
        try:
            if version is not None:
                self.shell(f'{self._pip} install {package}~={version}', force_check=True)
            else:
                self.shell(f'{self._pip} install --upgrade {package}', force_check=True)
            return f'{package}=={self.package_version(package)}'
        except subprocess.CalledProcessError:
            return False

    def uninstall_package(self, package: str) -> str | bool:
        try:
            version = self.package_version(package)
            self.shell(f'{self._pip} uninstall {package}', force_check=True)
            return f'{package}=={version}'
        except subprocess.CalledProcessError:
            return False
