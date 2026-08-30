from app.services.met_norway import _symbol_to_wmo


def test_met_norway_symbol_mapping():
    assert _symbol_to_wmo("clearsky_day") == 0
    assert _symbol_to_wmo("partlycloudy_day") == 2
    assert _symbol_to_wmo("rain") == 61
    assert _symbol_to_wmo("heavyrainandthunder") == 95
