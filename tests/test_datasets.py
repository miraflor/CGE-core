from pathlib import Path

import pytest

from cge_core import example_data


def test_example_data_returns_bundled_directory():
    path = example_data('stdcge')
    assert isinstance(path, Path)
    assert (path / 'param-sam-.csv').is_file()


def test_example_data_rejects_unknown_name():
    with pytest.raises(ValueError, match='Unknown example dataset'):
        example_data('unknown')
