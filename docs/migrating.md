# Migration Guide

This guide provides information on migrating from the `Kroo/reflex-clerk` package to the `reflex-clerk-api`. It's mostly a direct drop-in replacement, but there are a few small changes to be aware of. Also some improvements that fill some gaps in the previous package.

## Key Changes

1. **Import Path Update**:
   Update your imports to use `reflex_clerk_api` instead of `reflex_clerk`.

2. **Page Installation**:
   Use `clerk.add_sign_in_page(app)` and `clerk.add_sign_up_page(app)` instead of `clerk.install_pages(app)`.

3. **User Information Retrieval**:
   For full user info, use `await clerk.get_user()` inside event handlers instead of `clerk_state.user`. This makes the user data retrieval occur explicitly when needed. You can choose to cache the information however you like.

4. **ClerkUser**:
   If you just want basic user information, you can enable the `ClerkUser` state by setting `register_user_state=True` when calling `clerk.clerk_provider(...)`.

5. **On load Event Handling**:
   Wrap `on_load` events that depend on the user authentication state with `clerk.on_load(<on_load_events>)` to ensure the `ClerkState` is updated before other `on_load` events. This ensures that `is_signed_in` will be accurate. (This was not handled with the previous package).

6. **On Auth Change Handlers**:
   Use `clerk.register_on_auth_change_handler(<handler>)` to register event handlers that are called on authentication changes (login/logout). (This was not handled with the previous package).

7. **Backend API**:
   Note that you can also import and directly use the `clerk_backend_api` if desired, as it is a dependency of this plugin. The `client` used by the `ClerkState` is available as a property `clerk_state.client`.

!!! note

    The lower case `clerk_state` implies using `clerk_state = await self.get_state(clerk.ClerkState)` within an event handler method.
