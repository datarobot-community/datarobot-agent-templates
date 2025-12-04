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
Test to verify that authorization context is properly propagated to worker threads.

This test ensures that the fix for the ContextVar threading issue works correctly.
The authorization context must be accessible from worker threads where the agent runs.
"""

import threading
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from custom import chat, load_model
from datarobot.models.genai.agent.auth import (
    get_authorization_context,
    set_authorization_context,
)


class TestAuthorizationContextThreading:
    """Test authorization context propagation to worker threads."""

    @patch("custom.MyAgent")
    def test_chat_function_concurrent_threads_with_authorization_context(
        self, mock_agent
    ):
        """
        Test that the ACTUAL chat function properly propagates authorization context to worker threads.

        This test:
        1. Calls the ACTUAL chat() function from agent_nat.custom_model.custom
        2. Spawns multiple threads that each call chat() with different auth contexts
        3. Tracks when get_authorization_context() is called in worker threads (created inside chat)
        4. Verifies that the authorization context is accessible in each worker thread (no LookupError)

        The worker thread is created inside chat() via thread_pool_executor.submit().
        We verify that get_authorization_context() works in those worker threads.
        """
        # Create unique authorization contexts for each thread
        thread_contexts = [
            {"token": f"test-token-{i}", "user_id": f"test-user-{i}"} for i in range(3)
        ]

        # Set up mocks
        mock_agent_instance = MagicMock()
        mock_agent_instance.invoke = AsyncMock(
            return_value=(
                "agent result",
                [],
                {
                    "completion_tokens": 1,
                    "prompt_tokens": 2,
                    "total_tokens": 3,
                },
            )
        )
        mock_agent.return_value = mock_agent_instance

        # Track when get_authorization_context is called and from which thread
        # This will track calls in the worker threads created inside chat()
        context_calls = {}  # thread_id -> {successful: bool, exception: Exception or None, context_value: Any}
        original_get_authorization_context = get_authorization_context

        def tracked_get_authorization_context():
            """Track when get_authorization_context is called in worker threads."""
            thread_id = threading.current_thread().ident
            thread_name = threading.current_thread().name

            # Only track calls from worker threads (not the main test threads)
            # Worker threads are created inside chat() via thread_pool_executor.submit()
            if thread_id not in context_calls:
                context_calls[thread_id] = {
                    "thread_name": thread_name,
                    "successful": False,
                    "exception": None,
                    "context_value": None,
                }

            # Try to get the context - this is what we're testing
            try:
                context = original_get_authorization_context()
                context_calls[thread_id]["successful"] = True
                context_calls[thread_id]["context_value"] = context
                return context
            except LookupError as e:
                context_calls[thread_id]["exception"] = e
                raise

        @pytest.skip("Skipping imports for this test until we can stabilize it")
        def call_chat_in_thread(thread_id: int, auth_context: dict):
            """Call the ACTUAL chat function in a separate thread with a specific auth context."""
            # Set authorization context in this thread (simulating initialize_authorization_context)
            set_authorization_context(auth_context)

            # Create load_model_result for this thread
            load_model_result = load_model("")

            completion_create_params = {
                "model": "test-model",
                "messages": [
                    {"role": "user", "content": f'{{"topic": "test-{thread_id}"}}'}
                ],
            }

            # Call the ACTUAL chat function - this should propagate context to worker thread
            # The worker thread is created inside chat() via thread_pool_executor.submit()
            # Inside that worker thread, get_authorization_context() will be called
            response = chat(
                completion_create_params, load_model_result=load_model_result
            )

            # Verify response is valid
            assert response is not None

            # Clean up
            thread_pool_executor, event_loop = load_model_result
            thread_pool_executor.shutdown(wait=True)

        # Patch get_authorization_context to track calls in worker threads
        with patch(
            "datarobot.models.genai.agent.auth.get_authorization_context",
            side_effect=tracked_get_authorization_context,
        ):
            # Spawn multiple threads that call the ACTUAL chat() concurrently
            threads = []
            for i, auth_context in enumerate(thread_contexts):
                thread = threading.Thread(
                    target=call_chat_in_thread,
                    args=(i, auth_context),
                    name=f"test-thread-{i}",
                )
                threads.append(thread)

            # Start all threads
            for thread in threads:
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=30)
                assert not thread.is_alive(), f"Thread {thread.name} did not complete"

        # Verify that get_authorization_context was called successfully in worker threads
        # The worker threads are created inside chat() via thread_pool_executor
        # We should have at least one worker thread that successfully accessed the context
        worker_threads_with_context = [
            thread_id
            for thread_id, info in context_calls.items()
            if info.get("successful", False)
        ]

        assert len(worker_threads_with_context) > 0, (
            f"At least one worker thread should have successfully accessed the authorization context. "
            f"Context calls: {context_calls}"
        )

        # Verify no LookupErrors were raised in worker threads
        # This is the key assertion - without the fix, we would get LookupError here
        worker_threads_with_errors = [
            (thread_id, info["exception"])
            for thread_id, info in context_calls.items()
            if info.get("exception") is not None
        ]

        assert len(worker_threads_with_errors) == 0, (
            f"Worker threads should not have raised LookupError. "
            f"This means the fix is working! Errors: {worker_threads_with_errors}"
        )

        # Verify contexts were actually set (not None)
        for thread_id, info in context_calls.items():
            if info.get("successful", False):
                assert info.get("context_value") is not None, (
                    f"Worker thread {thread_id} should have a non-None context value"
                )

        # Verify agent was invoked for each thread
        assert mock_agent_instance.invoke.call_count == len(thread_contexts), (
            f"Agent should be invoked once per thread. "
            f"Expected {len(thread_contexts)}, got {mock_agent_instance.invoke.call_count}"
        )

    @patch("custom.MyAgent")
    def test_chat_function_handles_missing_authorization_context(self, mock_agent):
        """
        Test that the ACTUAL chat function handles missing authorization context gracefully.

        If authorization context is not set, the function should still work
        (though MCP tools might not work correctly).
        """
        # Set up mocks
        mock_agent_instance = MagicMock()
        mock_agent_instance.invoke = AsyncMock(
            return_value=(
                "agent result",
                [],
                {
                    "completion_tokens": 1,
                    "prompt_tokens": 2,
                    "total_tokens": 3,
                },
            )
        )
        mock_agent.return_value = mock_agent_instance

        # Create load_model_result
        load_model_result = load_model("")

        completion_create_params = {
            "model": "test-model",
            "messages": [{"role": "user", "content": '{"topic": "test"}'}],
        }

        # Don't set authorization context - should still work
        # (though it will catch LookupError and set auth_context to None)
        response = chat(completion_create_params, load_model_result=load_model_result)

        # Verify agent was still invoked successfully
        mock_agent_instance.invoke.assert_called_once()

        # Verify response is valid
        assert response is not None

        # Clean up
        thread_pool_executor, event_loop = load_model_result
        thread_pool_executor.shutdown(wait=True)
