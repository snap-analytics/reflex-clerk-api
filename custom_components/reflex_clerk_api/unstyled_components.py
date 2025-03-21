from reflex_clerk_api.base import ClerkBase


class SignInButton(ClerkBase):
    tag = "SignInButton"


class SignOutButton(ClerkBase):
    tag = "SignOutButton"


sign_in_button = SignInButton.create
sign_out_button = SignOutButton.create
