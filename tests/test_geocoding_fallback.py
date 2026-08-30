from app.services.geocoding_fallback import NominatimGeocodingService


def test_geocoding_fallback_service_constructs():
    service = NominatimGeocodingService()
    assert service is not None
