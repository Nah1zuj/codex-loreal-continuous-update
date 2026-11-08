"""Keep regression runs away from the user's settings and SQLite database."""
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from runtime import WORK, isolated_environment


def pytest_configure(config):
    WORK.mkdir(exist_ok=True)
    directory = TemporaryDirectory(prefix='pytest-', dir=WORK)
    config.add_cleanup(directory.cleanup)
    env = pytest.MonkeyPatch()
    config.add_cleanup(env.undo)
    for key, value in isolated_environment(Path(directory.name)).items():
        env.setenv(key, value)
    if config.option.basetemp is None:
        config.option.basetemp = str(Path(directory.name) / 'cases')
