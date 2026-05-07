import asyncio

import authlib.jose.errors as jose_errors
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
    assert (
        '[\"signed_in\", userId || \"\", orgId || \"\", sessionId || \"\"].join(\":\")'
        in js
    )
    assert "[isLoaded, isSignedIn, userId, orgId, sessionId, addEvents, getToken]" in js
    assert "skipCache: true" in js
    assert "isJwtExpired(token)" in js


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


def test_clerk_provider_defaults_clerk_js_version():
    from reflex_clerk_api.base import CLERK_JS_VERSION, CLERK_UI_VERSION
    from reflex_clerk_api.clerk_provider import ClerkProvider, clerk_provider

    assert f'__internal_clerkJSVersion:"{CLERK_JS_VERSION}"' in ClerkProvider.create().render()[
        "props"
    ]
    props = clerk_provider(publishable_key="pk_test").render()["props"]
    assert f'__internal_clerkJSVersion:"{CLERK_JS_VERSION}"' in props
    assert f'__internal_clerkUIVersion:"{CLERK_UI_VERSION}"' in props
    assert "ui:ui" in props


def test_clerk_provider_allows_clerk_frontend_version_overrides():
    from reflex_clerk_api.clerk_provider import ClerkProvider, clerk_provider

    assert '__internal_clerkJSVersion:"6.99.0"' in ClerkProvider.create(
        clerk_js_version="6.99.0",
        clerk_ui_version="1.99.0",
    ).render()["props"]
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
