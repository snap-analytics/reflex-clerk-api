# Getting Started with Reflex Clerk API

Welcome to the getting started guide for the `reflex-clerk-api`!

You can add `Clerk` user authentication to your app for free (up to 10,000 users) ([Clerk Pricing](https://clerk.com/pricing)).

This covers the basics to add authentication to your Reflex app.

## Clerk API

Sign up for a Clerk account [here](https://dashboard.clerk.com/sign-up).

## Installation

Installation is the same an any other python package:

### Using pip

```bash
pip install reflex-clerk-api
```

### Using a package manager

```bash
uv add reflex-clerk-api
```

or

```bash
poetry add reflex-clerk-api
```

etc.

## Basic Setup

After installation, you can start integrating the Clerk components into your Reflex application.

### Import the Package

To use the Reflex Clerk API in your app, start by importing the package:

```python
import reflex_clerk_api as clerk
```

All examples here assume the package is imported as `clerk`.

### Setting Up ClerkProvider

Typically, you'll wrap whole pages with the `ClerkProvider` component. This is required for clerk components within to work. This is a minimal example:

```python
import os

import reflex as rx
import reflex_clerk_api as clerk

def index() -> rx.Component:
    return clerk.clerk_provider(
        clerk.clerk_loading(
            rx.spinner(),
        ),
        clerk.clerk_loaded(
            clerk.show(
                clerk.sign_out_button(rx.button("Sign out")),
                when="signed-in",
            ),
            clerk.show(
                clerk.sign_in_button(rx.button("Sign in")),
                when="signed-out",
            ),
        ),
        publishable_key=os.environ["CLERK_PUBLISHABLE_KEY"],
        secret_key=os.environ["CLERK_SECRET_KEY"],
        register_user_state=True,
    )

app = rx.App()
app.add_page(index)
```

While Clerk is loading (checking user authentication), the spinner will be displayed. Then either the sign-in or sign-out button will be displayed based on the user's authentication status.

The `publishable_key` and `secret_key` can be obtained from your [Clerk dashboard](https://dashboard.clerk.com) (Configure/API keys). Read more [here](https://clerk.com/glossary/api-key)

!!! note

    The `register_user_state` parameter is optional. Setting this to `True` enables the `clerk.ClerkUser` state which can be used to access or display basic user information.

**alternatively**

Wrap the entire app (all pages) via:

```python

clerk.wrap_app(app, publishable_key=...)
```

Taking the same arguments as `clerk.clerk_provider`.

### Localization

Pass Clerk localization overrides through `clerk_provider` or `wrap_app`. Error
messages use Clerk's machine-stable error codes:

```python
clerk.wrap_app(
    app,
    publishable_key=...,
    localization={
        "unstable__errors": {
            "too_many_requests": (
                "Too many sign-in attempts. Please wait a moment before trying again."
            ),
        },
    },
)
```

Localization keys are forwarded unchanged so Clerk-specific names such as
`unstable__errors` and `too_many_requests` remain intact.

### Frontend Package Versions

`reflex-clerk-api` pins a compatible Clerk frontend set by default:

- `@clerk/react@6.12.0`
- `@clerk/ui@1.25.0`
- ClerkJS `6.25.0`

If your app needs a different compatible set, configure it before creating Clerk components or importing page modules that create them:

```python
import reflex_clerk_api as clerk

clerk.configure_clerk_frontend_versions(
    react_version="6.12.0",
    ui_version="1.25.0",
    clerk_js_version="6.25.0",
)
```

The configuration updates both `ClerkBase.library` and Reflex's stored component field defaults, so `clerk_provider(...)`, `wrap_app(...)`, and direct `ClerkProvider.create(...)` calls use the same version set.

### Environment Variables

A good way to provide the keys is via environment variables (to avoid accidentally sharing them). You can do this by creating a `.env` file in the root of your project with:

```
CLERK_PUBLISHABLE_KEY=your_publishable_key
CLERK_SECRET_KEY=your_secret_key
```

Then you can use the `python-dotenv` package to load the variables:

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()
```

This will load the environment variables from the `.env` file into the `os.environ` dictionary.

!!! warning

    Make sure to add the `.env` file to your `.gitignore` file to avoid accidentally sharing your keys.

## Adding Sign-In and Sign-Up Pages

You can additionally add some pages for signing in and signing up. By default they will be available at `/sign-in` and `/sign-up` respectively.

```python
app = rx.App()
app.add_page(index)
clerk.add_sign_in_page(app)
clerk.add_sign_up_page(app)
```

## Next Steps

- Explore more features of the Reflex Clerk API in the [Features](features.md) section.
- Visit the [Demo](https://reflex-clerk-api-demo.adventuresoftim.com) to see the Reflex Clerk API in action.
- Check out the [Migration Guide](migrating.md) if you're migrating from the `Kroo/reflex-clerk` package.
