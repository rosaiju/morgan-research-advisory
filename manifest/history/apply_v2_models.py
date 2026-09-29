"""One-off, recorded transformation: models.json v1 -> v2 (P24 -> P35). v1 is archived beside this file."""
import json
from pathlib import Path

M = Path(__file__).resolve().parents[1] / "models.json"
m = json.loads(M.read_text(encoding="utf-8"))
assert m["schema"] == "morgan-capability-models/1", "already applied"
p24 = next(x for x in m["models"] if x["id"] == "P24")
m["models"] = [x for x in m["models"] if x["id"] != "P24"]
m["schema"] = "morgan-capability-models/2"
m["status"] = "PROPOSED v2 (set tentatively accepted by the user 2026-09-29) - not executed; no inference, loading, weight or tokenizer-vocabulary download has occurred"
m["version_history"] = [
    {"version": 1, "date": "2026-09-29", "set": ["P24", "P25", "P27", "P28", "P29", "P34"],
     "archived_copy": "manifest/history/2026-09-29_v1_pre-MiMo/models.json"},
    {"version": 2, "date": "2026-09-29", "set": ["P35", "P25", "P27", "P28", "P29", "P34"],
     "change": "P24 DeepSeek-V4.1-Flash replaced by P35 MiMo-V2.6-Pro (doc 18; tentative user acceptance); hosted routes in runner/routes.json; transformation script manifest/history/apply_v2_models.py"},
]
m["common_study_settings"]["output_ceiling_tokens"] = {
    "value": None, "status": "pending",
    "rule": "v2: development calibration at C_dev = 131072, then the pre-registered ladder rule in evaluation.json budget_policy; calibrated=false"}
m["common_study_settings"]["execution"] = "hosted APIs or a dedicated deployment per runner/routes.json; the route is part of the configuration and is reported with every result"

p35 = {
    "id": "P35",
    "repository": "XiaomiMiMo/MiMo-V2.6-Pro-RL",
    "revision": "73875d00b30a89ef8cc353a0b60b0e9f9561952d",
    "source": "manifest/XiaomiMiMo--MiMo-V2.6-Pro-RL/ (hashes in source-lock.json); sibling MOPD checkpoint archived at manifest/XiaomiMiMo--MiMo-V2.6-Pro-MOPD/ (adea8e2c)",
    "checkpoint_choice": {"value": "RL checkpoint", "status": "proposed",
        "rationale": "the independent evidence used for selection (Artificial Analysis v4.3.2) links the RL checkpoint; MOPD (2026-09-27) targets agentic tool-call repetition. config.json, generation_config.json, chat_template.jinja, tokenizer_config.json and configuration_mimo_v2.py are byte-identical between RL and MOPD, so the two differ only in weights."},
    "hosted_identity": {"status": "pending",
        "value": "P35-deepinfra states MiMo-V2.6-Pro-RL (revision unconfirmed). The Xiaomi API model mimo-v2.6-pro cannot be tied to RL or MOPD (both model cards list the Xiaomi API; no snapshot ids; no system_fingerprint) and is therefore a DISTINCT hosted configuration 'H-MiMo-Xiaomi', never labelled as either released checkpoint.",
        "evidence": "19-readiness-and-calibration-plan.md section 1; runner/routes.json"},
    "interface": {"status": "verified", "evidence": "XiaomiMiMo--MiMo-V2.6-Pro-RL/chat_template.jinja",
        "value": "pinned chat_template.jinja: one boolean enable_thinking (thinking unless explicitly false); no effort or budget variable; reasoning inside <think>...</think>; turns end with <|im_end|>; no system prompt injected unless tools are passed"},
    "reasoning_effort": {"value": "thinking enabled (enable_thinking=true) = the native maximum; no effort levels exist", "status": "verified"},
    "sampling": {"value": {"do_sample": True, "temperature": 1.0, "top_p": 0.95, "top_k": "not set", "repetition_penalty": 1.0},
        "status": "proposed",
        "evidence": "README: recommended temperature=1.0, top_p=0.95. HAZARD: generation_config.json sets do_sample=false and max_new_tokens=2048 (greedy decoding and 2,048-token truncation if inherited); overridden explicitly. The Xiaomi API forces 1.0/0.95 in thinking mode."},
    "publisher_output_recommendation": {"value": "none published for no-tools reasoning; the Xiaomi API allows up to 131,072 generated tokens including reasoning", "status": "verified"},
    "context_limit": {"value": 1048576, "status": "verified", "evidence": "config.json max_position_embeddings 1048576; rope_type default (no YaRN)"},
    "stop_and_parse": {"status": "verified",
        "value": "EOS [151643, 151645, 151672] (generation_config); config eos 151645 '<|im_end|>'; vLLM/SGLang reasoning parser 'mimo'. Hosted routes return reasoning_content separately."},
    "precision_identity": {"status": "verified",
        "value": "quantization_config: quant_method fp8, fmt e4m3, store_dtype mxfp4, block 128x128 (stored MXFP4, computed FP8). HF dtype totals: U8 ~1.0T (packed), F8_E4M3 13.4B, BF16 10.6B. The ~524B figure shown on Hugging Face counts packed bytes; it is not a smaller model."},
    "modality": {"value": "omnimodal checkpoint; the study is text-only", "status": "verified"},
    "hosted_route": "P35-deepinfra (recommended, conditional) | P35-xiaomi (distinct configuration H-MiMo-Xiaomi)",
    "integration_gates": ["provider confirms served checkpoint, revision and precision (P35-deepinfra), otherwise results carry the H-MiMo-Xiaomi label",
                          "thinking enabled and reasoning returned separately", "sampling not inherited from generation_config",
                          "integration tests T1, T2, T3a pass"],
}
m["models"].insert(0, p35)

for x in m["models"]:
    if x["id"] in ("P27", "P28"):
        x["stop_and_parse"]["status"] = "pending (self-hosting only)"
        x["stop_and_parse"]["hosted_note"] = "on the recommended Z.ai route the provider returns reasoning_content/content and finish_reason; EOS naming matters only if self-hosted"
        x["hosted_route"] = f"{x['id']}-zai"
        x["hosted_open_question"] = "whether max_tokens includes reasoning tokens is undocumented (integration test T2)"
    if x["id"] == "P29":
        x["stop_and_parse"]["status"] = "pending (self-hosting only)"
        x["stop_and_parse"]["hosted_note"] = "Moonshot API returns reasoning_content/content and finish_reason; a study parser is needed only for self-hosting"
        x["reasoning_effort"]["hosted_note"] = "hosted API parameter reasoning_effort=max (API default max); the encoder keyword thinking_effort applies only to self-hosting"
        x["hosted_route"] = "P29-moonshot"
    if x["id"] == "P25":
        x["hosted_route"] = "P25-deepseek"
        x["reasoning_effort"]["hosted_note"] = "API reasoning_effort=max; the API DEFAULT is high, so max must be sent"
        x["sampling"]["hosted_note"] = "API: temperature has no effect in thinking mode (server value undisclosed); top_p honoured only in 0.95-1.0, set 1.0"
    if x["id"] == "P34":
        x["hosted_route"] = "P34-dedicated-fp8 (recommended; separate GPU authorisation) | P34-deepinfra-fp4 (fallback)"
        x["precision_identity"]["route_note"] = ("released checkpoint is BF16; the recommended route serves the publisher's FP8 release Qwen/Qwen3.8-2.4T-A95B-FP8 @ "
            "d2dc35658bcf77e66643428cb52e774cc3b5bd29 (chat_template, generation_config, tokenizer_config byte-identical to BF16; config differs only by quantization_config); "
            "the fallback serves FP4 (below native precision)")
        x["integration_gates"] = ["no context extension (max-model-len 262144; no YaRN)", "top_k/min_p honoured and logged",
                                  "client-rendered prompt hash logged (dedicated route)", "reasoning_effort xhigh reaches the template"]

p24["status"] = "SUPERSEDED 2026-09-29 by P35 (reserve; configuration retained for history)"
p24["superseded_reason"] = ("weakest no-tools reasoning evidence among the seven audited models (AA HLE 39, CritPt 14, Omniscience -5); "
                            "the publisher's own table shows V4-Pro >= V4.1-Flash on GPQA and HLE; V4.1-Flash's gains are agentic")
m["superseded_models"] = [p24]
M.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
print([x["id"] for x in m["models"]], "superseded:", [x["id"] for x in m["superseded_models"]])
