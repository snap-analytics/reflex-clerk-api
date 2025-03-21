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

    @rx.event
    async def do_something_on_load(self) -> EventType:
        return rx.toast.info(f"""
        State.is_hydrated: {self.is_hydrated}
        ClerkState.auth_checked: {clerk.ClerkState.auth_checked}
        ClerkState.is_logged_in: {clerk.ClerkState.is_logged_in}
        """)


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
                # rx.text(f"""State.is_hydrated: {State.is_hydrated},
                #         ClerkState.auth_checked: {clerk.ClerkState.auth_checked},
                #         ClerkState.is_logged_in: {clerk.ClerkState.is_logged_in}"""),
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
app.add_page(index)
