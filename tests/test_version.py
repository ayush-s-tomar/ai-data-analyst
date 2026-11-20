import re

from version import __version__


def test_version_looks_like_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)
