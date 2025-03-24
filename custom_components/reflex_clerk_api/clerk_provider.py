import asyncio
import logging
import os
import time
import uuid
from typing import Any, ClassVar, TypeVar

import authlib.jose.errors as jose_errors
import clerk_backend_api
import reflex as rx
from authlib.jose import JWTClaims, jwt
from reflex.event import EventCallback, EventType, IndividualEventType
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

    # NOTE: ClassVar tells reflex it doesn't need to include these in the persisted state per instance.
    _auth_wait_timeout_seconds: ClassVar[float] = 1.0
    _secret_key: ClassVar[str | None] = None
    """The Clerk secret_key set during clerk_provider creation."""
    _on_load_events: ClassVar[dict[uuid.UUID, EventType[()]]] = {}
    _dependent_handlers: ClassVar[dict[int, EventCallback]] = {}
    _client: ClassVar[clerk_backend_api.Clerk | None] = None
    _jwk_keys: ClassVar[dict[str, Any] | None] = None
    _last_jwk_reset: ClassVar[float] = 0.0
    _claims_options: ClassVar[dict[str, Any]] = {
        # "iss": {"value": "https://<your-iss>.clerk.accounts.dev"},
        "exp": {"essential": True},
        "nbf": {"essential": True},
        # "azp": {"essential": False, "values": ["http://localhost:3000", "https://example.com"]},
    }

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
    def set_auth_wait_timeout_seconds(cls, seconds: float) -> None:
        """Sets the max time to wait for initial auth check before running other on_load events.

        Note: on_load events will still be run after a timed out auth check.
        Check ClerkState.auth_checked to see if auth check is complete.
        """
        cls._auth_wait_timeout_seconds = seconds

    @classmethod
    def set_claims_options(cls, claims_options: dict[str, Any]) -> None:
        """Set the claims options for the JWT claims validation."""
        cls._claims_options = claims_options

    @property
    def client(self) -> clerk_backend_api.Clerk:
        if self._client is None:
            self._set_client()
        assert self._client is not None
        return self._client

    @rx.event
    async def set_clerk_session(self, token: str) -> EventType:
        """Manually obtain user session information via the Clerk JWT.

        This event is triggered by the frontend via the ClerkSessionSynchronizer/ClerkProvider component.
        """
        logging.debug("Setting Clerk session")
        jwks = await self._get_jwk_keys()
        try:
            decoded: JWTClaims = jwt.decode(
                token, {"keys": jwks}, claims_options=self._claims_options
            )
        except jose_errors.DecodeError as e:
            # E.g. DecodeError -- Something went wrong just getting the JWT
            # On next attempt, new JWKs will be fetched
            self.auth_error = e
            self._request_jwk_reset()
            logging.warning(f"JWT decode error: {e}")
            return ClerkState.clear_clerk_session
        try:
            # Validate the token according to the claim options (e.g. iss, exp, nbf, azp.)
            decoded.validate()
        except (jose_errors.InvalidClaimError, jose_errors.MissingClaimError) as e:
            logging.warning(f"JWT token is invalid: {e}")
            return ClerkState.clear_clerk_session

        self.is_signed_in = True
        self.claims = decoded
        self.user_id = str(decoded.get("sub"))
        self.auth_checked = True
        return list(self._dependent_handlers.values())

    @rx.event
    def clear_clerk_session(self) -> EventType:
        """Clear the Clerk session information.

        This event is triggered by the frontend via the ClerkSessionSynchronizer/ClerkProvider component.
        """
        logging.debug("Clearing Clerk session")
        self.reset()
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

        on_loads = self._on_load_events.get(uid, None)
        if on_loads is None:
            logging.warning("Waited for auth, but no on_load events registered.")
            on_loads = []

        start_time = time.time()
        while time.time() - start_time < self._auth_wait_timeout_seconds:
            if self.auth_checked:
                logging.debug("Auth check complete")
                return on_loads
            logging.debug("...waiting for auth...")
            # TODO: Ideally, wait on some event instead of sleeping
            await asyncio.sleep(0.05)
        logging.warning("Auth check timed out")
        return on_loads

    @classmethod
    def _set_secret_key(cls, secret_key: str) -> None:
        if not secret_key:
            raise MissingSecretKeyError("secret_key must be set (and not empty)")
        cls._secret_key = secret_key

    @classmethod
    def _set_on_load_events(cls, uid: uuid.UUID, on_load_events: EventType[()]) -> None:
        logging.debug(f"Registing on_load events: {uid}")
        cls._on_load_events[uid] = on_load_events

    @classmethod
    def _set_client(cls) -> None:
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

    @classmethod
    def _set_jwk_keys(cls, keys: dict[str, Any] | None) -> None:
        cls._jwk_keys = keys

    @classmethod
    def _request_jwk_reset(cls) -> None:
        """Reset the JWK keys so they will be re-fetched on next attempt.

        Only do so if it has been a while since last reset (to prevent malicious tokens from forcing
        constant re-fetching).
        """
        now = time.time()
        if now - cls._last_jwk_reset < 10:
            logging.warning("JWK reset requested too soon")
            return
        cls._last_jwk_reset = time.time()
        cls._jwk_keys = None

    async def _get_jwk_keys(self) -> dict[str, Any]:
        """Get the JWK keys from the Clerk API.

        Note: Cannot be a property because it requires async call to populate.
        Only needs to be done once (will be refreshed on errors).
        """
        if self._jwk_keys:
            return self._jwk_keys
        jwks = await self.client.jwks.get_async()
        assert jwks is not None
        assert jwks.keys is not None
        keys = jwks.model_dump()["keys"]
        self._set_jwk_keys(keys)
        return keys

    # @rx.event
    # def force_reset(self) -> None:
    #     """Force a reset of the Clerk state.
    #
    #     E.g. During development testing.
    #     """
    #     self.reset()
    #     self._set_jwk_keys(None)
    #     return rx.toast.success("Forced reset complete.")


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


def on_load(on_load_events: EventType[()] | None) -> list[IndividualEventType[()]]:
    if on_load_events is None:
        return []
    on_load_list = (
        on_load_events if isinstance(on_load_events, list) else [on_load_events]
    )

    # Add the on_load events to a registry in the ClerkState instead of actually passing them to on_load.
    #  Then, the wait_for_auth_check event will return the on_load events once auth_checked is True.
    #  Can't just use a blocking wait_for_auth_check because we are really waiting for the frontend event trigger to run,
    #  so we need to not block that while we wait.
    uid = uuid.uuid4()
    ClerkState._set_on_load_events(uid, on_load_list)
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
        ClerkState._set_secret_key(secret_key)

    if register_user_state:
        register_on_auth_change_handler(ClerkUser.load_user)

    return ClerkProvider.create(
        ClerkSessionSynchronizer.create(*children),
        publishable_key=publishable_key,
        **props,
    )
