import asyncio
import logging
import os
import time
import uuid
from typing import Any, ClassVar, TypeVar

import clerk_backend_api
import reflex as rx
from authlib.jose import JoseError, JWTClaims, jwt
from reflex.event import EventCallback, EventType
from reflex.utils.exceptions import ImmutableStateError
from reflex.utils.imports import ImportTypes

from reflex_clerk_api.base import ClerkBase


class ReflexClerkApiError(Exception):
    pass


class MissingSecretKeyError(ReflexClerkApiError):
    pass


class MissingUserError(ReflexClerkApiError):
    pass


class ClerkState(rx.State):
    is_signed_in: bool = False
    """Whether the user is logged in."""

    auth_checked: bool = False
    """Whether the auth state of the user has been checked yet.
    I.e., has Clerk sent a response to the frontend yet."""

    claims: JWTClaims | None = None
    """The JWT claims of the user, if they are logged in."""
    user_id: str | None = None
    """The clerk user ID of the user, if they are logged in."""

    # NOTE: ClassVar tells reflex it doesn't need to include these in the persisted state.
    _auth_wait_timeout_seconds: ClassVar[float] = 1.0
    _secret_key: ClassVar[str | None] = None
    """The Clerk secret_key set during clerk_provider creation."""
    _on_load_events: ClassVar[dict[uuid.UUID, EventType[()]]] = {}
    _dependent_handlers: ClassVar[dict[int, EventCallback]] = {}
    _client: ClassVar[clerk_backend_api.Clerk | None] = None
    # NOTE: Underscore only is still stored in state but is private
    _jwk_keys: dict[str, Any] | None = None

    @classmethod
    def register_dependent_handler(cls, handler: EventCallback) -> None:
        """Register a handler to be called any time this state updates.

        I.e. Any events that should be triggered on login/logout.
        """
        assert isinstance(handler, rx.EventHandler)
        hash_id = hash((handler.state_full_name, handler.fn))
        logging.debug(f"Dependent hash_id: {hash_id}")
        cls._dependent_handlers[hash_id] = handler

    @classmethod
    def set_secret_key(cls, secret_key: str) -> None:
        if not secret_key:
            raise MissingSecretKeyError("secret_key must be set (and not empty)")
        cls._secret_key = secret_key

    @classmethod
    def set_on_load_events(cls, uid: uuid.UUID, on_load_events: EventType[()]) -> None:
        logging.debug(f"Registing on_load events: {uid}")
        cls._on_load_events[uid] = on_load_events

    @classmethod
    def set_auth_wait_timeout_seconds(cls, seconds: float) -> None:
        cls._auth_wait_timeout_seconds = seconds

    @classmethod
    def set_client(cls) -> None:
        if cls._secret_key:
            secret_key = cls._secret_key
        else:
            if "CLERK_SECRET_KEY" not in os.environ:
                raise MissingSecretKeyError(
                    "CLERK_SECRET_KEY either needs to be passed into clerk_provider(...) or set as an environment variable."
                )
            secret_key = os.environ["CLERK_SECRET_KEY"]
        client = clerk_backend_api.Clerk(bearer_auth=secret_key)
        cls._client = client

    @property
    def client(self) -> clerk_backend_api.Clerk:
        if self._client is None:
            self.set_client()
        assert self._client is not None
        return self._client

    @rx.event
    async def set_clerk_session(self, token: str) -> EventType:
        logging.debug("Setting Clerk session")

        if not self._jwk_keys:
            # TODO: Could this be cached on the class instead of per instance?
            jwks = await self.client.jwks.get_async()
            assert jwks is not None
            assert jwks.keys is not None
            self._jwk_keys = jwks.model_dump()["keys"]

        try:
            decoded: JWTClaims = jwt.decode(token, {"keys": self._jwk_keys})
            self.is_signed_in = True
            self.claims = decoded
            self.user_id = str(decoded.get("sub"))
        except JoseError as e:
            self.auth_error = e
            logging.warning(f"JWT decode error: {e}")

        self.is_signed_in = True
        self.auth_checked = True
        return list(self._dependent_handlers.values())

    @rx.event
    def clear_clerk_session(self) -> EventType:
        logging.debug("Clearing Clerk session")
        self.is_signed_in = False
        self.claims = None
        self.user_id = None
        self.auth_checked = True
        return list(self._dependent_handlers.values())

    @rx.event(background=True)
    async def wait_for_auth_check(self, uid: uuid.UUID | str) -> EventType:
        """Wait for the Clerk authentication to complete (event sent from frontend).

        Can't just use a blocking wait_for_auth_check because we are really waiting for the frontend event trigger to run, so we need to not block that while we wait.

        This can then return on_load events once auth_checked is True.
        """
        uid = uuid.UUID(uid) if isinstance(uid, str) else uid
        logging.debug(f"Waiting for auth check: {uid} ({type(uid)})")
        start_time = time.time()
        while time.time() - start_time < self._auth_wait_timeout_seconds:
            if self.auth_checked:
                logging.debug("Auth check complete")
                return self._on_load_events.get(
                    uid, [rx.toast.info("Auth check complete (no on_loads)!")]
                )
            logging.debug("...sleeping...")
            # TODO: Ideally, wait on some event instead of sleeping
            await asyncio.sleep(0.05)
        logging.debug("Auth check timed out")
        return rx.toast.error("Auth check timed out!")

    @rx.event
    def dev_reset(self) -> None:
        self.is_signed_in = False
        self.auth_checked = False
        self.claims = None
        self.user_id = None
        self._jwk_keys = {}
        return rx.toast.success("Dev reset!")


class NotRegisteredError(ReflexClerkApiError):
    pass


class ClerkUser(rx.State):
    """Convenience class for using Clerk User information.

    This only contains a subset of the information available. Create your own state if you need more.

    Note: For this to be updated on login/logout events, it must be registered on the ClerkState.
    """

    first_name: str = ""
    last_name: str = ""
    username: str = ""
    email_address: str = ""
    has_image: bool = False
    image_url: str = ""

    # Set to True when the state is registered on the ClerkState to avoid registering it multiple times.
    _is_registered: ClassVar[bool] = False

    @rx.event
    async def load_user(self) -> None:
        try:
            user: clerk_backend_api.models.User = await get_user(self)
        except MissingUserError:
            logging.debug("Clearing user state")
            self.reset()
            return

        logging.debug("Updating user state")
        self.first_name = (
            user.first_name
            if user.first_name and user.first_name != clerk_backend_api.UNSET
            else ""
        )
        self.last_name = (
            user.last_name
            if user.last_name and user.last_name != clerk_backend_api.UNSET
            else ""
        )
        self.username = (
            user.username
            if user.username and user.username != clerk_backend_api.UNSET
            else ""
        )
        self.email_address = (
            user.email_addresses[0].email_address if user.email_addresses else ""
        )
        self.has_image = True if user.has_image is True else False
        self.image_url = user.image_url or ""


class ClerkSessionSynchronizer(rx.Component):
    """ClerkSessionSynchronizer component.

    This is slightly adapted from Elliot Kroo's reflex-clerk.
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
    if on_load_events is None:
        return None
    on_load_list = (
        on_load_events if isinstance(on_load_events, list) else [on_load_events]
    )

    # Add the on_load events to a registry in the ClerkState instead of actually passing them to on_load.
    #  Then, the wait_for_auth_check event will return the on_load events once auth_checked is True.
    #  Can't just use a blocking wait_for_auth_check because we are really waiting for the frontend event trigger to run,
    #  so we need to not block that while we wait.
    uid = uuid.uuid4()
    ClerkState.set_on_load_events(uid, on_load_list)
    return [ClerkState.wait_for_auth_check(uid)]


T = TypeVar("T", bound=rx.State)


async def _get_state_within_handler(
    current_state: rx.State, desired_state: type[T]
) -> T:
    """Get the desired state from within an event handler.

    Note: Need to be in `async with self` block if called from background event.
    """
    try:
        state = await current_state.get_state(desired_state)
    except ImmutableStateError:
        async with current_state:
            state = await current_state.get_state(desired_state)
    return state


async def get_user(current_state: rx.State) -> clerk_backend_api.models.User:
    """Get the User object from Clerk given the currently logged in user.

    Note: Must be used within an event handler in order to get the appropriate clerk_state.

    Args:
        current_state: The `self` state from the current event handler.

    Examples:

    ```python
    class State(rx.State):
        @rx.event
        async def handle_getting_user_email(self) -> EventType:
            user = await clerk.get_user(self)
            return rx.toast.info(f"User: {user.email}")
    ```
    """
    clerk_state = await _get_state_within_handler(current_state, ClerkState)
    user_id = clerk_state.user_id
    if user_id is None:
        raise MissingUserError("No user_id to get user for")
    user = await clerk_state.client.users.get_async(user_id=user_id)
    if user is None:
        raise MissingUserError("No user found")
    return user


def register_on_auth_change_handler(handler: EventCallback) -> None:
    """Register a handler to be called any time the user logs in or out.

    Args:
        handler: The event handler function to be called.
    """
    ClerkState.register_dependent_handler(handler)


def clerk_provider(
    *children,
    publishable_key: str,
    secret_key: str | None = None,
    register_user_state: bool = False,
    **props,
) -> rx.Component:
    """
    Create a ClerkProvider component to wrap your app/page that uses clerk authentication.

    Args:
        secret_key: Your Clerk app's Secret Key, which you can find in the Clerk Dashboard. It will be prefixed with sk_test_ in development instances and sk_live_ in production instances. Do not expose this on the frontend with a public environment variable.
    """
    logging.critical("running clerk_provider")
    if secret_key:
        ClerkState.set_secret_key(secret_key)

    if register_user_state:
        register_on_auth_change_handler(ClerkUser.load_user)

    return ClerkProvider.create(
        ClerkSessionSynchronizer.create(*children),
        publishable_key=publishable_key,
        **props,
    )
