"""Tests for Resrobot entry migration."""

import pytest
from homeassistant.components.sensor.const import DOMAIN as SENSOR_DOMAIN
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hasl3 import async_migrate_integration
from custom_components.hasl3.const import (
    CONF_DESTINATION,
    CONF_INTEGRATION_TYPE,
    CONF_RR_KEY,
    CONF_SOURCE,
    DOMAIN,
    SENSOR_RRARR,
    SENSOR_RRDEP,
    SENSOR_RRROUTE,
    SENSOR_RESROBOT_ARRIVAL,
    SENSOR_RESROBOT_DEPARTURE,
    SENSOR_RESROBOT_ROUTE,
    SENSOR_STATUS,
    SERVICE_RESROBOT_KEY,
)

NEW_VERSION = 5


def _legacy_rr_entry(
    hass,
    *,
    title: str,
    entry_id: str,
    rr_key: str,
    integration_type: str,
    data_extra: dict | None = None,
    version: int = 4,
):
    data = {
        CONF_INTEGRATION_TYPE: integration_type,
        CONF_RR_KEY: rr_key,
        **(data_extra or {}),
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=title,
        data=data,
        entry_id=entry_id,
        version=version,
    )
    entry.add_to_hass(hass)
    return entry


@pytest.mark.asyncio
async def test_migrate_resrobot_single_key_creates_parent_and_subentries(hass):
    entry_dep = _legacy_rr_entry(
        hass,
        title="RR Departures",
        entry_id="rrdep",
        rr_key="key-1",
        integration_type=SENSOR_RRDEP,
        data_extra={CONF_SOURCE: "1001"},
    )
    _legacy_rr_entry(
        hass,
        title="RR Arrivals",
        entry_id="rrarr",
        rr_key="key-1",
        integration_type=SENSOR_RRARR,
        data_extra={CONF_DESTINATION: "2002"},
    )
    _legacy_rr_entry(
        hass,
        title="RR Route",
        entry_id="rrroute",
        rr_key="key-1",
        integration_type=SENSOR_RRROUTE,
        data_extra={CONF_SOURCE: "1001", CONF_DESTINATION: "2002"},
    )

    await async_migrate_integration(hass)

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    parent = entries[0]
    assert parent.entry_id == entry_dep.entry_id
    assert parent.data == {
        CONF_RR_KEY: "key-1",
        CONF_INTEGRATION_TYPE: SERVICE_RESROBOT_KEY,
    }
    assert parent.options == {}
    assert parent.version == NEW_VERSION

    subentries = list(parent.subentries.values())
    assert len(subentries) == 3

    subentry_types = {subentry.data[CONF_INTEGRATION_TYPE] for subentry in subentries}
    assert subentry_types == {
        SENSOR_RESROBOT_DEPARTURE,
        SENSOR_RESROBOT_ARRIVAL,
        SENSOR_RESROBOT_ROUTE,
    }

    for subentry in subentries:
        assert CONF_RR_KEY not in subentry.data
        assert subentry.title in {"RR Departures", "RR Arrivals", "RR Route"}


@pytest.mark.asyncio
async def test_migrate_resrobot_multiple_keys_grouped(hass):
    _legacy_rr_entry(
        hass,
        title="RR Departures A",
        entry_id="rrdep_a",
        rr_key="key-a",
        integration_type=SENSOR_RRDEP,
        data_extra={CONF_SOURCE: "1001"},
    )
    _legacy_rr_entry(
        hass,
        title="RR Arrivals A",
        entry_id="rrarr_a",
        rr_key="key-a",
        integration_type=SENSOR_RRARR,
        data_extra={CONF_DESTINATION: "2002"},
    )
    _legacy_rr_entry(
        hass,
        title="RR Departures B",
        entry_id="rrdep_b",
        rr_key="key-b",
        integration_type=SENSOR_RRDEP,
        data_extra={CONF_SOURCE: "3003"},
    )

    await async_migrate_integration(hass)

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 2

    by_key = {entry.data[CONF_RR_KEY]: entry for entry in entries}
    assert set(by_key) == {"key-a", "key-b"}

    assert len(by_key["key-a"].subentries) == 2
    assert len(by_key["key-b"].subentries) == 1


@pytest.mark.asyncio
async def test_migrate_resrobot_updates_entity_registry(hass):
    entry_dep = _legacy_rr_entry(
        hass,
        title="RR Departures",
        entry_id="rrdep",
        rr_key="key-1",
        integration_type=SENSOR_RRDEP,
        data_extra={CONF_SOURCE: "1001"},
    )

    entity_registry = er.async_get(hass)
    entity = entity_registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        entry_dep.entry_id,
        suggested_object_id="rrdep",
    )

    await async_migrate_integration(hass)

    parent = hass.config_entries.async_entries(DOMAIN)[0]
    subentry = next(iter(parent.subentries.values()))
    updated = entity_registry.async_get(entity.entity_id)

    assert updated.config_entry_id == parent.entry_id
    assert updated.config_subentry_id == subentry.subentry_id
    assert updated.unique_id == subentry.subentry_id


@pytest.mark.asyncio
async def test_migrate_resrobot_idempotent_when_version_is_new(hass):
    entry = _legacy_rr_entry(
        hass,
        title="RR Departures",
        entry_id="rrdep",
        rr_key="key-1",
        integration_type=SENSOR_RRDEP,
        data_extra={CONF_SOURCE: "1001"},
        version=NEW_VERSION,
    )

    await async_migrate_integration(hass)

    entries = hass.config_entries.async_entries(DOMAIN)
    assert entries == [entry]
    assert entries[0].data[CONF_INTEGRATION_TYPE] == SENSOR_RRDEP


@pytest.mark.asyncio
async def test_migrate_non_resrobot_entries_untouched(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Status",
        data={CONF_INTEGRATION_TYPE: SENSOR_STATUS},
        entry_id="status",
        version=4,
    )
    entry.add_to_hass(hass)

    await async_migrate_integration(hass)

    entries = hass.config_entries.async_entries(DOMAIN)
    assert entries == [entry]
    assert entries[0].data[CONF_INTEGRATION_TYPE] == SENSOR_STATUS
