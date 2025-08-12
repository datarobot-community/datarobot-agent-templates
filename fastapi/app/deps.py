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
import logging

logger = logging.getLogger(__name__)


@dataclass
class Deps:
    config: Config


@asynccontextmanager
async def create_deps(
    config: Config, deps: Deps | None = None
) -> AsyncGenerator[Deps, None]:
    """
    Create a dependency context for the application (with both startup and shutdown routines).
    Dependencies are basically singletons that are shared on the application server level.
    """
    if deps:
        # this is used for testing when dependencies are given for us
        yield deps
        return

    # startup routine
    
    yield Deps(
        config=config,
        db=db,
        user_repo=UserRepository(db),
        identity_repo=identity_repo,
        knowledge_base_repo=KnowledgeBaseRepository(db),
        file_repo=FileRepository(db),
        chat_repo=ChatRepository(db),
        message_repo=MessageRepository(db),
        api_key_validator=api_key_validator,
        auth=oauth,
        tokens=Tokens(oauth, identity_repo),
        upload_path=upload_path,
    )

    # shutdown routine
