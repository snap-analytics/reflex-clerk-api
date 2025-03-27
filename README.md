![Test Status](https://github.com/TimChild/reflex-clerk-api/actions/workflows/ci.yml/badge.svg?branch=v0.2.3)
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

- How should the `condition` and `fallback` props be defined on `Protect`? They are supposed to be `Javascript` and `JSX` respectively, but are just `str` for now... Is `Javascript` `rx.Script`? And `JSX` `rx.Component`?
