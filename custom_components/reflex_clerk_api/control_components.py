import reflex as rx

from reflex_clerk_api.base import ClerkBase

SignInInitialValues = dict[str, str]
SignUpInitialValues = dict[str, str]


class ClerkLoaded(ClerkBase):
    """Only renders children after authentication has been checked."""

    tag = "ClerkLoaded"


class ClerkLoading(ClerkBase):
    """Only renders childen while Clerk authenticates the user."""

    tag = "ClerkLoading"


class Show(ClerkBase):
    tag = "Show"

    when: dict | str | None = None
    (
        "The condition to evaluate. Supports 'signed-in' / 'signed-out' strings and "
        "object checks like {'feature': '...'} or {'plan': '...'}."
    )
    # Known limitation: callback-style `when=(has) => ...` is not supported with the
    # current str/dict prop typing and would serialize as a quoted string literal.
    fallback: rx.Component | None = None
    "Optional UI to render if the condition fails."
    treat_pending_as_signed_out: bool | None = None
    "Whether pending sessions are treated as signed out. Defaults to true in Clerk."


class RedirectToSignIn(ClerkBase):
    """Immediately redirects the user to the sign in page when rendered."""

    tag = "RedirectToSignIn"

    sign_in_fallback_redirect_url: str | None = None
    "The fallback URL to redirect to after the user signs in, if there's no redirect_url in the path already. Defaults to /."
    sign_in_force_redirect_url: str | None = None
    "If provided, this URL will always be redirected to after the user signs in."
    initial_values: SignInInitialValues | None = None
    "The values used to prefill the sign-in fields with."


class RedirectToSignUp(ClerkBase):
    """Immediately redirects the user to the sign up page when rendered."""

    tag = "RedirectToSignUp"

    sign_up_fallback_redirect_url: str | None = None
    "The fallback URL to redirect to after the user signs up, if there's no redirect_url in the path already. Defaults to /."
    sign_up_force_redirect_url: str | None = None
    "If provided, this URL will always be redirected to after the user signs up."
    initial_values: SignUpInitialValues | None = None
    "The values used to prefill the sign-up fields with."


class RedirectToUserProfile(ClerkBase):
    """Immediately redirects the user to their profile page when rendered."""

    tag = "RedirectToUserProfile"


class RedirectToOrganizationProfile(ClerkBase):
    tag = "RedirectToOrganizationProfile"


class RedirectToCreateOrganization(ClerkBase):
    tag = "RedirectToCreateOrganization"


clerk_loaded = ClerkLoaded.create
clerk_loading = ClerkLoading.create
show = Show.create
redirect_to_sign_in = RedirectToSignIn.create
redirect_to_sign_up = RedirectToSignUp.create
redirect_to_user_profile = RedirectToUserProfile.create
redirect_to_organization_profile = RedirectToOrganizationProfile.create
redirect_to_create_organization = RedirectToCreateOrganization.create
