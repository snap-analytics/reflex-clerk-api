from reflex_clerk_api.base import ClerkBase


class SignUpButton(ClerkBase):
    tag = "SignUpButton"


class SignInButton(ClerkBase):
    tag = "SignInButton"


class SignOutButton(ClerkBase):
    tag = "SignOutButton"


sign_up_button = SignUpButton.create
sign_in_button = SignInButton.create
sign_out_button = SignOutButton.create
