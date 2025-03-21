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
