import reflex as rx

CLERK_REACT_VERSION = "6.4.6"
CLERK_UI_VERSION = "1.6.8"
CLERK_JS_VERSION = "6.7.8"


class ClerkBase(rx.Component):
    # The React library to wrap.
    # `Show` is exported from `@clerk/react` (v6+), not `@clerk/clerk-react`.
    library = f"@clerk/react@{CLERK_REACT_VERSION}"
