"""HA API types."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HAEvents:
    """Response from the get_events request.

    {
      "event": "state_changed",
      "listener_count": 5
    }
    """

    event: str = ""
    listener_count: int = 0


@dataclass
class HAService:
    """Response from the get_services request.

    {
      "domain": "light",
      "service": "turn_on"
    }
    """

    domain: str = ""
    service: list[str] = field(default_factory=list)


@dataclass
class HAState:
    """Response from a call_service request.

    {
        "attributes": {},
        "entity_id": "sun.sun",
        "last_changed": "2016-05-30T21:43:32.418320+00:00",
        "state": "below_horizon"
    }
    """

    entity_id: str
    state: str

    attributes: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    last_changed: str = ""
    last_reported: str = ""
    last_updated: str = ""


@dataclass
class HAEntityShort:
    """Entity from the Entity Register (for display).

    https://developers.home-assistant.io/docs/api/websocket#entities

    {
      "ei": "light.living_room",
      "pl": "hue",
      "ai": "living_room",
      "di": "abc123def456",
      "en": "Living Room",
      "hn": true
    }

    Name	Type	Required	Description	Source
    ei	string	Yes	Entity ID - unique identifier for the entity (e.g., "light.living_room")	RegistryEntry.entity_id
    pl	string	Yes	Platform - the integration that created this entity (e.g., "hue", "mqtt")	RegistryEntry.platform
    ai	string	No	Area ID - the area this entity is assigned to	RegistryEntry.area_id (only if not null)
    lb	array[string]	No	Labels - list of label id's assigned to this entity for organization	RegistryEntry.labels (converted to list, only if not empty)
    di	string	No	Device ID - the device this entity belongs to	RegistryEntry.device_id (only if not null)
    ic	string	No	Icon - custom icon set by the user (overrides state icon, so if this is set, don't use the attribute value in the state) icons are in the format "prefix:icon-name", for example: "mdi:lightbulb-on"	RegistryEntry.icon (only if not null)
    tk	string	No	Translation Key - key used for translating entity name from the integration	RegistryEntry.translation_key (only if not null)
    ec	integer	No	Entity Category (index) - numeric index into the entity_categories mapping	RegistryEntry.entity_category (only if not null)
    hb	boolean	No	Hidden By - present (true) if entity is hidden by user or integration	RegistryEntry.hidden_by (only present as true if not null)
    hn	boolean	No	Has Entity Name - present (true) if entity uses the integration-provided name	RegistryEntry.has_entity_name (only present as true if true)
    en	string	No	Entity Name - display name for the entity (prioritizes user customization)	User-set RegistryEntry.name or falls back to RegistryEntry.original_name (only if either is set)
    dp	integer	No	Display Precision - sensor-specific precision for displaying values. The user-configured display_precision takes priority; falls back to the integration-provided suggested_display_precision	RegistryEntry.options["sensor"]["display_precision"] (preferred) or RegistryEntry.options["sensor"]["suggested_display_precision"] (sensor domain only, only if set)
    """

    ei: str
    """Entity ID."""
    pl: str
    """Platform."""
    ai: str
    """Area ID."""
    di: str
    """Device ID."""
    en: str
    """Entity name."""
    lb: list[str] = field(default_factory=list)
    """Labels."""
    tk: str = ""
    """Translation key."""
    ec: int | None = None
    """Entity category."""
    hb: bool = False
    """Hidden by."""
    hn: bool = False
    """Has entity name."""
    dp: int | None = None
    """Display precision."""


@dataclass
class HAEntity:
    """Entity from the Entity Register.

    https://developers.home-assistant.io/docs/api/websocket#entities
    """

    entity_id: str
    """Entity ID."""
    platform: str
    """Platform."""
    area_id: str
    """Area ID."""
    categories: dict[str, str] = field(default_factory=dict)
    """Categories."""
    device_id: str = ""
    """Device ID."""
    name: str = ""
    """Entity name."""
    labels: list[str] = field(default_factory=list)
    """Labels."""
    translation_key: str = ""
    """Translation key."""
    entity_category: str = ""
    """Entity category."""
    hidden_by: bool = False
    """Hidden by."""
    has_entity_name: bool = False
    """Has entity name."""
    display_precision: int | None = None
    """Display precision."""

    config_entry_id: str = ""
    created_at: float = 0.0
    modified_at: float = 0.0
    config_subentry_id: str = ""
    original_name: str = ""
    unique_id: str = ""
    icon: str = ""
    id: str = ""
    disabled_by: str = ""
    options: dict[str, Any] = field(default_factory=dict)
