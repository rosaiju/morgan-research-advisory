"""pytest plugin / import hook: make IFEval's language checks deterministic.

The official evaluator calls langdetect.detect() unseeded (instructions.py L158, L1416, L1448); langdetect
is randomised, so 'language:response_language', 'change_case:english_capital' and
'change_case:english_lowercase' verdicts can flip between runs (observed: 1 of 10 calls returned 'de' for
an all-caps English sentence). The study fixes DetectorFactory.seed = 0 (disclosed deviation; the
evaluator code itself is unchanged).
"""
import langdetect

langdetect.DetectorFactory.seed = 0
