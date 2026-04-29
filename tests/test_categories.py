from local_deal_radar.categories import CATEGORY_PROFILES, get_category_profile


REQUIRED_CATEGORIES = {
    "cameras",
    "lenses",
    "vintage_audio",
    "bikes",
    "bike_parts",
    "outdoor_gear",
    "tools",
    "electronics",
    "video_games",
    "collectibles",
    "musical_instruments",
    "default",
}


def test_all_required_category_profiles_exist() -> None:
    assert REQUIRED_CATEGORIES.issubset(CATEGORY_PROFILES)


def test_unknown_category_falls_back_to_default() -> None:
    profile = get_category_profile("unknown category")

    assert profile.name == "default"


def test_category_lookup_is_case_insensitive() -> None:
    profile = get_category_profile("CAMERAS")

    assert profile.name == "cameras"


def test_category_lookup_tolerates_spaces_and_hyphens() -> None:
    assert get_category_profile("Vintage Audio").name == "vintage_audio"
    assert get_category_profile("bike-parts").name == "bike_parts"


def test_bulky_high_risk_categories_have_higher_costs_than_small_categories() -> None:
    bikes = get_category_profile("bikes")
    video_games = get_category_profile("video_games")

    assert bikes.default_shipping_cost > video_games.default_shipping_cost
    assert bikes.hassle_score > video_games.hassle_score
