"""Docker-sandboxed execution of student programming answers (replaces the host-subprocess `code` check).

The app grader (open-source-ai-model app/evaluation/graders.py `_check_code`) runs model-written code in a bare
`python -I` subprocess on the host; its own docstring says that is not a sandbox. Stage 1 must never run untrusted
model output on the Windows host, so `score_local.py` grades `code` checks here instead. Grading semantics are kept
identical to `_check_code`: same fence stripping, same per-case token-tagged harness appended to the source, same
report parsing, same partial credit and the same detail strings. Only *where* the program runs differs.

Sandbox (see SANDBOX below; every value is part of the Stage 1 freeze):
  - image pinned by digest (python:3.14-slim, the scorer venv's minor version); never pulled implicitly
  - no network (--network none), no host mounts at all, no Docker socket; the program arrives on stdin
  - read-only root filesystem; writable paths are two small tmpfs mounts only: /tmp (16 MiB, the program's scratch)
    and /out (4 MiB, captured output); both noexec, nosuid, nodev
  - unprivileged user 65534 (nobody), all capabilities dropped, no-new-privileges, private IPC
  - memory 256 MiB with no swap, 1 CPU, 32 PIDs, 64 open files
  - wall clock: `timeout` inside the container (same limit as the app's code_timeout, 15 s; TERM, then KILL after
    2 s) plus a host-side backstop (+60 s) that force-removes the container and raises SandboxError
  - stdout/stderr are capped (1 MiB / 64 KiB) before they reach the host. Difference from the host path: a program
    printing more than 4 MiB fails with a write error (graded 0) instead of having all output captured.
Infrastructure failures (daemon down, image missing) raise SandboxError; they are never scored as a wrong answer.
"""
from __future__ import annotations

import ast
import json
import shutil
import subprocess
import uuid
from dataclasses import dataclass

IMAGE = "python@sha256:0741d101873c12ab927e6f8653feb8862b9bd58771177acb1b885b95141f91b4"  # python:3.14-slim, linux/amd64
IMAGE_TAG = "python:3.14-slim"
LABEL = "morgan.grader=code"
CODE_TIMEOUT_S = 15.0          # app graders.grade() default code_timeout
HOST_BACKSTOP_S = 60.0         # container start/stop overhead on top of CODE_TIMEOUT_S
STDOUT_CAP = 1 << 20           # bytes returned to the host
STDERR_CAP = 1 << 16
SANDBOX = [
    "--network", "none",
    "--read-only",
    "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777",
    "--tmpfs", "/out:rw,noexec,nosuid,nodev,size=4m,mode=1777",   # captured stdout/stderr, separate from /tmp
    "--workdir", "/tmp",
    "--user", "65534:65534",
    "--cap-drop", "ALL",
    "--security-opt", "no-new-privileges",
    "--ipc", "none",
    "--memory", "256m", "--memory-swap", "256m",
    "--cpus", "1",
    "--pids-limit", "32",
    "--ulimit", "nofile=64:64",
    "--ulimit", "nproc=32:32",
    "--env", "PYTHONDONTWRITEBYTECODE=1",
    "--pull", "never",
]
# Inside the container: run the program from stdin with a TERM-then-KILL timeout (exit 124 = timed out), write
# output to the size-limited tmpfs, then return only capped prefixes. The program's own exit status is preserved.
# The last stderr line is a sentinel carrying the program's status; its absence means the sandbox itself failed
# (candidate code cannot fake it, because the sentinel is always written after the program's output).
_SENTINEL = "__MORGAN_SANDBOX_RC="
_INNER = (
    "timeout -k 2 {t} python -I - >/out/o 2>/out/e; rc=$?; "
    "head -c {oc} /out/o; head -c {ec} /out/e >&2; printf '\\n%s%s\\n' '" + _SENTINEL + "' \"$rc\" >&2; exit 0"
)


class SandboxError(RuntimeError):
    """The sandbox itself failed (not the candidate program). Scoring must stop, not record a wrong answer."""


@dataclass
class _Run:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool


def docker_exe() -> str:
    exe = shutil.which("docker")
    if not exe:
        raise SandboxError("docker executable not found on PATH")
    return exe


def check_ready() -> str:
    """Raise SandboxError unless the daemon is up and the pinned image is present locally. Returns a summary."""
    exe = docker_exe()
    p = subprocess.run([exe, "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"],
                       capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise SandboxError(f"pinned image not available ({IMAGE_TAG}): {(p.stderr or p.stdout).strip()[:200]} "
                           f"-- run: docker pull {IMAGE}")
    return p.stdout.strip()


def run_in_sandbox(source: str, timeout: float = CODE_TIMEOUT_S) -> _Run:
    exe = docker_exe()
    name = f"morgan-grade-{uuid.uuid4().hex[:16]}"
    inner = _INNER.format(t=f"{timeout:g}", oc=STDOUT_CAP, ec=STDERR_CAP)
    cmd = [exe, "run", "--rm", "-i", "--name", name, "--label", LABEL, *SANDBOX, IMAGE, "sh", "-c", inner]
    try:
        p = subprocess.run(cmd, input=source.encode("utf-8"), capture_output=True, timeout=timeout + HOST_BACKSTOP_S)
    except subprocess.TimeoutExpired:
        # the in-container timeout always fires first; reaching the backstop means Docker itself hung
        subprocess.run([exe, "rm", "-f", name], capture_output=True, timeout=60)
        raise SandboxError(f"sandbox did not finish within {timeout + HOST_BACKSTOP_S:g}s (container removed)")
    out = p.stdout[:STDOUT_CAP].decode("utf-8", "replace")
    err = p.stderr.decode("utf-8", "replace")
    lines = err.rstrip("\n").split("\n")
    if p.returncode != 0 or not lines[-1].startswith(_SENTINEL):
        raise SandboxError(f"docker run failed (exit {p.returncode}): {err.strip()[-300:]}")
    rc = int(lines[-1][len(_SENTINEL):])
    err = "\n".join(lines[:-1]).rstrip("\n")[:STDERR_CAP]
    return _Run(rc, out, err, rc == 124)


def strip_code_fences(text: str) -> str:
    import re
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.S)
    return match.group(1) if match else text


def check_code(spec: dict, reply: str, *, timeout: float = CODE_TIMEOUT_S):
    """Same contract and result as graders._check_code(allow_execution=True), executed in the Docker sandbox."""
    from app.evaluation.graders import CheckResult

    source = strip_code_fences(reply)
    function = spec["function"]
    cases = spec["cases"]
    token = uuid.uuid4().hex

    harness_lines = ["", "import json as _json"]
    for i, (expression, _expected) in enumerate(cases):
        harness_lines += [
            "try:",
            f"    _r{i} = {expression}",
            "    print("
            f"        {token!r}, {i}, 'ok',"
            f"        _json.dumps({{'v': _r{i}, 't': type(_r{i}).__name__}}, default=repr),"
            "    )",
            "except Exception as _exc:",
            f"    print({token!r}, {i}, 'error', type(_exc).__name__ + ': ' + str(_exc))",
        ]
    harness = "\n".join(harness_lines)

    completed = run_in_sandbox(source + "\n" + harness, timeout)
    if completed.timed_out:
        return CheckResult("code", 0.0, f"timed out after {timeout:g}s")
    if completed.returncode != 0:
        return CheckResult("code", 0.0, f"did not run successfully: process exited with code {completed.returncode}")

    reports: dict[int, tuple[str, str]] = {}
    prefix = token + " "
    for line in completed.stdout.splitlines():
        if not line.startswith(prefix):
            continue
        parts = line[len(prefix):].split(" ", 2)
        if len(parts) != 3:
            continue
        idx_str, status, payload = parts
        if (not idx_str.isdigit() or int(idx_str) in reports
                or int(idx_str) >= len(cases) or status not in {"ok", "error"}):
            return CheckResult("code", 0.0, "invalid or duplicate case report")
        reports[int(idx_str)] = (status, payload)

    if not reports:
        stderr = (completed.stderr or "").strip().splitlines()
        reason = stderr[-1] if stderr else "no output"
        if function not in source:
            reason = f"no function named {function}(); {reason}"
        return CheckResult("code", 0.0, f"did not run: {reason[:120]}")

    passed = 0
    failures = []
    for i, (expression, expected) in enumerate(cases):
        if i not in reports:
            failures.append(f"{expression} -> no result (process exited early)")
            continue
        status, payload = reports[i]
        if status == "error":
            failures.append(f"{expression} raised {payload}")
            continue
        try:
            got = json.loads(payload)
            want = ast.literal_eval(expected)
        except (ValueError, SyntaxError):
            failures.append(f"{expression} -> could not compare result")
            continue
        if not isinstance(got, dict) or set(got) != {"v", "t"} or not isinstance(got["t"], str):
            failures.append(f"{expression} -> invalid result shape")
            continue
        if got["v"] == want and got["t"] == type(want).__name__:
            passed += 1
        else:
            failures.append(f"{expression} -> {got['v']!r}")

    total = len(cases)
    detail = f"{passed}/{total} cases"
    if failures:
        detail += " | " + "; ".join(failures[:3])
    return CheckResult("code", passed / total if total else 0.0, detail[:300])


def grade(prompt, reply: str):
    """graders.grade() with every `code` check executed in the sandbox; all other checks are the app's own."""
    from app.evaluation import graders

    base = graders.grade(prompt, reply, allow_code_execution=False)
    results = list(base.checks)
    for i, spec in enumerate(prompt.checks):
        if spec["kind"] == "code":
            results[i] = check_code(spec, reply)
    graded = [r for r in results if not r.skipped]
    if not graded:
        return graders.GradeResult(score=0.0, passed=False, checks=results, skipped=True)
    score = sum(r.score for r in graded) / len(graded)
    return graders.GradeResult(score=round(score, 4), passed=all(r.score >= 1.0 for r in graded),
                               checks=results, skipped=False)


def leaked_containers() -> list[str]:
    p = subprocess.run([docker_exe(), "ps", "-aq", "--filter", f"label={LABEL}"], capture_output=True, text=True,
                       timeout=60)
    return p.stdout.split()
