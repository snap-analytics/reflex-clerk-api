from pathlib import Path

import pytest
from playwright.sync_api import Page, expect
from reflex.testing import AppHarness


@pytest.fixture(scope="session")
def demo_app():
    app_root = Path(__file__).parent.parent / "clerk_api_demo"
    with AppHarness.create(root=app_root) as harness:
        yield harness


def test_render(demo_app: AppHarness, page: Page):
    """Check that the demo renders correctly.

    I.e. Check components are visible.
    """
    assert demo_app.frontend_url is not None

    page.goto(demo_app.frontend_url)

    expect(page.locator('[id="__next"]')).to_contain_text("reflex-clerk-api demo")
    expect(page.locator('[id="__next"]')).to_contain_text("Getting Started")
    expect(page.locator('[id="__next"]')).to_contain_text("Demos")
    expect(page.locator('[id="__next"]')).to_contain_text(
        "ClerkState variables and methods"
    )
    expect(page.locator('[id="__next"]')).to_contain_text(
        "Clerk loaded and signed in/out areas"
    )
    expect(page.locator('[id="__next"]')).to_contain_text("Better on_load handling")
    expect(page.locator('[id="__next"]')).to_contain_text("On auth change callbacks")
    expect(page.locator('[id="__next"]')).to_contain_text("ClerkUser info")
    expect(page.locator('[id="__next"]')).to_contain_text("Sign-in and sign-up pages")
    expect(page.locator('[id="__next"]')).to_contain_text("User profile management")
    page.pause()
