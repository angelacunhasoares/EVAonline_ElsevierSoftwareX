"""Unit tests for MATOPIBA map helpers."""

from dash import html

from backend.core.map_results import matopiba_forecasts as forecasts


def test_ensure_list_handles_strings_and_none():
    assert forecasts._ensure_list(None) == []
    assert forecasts._ensure_list("eto") == ["eto"]
    assert forecasts._ensure_list(["eto", "precipitation"]) == [
        "eto",
        "precipitation",
    ]


def test_render_maps_accepts_string_inputs(monkeypatch):
    def fake_create_eto_maps(cities_data, selected_days, validation):
        assert selected_days == ["tomorrow"]
        return "ETO MAP"

    monkeypatch.setattr(forecasts, "create_eto_maps", fake_create_eto_maps)
    monkeypatch.setattr(
        forecasts,
        "create_precipitation_maps",
        lambda *args, **kwargs: "PRECIP MAP",
    )

    forecast_data = {
        "forecasts": {
            "city": {
                "today": {"eto": 4.0, "precipitation": 1.0},
                "tomorrow": {"eto": 5.0, "precipitation": 1.2},
                "metadata": {"city_name": "City", "state": "ST"},
            }
        },
        "validation": {},
    }

    result = forecasts.render_maps(forecast_data, "eto", "tomorrow")

    assert isinstance(result, html.Div)
    assert result.children == ["ETO MAP"]
