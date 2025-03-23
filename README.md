# clerk-api

A Reflex custom component for integrating Clerk authentication into a Reflex application.

See a demo of it in action [here](https://reflex-clerk-api-demo.adventuresoftim.com).

Documentation will soon be available [here](https://timchild.github.io/reflex-clerk-api/)

## Installation

Any of:

```bash
uv add reflex-clerk-api

pip install reflex-clerk-api

poetry add reflex-clerk-api
```

## Usage

```python
import reflex_clerk_api as clerk

def index() -> rx.Component:
    return clerk.clerk_provider(
        rx.container(
            clerk.clerk_loaded(
                clerk.signed_in(
                    clerk.sign_on(
                        rx.button("Sign out"),
                    ),
                ),
                clerk.signed_out(
                    rx.button("Sign in"),
                ),
            ),
        ),
        publishable_key=os.environ["CLERK_PUBLISHABLE_KEY"],
        secret_key=os.environ["CLERK_SECRET_KEY"],
        register_user_state=True,
    )
```
