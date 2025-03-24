from reflex_clerk_api.base import ClerkBase


class UserButton(ClerkBase):
    tag = "UserButton"


class UserProfile(ClerkBase):
    tag = "UserProfile"


user_button = UserButton.create
user_profile = UserProfile.create
