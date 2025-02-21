"""Test Shopping List intents."""

from homeassistant.components.shopping_list.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent


async def test_add_item(hass: HomeAssistant, sl_setup) -> None:
    """Test adding an item intent."""

    response = await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": " beer "}}
    )
    assert len(hass.data[DOMAIN].items) == 1
    assert hass.data[DOMAIN].items[0]["name"] == "beer"  # name was trimmed

    # Response text is now handled by default conversation agent
    assert response.response_type == intent.IntentResponseType.ACTION_DONE


async def test_complete_item(hass: HomeAssistant, sl_setup) -> None:
    """Test completing an item intent."""

    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "cheese"}}
    )

    response = await intent.async_handle(
        hass, "test", "HassShoppingListCompleteItem", {"item": {"value": "beer"}}
    )
    assert len(hass.data[DOMAIN].items) == 2
    assert hass.data[DOMAIN].items[0]["name"] == "beer"
    assert hass.data[DOMAIN].items[0]["complete"] is True

    # Response text is now handled by default conversation agent
    assert response.response_type == intent.IntentResponseType.ACTION_DONE


async def test_recent_items_intent(hass: HomeAssistant, sl_setup) -> None:
    """Test recent items."""
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "wine"}}
    )
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "soda"}}
    )

    response = await intent.async_handle(hass, "test", "HassShoppingListLastItems")

    assert (
        response.speech["plain"]["speech"]
        == "These are the top 3 items on your shopping list: soda, wine, beer"
    )


async def test_recent_items_intent_no_items(hass: HomeAssistant, sl_setup) -> None:
    """Test recent items."""
    response = await intent.async_handle(hass, "test", "HassShoppingListLastItems")

    assert (
        response.speech["plain"]["speech"] == "There are no items on your shopping list"
    )
