"""Tests for the vendored pyintellicenter PoolObject/PoolModel classes.

These are pure-Python with no Home Assistant or asyncio dependency.
"""

from custom_components.intellicenter.pyintellicenter import PoolModel, PoolObject
from custom_components.intellicenter.pyintellicenter.attributes import CIRCUIT_TYPE


def test_poolobject_pops_type_and_subtype_from_params():
    obj = PoolObject("C0006", {"OBJTYP": "CIRCUIT", "SUBTYP": "POOL", "SNAME": "Pool"})

    assert obj.objnam == "C0006"
    assert obj.objtype == "CIRCUIT"
    assert obj.subtype == "POOL"
    assert obj.sname == "Pool"
    # OBJTYP/SUBTYP shouldn't leak into the generic properties/attributes
    assert "OBJTYP" not in obj.properties
    assert "SUBTYP" not in obj.properties


def test_poolobject_subtype_defaults_to_none():
    obj = PoolObject("_5451", {"OBJTYP": "SYSTEM", "SNAME": "x"})

    assert obj.subtype is None


def test_poolobject_getitem_returns_none_for_missing_key():
    obj = PoolObject("C0006", {"OBJTYP": "CIRCUIT", "STATUS": "ON"})

    assert obj["STATUS"] == "ON"
    assert obj["MISSING"] is None


def test_poolobject_on_off_status_depends_on_type():
    pump = PoolObject("PMP01", {"OBJTYP": "PUMP"})
    circuit = PoolObject("C0006", {"OBJTYP": "CIRCUIT"})

    assert pump.onStatus == "10"
    assert pump.offStatus == "4"
    assert circuit.onStatus == "ON"
    assert circuit.offStatus == "OFF"


def test_poolobject_is_a_light_for_known_subtypes():
    light = PoolObject("C0005", {"OBJTYP": "CIRCUIT", "SUBTYP": "GLOWT"})
    not_a_light = PoolObject("C0006", {"OBJTYP": "CIRCUIT", "SUBTYP": "GENERIC"})

    assert light.isALight is True
    assert not_a_light.isALight is False


def test_poolobject_support_color_effects_only_for_some_light_subtypes():
    glow = PoolObject("C0005", {"OBJTYP": "CIRCUIT", "SUBTYP": "GLOW"})
    dimmer = PoolObject("C0006", {"OBJTYP": "CIRCUIT", "SUBTYP": "DIMMER"})

    assert glow.supportColorEffects is True
    assert dimmer.supportColorEffects is False


def test_poolobject_is_a_light_show():
    show = PoolObject("X0001", {"OBJTYP": "CIRCUIT", "SUBTYP": "LITSHO"})
    not_show = PoolObject("X0002", {"OBJTYP": "CIRCUIT", "SUBTYP": "GENERIC"})

    assert show.isALightShow is True
    assert not_show.isALightShow is False


def test_poolobject_is_featured():
    featured = PoolObject("C0002", {"OBJTYP": "CIRCUIT", "FEATR": "ON"})
    not_featured = PoolObject("C0003", {"OBJTYP": "CIRCUIT", "FEATR": "OFF"})

    assert featured.isFeatured is True
    assert not_featured.isFeatured is False


def test_poolobject_update_returns_only_changed_attributes():
    obj = PoolObject("C0006", {"OBJTYP": "CIRCUIT", "STATUS": "OFF", "SNAME": "Pool"})

    changed = obj.update({"STATUS": "ON", "SNAME": "Pool"})

    assert changed == {"STATUS": "ON"}
    assert obj["STATUS"] == "ON"


def test_poolobject_update_can_change_type_and_subtype():
    obj = PoolObject("C0006", {"OBJTYP": "CIRCUIT", "SUBTYP": "POOL"})

    changed = obj.update({"OBJTYP": "CIRCUIT", "SUBTYP": "SPA"})

    assert obj.subtype == "SPA"
    # OBJTYP/SUBTYP live outside `properties`, so the "ignore if unchanged" dedup
    # (which only checks `properties`) doesn't apply to them: an unchanged OBJTYP
    # is still reported as "changed".
    assert changed == {"OBJTYP": "CIRCUIT", "SUBTYP": "SPA"}


def test_poolmodel_add_object_rejects_unmapped_types():
    model = PoolModel(attributeMap={CIRCUIT_TYPE: {"SNAME"}})

    circuit = model.addObject("C0006", {"OBJTYP": "CIRCUIT", "SNAME": "Pool"})
    system = model.addObject("_5451", {"OBJTYP": "SYSTEM", "SNAME": "x"})

    assert circuit is not None
    assert model.numObjects == 1
    assert model["C0006"] is circuit
    # SYSTEM isn't in the attributeMap so it's not tracked as a regular object...
    assert system is None
    assert model["_5451"] is None


def test_poolmodel_add_object_is_idempotent_and_updates_existing():
    model = PoolModel(attributeMap={CIRCUIT_TYPE: {"SNAME", "STATUS"}})
    model.addObject("C0006", {"OBJTYP": "CIRCUIT", "SNAME": "Pool", "STATUS": "OFF"})

    model.addObject("C0006", {"STATUS": "ON"})

    assert model.numObjects == 1
    assert model["C0006"]["STATUS"] == "ON"


def test_poolmodel_add_objects_bulk():
    model = PoolModel(attributeMap={CIRCUIT_TYPE: {"SNAME"}})

    model.addObjects(
        [
            {"objnam": "C0001", "params": {"OBJTYP": "CIRCUIT", "SNAME": "Spa"}},
            {"objnam": "C0006", "params": {"OBJTYP": "CIRCUIT", "SNAME": "Pool"}},
        ]
    )

    assert model.numObjects == 2
    assert {o.sname for o in model.objectList} == {"Spa", "Pool"}


def test_poolmodel_get_by_type_and_subtype():
    model = PoolModel(attributeMap={"BODY": {"SNAME"}})
    model.addObjects(
        [
            {"objnam": "B1101", "params": {"OBJTYP": "BODY", "SUBTYP": "POOL", "SNAME": "Pool"}},
            {"objnam": "B1202", "params": {"OBJTYP": "BODY", "SUBTYP": "SPA", "SNAME": "Spa"}},
        ]
    )

    assert [o.objnam for o in model.getByType("BODY")] == ["B1101", "B1202"]
    assert [o.objnam for o in model.getByType("BODY", "SPA")] == ["B1202"]


def test_poolmodel_get_children():
    model = PoolModel(attributeMap={CIRCUIT_TYPE: {"SNAME", "PARENT"}})
    model.addObjects(
        [
            {"objnam": "M0101", "params": {"OBJTYP": "CIRCUIT", "SNAME": "Module", "PARENT": "00000"}},
            {"objnam": "C0006", "params": {"OBJTYP": "CIRCUIT", "SNAME": "Pool", "PARENT": "M0101"}},
            {"objnam": "C0001", "params": {"OBJTYP": "CIRCUIT", "SNAME": "Spa", "PARENT": "M0101"}},
        ]
    )

    module = model["M0101"]
    children = model.getChildren(module)

    assert {c.objnam for c in children} == {"C0006", "C0001"}


def test_poolmodel_attributes_to_track_defaults_to_all_attributes_for_type():
    # the type must still be a key in the map (that's what addObject gates on),
    # but an empty/falsy value for it triggers the ALL_ATTRIBUTES_BY_TYPE fallback
    model = PoolModel(attributeMap={"PUMP": set()})
    model.addObject("PMP01", {"OBJTYP": "PUMP", "SNAME": "VSF"})

    query = model.attributesToTrack()

    assert len(query) == 1
    assert query[0]["objnam"] == "PMP01"
    assert "SNAME" in query[0]["keys"]


def test_poolmodel_process_updates_only_reports_changed_objects():
    model = PoolModel(attributeMap={CIRCUIT_TYPE: {"SNAME", "STATUS"}})
    model.addObject("C0006", {"OBJTYP": "CIRCUIT", "SNAME": "Pool", "STATUS": "OFF"})
    model.addObject("C0001", {"OBJTYP": "CIRCUIT", "SNAME": "Spa", "STATUS": "OFF"})

    updated = model.processUpdates(
        [
            {"objnam": "C0006", "params": {"STATUS": "ON"}},
            {"objnam": "C0001", "params": {"STATUS": "OFF"}},  # unchanged
            {"objnam": "UNKNOWN", "params": {"STATUS": "ON"}},  # not in model
        ]
    )

    assert updated == {"C0006": {"STATUS": "ON"}}
