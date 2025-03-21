from reflex_clerk_api.base import ClerkBase


class ClerkLoaded(ClerkBase):
    tag = "ClerkLoaded"


class ClerkLoading(ClerkBase):
    tag = "ClerkLoading"


class Protect(ClerkBase):
    tag = "Protect"


class RedirectToSignIn(ClerkBase):
    tag = "RedirectToSignIn"


class RedirectToSignUp(ClerkBase):
    tag = "RedirectToSignUp"


class RedirectToUserProfile(ClerkBase):
    tag = "RedirectToUserProfile"


class RedirectToOrganizationProfile(ClerkBase):
    tag = "RedirectToOrganizationProfile"


class RedirectToCreateOrganization(ClerkBase):
    tag = "RedirectToCreateOrganization"


class SignedIn(ClerkBase):
    tag = "SignedIn"


class SignedOut(ClerkBase):
    tag = "SignedOut"


signed_in = SignedIn.create
signed_out = SignedOut.create
