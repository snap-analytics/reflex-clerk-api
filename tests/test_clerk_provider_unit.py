import asyncio
import uuid

import authlib.jose.errors as jose_errors
import pytest
import reflex as rx
from reflex.utils.imports import ImportVar


def test_set_clerk_session_expired_token_clears(monkeypatch):
    """Expired tokens should not crash the handler; they should clear session."""
    # Import inside the test so the module is importable in different test layouts.
    # We need the actual module object (not just ClerkState) to monkeypatch jwt.decode
    # where it's used. importlib is required because reflex_clerk_api.clerk_provider
    # resolves to the function via __init__.py re-exports.
    import importlib

    clerk_provider_module = importlib.import_module("reflex_clerk_api.clerk_provider")
    from reflex_clerk_api.clerk_provider import ClerkState

    # Instantiate state in a framework-safe way for tests.
    state = ClerkState(_reflex_internal_init=True)

    async def fake_get_jwk_keys(self):
        return {}

    monkeypatch.setattr(ClerkState, "_get_jwk_keys", fake_get_jwk_keys, raising=True)

    validate_calls: dict[str, object] = {}

    class FakeClaims:
        def validate(self, leeway=None):
            validate_calls["leeway"] = leeway
            raise jose_errors.ExpiredTokenError()

    monkeypatch.setattr(
        clerk_provider_module.jwt,
        "decode",
        lambda *args, **kwargs: FakeClaims(),
        raising=True,
    )

    result = asyncio.run(ClerkState.set_clerk_session.fn(state, token="fake"))
    assert validate_calls["leeway"] == 60
    assert result == []
    assert state.auth_checked is True
    assert state.is_signed_in is False


def test_clerk_session_synchronizer_js_contains_reconnect_safe_deps_and_skipcache():
    """String-based regression test for the generated JS."""
    from reflex_clerk_api.clerk_provider import ClerkSessionSynchronizer

    js = ClerkSessionSynchronizer.create().add_custom_code()[0]
    assert "orgId" in js
    assert "sessionId" in js
    assert "userId" in js
    assert '["signed_in", userId || "", orgId || "", sessionId || ""].join(":")' in js
    assert "[isLoaded, isSignedIn, userId, orgId, sessionId, addEvents, getToken]" in js
    assert "skipCache: true" in js
    assert "isJwtExpired(token)" in js
    assert "setTimeout" in js
    assert "release_pending_auth_on_loads" in js
    assert "clear_clerk_session" in js
    assert "Promise.race([tokenRequest, tokenTimeout])" in js
    assert "scheduleTokenRetry()" in js
    expired_token_start = js.index("if (isJwtExpired(token))")
    expired_token_branch = js[
        expired_token_start : js.index("clear_clerk_session", expired_token_start)
    ]
    assert "lastSentRef.current" not in expired_token_branch


def test_clerk_session_synchronizer_js_uses_configured_auth_fallback_timeout():
    """The frontend fallback timeout should use ClerkState configuration."""
    from reflex_clerk_api.clerk_provider import ClerkSessionSynchronizer, ClerkState

    original_timeout = ClerkState._auth_wait_timeout_seconds
    try:
        ClerkState.set_auth_wait_timeout_seconds(2.5)
        js = ClerkSessionSynchronizer.create().add_custom_code()[0]
    finally:
        ClerkState.set_auth_wait_timeout_seconds(original_timeout)

    assert "}, 2500)" in js


def test_set_auth_wait_timeout_seconds_requires_positive_value():
    """Zero would create immediate frontend timeout/retry loops."""
    from reflex_clerk_api.clerk_provider import ClerkState

    original_timeout = ClerkState._auth_wait_timeout_seconds
    try:
        with pytest.raises(ValueError, match="auth wait timeout must be positive"):
            ClerkState.set_auth_wait_timeout_seconds(0)
        with pytest.raises(ValueError, match="auth wait timeout must be positive"):
            ClerkState.set_auth_wait_timeout_seconds(-0.1)
    finally:
        ClerkState.set_auth_wait_timeout_seconds(original_timeout)


def test_wait_for_auth_check_queues_and_set_clerk_session_flushes(monkeypatch):
    """Auth-gated on_loads should flush when the Clerk session sync succeeds."""
    import importlib

    clerk_provider_module = importlib.import_module("reflex_clerk_api.clerk_provider")
    from reflex_clerk_api.clerk_provider import ClerkState

    state = ClerkState(_reflex_internal_init=True)
    uid = uuid.uuid4()
    on_load_event = rx.noop()
    ClerkState._on_load_events = {uid: [on_load_event]}

    async def fake_get_jwk_keys(self):
        return {}

    class FakeClaims(dict):
        def validate(self, leeway=None):
            return None

    monkeypatch.setattr(ClerkState, "_get_jwk_keys", fake_get_jwk_keys, raising=True)
    monkeypatch.setattr(
        clerk_provider_module.jwt,
        "decode",
        lambda *args, **kwargs: FakeClaims(sub="user_123"),
        raising=True,
    )

    queued = asyncio.run(ClerkState.wait_for_auth_check.fn(state, uid=uid))
    assert queued == []
    assert state._pending_auth_on_load_event_ids == [str(uid)]

    flushed = asyncio.run(ClerkState.set_clerk_session.fn(state, token="fake"))
    assert flushed == [on_load_event]
    assert state.auth_checked is True
    assert state.is_signed_in is True
    assert state.user_id == "user_123"
    assert state._pending_auth_on_load_event_ids == []
    assert ClerkState._on_load_events[uid] == [on_load_event]

    next_state = ClerkState(_reflex_internal_init=True)
    next_state.auth_checked = True
    repeat = asyncio.run(ClerkState.wait_for_auth_check.fn(next_state, uid=uid))
    assert repeat == [on_load_event]


def test_wait_for_auth_check_queues_and_timeout_releases_without_state_change():
    """Frontend auth timeout should not be treated as an auth result."""
    from reflex_clerk_api.clerk_provider import ClerkState

    state = ClerkState(_reflex_internal_init=True)
    state.is_signed_in = True
    state.user_id = "user_existing"
    uid = uuid.uuid4()
    on_load_event = rx.noop()
    ClerkState._on_load_events = {uid: [on_load_event]}

    queued = asyncio.run(ClerkState.wait_for_auth_check.fn(state, uid=uid))
    assert queued == []

    flushed = ClerkState.release_pending_auth_on_loads.fn(state)
    assert flushed == [on_load_event]
    assert state.auth_checked is False
    assert state.is_signed_in is True
    assert state.user_id == "user_existing"
    assert state._pending_auth_on_load_event_ids == []
    assert ClerkState._on_load_events[uid] == [on_load_event]


def test_auth_timeout_before_queue_does_not_strand_on_load():
    """If timeout arrives before wait_for_auth_check, on_load still runs."""
    from reflex_clerk_api.clerk_provider import ClerkState

    state = ClerkState(_reflex_internal_init=True)
    uid = uuid.uuid4()
    on_load_event = rx.noop()
    ClerkState._on_load_events = {uid: [on_load_event]}

    released = ClerkState.release_pending_auth_on_loads.fn(state)
    assert released == []
    assert state.auth_checked is False
    assert state._auth_on_loads_released is True

    on_loads = asyncio.run(ClerkState.wait_for_auth_check.fn(state, uid=uid))
    assert on_loads == [on_load_event]
    assert state._pending_auth_on_load_event_ids == []
    assert ClerkState._on_load_events[uid] == [on_load_event]


def test_wait_for_auth_check_queues_and_clear_clerk_session_flushes(monkeypatch):
    """An explicit signed-out sync should flush queued on_loads as signed-out."""
    from reflex_clerk_api.clerk_provider import ClerkState

    state = ClerkState(_reflex_internal_init=True)
    uid = uuid.uuid4()
    on_load_event = rx.noop()
    ClerkState._on_load_events = {uid: [on_load_event]}

    queued = asyncio.run(ClerkState.wait_for_auth_check.fn(state, uid=uid))
    assert queued == []

    # Bare ClerkState instances do not have a parent root state in unit tests,
    # so bypass Reflex's full-tree reset and isolate this handler's behavior.
    monkeypatch.setattr(ClerkState, "reset", lambda self: None, raising=True)
    flushed = ClerkState.clear_clerk_session.fn(state)
    assert flushed == [on_load_event]
    assert state.auth_checked is True
    assert state.is_signed_in is False
    assert state._pending_auth_on_load_event_ids == []
    assert ClerkState._on_load_events[uid] == [on_load_event]


def test_clerk_session_synchronizer_imports_pinned_clerk_react():
    from reflex_clerk_api.base import CLERK_REACT_LIBRARY
    from reflex_clerk_api.clerk_provider import ClerkSessionSynchronizer

    imports = ClerkSessionSynchronizer.create().add_imports()
    assert imports.get(CLERK_REACT_LIBRARY) == ["useAuth"]
    assert "@clerk/react" not in imports


def test_clerk_base_components_import_pinned_clerk_react():
    from reflex_clerk_api.base import (
        CLERK_REACT_LIBRARY,
        CLERK_REACT_VERSION,
        DEFAULT_CLERK_FRONTEND_VERSIONS,
        ClerkBase,
    )
    from reflex_clerk_api.user_components import UserButton

    component = UserButton.create()
    imports = component._get_imports()
    assert ClerkBase.library == f"@clerk/react@{CLERK_REACT_VERSION}"
    assert component.library == CLERK_REACT_LIBRARY
    assert UserButton.get_fields()["library"].default == CLERK_REACT_LIBRARY
    assert CLERK_REACT_LIBRARY in imports
    for dependency in DEFAULT_CLERK_FRONTEND_VERSIONS.dependency_libraries:
        assert dependency in imports
        assert all(import_var.render is False for import_var in imports[dependency])


def test_clerk_provider_imports_pinned_clerk_ui_by_default():
    from reflex_clerk_api.base import CLERK_UI_LIBRARY
    from reflex_clerk_api.clerk_provider import ClerkProvider

    imports = ClerkProvider.create().add_imports()
    assert imports.get(CLERK_UI_LIBRARY) == ["ui"]
    assert "@clerk/ui" not in imports


def test_clerk_provider_defaults_clerk_ui_version():
    from reflex_clerk_api.base import CLERK_UI_VERSION
    from reflex_clerk_api.clerk_provider import ClerkProvider

    props = ClerkProvider.create().render()["props"]
    assert f'__internal_clerkUIVersion:"{CLERK_UI_VERSION}"' in props
    assert "ui:ui" in props


def test_clerk_provider_allows_ui_override():
    from reflex_clerk_api.clerk_provider import ClerkProvider

    props = ClerkProvider.create(ui="custom-ui").render()["props"]
    assert 'ui:"custom-ui"' in props


def test_clerk_provider_preserves_localization_error_keys() -> None:
    from reflex_clerk_api.clerk_provider import ClerkProvider

    props = ClerkProvider.create(
        localization={
            "unstable__errors": {
                "too_many_requests": "Too many sign-in attempts. Try again shortly.",
            }
        }
    ).render()["props"]

    localization_prop = next(prop for prop in props if prop.startswith("localization:"))
    assert '["unstable__errors"]' in localization_prop
    assert '["too_many_requests"]' in localization_prop
    assert '"Too many sign-in attempts. Try again shortly."' in localization_prop


def test_clerk_provider_defaults_clerk_js_version():
    from reflex_clerk_api.base import CLERK_JS_VERSION, CLERK_UI_VERSION
    from reflex_clerk_api.clerk_provider import ClerkProvider, clerk_provider

    assert (
        f'__internal_clerkJSVersion:"{CLERK_JS_VERSION}"'
        in ClerkProvider.create().render()["props"]
    )
    props = clerk_provider(publishable_key="pk_test").render()["props"]
    assert f'__internal_clerkJSVersion:"{CLERK_JS_VERSION}"' in props
    assert f'__internal_clerkUIVersion:"{CLERK_UI_VERSION}"' in props
    assert "ui:ui" in props


def test_clerk_provider_allows_clerk_frontend_version_overrides():
    from reflex_clerk_api.clerk_provider import ClerkProvider, clerk_provider

    assert (
        '__internal_clerkJSVersion:"6.99.0"'
        in ClerkProvider.create(
            clerk_js_version="6.99.0",
            clerk_ui_version="1.99.0",
        ).render()["props"]
    )
    provider_props = clerk_provider(
        publishable_key="pk_test",
        clerk_js_version="6.99.0",
        clerk_ui_version="1.99.0",
    ).render()["props"]
    assert '__internal_clerkJSVersion:"6.99.0"' in provider_props
    assert '__internal_clerkUIVersion:"1.99.0"' in provider_props


def test_wrap_app_defaults_clerk_js_version():
    from reflex_clerk_api.base import CLERK_JS_VERSION, CLERK_UI_VERSION
    from reflex_clerk_api.clerk_provider import wrap_app

    app = rx.App()
    wrap_app(app, publishable_key="pk_test")

    component = app.app_wraps[(1, "ClerkProvider")](None)
    props = component.render()["props"]
    assert f'__internal_clerkJSVersion:"{CLERK_JS_VERSION}"' in props
    assert f'__internal_clerkUIVersion:"{CLERK_UI_VERSION}"' in props
    assert "ui:ui" in props


def test_wrap_app_allows_clerk_frontend_version_overrides():
    from reflex_clerk_api.clerk_provider import wrap_app

    app = rx.App()
    wrap_app(
        app,
        publishable_key="pk_test",
        clerk_js_version="6.99.0",
        clerk_ui_version="1.99.0",
    )

    component = app.app_wraps[(1, "ClerkProvider")](None)
    props = component.render()["props"]
    assert '__internal_clerkJSVersion:"6.99.0"' in props
    assert '__internal_clerkUIVersion:"1.99.0"' in props


def test_wrap_app_passes_localization_to_clerk_provider() -> None:
    from reflex_clerk_api.clerk_provider import wrap_app

    app = rx.App()
    wrap_app(
        app,
        publishable_key="pk_test",
        localization={
            "unstable__errors": {
                "too_many_requests": "Too many sign-in attempts. Try again shortly.",
            }
        },
    )

    component = app.app_wraps[(1, "ClerkProvider")](False)
    assert component is not None
    props = component.render()["props"]
    localization_prop = next(prop for prop in props if prop.startswith("localization:"))
    assert '["unstable__errors"]' in localization_prop
    assert '["too_many_requests"]' in localization_prop
    assert '"Too many sign-in attempts. Try again shortly."' in localization_prop


def test_configure_clerk_frontend_versions_updates_field_defaults():
    from reflex_clerk_api.base import (
        configure_clerk_frontend_versions,
        reset_clerk_frontend_versions,
    )
    from reflex_clerk_api.clerk_provider import ClerkProvider
    from reflex_clerk_api.user_components import UserButton

    try:
        versions = configure_clerk_frontend_versions(
            react_version="6.7.0",
            ui_version="1.10.0",
            clerk_js_version="6.11.0",
        )

        assert versions.react_library == "@clerk/react@6.7.0"
        assert UserButton.library == versions.react_library
        assert UserButton.lib_dependencies == versions.dependency_libraries
        assert UserButton.get_fields()["library"].default == versions.react_library
        assert (
            UserButton.get_fields()["lib_dependencies"].default
            == versions.dependency_libraries
        )
        assert UserButton.create().library == versions.react_library
        assert versions.react_library in UserButton.create()._get_imports()
        assert (
            ClerkProvider.get_fields()["clerk_js_version"].default
            == versions.clerk_js_version
        )
        assert ClerkProvider.get_fields()["clerk_ui_version"].default == "1.10.0"
        props = ClerkProvider.create().render()["props"]
        assert '__internal_clerkJSVersion:"6.11.0"' in props
        assert '__internal_clerkUIVersion:"1.10.0"' in props
    finally:
        reset_clerk_frontend_versions()


def test_custom_component_reads_clerk_base_library_at_call_time():
    from reflex_clerk_api.base import (
        DEFAULT_CLERK_FRONTEND_VERSIONS,
        ClerkBase,
        configure_clerk_frontend_versions,
    )

    class CustomUserButton(rx.Component):
        library = None
        tag = "CustomUserButton"

        def _get_imports(self):
            return {ClerkBase.library: [ImportVar(tag="UserButton")]}

    try:
        configure_clerk_frontend_versions(
            react_version="6.8.0",
            ui_version="1.11.0",
            clerk_js_version="6.12.0",
        )

        assert "@clerk/react@6.8.0" in CustomUserButton.create()._get_imports()
    finally:
        configure_clerk_frontend_versions(DEFAULT_CLERK_FRONTEND_VERSIONS)


def test_on_load_registration_key_survives_process_replacement():
    """The same key re-derives the same registry id, as a restarted process would."""
    from reflex_clerk_api.clerk_provider import ClerkState, on_load

    ClerkState._on_load_events = {}
    first = on_load(rx.noop(), registration_key="/project/[project_id]")
    ids_after_first = set(ClerkState._on_load_events)

    ClerkState._on_load_events = {}
    second = on_load(rx.noop(), registration_key="/project/[project_id]")

    assert len(first) == 1
    assert len(second) == 1
    assert set(ClerkState._on_load_events) == ids_after_first
    assert len(ids_after_first) == 1


def test_on_load_distinct_registration_keys_get_distinct_ids():
    """Different routes must not share a registration slot."""
    from reflex_clerk_api.clerk_provider import ClerkState, on_load

    ClerkState._on_load_events = {}
    on_load(rx.noop(), registration_key="/project/[project_id]")
    on_load(rx.noop(), registration_key="/project/[project_id]/billing")

    assert len(ClerkState._on_load_events) == 2


def test_on_load_without_registration_key_mints_random_ids():
    """The default keeps today's behavior: every registration is unique."""
    from reflex_clerk_api.clerk_provider import ClerkState, on_load

    ClerkState._on_load_events = {}
    on_load(rx.noop())
    on_load(rx.noop())

    assert len(ClerkState._on_load_events) == 2
