from typing import ClassVar

import reflex as rx
from reflex.event import EventType
from reflex.utils.imports import ImportTypes
from reflex_clerk_api.base import ClerkBase
import logging


class ClerkState(rx.State):
    is_logged_in: bool = False
    """Whether the user is logged in."""

    auth_checked: bool = False
    """Whether the auth state of the user has been checked yet.
    I.e., has Clerk sent a response to the frontend yet."""

    _secret_key: ClassVar[str | None] = None
    """The Clerk secret_key set during clerk_provider creation."""

    @classmethod
    def set_secret_key(cls, secret_key: str) -> None:
        if not secret_key:
            raise ValueError("secret_key must be set (and not empty)")
        cls._secret_key = secret_key

    @rx.event
    def set_clerk_session(self, token: str) -> None:
        logging.debug("Setting Clerk session")
        self.is_logged_in = True
        self.auth_checked = True
        return rx.toast.success("Logged in!")

    @rx.event
    def clear_clerk_session(self) -> None:
        logging.debug("Clearing Clerk session")
        self.is_logged_in = False
        self.auth_checked = True
        return rx.toast.success("Logged out!")


class ClerkSessionSynchronizer(rx.Component):
    """ClerkSessionSynchronizer component.

    This is borrowed directly from "kroo/reflex-clerk".
    """

    tag = "ClerkSessionSynchronizer"

    def add_imports(
        self,
    ) -> rx.ImportDict:
        addl_imports: dict[str, ImportTypes] = {
            "@clerk/clerk-react": ["useAuth"],
            "react": ["useContext", "useEffect"],
            "/utils/context": ["EventLoopContext"],
            "/utils/state": ["Event"],
        }
        return addl_imports

    def add_custom_code(self) -> list[str]:
        clerk_state_name = ClerkState.get_full_name()

        return [
            """
function ClerkSessionSynchronizer({ children }) {
  const { getToken, isLoaded, isSignedIn } = useAuth()
  const [ addEvents, connectErrors ] = useContext(EventLoopContext)

  useEffect(() => {
      if (isLoaded && !!addEvents) {
        if (isSignedIn) {
          getToken().then(token => {
            addEvents([Event("%s.set_clerk_session", {token})])
          })
        } else {
          addEvents([Event("%s.clear_clerk_session")])
        }
      }
  }, [isSignedIn])

  return (
      <>{children}</>
  )
}
"""
            % (clerk_state_name, clerk_state_name)
        ]


class ClerkProvider(ClerkBase):
    """ClerkProvider component."""

    # The React component tag.
    tag = "ClerkProvider"

    # The props of the React component.
    # Note: when Reflex compiles the component to Javascript,
    # `snake_case` property names are automatically formatted as `camelCase`.
    # The prop names may be defined in `camelCase` as well.
    # some_prop: rx.Var[str] = "some default value"
    # some_other_prop: rx.Var[int] = 1

    # Event triggers declaration if any.
    # Below is equivalent to merging `{ "on_change": lambda e: [e] }`
    # onto the default event triggers of parent/base Component.
    # The function defined for the `on_change` trigger maps event for the javascript
    # trigger to what will be passed to the backend event handler function.
    # on_change: rx.EventHandler[lambda e: [e]]

    publishable_key: str
    """
    The Clerk Publishable Key for your instance. This can be found on the API keys page in the Clerk Dashboard.
    """

    @classmethod
    def create(cls, *children, **props) -> "ClerkProvider":
        return super().create(*children, **props)

    def add_custom_code(self) -> list[str]:
        return []


def on_load(on_load_events: EventType[()] | None) -> EventType[()] | None:
    return on_load_events


def clerk_provider(
    *children, publishable_key: str, secret_key: str, **props
) -> rx.Component:
    """

    Args:
        secret_key: Your Clerk app's Secret Key, which you can find in the Clerk Dashboard. It will be prefixed with sk_test_ in development instances and sk_live_ in production instances. Do not expose this on the frontend with a public environment variable.
    """
    ClerkState.set_secret_key(secret_key)
    return ClerkProvider.create(
        ClerkSessionSynchronizer.create(*children),
        publishable_key=publishable_key,
        **props,
    )
