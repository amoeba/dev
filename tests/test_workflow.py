# Copyright (c) 2025 ADBC Drivers Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from pydantic import ValidationError

from adbc_drivers_dev.generate import GenerateConfig, LangConfig


def test_model_default() -> None:
    config = GenerateConfig.model_validate({})
    assert config.driver == "(unknown)"
    assert config.environment is None
    assert config.private is False
    assert config.lang == {}
    assert config._processed_secrets == {
        "all": {},
        "build:release": {},
        "test": {},
        "validate": {},
    }
    assert config._permissions == {}
    assert config.aws is None
    assert config.gcloud is False
    assert config.validation.extra_dependencies == {}

    assert config.to_dict() == {
        "driver": "(unknown)",
        "environment": None,
        "private": False,
        "lang": {},
        "secrets": {
            "all": {},
            "build:release": {},
            "test": {},
            "validate": {},
        },
        "permissions": {},
        "aws": None,
        "gcloud": False,
        "validation": {"extra_dependencies": {}},
    }

    assert config == GenerateConfig.model_validate({})


def test_model_custom() -> None:
    config = GenerateConfig.model_validate({"driver": "postgresql"})
    assert config.driver == "postgresql"
    assert config.to_dict()["driver"] == "postgresql"
    assert config == config
    assert config != GenerateConfig.model_validate({})

    config = GenerateConfig.model_validate({"environment": "ci-env"})
    assert config.environment == "ci-env"
    assert config.to_dict()["environment"] == "ci-env"
    assert config == config
    assert config != GenerateConfig.model_validate({})

    config = GenerateConfig.model_validate({"private": True})
    assert config.private is True
    assert config.to_dict()["private"] is True
    assert config == config
    assert config != GenerateConfig.model_validate({})

    config = GenerateConfig.model_validate({"lang": {"python": True, "java": False}})
    assert config.lang == {"python": LangConfig(), "java": None}
    assert config == config
    assert config != GenerateConfig.model_validate({})


def test_params_secrets() -> None:
    config = GenerateConfig.model_validate(
        {
            "secrets": {
                "foo": "bar",
                "spam": {"secret": "eggs"},
                "fizz": {"secret": "buzz", "contexts": ["test", "validate"]},
            }
        }
    )
    assert config._processed_secrets == {
        "all": {"foo": "bar", "spam": "eggs", "fizz": "buzz"},
        "build:release": {"foo": "bar", "spam": "eggs"},
        "test": {"foo": "bar", "spam": "eggs", "fizz": "buzz"},
        "validate": {"foo": "bar", "spam": "eggs", "fizz": "buzz"},
    }
    assert config.to_dict()["secrets"] == {
        "all": {"foo": "bar", "spam": "eggs", "fizz": "buzz"},
        "build:release": {"foo": "bar", "spam": "eggs"},
        "test": {"foo": "bar", "spam": "eggs", "fizz": "buzz"},
        "validate": {"foo": "bar", "spam": "eggs", "fizz": "buzz"},
    }


def test_params_aws() -> None:
    config = GenerateConfig.model_validate({"aws": {"region": "us-west-2"}})
    assert config.aws.region == "us-west-2"
    assert config._permissions == {"id_token": True}
    assert config.to_dict()["permissions"] == {"id_token": True}
    assert config._processed_secrets == {
        "all": {
            "AWS_ROLE": "AWS_ROLE",
            "AWS_ROLE_SESSION_NAME": "AWS_ROLE_SESSION_NAME",
        },
        "build:release": {},
        "test": {},
        "validate": {},
    }
    assert config.to_dict()["secrets"] == {
        "all": {
            "AWS_ROLE": "AWS_ROLE",
            "AWS_ROLE_SESSION_NAME": "AWS_ROLE_SESSION_NAME",
        },
        "build:release": {},
        "test": {},
        "validate": {},
    }


def test_params_gcloud() -> None:
    config = GenerateConfig.model_validate({"gcloud": True})
    assert config.gcloud is True
    assert config._permissions == {"id_token": True}
    assert config.to_dict()["permissions"] == {"id_token": True}
    assert config._processed_secrets == {
        "all": {
            "GCLOUD_SERVICE_ACCOUNT": "GCLOUD_SERVICE_ACCOUNT",
            "GCLOUD_WORKLOAD_IDENTITY_PROVIDER": "GCLOUD_WORKLOAD_IDENTITY_PROVIDER",
        },
        "build:release": {},
        "test": {},
        "validate": {},
    }
    assert config.to_dict()["secrets"] == {
        "all": {
            "GCLOUD_SERVICE_ACCOUNT": "GCLOUD_SERVICE_ACCOUNT",
            "GCLOUD_WORKLOAD_IDENTITY_PROVIDER": "GCLOUD_WORKLOAD_IDENTITY_PROVIDER",
        },
        "build:release": {},
        "test": {},
        "validate": {},
    }


def test_params_invalid() -> None:
    with pytest.raises(ValidationError):
        GenerateConfig.model_validate({"private": ""})

    with pytest.raises(ValidationError):
        GenerateConfig.model_validate({"environment": 2})

    with pytest.raises(ValidationError):
        GenerateConfig.model_validate({"environment": ""})

    with pytest.raises(ValidationError):
        GenerateConfig.model_validate(
            {
                "secrets": {
                    "fizz": {
                        "secret": "buzz",
                        "contexts": ["test", "validate"],
                        "foo": "bar",
                    },
                }
            }
        )

    with pytest.raises(ValidationError):
        GenerateConfig.model_validate(
            {
                "secrets": {
                    "fizz": {"secret": "buzz", "contexts": ["asdf"], "foo": "bar"},
                }
            }
        )


def test_model_unknown() -> None:
    with pytest.raises(ValidationError):
        GenerateConfig.model_validate({"unknown_key": "value"})

    with pytest.raises(ValidationError):
        GenerateConfig.model_validate({"aws": {"foo": "bar"}})

    with pytest.raises(ValidationError):
        GenerateConfig.model_validate({"aws": {"region": "foo", "foo": "bar"}})


def test_validation_config_alias() -> None:
    config = GenerateConfig.model_validate(
        {"validation": {"extra-dependencies": {"pytest": "^7.0", "black": "*"}}}
    )
    assert config.validation.extra_dependencies == {"pytest": "^7.0", "black": "*"}

    config = GenerateConfig.model_validate(
        {"validation": {"extra_dependencies": {"mypy": "^1.0"}}}
    )
    assert config.validation.extra_dependencies == {"mypy": "^1.0"}


def test_params_aws_and_gcloud() -> None:
    config = GenerateConfig.model_validate(
        {"aws": {"region": "us-west-2"}, "gcloud": True}
    )
    assert config.aws.region == "us-west-2"
    assert config.gcloud is True
    assert config._permissions == {"id_token": True}

    # Ensure both sets of secrets end up in "all"
    assert config._processed_secrets["all"] == {
        "AWS_ROLE": "AWS_ROLE",
        "AWS_ROLE_SESSION_NAME": "AWS_ROLE_SESSION_NAME",
        "GCLOUD_SERVICE_ACCOUNT": "GCLOUD_SERVICE_ACCOUNT",
        "GCLOUD_WORKLOAD_IDENTITY_PROVIDER": "GCLOUD_WORKLOAD_IDENTITY_PROVIDER",
    }

    # Individual contexts should be empty too
    assert config._processed_secrets["build:release"] == {}
    assert config._processed_secrets["test"] == {}
    assert config._processed_secrets["validate"] == {}


def test_default_model() -> None:
    config = GenerateConfig().model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )

    # Should include the basic fields with defaults
    assert config["driver"] == "(unknown)"
    assert config["private"] is False
    assert config["lang"] == {}
    assert config["secrets"] == {}
    assert config["gcloud"] is False
    assert config["validation"] == {"extra-dependencies": {}}

    # Should not include None values (environment, aws)
    assert "environment" not in config
    assert "aws" not in config

    # Should not include private fields
    assert "_processed_secrets" not in config
    assert "_permissions" not in config
