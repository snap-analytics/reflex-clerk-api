"""Reflex custom component ClerkProvider."""

# For wrapping react guide, visit https://reflex.dev/docs/wrapping-react/overview/

import reflex as rx
from reflex.event import EventType

# Some libraries you want to wrap may require dynamic imports.
# This is because they they may not be compatible with Server-Side Rendering (SSR).
# To handle this in Reflex, all you need to do is subclass `NoSSRComponent` instead.
# For example:
# from reflex.components.component import NoSSRComponent
# class ClerkApi(NoSSRComponent):
#     pass


class ClerkState(rx.State):
    is_logged_in: bool = False
    """Whether the user is logged in."""

    auth_checked: bool = False
    """Whether the auth state of the user has been checked yet.
    I.e., has Clerk sent a response to the frontend yet."""


class ClerkProvider(rx.Component):
    """ClerkProvider component."""

    # The React library to wrap.
    library = "@clerk/clerk-react"

    # The React component tag.
    tag = "ClerkProvider"

    # If the tag is the default export from the module, you must set is_default = True.
    # This is normally used when components don't have curly braces around them when importing.
    # is_default = True

    # If you are wrapping another components with the same tag as a component in your project
    # you can use aliases to differentiate between them and avoid naming conflicts.
    # alias = "OtherClerkApi"

    # The props of the React component.
    # Note: when Reflex compiles the component to Javascript,
    # `snake_case` property names are automatically formatted as `camelCase`.
    # The prop names may be defined in `camelCase` as well.
    # some_prop: rx.Var[str] = "some default value"
    # some_other_prop: rx.Var[int] = 1

    # By default Reflex will install the library you have specified in the library property.
    # However, sometimes you may need to install other libraries to use a component.
    # In this case you can use the lib_dependencies property to specify other libraries to install.
    # lib_dependencies: list[str] = []

    # Event triggers declaration if any.
    # Below is equivalent to merging `{ "on_change": lambda e: [e] }`
    # onto the default event triggers of parent/base Component.
    # The function defined for the `on_change` trigger maps event for the javascript
    # trigger to what will be passed to the backend event handler function.
    # on_change: rx.EventHandler[lambda e: [e]]

    # To add custom code to your component
    # def _get_custom_code(self) -> str:
    #     return "const customCode = 'customCode';"

    publishable_key: str
    """
    The Clerk Publishable Key for your instance. This can be found on the API keys page in the Clerk Dashboard.
    """

    @classmethod
    def create(cls, *children, **props) -> "ClerkProvider":
        assert "publishable_key" in props, "publishable_key is required."
        return super().create(*children, **props)


def on_load(on_load_events: EventType[()] | None) -> EventType[()] | None:
    return on_load_events


def clerk_provider(
    *children, publishable_key: str, secret_key: str, **props
) -> ClerkProvider:
    """

    Args:
        secret_key: Your Clerk app's Secret Key, which you can find in the Clerk Dashboard. It will be prefixed with sk_test_ in development instances and sk_live_ in production instances. Do not expose this on the frontend with a public environment variable.
    """
    # TODO: Do something with secret key
    _ = secret_key
    return ClerkProvider.create(*children, publishable_key=publishable_key, **props)
