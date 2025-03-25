from reflex_clerk_api.base import ClerkBase


class ClerkLoaded(ClerkBase):
    """Only renders children after authentication has been checked."""

    tag = "ClerkLoaded"


class ClerkLoading(ClerkBase):
    """Only renders childen while Clerk authenticates the user."""

    tag = "ClerkLoading"


class Protect(ClerkBase):
    tag = "Protect"


class RedirectToSignIn(ClerkBase):
    """Immediately redirects the user to the sign in page when rendered."""

    tag = "RedirectToSignIn"


class RedirectToSignUp(ClerkBase):
    """Immediately redirects the user to the sign up page when rendered."""

    tag = "RedirectToSignUp"


class RedirectToUserProfile(ClerkBase):
    """Immediately redirects the user to their profile page when rendered."""

    tag = "RedirectToUserProfile"


class RedirectToOrganizationProfile(ClerkBase):
    tag = "RedirectToOrganizationProfile"


class RedirectToCreateOrganization(ClerkBase):
    tag = "RedirectToCreateOrganization"


class SignedIn(ClerkBase):
    """Only renders children when the user is signed in."""

    tag = "SignedIn"


class SignedOut(ClerkBase):
    """Only renders children when the user is signed out."""

    tag = "SignedOut"


clerk_loaded = ClerkLoaded.create
clerk_loading = ClerkLoading.create
protect = Protect.create
redirect_to_sign_in = RedirectToSignIn.create
redirect_to_sign_up = RedirectToSignUp.create
redirect_to_user_profile = RedirectToUserProfile.create
redirect_to_organization_profile = RedirectToOrganizationProfile.create
redirect_to_create_organization = RedirectToCreateOrganization.create
signed_in = SignedIn.create
signed_out = SignedOut.create
