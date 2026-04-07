import reflex as rx


class ClerkBase(rx.Component):
    # The React library to wrap.
    # `Show` is exported from `@clerk/react` (v6+), not `@clerk/clerk-react`.
    library = "@clerk/react@^6.2.0"
