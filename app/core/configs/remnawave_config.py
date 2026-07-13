from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

from pydantic import Field, HttpUrl, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions import EnvException, RemnawaveAuthError
from app.utils.path import env_file
from app.utils.log import log


class _RemnawaveConfig(BaseSettings):
    """
    Configuration for Remnawave API
    Parameters:
    - REMNAWAVE_URL_PANEL: URL of the Remnawave admin panel (required)
    - REMNAWAVE_ADMIN_LOGIN: Admin login for authentication (optional if API key is provided)
    - REMNAWAVE_ADMIN_PASSWORD: Admin password for authentication (optional if API key is provided)
    - REMNAWAVE_ADMIN_TOKEN: API key for authentication (optional if login/password is provided)
    At least one authentication method must be provided: either login/password or API key.
    """
    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        frozen=True,
    )

    remnawave_admin_panel: HttpUrl = Field(
        default=...,
        description="",
        validation_alias="REMNAWAVE_URL_PANEL",
    )

    remnawave_admin_login: Optional[str] = Field(
        default=None,
        description="",
        validation_alias="REMNAWAVE_ADMIN_LOGIN",
    )

    remnawave_admin_password: Optional[SecretStr] = Field(
        default=None,
        description="",
        validation_alias="REMNAWAVE_ADMIN_PASSWORD",
    )

    remnawave_admin_token: Optional[SecretStr] = Field(
        default=None,
        description="",
        validation_alias="REMNAWAVE_ADMIN_TOKEN",
    )

    @field_validator("remnawave_admin_panel")
    @classmethod
    def validate_admin_panel(cls, value: HttpUrl) -> HttpUrl:
        """Validate URL Admin panel"""

        if value.host == "0.0.0.0":
            raise EnvException("⚠ REMNAWAVE_ADMIN_PANEL cannot point to 0.0.0.0")

        if value.host in ["localhost", "127.0.0.1"]:
            log.warning(f"⚠️ Using localhost for admin panel: {value}")
            
        if value.scheme == "http" and value.host not in ["localhost", "127.0.0.1"]:
            log.warning(f"⚠️ Admin panel URL uses HTTP (not secure): {value}")

        return value

    @field_validator("remnawave_admin_login")
    @classmethod
    def validate_remnawave_admin_login(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(value.strip()) == 0:
            raise EnvException("⚠ 'REMNAWAVE_ADMIN_LOGIN' cannot be empty!")
        return value

    @field_validator("remnawave_admin_password")
    @classmethod
    def validate_remnawave_admin_password(cls, value: Optional[SecretStr]) -> Optional[SecretStr]:
        if value is None:
            return value

        if len(value.get_secret_value()) < 8:
            raise EnvException("❌ Remnawave password cannot be less than 8 characters long.")

        return value

    @model_validator(mode="after")
    def validate_authentication_method(self) -> "_RemnawaveConfig":
        has_password_auth = self._has_password_auth_credentials(
            self.remnawave_admin_login, self.remnawave_admin_password
        )
        has_api_key = self._has_api_key_value(self.remnawave_admin_token)

        if not (has_password_auth or has_api_key):
            raise RemnawaveAuthError(
                "At least one authentication method must be specified:\n"
                "- Login and password (REMNAWAVE_ADMIN_LOGIN + REMNAWAVE_ADMIN_PASSWORD)\n"
                "- API key (REMNAWAVE_ADMIN_TOKEN)"
            )

        if has_password_auth and has_api_key:
            log.info("🔐 Using both: login/password and API Key")
        elif has_password_auth:
            log.info("🔐 Using: login/password")
        elif has_api_key:
            log.info("🔐 Using: API Key")

        return self

    def get_auth_data(self) -> Dict[str, str]:
        """Get authentication data for login requests"""
        auth_data: Dict[str, str] = {}

        if self.remnawave_admin_login and self.remnawave_admin_password:
            auth_data = {
                "username": self.remnawave_admin_login,
                "password": self.remnawave_admin_password.get_secret_value(),
            }
            log.debug("Using password authentication data")

        return auth_data

    @staticmethod
    def _has_non_empty_secret(value: Optional[SecretStr]) -> bool:
        return bool(value and value.get_secret_value().strip())

    @classmethod
    def _has_password_auth_credentials(
        cls, login: Optional[str], password: Optional[SecretStr]
    ) -> bool:
        return bool(login and login.strip() and cls._has_non_empty_secret(password))

    @classmethod
    def _has_api_key_value(cls, api_key: Optional[SecretStr]) -> bool:
        return cls._has_non_empty_secret(api_key)

    @property
    def has_password_auth(self) -> bool:
        """Check if password authentication is available"""
        return self._has_password_auth_credentials(
            self.remnawave_admin_login, self.remnawave_admin_password
        )

    @property
    def has_api_key(self) -> bool:
        """Check if API key authentication is available"""
        return self._has_api_key_value(self.remnawave_admin_token)

    def assert_login_credentials(self) -> Tuple[str, SecretStr]:
        if (
            self.remnawave_admin_login is None
            or self.remnawave_admin_password is None
        ):
            raise EnvException("❌ Login credentials are not properly configured!")

        return self.remnawave_admin_login, self.remnawave_admin_password

    def get_api_client_config(self) -> Dict[str, Any]:
        """
        Get complete configuration for API client

        Returns:
            Dictionary with base_url and authentication configuration
        """
        config = {
            "base_url": str(self.remnawave_admin_panel),
            "auth_method": None,
        }
        if self.has_api_key:
            config["auth_method"] = "api_key"
            config["api_key"] = self.remnawave_admin_token
        elif self.has_password_auth:
            config["auth_method"] = "password"
            config["login"] = self.remnawave_admin_login
            config["password"] = self.remnawave_admin_password

        return config

    def __str__(self) -> str:
        auth_methods = []
        if self.has_password_auth:
            auth_methods.append("🔑 Password")
        if self.has_api_key:
            auth_methods.append("🔐 API Key")

        return (
            f"RemnawaveConfig(\n"
            f"  URL: {self.remnawave_admin_panel}\n"
            f"  Auth: {', '.join(auth_methods) if auth_methods else '❌ None'}\n"
            f")"
        )

@lru_cache()
def get_remnawave_config() -> Optional["_RemnawaveConfig"]:
    """Returns Remnawave config, or None if not configured."""
    try:
        return _RemnawaveConfig()
    except Exception:
        return None


try:
    remnawave = get_remnawave_config()
    if remnawave:
        log.success("✅ Remnawave config initialized successfully")
        log.debug(f"Remnawave: {remnawave}")
    else:
        log.warning(
            "⚠️ Remnawave is not configured. VPN panel features will be unavailable."
        )
except Exception as e:
    log.warning(
        "⚠️ Failed to initialize Remnawave config: {}. "
        "VPN panel features will be unavailable.",
        e,
    )
