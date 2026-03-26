"""Tests for the weather generation module."""

from calcio_manager.engine.weather import Weather, generate_weather


class TestGenerateWeather:
    """Test generate_weather produces realistic results."""

    def test_returns_weather_object(self) -> None:
        """generate_weather returns a Weather dataclass."""
        result = generate_weather(6)
        assert isinstance(result, Weather)
        assert isinstance(result.key, str)
        assert isinstance(result.icon, str)
        assert isinstance(result.temperature, int)

    def test_no_snow_in_summer(self) -> None:
        """Snow must not appear in summer months (May–September)."""
        summer_months = [5, 6, 7, 8, 9]
        for month in summer_months:
            for _ in range(200):
                w = generate_weather(month)
                assert w.key != "snow", (
                    f"Got snow in month {month}"
                )

    def test_snow_possible_in_winter(self) -> None:
        """Snow should be possible in winter months (Dec, Jan, Feb)."""
        winter_months = [12, 1, 2]
        snow_seen = False
        for month in winter_months:
            for _ in range(500):
                w = generate_weather(month)
                if w.key == "snow":
                    snow_seen = True
                    break
            if snow_seen:
                break
        assert snow_seen, "Expected snow at least once across winter months"

    def test_summer_temperatures_warm(self) -> None:
        """Summer temperatures should be above freezing."""
        for _ in range(200):
            w = generate_weather(7)
            assert w.temperature >= 15, (
                f"July temp {w.temperature}°C too cold"
            )

    def test_winter_temperatures_cold(self) -> None:
        """Winter temperatures should not be hot."""
        for _ in range(200):
            w = generate_weather(1)
            assert w.temperature <= 10, (
                f"January temp {w.temperature}°C too warm"
            )

    def test_all_months_valid(self) -> None:
        """All 12 months should produce valid weather."""
        for month in range(1, 13):
            w = generate_weather(month)
            assert w.key
            assert w.icon
            assert -10 <= w.temperature <= 40

    def test_fallback_for_unknown_month(self) -> None:
        """Unknown months default to September conditions."""
        w = generate_weather(99)
        assert isinstance(w, Weather)
