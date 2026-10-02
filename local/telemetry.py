"""Background resource sampler: GPU (nvidia-smi, 1 s) and RAM (psutil) while a model is loaded.

Writes one JSON line per sample to <run>/telemetry_<model>.jsonl and keeps running peaks.
GPU memory is the device total (includes the Windows desktop's share); the desktop baseline is recorded
before the server starts so the model's own VRAM = peak - baseline.
"""
from __future__ import annotations

import json
import subprocess
import threading
import time
from pathlib import Path

import psutil

QUERY = "memory.used,memory.total,utilization.gpu,temperature.gpu,clocks.sm,power.draw,clocks_throttle_reasons.active"


def gpu_snapshot() -> dict:
    out = subprocess.run(["nvidia-smi", f"--query-gpu={QUERY}", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, timeout=15).stdout.strip().splitlines()[0]
    f = [x.strip() for x in out.split(",")]

    def num(x):
        try:
            return float(x)
        except ValueError:
            return None
    return {"gpu_mem_used_mib": num(f[0]), "gpu_mem_total_mib": num(f[1]), "gpu_util_pct": num(f[2]),
            "gpu_temp_c": num(f[3]), "gpu_sm_clock_mhz": num(f[4]), "gpu_power_w": num(f[5]),
            "gpu_throttle_reasons": f[6]}


class Sampler:
    def __init__(self, out_path: Path, pid: int | None, interval_s: float = 1.0):
        self.out_path, self.pid, self.interval = out_path, pid, interval_s
        self.peaks = {"gpu_mem_used_mib": 0.0, "proc_rss_mib": 0.0, "proc_private_mib": 0.0,
                      "sys_used_mib": 0.0, "gpu_temp_c": 0.0}
        self.throttle_seen: set[str] = set()
        self.min_sm_clock = None
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)

    def _sample(self) -> dict:
        s = {"t": time.time(), **gpu_snapshot()}
        vm = psutil.virtual_memory()
        s["sys_used_mib"] = round((vm.total - vm.available) / 2**20, 1)
        s["sys_total_mib"] = round(vm.total / 2**20, 1)
        if self.pid:
            try:
                mi = psutil.Process(self.pid).memory_info()
                s["proc_rss_mib"] = round(mi.rss / 2**20, 1)
                s["proc_private_mib"] = round(getattr(mi, "private", mi.vms) / 2**20, 1)
            except psutil.Error:
                pass
        return s

    def _run(self):
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        with self.out_path.open("a", encoding="utf-8") as f:
            while not self._stop.is_set():
                try:
                    s = self._sample()
                    f.write(json.dumps(s) + "\n")
                    f.flush()
                    for k in self.peaks:
                        if s.get(k) is not None:
                            self.peaks[k] = max(self.peaks[k], s[k])
                    if s.get("gpu_throttle_reasons") not in (None, "0x0000000000000000"):
                        self.throttle_seen.add(s["gpu_throttle_reasons"])
                    if s.get("gpu_sm_clock_mhz") and s.get("gpu_util_pct", 0) > 50:
                        c = s["gpu_sm_clock_mhz"]
                        self.min_sm_clock = c if self.min_sm_clock is None else min(self.min_sm_clock, c)
                except Exception as e:  # telemetry must never break a run
                    f.write(json.dumps({"t": time.time(), "error": repr(e)}) + "\n")
                self._stop.wait(self.interval)

    def start(self):
        self._t.start()
        return self

    def stop(self) -> dict:
        self._stop.set()
        self._t.join(timeout=10)
        return {"peaks": self.peaks, "throttle_reasons_seen": sorted(self.throttle_seen),
                "min_sm_clock_mhz_under_load": self.min_sm_clock}
