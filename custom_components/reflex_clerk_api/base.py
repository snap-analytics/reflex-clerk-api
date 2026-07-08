from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, replace

import reflex as rx


def _versioned_package(package: str, version: str) -> str:
    return f"{package}@{version}"


@dataclass(frozen=True)
class ClerkFrontendVersions:
    """Frontend package versions that must stay compatible with each other."""

    react_version: str
    ui_version: str
    clerk_js_version: str
    shared_version: str | None = None
    localizations_version: str | None = None
    tanstack_query_core_version: str | None = None

    @property
    def react_library(self) -> str:
        """The versioned @clerk/react package import used by Reflex."""
        return _versioned_package("@clerk/react", self.react_version)

    @property
    def ui_library(self) -> str:
        """The versioned @clerk/ui package import used by Reflex."""
        return _versioned_package("@clerk/ui", self.ui_version)

    @property
    def dependency_libraries(self) -> tuple[str, ...]:
        """Additional frontend dependencies to install alongside Clerk."""
        dependencies = (
            ("@clerk/shared", self.shared_version),
            ("@clerk/localizations", self.localizations_version),
            ("@tanstack/query-core", self.tanstack_query_core_version),
        )
        return tuple(
            _versioned_package(package, version)
            for package, version in dependencies
            if version is not None
        )


DEFAULT_CLERK_FRONTEND_VERSIONS = ClerkFrontendVersions(
    react_version="6.12.0",
    ui_version="1.25.0",
    clerk_js_version="6.25.0",
    shared_version="4.25.0",
    localizations_version="4.13.0",
    tanstack_query_core_version="5.101.2",
)

CLERK_REACT_VERSION = DEFAULT_CLERK_FRONTEND_VERSIONS.react_version
CLERK_UI_VERSION = DEFAULT_CLERK_FRONTEND_VERSIONS.ui_version
CLERK_JS_VERSION = DEFAULT_CLERK_FRONTEND_VERSIONS.clerk_js_version
CLERK_REACT_LIBRARY = DEFAULT_CLERK_FRONTEND_VERSIONS.react_library
CLERK_UI_LIBRARY = DEFAULT_CLERK_FRONTEND_VERSIONS.ui_library

_clerk_frontend_versions = DEFAULT_CLERK_FRONTEND_VERSIONS


class ClerkBase(rx.Component):
    # The React library to wrap.
    # `Show` is exported from `@clerk/react` (v6+), not `@clerk/clerk-react`.
    library = CLERK_REACT_LIBRARY
    lib_dependencies: tuple[str, ...] = DEFAULT_CLERK_FRONTEND_VERSIONS.dependency_libraries

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Keep future subclasses aligned with the active frontend version set."""
        super().__init_subclass__(**kwargs)
        _sync_clerk_component_class(cls)


def get_clerk_frontend_versions() -> ClerkFrontendVersions:
    """Return the active Clerk frontend version set."""
    return _clerk_frontend_versions


def get_clerk_react_library() -> str:
    """Return the active versioned @clerk/react package name."""
    return _clerk_frontend_versions.react_library


def get_clerk_ui_library() -> str:
    """Return the active versioned @clerk/ui package name."""
    return _clerk_frontend_versions.ui_library


def configure_clerk_frontend_versions(
    versions: ClerkFrontendVersions | None = None,
    *,
    react_version: str | None = None,
    ui_version: str | None = None,
    clerk_js_version: str | None = None,
    shared_version: str | None = None,
    localizations_version: str | None = None,
    tanstack_query_core_version: str | None = None,
) -> ClerkFrontendVersions:
    """Configure the Clerk frontend packages emitted by Reflex.

    Call this before creating pages/components if an app needs to override the
    package defaults. Already-imported Clerk component classes are updated too,
    including Reflex's stored field defaults.
    """
    global _clerk_frontend_versions

    next_versions = versions or _clerk_frontend_versions
    replacements = {
        "react_version": react_version,
        "ui_version": ui_version,
        "clerk_js_version": clerk_js_version,
        "shared_version": shared_version,
        "localizations_version": localizations_version,
        "tanstack_query_core_version": tanstack_query_core_version,
    }
    next_versions = replace(
        next_versions,
        **{key: value for key, value in replacements.items() if value is not None},
    )

    _clerk_frontend_versions = next_versions
    for component_cls in _iter_clerk_component_classes():
        _sync_clerk_component_class(component_cls)
    return next_versions


def reset_clerk_frontend_versions() -> ClerkFrontendVersions:
    """Reset Clerk frontend packages to the package defaults."""
    return configure_clerk_frontend_versions(DEFAULT_CLERK_FRONTEND_VERSIONS)


def _sync_clerk_component_class(component_cls: type[rx.Component]) -> None:
    """Sync class attributes and Reflex field defaults for Clerk components."""
    versions = get_clerk_frontend_versions()
    component_cls.library = versions.react_library
    component_cls.lib_dependencies = versions.dependency_libraries

    fields = component_cls.get_fields()
    if "library" in fields:
        fields["library"].default = versions.react_library
    if "lib_dependencies" in fields:
        fields["lib_dependencies"].default = versions.dependency_libraries
    if "clerk_js_version" in fields:
        component_cls.clerk_js_version = versions.clerk_js_version
        fields["clerk_js_version"].default = versions.clerk_js_version
    if "clerk_ui_version" in fields:
        component_cls.clerk_ui_version = versions.ui_version
        fields["clerk_ui_version"].default = versions.ui_version


def _iter_clerk_component_classes() -> Iterator[type[rx.Component]]:
    yield ClerkBase
    yield from _iter_clerk_component_subclasses(ClerkBase)


def _iter_clerk_component_subclasses(
    component_cls: type[rx.Component],
) -> Iterator[type[rx.Component]]:
    for subclass in component_cls.__subclasses__():
        yield subclass
        yield from _iter_clerk_component_subclasses(subclass)


_sync_clerk_component_class(ClerkBase)
