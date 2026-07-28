import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mia.__main__ import _try_direct_tool_call
from mia.actions import files
from mia.actions.executor import setup_executor
from mia.actions.shell import run_powershell
from mia.core.agent import Agent
from mia.llm.base import LLMResponse, ToolCall
from mia.llm.router import LLMRouter
from mia import server


class FakeRouter:
    def __init__(self, responses, mode="local", model_name="Mock"):
        self.responses = list(responses)
        self.mode = mode
        self.messages_seen = []

    def get_model_name(self):
        return "Mock"

    def chat(self, messages, tools=None):
        self.messages_seen.append(messages)
        return self.responses.pop(0)

    def set_mode(self, mode):
        self.mode = mode


class FakeCloudRouter(FakeRouter):
    def __init__(self):
        super().__init__([LLMResponse(text="ok")], mode="cloud")

    def get_model_name(self):
        return "Gemini (gemini-2.0-flash)"


class FakeA11y:
    def __init__(self, title):
        self.title = title

    def get_active_window_tree(self):
        return {
            "title": self.title,
            "type": "Window",
            "elements": [{"name": "password", "type": "Edit", "value": "secret"}],
        }


class FailingScreen:
    def capture_active_monitor(self):
        raise AssertionError("screen capture should have been blocked")


class LocalClient:
    model_name = "local"

    def chat(self, messages, tools=None):
        return LLMResponse(text="local")


class UnconfiguredCloudClient:
    model_name = "cloud"
    client = None

    def chat(self, messages, tools=None):
        raise AssertionError("auto mode should not call an unconfigured cloud client")


class FakeAgent:
    def __init__(self):
        self.executor = setup_executor()


class CoreBehaviorTests(unittest.TestCase):
    def test_executor_exposes_readme_tool_count(self):
        executor = setup_executor()
        expected = {
            "launch_app",
            "open_url",
            "focus_window",
            "type_text",
            "hotkey",
            "click_element",
            "web_search",
            "read_webpage",
            "list_directory",
            "read_file",
            "write_file",
            "create_directory",
            "activate_workflow",
            "list_workflows",
            "run_powershell",
            "wait",
            "respond",
        }
        self.assertEqual(set(executor.list_tools()), expected)

    def test_direct_cli_tool_call_supports_positional_args(self):
        agent = FakeAgent()
        result = _try_direct_tool_call(agent, "respond The tool path works")
        self.assertEqual(result, "The tool path works")

    def test_direct_cli_tool_call_supports_json_args(self):
        agent = FakeAgent()
        result = _try_direct_tool_call(agent, 'respond {"text": "JSON works"}')
        self.assertEqual(result, "JSON works")

    def test_file_sandbox_blocks_prefix_sibling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            allowed = root / "allowed"
            sibling = root / "allowed_evil"
            allowed.mkdir()
            sibling.mkdir()
            target = sibling / "secret.txt"
            target.write_text("nope", encoding="utf-8")

            original = files._ALLOWED_DIRS
            try:
                files._ALLOWED_DIRS = [str(allowed)]
                self.assertFalse(files._is_path_allowed(str(target)))
            finally:
                files._ALLOWED_DIRS = original

    def test_powershell_blocks_command_chaining_and_prefix_spoofing(self):
        self.assertIn("command chaining is not allowed", run_powershell("echo ok; whoami"))
        self.assertIn("blocked by safety policy", run_powershell("Get-Contentevil README.md"))

    def test_agent_preserves_respond_if_followup_model_call_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = Agent({"database": {"path": str(Path(tmp) / "mia.db")}})
            try:
                agent.screen = None
                agent.a11y = None
                agent.router = FakeRouter([
                    LLMResponse(tool_calls=[
                        ToolCall(id="1", name="respond", arguments={"text": "Opening Spotify now."}),
                        ToolCall(id="2", name="launch_app", arguments={"name": "spotify"}),
                    ]),
                    LLMResponse(text="[Ollama error] Failed to connect to Ollama"),
                ])
                agent.executor.execute = lambda name, args: "Success"

                self.assertEqual(agent.process("open spotify"), "Opening Spotify now.")
            finally:
                agent.db.close()

    def test_cloud_mode_blocks_sensitive_screen_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = Agent({"database": {"path": str(Path(tmp) / "mia.db")}})
            try:
                agent.router = FakeCloudRouter()
                agent.a11y = FakeA11y("Bitwarden")
                agent.screen = FailingScreen()
                agent.redactor.blocklist = ["Bitwarden"]

                self.assertEqual(agent.process("what is on screen?"), "ok")
                current_message = agent.router.messages_seen[0][-1]
                self.assertIsInstance(current_message["content"], str)
                self.assertIn("Screen context blocked", current_message["content"])
                self.assertNotIn("secret", current_message["content"])
            finally:
                agent.db.close()

    def test_auto_router_skips_unconfigured_cloud_client(self):
        router = LLMRouter({"llm": {"mode": "auto"}})
        router.local_client = LocalClient()
        router.cloud_client = UnconfiguredCloudClient()

        response = router.chat([
            {"role": "user", "content": [
                {"type": "text", "text": "look"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}},
            ]}
        ])

        self.assertEqual(response.text, "local")

    def test_screen_endpoint_blocks_sensitive_window(self):
        previous = server.MiaBackend._instance

        class Backend:
            def __init__(self):
                self.agent = type("AgentLike", (), {})()
                self.agent.screen = FailingScreen()
                self.agent.a11y = FakeA11y("Bitwarden")
                self.agent.redactor = type(
                    "RedactorLike",
                    (),
                    {"is_sensitive": staticmethod(lambda title: "Bitwarden" in title)},
                )()

        try:
            server.MiaBackend._instance = Backend()
            result = server.get_screen()
            self.assertTrue(result["blocked"])
            self.assertIsNone(result["image"])
        finally:
            server.MiaBackend._instance = previous


if __name__ == "__main__":
    unittest.main()
