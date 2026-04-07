import reflex as rx

from reflex_clerk_api.base import ClerkBase
from reflex_clerk_api.models import Appearance


class PricingTable(ClerkBase):
    tag = "PricingTable"

    _rename_props: dict[str, str] = {"for_": "for"}

    for_: str | None = None
    collapse_features: bool | None = None
    cta_position: str | None = None
    fallback: rx.Component | None = None
    new_subscription_redirect_url: str | None = None
    appearance: Appearance | None = None


pricing_table = PricingTable.create
