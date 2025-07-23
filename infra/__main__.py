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
"""
* Discover and load all modules with Pulumi resources in the infra directory.
* Discover and validate all required features flags
"""

from infra import *  # noqa: F403
import importlib
from pathlib import Path

from datarobot_pulumi_utils.common.feature_flags import check_feature_flags


def import_infra_modules():
    """
    Dynamically import all top-level modules in the infra package.
    This function is executed after the initial import from __init__.
    """
    infra_dir = Path(__file__).parent / "infra"
    # Get all Python files in the infra directory
    for file_path in infra_dir.glob("*.py"):
        filename = file_path.name
        if filename == "__init__.py" or filename == "__main__.py":
            continue
        module_name = f"infra.{filename[:-3]}"
        # Import the module
        module = importlib.import_module(module_name)

        # Import all from the module to the current namespace
        for attr in dir(module):
            if attr.startswith("_"):  # Skip private attributes
                continue
            globals()[attr] = getattr(module, attr)


def check_all_feature_flags():
    """
    Discover and check all feature flag files in the infra directory.

    See the README.md in the `feature_flags` folder for more detail and example
    feature flag file examples.
    """
    infra_dir = Path(__file__).parent / "feature_flags"
    for feature_flag_file in infra_dir.glob("*.y*ml"):
        if feature_flag_file.is_file():
            check_feature_flags(feature_flag_file)


# Validate all feature flags
check_all_feature_flags()

# Execute the function to import all modules after the initial import
import_infra_modules()
