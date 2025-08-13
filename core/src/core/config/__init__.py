# Copyright 2025 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import os
from pathlib import Path
from typing import Any, Mapping

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import EnvSettingsSource, PydanticBaseSettingsSource
from pydantic_settings.sources.utils import parse_env_vars


def getenv(name: str, default: str | None = None) -> str | None:
    rt_name = f"MLOPS_RUNTIME_PARAM_{name}"

    raw = os.getenv(rt_name)

    if raw is None:
        return os.getenv(name, default)

    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        # not a json, but some primitive type, so return it right away
        return raw

    if isinstance(value, dict):
        if value.get("type") == "string":
            return str(value["payload"])
        if len(value) == 1:
            return str(list(value.values())[0])
        elif "payload" in value:
            payload = value["payload"]
            if "apiToken" in payload:
                return str(payload["apiToken"])

    return raw


class PulumiConfigSettingsSource(EnvSettingsSource):
    """A source class that takes settings from a pulumi_config.json file."""

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        pulumi_config_file: str | None = None,
        pulumi_config_file_encoding: str | None = None,
        **kwargs: Any,
    ):
        self.pulumi_config_file = pulumi_config_file
        self.pulumi_config_file_encoding = pulumi_config_file_encoding
        super().__init__(settings_cls, **kwargs)

    def _find_config_file(self, config_file: str) -> Path | None:
        """Find config file by searching up the directory tree like .env files."""
        config_path = Path(config_file)

        # If it's an absolute path, just return it if it exists
        if config_path.is_absolute():
            return config_path if config_path.is_file() else None

        # Search from current directory up to root
        cwd = Path.cwd()
        for path in [cwd, *cwd.parents]:
            potential_path = path / config_file
            if potential_path.is_file():
                return potential_path

        return None

    def _load_env_vars(self) -> Mapping[str, str | None]:
        """Load environment variables with pulumi config values as fallback."""
        # Get normal environment variables first
        env_vars = dict(super()._load_env_vars())

        # Load pulumi config and add to env_vars (not os.environ)
        pulumi_config_file = self.pulumi_config_file or "pulumi_config.json"
        pulumi_config_path = self._find_config_file(pulumi_config_file)

        if pulumi_config_path is not None:
            encoding = self.pulumi_config_file_encoding or "utf-8"
            with open(pulumi_config_path, "r", encoding=encoding) as f:
                file_data = json.load(f)

            if isinstance(file_data, dict):
                # Add pulumi config values for each field (only if not already in env)
                for field_name in self.settings_cls.model_fields.keys():
                    env_key = field_name.upper()

                    # Skip if already set in environment
                    if env_key in env_vars and env_vars[env_key]:
                        continue

                    value = None
                    if field_name in file_data:
                        value = file_data[field_name]
                    elif env_key in file_data:
                        value = file_data[env_key]

                    if value is not None and value != "":
                        env_vars[env_key] = str(value)

        return parse_env_vars(
            env_vars,
            self.case_sensitive,
            self.env_ignore_empty,
            self.env_parse_none_str,
        )

    def __repr__(self) -> str:
        return f"PulumiConfigSettingsSource(pulumi_config_file={self.pulumi_config_file!r}, pulumi_config_file_encoding={self.pulumi_config_file_encoding!r})"


class GetenvSettingsSource(EnvSettingsSource):
    """A source class that uses the custom getenv function."""

    def _load_env_vars(self) -> Mapping[str, str | None]:
        """Load environment variables using the custom getenv function."""
        # Start with normal environment variables
        env_vars = dict(super()._load_env_vars())

        # Override with custom getenv for each field
        for field_name in self.settings_cls.model_fields.keys():
            env_key = field_name.upper()
            value = getenv(env_key)
            if value is not None and value != "":
                env_vars[env_key] = value

        return parse_env_vars(
            env_vars,
            self.case_sensitive,
            self.env_ignore_empty,
            self.env_parse_none_str,
        )

    def __repr__(self) -> str:
        return "GetenvSettingsSource()"


class DataRobotAppFrameworkBaseSettings(BaseSettings):
    """
    Base settings class that uses custom source priority:
    1. env variables (including Runtime Parameters)
    2. .env file
    3. file_secrets
    4. pulumi_config.json (fallback)
    """

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            GetenvSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
            PulumiConfigSettingsSource(settings_cls),
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )
