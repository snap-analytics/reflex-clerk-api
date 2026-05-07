![Test Status](https://github.com/TimChild/reflex-clerk-api/actions/workflows/ci.yml/badge.svg?branch=v1.0.0)
![PyPi publish Status](https://github.com/TimChild/reflex-clerk-api/actions/workflows/publish.yml/badge.svg)
![Demo Deploy Status](https://github.com/TimChild/reflex-clerk-api/actions/workflows/deploy.yml/badge.svg)

# reflex-clerk-api

A Reflex custom component for integrating Clerk authentication into a Reflex application.

See a [Demo](https://reflex-clerk-api-demo.adventuresoftim.com).

See the [Docs](https://timchild.github.io/reflex-clerk-api/about/)

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
                clerk.show(
                    clerk.sign_on(
                        rx.button("Sign out"),
                    ),
                    when="signed-in",
                ),
                clerk.show(
                    rx.button("Sign in"),
                    when="signed-out",
                ),
            ),
        ),
        publishable_key=os.environ["CLERK_PUBLISHABLE_KEY"],
        secret_key=os.environ["CLERK_SECRET_KEY"],
        register_user_state=True,
    )
```

The package pins a compatible Clerk frontend set by default (`@clerk/react@6.6.0`, `@clerk/ui@1.9.0`, ClerkJS `6.10.0`). Apps that need another compatible set can call `clerk.configure_clerk_frontend_versions(...)` before creating Clerk components.

## Contributing

Feel free to open issues or make PRs.

Usual process for contributing:

- Fork the repo
- Make changes on a feature branch
- Ideally, add tests for any changes (this will mean your changes don't get broken in the future too).
- Submit a PR

I use [Taskfile](https://taskfile.dev/) (similar to `makefile`) to make common tasks easier. If you have that installed, you can run:

- `task install` -- Install dev dependencies and pre-commit.
- `task run` -- Run the demo locally
- `task run-docs` -- Run the docs locally
- `task test` -- Run tests
- `task bump-patch/minor/major` -- Bump the version (`patch` for a bug fix, `minor` for an added feature).


## TODO:

- Add migration notes for deprecated wrappers removed in the next major release.
