import reflex_clerk_api as clerk


def test_show_is_exported():
    assert hasattr(clerk, "show")


def test_deprecated_control_helpers_are_not_exported():
    assert not hasattr(clerk, "protect")
    assert not hasattr(clerk, "signed_in")
    assert not hasattr(clerk, "signed_out")
