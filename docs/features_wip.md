# Features of Reflex Clerk API

This documentation outlines the key components and functionalities available in the package.

## Core Components

The components implementation largely follows that of the [Clerk react overview](https://clerk.com/docs/references/react/overview).

### ClerkProvider

The `ClerkProvider` component is essential for wrapping your application or pages. It ensures that the Clerk authentication is properly managed and synchronized with the backend.

::: reflex_clerk_api.clerk_provider.clerk_provider

!!! note

    This is additionally wrapped in a custom `ClerkSessionSynchronizer` component to facilitate the backend synchronization.

### Authentication Components

- **SignIn** and **SignUp**: Components to create customizable sign-in and sign-up forms.

::: reflex_clerk_api.sign_in

::: reflex_clerk_api.sign_up

### User Components

- **UserButton**: Displays a button with the user's name and avatar.

::: reflex_clerk_api.user_button

- **UserProfile**: Displays a user profile with additional information.

::: reflex_clerk_api.user_profile

### Organization Components

These are only minimally implemented, and not tested. If you would like to use these, I will happily accept pull requests.

### Waitlist Component

This is only minimally implemented, and not tested. If you would like to use this, I will happily accept pull requests.

### Control Components

These determine what content is displayed based on the user's authentication state:

- **ClerkLoaded**: Displays content once Clerk is fully loaded.

::: reflex_clerk_api.clerk_loaded

- **ClerkLoading**: Displays content while Clerk is loading.

::: reflex_clerk_api.clerk_loading

- **Protect**: Protects specific content to ensure only authenticated users can access them.

::: reflex_clerk_api.protect

- **RedirectToSignIn**: Redirects users to the sign-in page if they are not authenticated.

<!-- ::: reflex_clerk_api.redirect_to_sign_in -->

- **RedirectToSignUp**: Redirects users to the sign-up page if they are not authenticated.

<!-- ::: reflex_clerk_api.redirect_to_sign_up -->

- **RedirectToUserProfile**: Redirects users to their profile page.

::: reflex_clerk_api.redirect_to_user_profile

- **RedirectToOrganizationProfile**: Redirects users to their organization profile page.

<!-- ::: reflex_clerk_api.redirect_to_organization_profile -->

- **RedirectToCreateOrganization**: Redirects users to create an organization.

<!-- ::: reflex_clerk_api.redirect_to_create_organization -->

- **SignedIn** and **SignedOut**: Conditional rendering based on user authentication state.

::: reflex_clerk_api.signed_in

::: reflex_clerk_api.signed_out

### Unstyled Components

These components manage user authentication states and interactions:

- **SignInButton**, **SignUpButton**, and **SignOutButton**: Button components to trigger sign-in and sign-out actions.

::: reflex_clerk_api.sign_in_button

::: reflex_clerk_api.sign_out_button

::: reflex_clerk_api.sign_up_button

- **SignInWithMetamaskButton**: Not yet implemented.

## Backend Synchronization

The Reflex Clerk API ensures that the backend states are synchronized with the Clerk authentication happening in the frontend. The main backend states include:

- **ClerkState**: Manages the authentication state of the user.

::: reflex_clerk_api.ClerkState

- **ClerkUser**: Provides access to additional user information.

::: reflex_clerk_api.ClerkUser

### Helper methods

- **On Load Event Handling**: Use `clerk.on_load(<on_load_events>)` to ensure the `ClerkState` is updated before other `on_load` events. This ensures that `is_signed_in` will be accurate.

::: reflex_clerk_api.on_load

- **On Auth Change Handlers**: Register event handlers that are called on authentication changes (login/logout) using `clerk.register_on_auth_change_handler(<handler>)`.

::: reflex_clerk_api.register_on_auth_change_handler

## Demos

To see these features in action, visit the [demo](https://reflex-clerk-api-demo.adventuresoftim.com).
