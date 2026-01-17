# Unit tests for configuration file

import pytest

from config import settings
from config import settings as settings1
from config import settings as settings2


@pytest.mark.unit
def test_settings_is_singleton():
    """Verify settings is the same object across imports"""
    assert settings1 is settings2
    assert settings1.DATABASE_URL == settings2.DATABASE_URL
    print("Settings is a singleton")


@pytest.mark.unit
def test_settings_values_loaded():
    """Verify settings loaded from .env"""
    assert settings.DATABASE_URL is not None
    assert settings.JWT_SECRET_KEY is not None
    assert settings.ADMIN_EMAIL is not None
    print("Settings loaded from .env")
