"""Test the dirods package."""


def test_version_is_string():
    import dirods
    assert isinstance(dirods.__version__, str)
