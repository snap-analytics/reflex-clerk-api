from reflex_clerk_api.base import CLERK_REACT_VERSION
from reflex_clerk_api.clerk_provider import ClerkProvider
from reflex_clerk_api.control_components import Show


def _render_props(component: Show) -> list[str]:
    return component.render()["props"]


def test_show_create_with_no_props_renders_show_tag():
    component = Show.create()

    rendered = component.render()
    assert rendered["name"] == "Show"
    assert rendered["props"] == []


def test_show_create_with_signed_in_string_when():
    component = Show.create(when="signed-in")

    props = _render_props(component)
    assert 'when:"signed-in"' in props


def test_show_create_with_feature_when_serializes_to_js_object():
    component = Show.create(when={"feature": "premium"})

    props = _render_props(component)
    when_prop = next(prop for prop in props if prop.startswith("when:"))
    assert when_prop.startswith("when:({")
    assert '["feature"] : "premium"' in when_prop
    assert 'when:"{' not in when_prop


def test_show_create_with_plan_when_serializes_to_js_object():
    component = Show.create(when={"plan": "pro"})

    props = _render_props(component)
    when_prop = next(prop for prop in props if prop.startswith("when:"))
    assert when_prop.startswith("when:({")
    assert '["plan"] : "pro"' in when_prop
    assert 'when:"{' not in when_prop


def test_show_create_with_treat_pending_as_signed_out():
    component = Show.create(treat_pending_as_signed_out=True)

    props = _render_props(component)
    assert "treatPendingAsSignedOut:true" in props


def test_show_uses_exact_clerk_library_version():
    assert Show.library == f"@clerk/react@{CLERK_REACT_VERSION}"


def test_clerk_provider_uses_exact_clerk_library_version():
    assert ClerkProvider.library == f"@clerk/react@{CLERK_REACT_VERSION}"
