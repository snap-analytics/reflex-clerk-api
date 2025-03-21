"""Welcome to Reflex! This file showcases the custom component in a basic app."""

from reflex.event import EventType
from rxconfig import config
import os

import reflex as rx

import reflex_clerk_api as clerk
from dotenv import load_dotenv

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
        ClerkState.auth_checked: {clerk_state.auth_checked}
        ClerkState.is_logged_in: {clerk_state.is_logged_in}
        """
        return rx.toast.info("Loaded!")


def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("reflex-clerk-api demo", size="9"),
            rx.heading(
                "This demonstrates the ClerkAPI component (wrapping `@clerk/clerk-react`).",
                size="4",
            ),
            rx.text(
                "This is intended to be roughly a drop-in replacement of `kroo/reflex-clerk` as that repository is no longer maintained."
            ),
            rx.text("Note that everything above here is NOT inside the ClerkProvider."),
            rx.divider(),
            rx.text(
                "Test your custom component by editing ",
                rx.code(filename),
                font_size="2em",
            ),
            clerk.clerk_provider(
                rx.vstack(
                    rx.text("Everything inside here is inside the ClerkProvider."),
                    width="100%",
                    border="1px solid green",
                    border_radius="10px",
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
                rx.card(
                    rx.text("What the current values are:"),
                    rx.text(
                        f"""State.is_hydrated: {State.is_hydrated},
                        ClerkState.auth_checked: {clerk.ClerkState.auth_checked},
                        ClerkState.is_logged_in: {clerk.ClerkState.is_logged_in}""",
                        white_space="pre-line",
                        margin_top="1em",
                    ),
                ),
                clerk.signed_in(
                    "You are signed in.",
                    clerk.sign_out_button(rx.button("Sign out")),
                ),
                clerk.signed_out(
                    "You are signed out.",
                    clerk.sign_in_button(rx.button("Sign in")),
                ),
                publishable_key=os.environ["CLERK_PUBLISHABLE_KEY"],
                secret_key=os.environ["CLERK_SECRET_KEY"],
            ),
            align="center",
            spacing="7",
        ),
        height="100vh",
    )


# Add state and page to the app.
app = rx.App()
# app.add_page(index, on_load=clerk.on_load([State.do_something_on_load]))
app.add_page(index, on_load=State.do_something_on_load)
