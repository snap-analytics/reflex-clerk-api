import asyncio
from typing import ClassVar, Any
import time
import uuid
from clerk_backend_api import Clerk
from authlib.jose import JoseError, jwt, JWTClaims

import reflex as rx
from reflex.event import EventType
from reflex.utils.imports import ImportTypes
from reflex_clerk_api.base import ClerkBase
import logging


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
    _client: ClassVar[Clerk | None] = None
    # NOTE: Underscore only is still stored in state but is private
    _jwk_keys: dict[str, Any] = {}

    @classmethod
    def set_secret_key(cls, secret_key: str) -> None:
        if not secret_key:
            raise ValueError("secret_key must be set (and not empty)")
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
        if cls._secret_key is None:
            raise ValueError("Clerk secret_key must be set before creating the client.")
        client = Clerk(bearer_auth=cls._secret_key)
        cls._client = client

    @property
    def client(self) -> Clerk:
        if self._client is None:
            self.set_client()
        assert self._client is not None
        return self._client

    @rx.event
    async def set_clerk_session(self, token: str) -> None:
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
        return rx.toast.success("Logged in!")

    @rx.event
    def clear_clerk_session(self) -> None:
        logging.debug("Clearing Clerk session")
        self.is_signed_in = False
        self.claims = None
        self.user_id = None
        self.auth_checked = True
        return rx.toast.success("Logged out!")

    @rx.event(background=True)
    async def wait_for_auth_check(self, uid: uuid.UUID | str) -> EventType:
        """Wait for the Clerk authentication to complete (event sent from frontend).

        Can't just use a blocking wait_for_auth_check because we are really waiting for the frontend event trigger to run,
        so we need to not block that while we wait.
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
            # TODO: Ideally wait on some event instead of sleeping
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
