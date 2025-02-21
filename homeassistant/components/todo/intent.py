"""Intents for the todo integration."""

from __future__ import annotations

from abc import ABC, abstractmethod

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent

from . import TodoItem, TodoItemStatus, TodoListEntity
from .const import DATA_COMPONENT, DOMAIN

INTENT_LIST_ADD_ITEM = "HassListAddItem"
INTENT_LIST_COMPLETE_ITEM = "HassListCompleteItem"


async def async_setup_intents(hass: HomeAssistant) -> None:
    """Set up the todo intents."""
    intent.async_register(hass, ListAddItemIntent())
    intent.async_register(hass, ListCompleteItemIntent())


class ListItemIntentBase(ABC, intent.IntentHandler):
    """Base Class for List Item Intents."""

    @abstractmethod
    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""

    def get_list(self, intent_obj: intent.Intent, list_name: str) -> TodoListEntity:
        """Get the list entity from the intent."""
        hass = intent_obj.hass

        match_constraints = intent.MatchTargetsConstraints(
            name=list_name, domains=[DOMAIN], assistant=intent_obj.assistant
        )
        match_result = intent.async_match_targets(hass, match_constraints)
        if not match_result.is_match:
            raise intent.MatchFailedError(
                result=match_result, constraints=match_constraints
            )

        target_list = hass.data[DATA_COMPONENT].get_entity(
            match_result.states[0].entity_id
        )
        if target_list is None:
            raise intent.IntentHandleError(f"No to-do list: {list_name}")

        return target_list

    def get_list_item(self, list_entity: TodoListEntity, item_name: str) -> TodoItem:
        """Get the list item entity from the item name."""
        for item in list_entity.todo_items or []:
            if item.summary == item_name:
                return item

        raise intent.IntentHandleError(
            f"No item: {item_name} in list: {list_entity.name}"
        )


class ListAddItemIntent(ListItemIntentBase):
    """Handle ListAddItem intents."""

    intent_type = INTENT_LIST_ADD_ITEM
    description = "Add item to a todo list"
    slot_schema = {
        vol.Required("item"): intent.non_empty_string,
        vol.Required("name"): intent.non_empty_string,
    }
    platforms = {DOMAIN}

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        slots = self.async_validate_slots(intent_obj.slots)
        item = slots["item"]["value"].strip()
        list_name = slots["name"]["value"]

        target_list = self.get_list(intent_obj, list_name)

        # Add to list
        await target_list.async_create_todo_item(
            TodoItem(summary=item, status=TodoItemStatus.NEEDS_ACTION)
        )

        response = intent_obj.create_response()
        response.response_type = intent.IntentResponseType.ACTION_DONE
        response.async_set_results(
            [
                intent.IntentResponseTarget(
                    type=intent.IntentResponseTargetType.ENTITY,
                    name=list_name,
                    id=target_list.entity_id,
                )
            ]
        )
        return response


class ListCompleteItemIntent(ListItemIntentBase):
    """Handle ListCompleteItem intents."""

    intent_type = INTENT_LIST_COMPLETE_ITEM
    description = "Complete item on a todo list"
    slot_schema = {
        vol.Required("item"): intent.non_empty_string,
        vol.Required("name"): intent.non_empty_string,
    }
    platforms = {DOMAIN}

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        slots = self.async_validate_slots(intent_obj.slots)
        item = slots["item"]["value"].strip()
        list_name = slots["name"]["value"]

        target_list = self.get_list(intent_obj, list_name)
        target_list_item = self.get_list_item(target_list, item)
        if target_list_item.status == TodoItemStatus.COMPLETED:
            raise intent.IntentHandleError("Item is already completed")

        # Complete item
        target_list_item.status = TodoItemStatus.COMPLETED
        await target_list.async_update_todo_item(target_list_item)

        response = intent_obj.create_response()
        response.response_type = intent.IntentResponseType.ACTION_DONE
        response.async_set_results(
            [
                intent.IntentResponseTarget(
                    type=intent.IntentResponseTargetType.ENTITY,
                    name=list_name,
                    id=target_list.entity_id,
                )
            ]
        )
        return response
