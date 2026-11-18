#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile


HERE = Path(__file__).resolve().parent
RUNTIME = HERE / "run-worker.sh"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="mira-worker-runtime-") as td:
        root = Path(td)
        runner_temp = root / "runner-temp"
        worker_root = runner_temp / "mira-worker"
        bin_dir = root / "bin"
        workspace = root / "workspace"
        runner_temp.mkdir()
        worker_root.mkdir()
        bin_dir.mkdir()
        workspace.mkdir()

        (worker_root / "provider-route.json").write_text(json.dumps({
            "provider": "opencode-go",
            "model": "fixture-model",
            "model_route": "opencode-go/fixture-model",
            "provider_config": {},
        }))
        (worker_root / "issue.json").write_text(json.dumps({
            "number": 85,
            "title": "AGT-068 runtime fixture",
            "body": "Continue the same Candidate from trusted repair evidence.",
        }))
        (worker_root / "maintainer-comments.json").write_text(json.dumps([{
            "id": 7,
            "author": "maintainer",
            "created_at": "2026-11-18T00:00:00Z",
            "body": "Scope change: preserve the correct part.",
        }]))
        (worker_root / "org-AGENTS.md").write_text("fixture organization policy\n")
        context = worker_root / "repair-context.json"
        context.write_text(json.dumps({
            "schema_version": 1,
            "state": "RETURNED",
            "repair_round": 1,
            "validation": {
                "result": "REPAIR",
                "failed_check": "unit",
            },
            "marker": "TRUSTED_REPAIR_CONTEXT_MARKER",
        }))
        (workspace / "AGENTS.md").write_text("fixture repository instructions\n")

        captured_prompt = root / "captured-prompt.txt"
        fake_opencode = bin_dir / "opencode"
        fake_opencode.write_text("""#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
if args[:2] == ["session", "list"]:
    print("[]")
    raise SystemExit(0)
if args and args[0] == "run":
    Path(os.environ["FAKE_PROMPT_CAPTURE"]).write_text(args[-1])
    print("fixture worker output")
    raise SystemExit(0)
print("unexpected fake opencode invocation: " + repr(args), file=sys.stderr)
raise SystemExit(2)
""")
        fake_opencode.chmod(0o755)

        fake_secret = "fixture-provider-secret-must-not-persist"
        env = dict(os.environ)
        env.update({
            "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
            "RUNNER_TEMP": str(runner_temp),
            "FREE_MODE": "false",
            "PROVIDER": "opencode-go",
            "MODEL_ROUTE": "opencode-go/fixture-model",
            "OPENCODE_GO_API_KEY": fake_secret,
            "PROVIDER_API_KEY": "",
            "GITHUB_REPOSITORY": "uichat-mira/runtime-fixture",
            "ISSUE_NUMBER": "85",
            "BASE_BRANCH": "dev",
            "BASE_SHA": "a" * 40,
            "SOFT_BUDGET_MINUTES": "60",
            "WORKER_CONTEXT_FILE": str(context),
            "FAKE_PROMPT_CAPTURE": str(captured_prompt),
            "OPENCODE_DISABLE_AUTOUPDATE": "1",
            "OPENCODE_DISABLE_DEFAULT_PLUGINS": "1",
            "OPENCODE_DISABLE_LSP_DOWNLOAD": "1",
            "OPENCODE_DISABLE_MODELS_FETCH": "1",
            "NO_COLOR": "1",
        })

        proc = subprocess.run(
            ["bash", str(RUNTIME)],
            cwd=workspace,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(
                f"shared Worker runtime returned {proc.returncode}\n"
                f"stdout={proc.stdout}\nstderr={proc.stderr}"
            )

        prompt = captured_prompt.read_text()
        assert "WORKER_CONTINUATION_CONTEXT" in prompt
        assert "TRUSTED_REPAIR_CONTEXT_MARKER" in prompt
        assert "Scope change: preserve the correct part." in prompt
        assert "fixture organization policy" in prompt
        assert "Advisory work budget: 60 minutes" in prompt

        worker_output = (worker_root / "worker-output.txt").read_text()
        assert "fixture worker output" in worker_output
        summary = json.loads((worker_root / "session-summary.json").read_text())
        assert summary["available"] is False
        assert summary["reason"] == "session_id_unresolved"

        # Provider credentials must remain process-local and never be serialized
        # into prompt/output/session evidence.
        persisted = []
        for path in worker_root.rglob("*"):
            if path.is_file():
                persisted.append(path.read_bytes())
        persisted.append(captured_prompt.read_bytes())
        assert all(fake_secret.encode() not in data for data in persisted)

        print("PASS shared Worker runtime: continuation context reaches OpenCode prompt")
        print("PASS shared Worker runtime: provider credential is not persisted")


if __name__ == "__main__":
    main()
