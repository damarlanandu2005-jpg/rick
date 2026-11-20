"""fulltest/usage_meter.py -- measured usage for a run: seconds per step, frames, seconds per frame, output size, and Colab session time.
Colab compute units are an ESTIMATE: CU_PER_HOUR is an assumed rate for a T4 runtime (check the real number in Colab's Resources panel); the seconds are measured."""
import json, os, time
CU_PER_HOUR_T4 = 1.8   # assumption, not a measurement
class Meter:
    def __init__(self): self.steps = []; self.t0 = time.time()
    def add(self, label, seconds): self.steps.append((label, round(seconds, 1)))
    def session_minutes(self):
        try: return float(open("/proc/uptime").read().split()[0]) / 60.0
        except Exception: return None
    def report(self, frames=0, out_dir=None):
        total = sum(s for _, s in self.steps) or 1; lines = ["USAGE METER (measured seconds, this run)", "| step | seconds | share |", "|---|---|---|"]
        lines += ["| %s | %.1f | %.0f%% |" % (l, s, 100 * s / total) for l, s in self.steps]
        lines.append("| total of listed steps | %.1f | |" % total)
        if frames: lines.append("render+setup cost per output frame: %.2f s (%d frames)" % (total / frames, frames))
        if out_dir and os.path.isdir(out_dir):
            mb = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(out_dir) for f in fs) / 1e6; lines.append("output folder: %.0f MB" % mb)
        sm = self.session_minutes()
        if sm is not None: lines.append("Colab session so far: %.1f min  ~ %.2f compute units (ASSUMED %.1f CU/h for a T4; real figure is in Colab > Resources)" % (sm, sm / 60 * CU_PER_HOUR_T4, CU_PER_HOUR_T4))
        lines.append("Claude side: no token counter exists here; effort is tracked as context windows and Colab rounds in the chat.")
        return "\n".join(lines)
    def save(self, path): json.dump({"steps": self.steps, "session_min": self.session_minutes()}, open(path, "w"), indent=1)
