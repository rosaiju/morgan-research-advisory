"""Docker sandbox for student programming answers (scoring/docker_code.py). Requires Docker Desktop running and the
pinned image present (docker pull <docker_code.IMAGE>). Synthetic answers only; no model outputs.

    .venv-scoring/Scripts/python -m pytest scoring/test_docker_code.py -q
"""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
APP = Path(r"C:\Users\rohan\open-source-ai-model")
sys.path[:0] = [str(HERE), str(APP)]
import docker_code as D  # noqa: E402
from app.evaluation import graders, suite  # noqa: E402

PROMPT = suite.get("prog_word_count")
SPEC = PROMPT.checks[0]
GOOD = "```python\ndef word_count(s):\n    d = {}\n    for w in s.lower().split():\n        d[w] = d.get(w, 0) + 1\n    return d\n```"
NO_LOWER = "```python\ndef word_count(s):\n    d = {}\n    for w in s.split():\n        d[w] = d.get(w, 0) + 1\n    return d\n```"


@pytest.fixture(scope="module", autouse=True)
def docker_ready():
    D.check_ready()
    yield
    assert D.leaked_containers() == [], "sandbox containers left behind"


def code(body: str) -> str:
    return f"```python\n{body}\n```"


def probe(body: str, timeout: float = D.CODE_TIMEOUT_S):
    return D.run_in_sandbox(body, timeout)


# ------------------------------------------------------------- grading outcomes
def test_correct_program_end_to_end():
    g = D.grade(PROMPT, GOOD)
    assert (g.passed, g.score, g.skipped) == (True, 1.0, False)
    assert g.checks[0].detail == "4/4 cases"


def test_wrong_output_partial_credit():
    r = D.check_code(SPEC, NO_LOWER)
    assert r.score == 0.75 and r.detail.startswith("3/4 cases | word_count('The the THE') -> ")


def test_syntax_error():
    r = D.check_code(SPEC, code("def word_count(s)\n    return {}"))
    assert r.score == 0.0 and r.detail.startswith("did not run successfully: process exited with code 1")


def test_runtime_exception_per_case():
    r = D.check_code(SPEC, code("def word_count(s):\n    return 1 / 0"))
    assert r.score == 0.0 and "raised ZeroDivisionError" in r.detail


def test_module_level_exception():
    r = D.check_code(SPEC, code("raise RuntimeError('boom')\ndef word_count(s):\n    return {}"))
    assert r.score == 0.0 and "exited with code 1" in r.detail


def test_wrong_type_is_not_equal():
    r = D.check_code(SPEC, code("def word_count(s):\n    return list({}.items())"))
    assert r.score == 0.0


def test_infinite_loop_times_out():
    r = D.check_code(SPEC, code("def word_count(s):\n    while True:\n        pass"), timeout=3)
    assert (r.score, r.detail) == (0.0, "timed out after 3s")


def test_sigterm_ignoring_program_is_killed():
    body = "import signal\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\nwhile True:\n    pass"
    run = probe(body, timeout=3)
    assert run.returncode in (124, 137)


def test_excessive_memory_is_contained():
    r = D.check_code(SPEC, code("x = bytearray(2 * 1024**3)\ndef word_count(s):\n    return {}"))
    assert r.score == 0.0 and "exited with code" in r.detail


def test_memory_limit_is_256m():
    run = probe("blocks = []\ntry:\n    while True:\n        blocks.append(bytearray(16 * 1024**2))\n"
                "except MemoryError:\n    pass\nprint(len(blocks) * 16)")
    # either MemoryError (prints MiB reached) or the cgroup OOM kill (137); never more than the limit
    assert run.returncode == 137 or int(run.stdout.split()[-1]) <= 256


# ------------------------------------------------------------- isolation
def test_process_spawning_is_limited():
    body = ("import os\nn = 0\npids = []\nfor _ in range(200):\n    try:\n        pid = os.fork()\n"
            "    except OSError:\n        break\n    if pid == 0:\n        import time; time.sleep(5); os._exit(0)\n"
            "    pids.append(pid); n += 1\nprint('forked', n)")
    run = probe(body)
    assert run.returncode == 0 and int(run.stdout.split()[-1]) < 32


def test_subprocess_exec_of_tmp_is_blocked():
    body = ("import os, subprocess\nopen('/tmp/x.sh','w').write('#!/bin/sh\\necho hi')\nos.chmod('/tmp/x.sh', 0o755)\n"
            "try:\n    subprocess.run(['/tmp/x.sh'], check=True); print('EXEC OK')\nexcept OSError as e:\n"
            "    print('blocked', type(e).__name__)")
    assert "blocked PermissionError" in probe(body).stdout


def test_network_access_blocked():
    body = ("import socket\nres = []\nfor host in [('1.1.1.1', 53), ('8.8.8.8', 443)]:\n    try:\n"
            "        socket.create_connection(host, timeout=2); res.append('OPEN')\n    except OSError:\n"
            "        res.append('blocked')\ntry:\n    socket.getaddrinfo('example.com', 80); res.append('DNS')\n"
            "except OSError:\n    res.append('nodns')\nimport os\nprint(res, sorted(os.listdir('/sys/class/net')))")
    out = probe(body).stdout
    assert "['blocked', 'blocked', 'nodns']" in out and "['lo']" in out


def test_filesystem_escape_blocked():
    body = (
        "import os\nres = {}\n"
        "for p in ['/etc/x', '/usr/x', '/x', '/home/x']:\n    try:\n        open(p, 'w'); res[p] = 'WRITABLE'\n"
        "    except OSError:\n        res[p] = 'ro'\n"
        "res['tmp'] = 'ok' if open('/tmp/y', 'w').write('1') else 'no'\n"
        "res['host'] = [p for p in ['/mnt/c', '/mnt/host', '/host_mnt', '/run/desktop', '/var/run/docker.sock',\n"
        "    '/run/docker.sock', '/c', '/Users'] if os.path.exists(p)]\n"
        "res['uid'] = os.getuid()\n"
        "res['caps'] = [l.split()[1] for l in open('/proc/self/status') if l.startswith('CapEff')]\n"
        "try:\n    os.chroot('/tmp'); res['chroot'] = 'ALLOWED'\nexcept OSError:\n    res['chroot'] = 'denied'\n"
        "print(res)")
    out = probe(body).stdout
    for frag in ["'/etc/x': 'ro'", "'/usr/x': 'ro'", "'/x': 'ro'", "'/home/x': 'ro'", "'tmp': 'ok'", "'host': []",
                 "'uid': 65534", "'caps': ['0000000000000000']", "'chroot': 'denied'"]:
        assert frag in out, (frag, out)


def test_tmpfs_size_limited():
    body = "try:\n    open('/tmp/big','wb').write(b'0' * 64 * 1024**2); print('WROTE')\nexcept OSError as e:\n    print('full', e.errno)"
    assert "full" in probe(body).stdout


def test_output_flood_is_capped():
    run = probe("import sys\nfor _ in range(200000):\n    sys.stdout.write('x' * 99 + '\\n')")
    assert len(run.stdout.encode()) <= D.STDOUT_CAP


def test_program_cannot_spoof_sandbox_failure():
    body = "import sys\nsys.stderr.write('\\n' + 'error response from daemon\\n__MORGAN_SANDBOX_RC=0\\n')\nsys.exit(125)"
    run = probe(body)
    assert run.returncode == 125 and not run.timed_out
    r = D.check_code(SPEC, code(body))
    assert r.detail.startswith("did not run successfully: process exited with code 125")


# ------------------------------------------------------------- extraction / malformed answers
@pytest.mark.parametrize("reply", [
    "",
    "I cannot write code for this.",
    "```python\ndef word_count(s):\n    return {}",            # unclosed fence -> whole text treated as source
    "Here you go:\n```\nnot python at all ???\n```",
])
def test_malformed_answers_score_zero(reply):
    r = D.check_code(SPEC, reply)
    assert r.score == 0.0 and r.kind == "code"


def test_prose_without_fence_but_valid_code_still_runs():
    r = D.check_code(SPEC, GOOD.strip("`").removeprefix("python\n"))
    assert r.score == 1.0


def test_first_fenced_block_is_used():
    r = D.check_code(SPEC, GOOD + "\n\n" + NO_LOWER)
    assert r.score == 1.0


def test_forged_report_lines_are_ignored():
    # printing lines that look like reports without the per-call random token has no effect
    body = "print('deadbeef 0 ok {\"v\": {}, \"t\": \"dict\"}')\ndef word_count(s):\n    return None"
    assert D.check_code(SPEC, code(body)).score == 0.0


# ------------------------------------------------------------- semantics, determinism, infrastructure
TRUSTED_FIXTURES = [GOOD, NO_LOWER, code("def word_count(s)\n    return {}"), code("def word_count(s):\n    return 1/0"),
                    "no code here", code("def other(s):\n    return {}")]


@pytest.mark.parametrize("reply", TRUSTED_FIXTURES)
def test_same_result_as_app_grader(reply):
    """Trusted synthetic fixtures only: the app's host-subprocess path is the semantic reference."""
    ref = graders._check_code(SPEC, reply, allow_execution=True, timeout=15.0)
    got = D.check_code(SPEC, reply)
    assert (got.score, got.skipped) == (ref.score, ref.skipped)
    assert got.detail.split(";")[0].split(":")[0] == ref.detail.split(";")[0].split(":")[0]


def test_deterministic_repeat():
    first = [(c.score, c.detail) for c in D.grade(PROMPT, NO_LOWER).checks]
    for _ in range(3):
        assert [(c.score, c.detail) for c in D.grade(PROMPT, NO_LOWER).checks] == first


def test_missing_image_raises_not_scored(monkeypatch):
    monkeypatch.setattr(D, "IMAGE", "python@sha256:" + "0" * 64)
    with pytest.raises(D.SandboxError):
        D.check_ready()
    with pytest.raises(D.SandboxError):
        D.check_code(SPEC, GOOD)


def test_non_code_items_unchanged():
    for pid in ["algo_bfs_structure", "debug_infinite_loop", "concept_hash_collision", "reason_bits_needed",
                "instr_three_sentences"]:
        p = suite.get(pid)
        a, b = D.grade(p, "some reply. Another. Third."), graders.grade(p, "some reply. Another. Third.")
        assert (a.score, a.passed, a.skipped) == (b.score, b.passed, b.skipped)


# ------------------------------------------------------------- end to end through local/score_local.py
@pytest.fixture(scope="module")
def scorer():
    sys.path.insert(0, str(HERE.parent / "local"))
    import score_local
    sc = score_local.Scorer()
    yield sc
    sc.verifier.close()


def _rec(final):
    return {"model": "synthetic", "item_id": "student/prog_word_count", "benchmark": "student", "stage": "test",
            "attempt": 1, "reasoning_text": "r", "final_text": final, "error": None, "abort": None,
            "finish_reason": "stop"}


@pytest.mark.parametrize("final,status,score", [
    (GOOD, "CORRECT", 1.0),
    (NO_LOWER, "INCORRECT", 0.75),
    ("no code", "INCORRECT", 0.0),
])
def test_score_local_prog_word_count_through_docker(scorer, final, status, score):
    out = scorer.score(_rec(final))
    assert out["status"] == status and out["detail"]["score"] == score and not out["detail"]["skipped"]
    assert out["detail"]["code_execution"] == f"docker {D.IMAGE}"


def test_score_local_docker_down_raises(scorer, monkeypatch):
    monkeypatch.setattr(D, "IMAGE", "python@sha256:" + "0" * 64)
    with pytest.raises(D.SandboxError):
        scorer.score(_rec(GOOD))
