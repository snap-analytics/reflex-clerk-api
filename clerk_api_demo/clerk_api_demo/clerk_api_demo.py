"""Welcome to Reflex! This file showcases the custom component in a basic app."""

from reflex.event import EventType
from rxconfig import config
import os
import logging
from textwrap import dedent

import reflex as rx

import reflex_clerk_api as clerk
from dotenv import load_dotenv

# Set up debug logging with a console handler
logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()])
logging.debug("Logging is set up.")


load_dotenv()

filename = f"{config.app_name}/{config.app_name}.py"


class State(rx.State):
    """The app state."""

    info_from_load: str = "Nothing yet."

    @rx.event
    async def do_something_on_load(self) -> EventType:
        clerk_state = await self.get_state(clerk.ClerkState)
        self.info_from_load = f"""\
        State.is_hydrated: {self.is_hydrated}
        clerkstate.auth_checked: {clerk_state.auth_checked}
        ClerkState.is_logged_in: {clerk_state.is_signed_in}
        """
        return rx.toast.info("Loaded!")

    @rx.var
    def hidden_value(self) -> int:
        return self._temp


def header_and_description() -> rx.Component:
    return rx.vstack(
        rx.heading("reflex-clerk-api demo", size="9"),
        rx.heading(
            "This demonstrates the ClerkAPI component (wrapping `@clerk/clerk-react`).",
            size="4",
        ),
        rx.text(
            "This is intended to be roughly a drop-in replacement of `kroo/reflex-clerk` as that repository is no longer maintained."
        ),
        rx.text("Additionally, this implementation:"),
        rx.unordered_list(
            rx.list_item("uses Clerk's maintained python backend api"),
            rx.list_item("uses async/await for requests to Clerk"),
            rx.list_item("fully supports reflex 0.7.x"),
            rx.list_item(
                "includes a helper for handling `on_load` events (ensuring the ClerkState is updated before other on_load events)"
            ),
        ),
    )


def current_clerk_state_values() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Current ClerkState values:", size="5"),
            rx.text(
                f"""State.is_hydrated: {State.is_hydrated},
                ClerkState.auth_checked: {clerk.ClerkState.auth_checked},
                ClerkState.is_logged_in: {clerk.ClerkState.is_signed_in}""",
                white_space="pre-line",
                margin_top="1em",
            ),
        )
    )


def on_load_demo() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("on_load event demo", size="5"),
            rx.markdown(
                dedent("""\
            By using setting `on_load=clerk.on_load([...])`,
            you can ensure that the `ClerkState` is updated before any other `on_load` events are run.

            This is necessary because the ClerkState authentication is triggered from a frontend event that
            can't be guaranteed to run before the other `on_load` events.
            """)
            ),
            rx.card(
                rx.text("What the state saw during it's on_load event:"),
                rx.text(
                    State.info_from_load,
                    read_only=True,
                    white_space="pre-line",
                    margin_top="1em",
                ),
            ),
        ),
        max_width="30em",
    )


def signed_in_area() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text("You'll only see content below if you are signed in"),
            clerk.signed_in(
                "You are signed in.",
                clerk.sign_out_button(rx.button("Sign out")),
            ),
        )
    )


def signed_out_area() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text("You'll only see content below if you are signed out"),
            clerk.signed_out(
                "You are signed out.",
                clerk.sign_in_button(rx.button("Sign in")),
            ),
        )
    )


def index() -> rx.Component:
    return clerk.clerk_provider(
        rx.center(
            rx.vstack(
                header_and_description(),
                rx.button("Dev reset", on_click=clerk.ClerkState.dev_reset),
                rx.divider(),
                rx.hstack(
                    current_clerk_state_values(),
                    on_load_demo(),
                ),
                rx.grid(
                    signed_in_area(),
                    signed_out_area(),
                    columns="2",
                ),
                align="center",
                spacing="7",
            ),
            height="100vh",
        ),
        publishable_key=os.environ["CLERK_PUBLISHABLE_KEY"],
        secret_key=os.environ["CLERK_SECRET_KEY"],
    )


# Add state and page to the app.
app = rx.App()
# NOTE: Use the `clerk.on_load` to ensure that the ClerkState is updated *before* any other on_load events are run.
#  The `ClerkState` is updated by an event sent from the frontend that is not guaranteed to run before the reflex on_load events.
app.add_page(index, on_load=clerk.on_load([State.do_something_on_load]))
