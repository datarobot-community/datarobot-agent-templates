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
from pathlib import Path
from typing import Any

from datarobot_genai.nat.agent import NatAgent


class MyAgent(NatAgent):
    """MyAgent is a custom agent that uses NVIDIA NeMo Agent Toolkit and can be used for creating
    a custom agentic flow defined in workflow.yaml. It utilizes DataRobot's LLM Gateway or a
    specific deployment for language model interactions. This example illustrates 3 agents that
    handle content creation tasks, including planning, writing, and editing blog posts.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        model: str | None = None,
        verbose: bool | str | None = True,
        timeout: int | None = 90,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            workflow_path=Path(__file__).parent / "workflow.yaml",
            api_key=api_key,
            api_base=api_base,
            model=model,
            verbose=verbose,
            timeout=timeout,
            **kwargs,
        )
