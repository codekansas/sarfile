"""Pytest configuration file."""

from _pytest.python import Function, Metafunc


def pytest_runtest_setup(item: Function) -> None:
    pass


def pytest_collection_modifyitems(items: list[Function]) -> None:
    items.sort(key=lambda x: x.get_closest_marker("slow") is not None)


def pytest_generate_tests(metafunc: Metafunc) -> None:
    pass
