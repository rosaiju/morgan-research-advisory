"""pytest plugin: disable Math-Verify's inner timeout decorator (Windows multiprocessing path).

The study never relies on the inner timeout: scoring/math500_scorer.py runs Math-Verify inside a worker
subprocess with an outer hard timeout (evaluation.json: 'runs in a subprocess with a hard timeout (no
SIGALRM dependency)'). This plugin reproduces that condition for the upstream test suite without
modifying the vendored source.   pytest -p mv_no_inner_timeout ...
"""

import math_verify.grader as grader
import math_verify.parser as parser


def _identity_timeout(timeout_seconds=None):
    def deco(func):
        return func
    return deco


parser.timeout = _identity_timeout
grader.timeout = _identity_timeout
