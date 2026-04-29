import reflex as rx

CLERK_REACT_VERSION = "6.4.6"


class ClerkBase(rx.Component):
    # The React library to wrap.
    # `Show` is exported from `@clerk/react` (v6+), not `@clerk/clerk-react`.
    library = f"@clerk/react@{CLERK_REACT_VERSION}"
