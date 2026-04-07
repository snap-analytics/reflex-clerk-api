from reflex_clerk_api.billing_components import PricingTable


def _render_props(component: PricingTable) -> list[str]:
    return component.render()["props"]


def test_pricing_table_create_with_no_props_renders_pricing_table_tag():
    component = PricingTable.create()

    rendered = component.render()
    assert rendered["name"] == "PricingTable"
    assert rendered["props"] == []


def test_pricing_table_create_for_renames_to_for():
    component = PricingTable.create(for_="organization")

    props = _render_props(component)
    assert 'for:"organization"' in props
    assert all(not prop.startswith("for_:") for prop in props)


def test_pricing_table_create_with_collapse_features():
    component = PricingTable.create(collapse_features=True)

    props = _render_props(component)
    assert "collapseFeatures:true" in props


def test_pricing_table_create_with_new_subscription_redirect_url():
    component = PricingTable.create(new_subscription_redirect_url="/billing")

    props = _render_props(component)
    assert 'newSubscriptionRedirectUrl:"/billing"' in props


def test_pricing_table_rename_props_maps_for__to_for():
    assert PricingTable._rename_props["for_"] == "for"
