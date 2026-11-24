#!/usr/bin/env python3
"""R8 end-to-end on the EXISTING R6 synthetic production fixture (r6/fixture_mech.py, TEST_FIXTURE_ONLY, stamped production:false; not a new creative film, not the R5 Hat Toss):
the same film with an "audio" block and sound cues in film.json (so the APPROVAL signs them), synthetic fixture audio (r8/fixture_audio.py), then the real production pipeline:
G1-G9 -> lock -> ONE final 430-frame render -> QA -> 11 sound (validate, mix, mux, video stream copied) -> 12 delivery QA on the decoded MP4.
  python3 r8/e2e_production.py <dir>     (about 15 minutes on 2 CPUs: almost all of it is the visual render)"""
import copy, json, os, shutil, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "r2"), str(ROOT / "r6"), str(ROOT / "r8")]
import fixture_mech as FM, fixture_audio as FA
fails = []
def t(name, ok): print(("PASS " if ok else "FAIL ") + name, flush=True); (ok or fails.append(name))
tmp = Path(sys.argv[1]); RESUME = "--resume" in sys.argv   # --resume: keep the built, approved fixture and its cached render; redo only the audio and re-run the same pipeline command
if not RESUME: shutil.rmtree(tmp, ignore_errors=True)
FM.FILM = copy.deepcopy(FM.FILM); FM.FILM["audio"] = {"required": ["voice", "music", "sfx", "ambience"]}
FM.FILM["sound"] = [dict(at=0, name="voice", type="voice", file="voice/voice.wav"), dict(at=0, name="bed", type="music", file="sound/music/bed.wav", until="end", gain=-20, fade_in=0.8, fade_out=1.5),
                    dict(at=0, name="wind", type="ambience", file="sound/amb/wind.wav", until="end", gain=-10, fade_in=1.0, fade_out=1.0),
                    dict(at=["kneels", 1], name="footstep", gain=-6), dict(at=["taps", 1], name="impact", gain=-4), dict(at=["taps", 1, 6], name="impact", gain=-6), dict(at=["train", 1], name="whoosh", gain=-6)]
t0 = time.time(); ep = FM.build(tmp) if not RESUME else tmp / "ep"; TB = round(time.time() - t0, 1)
words = json.load(open(ep / "voice/words.json")); n = len(json.load(open(ep / "out/plan/camera_baked.json"))["frames"])
t0 = time.time(); FA.write_all(ep, ep / "voice/words.json", min(words[-1]["e"] + 0.3, n / 30 - 0.05)); TA = round(time.time() - t0, 3)
for p in (ep / "sound/sfx/corrupt.wav", ep / "sound/music/short.wav", ep / "sound/sfx/click.wav"): p.unlink()
if RESUME: import shutil as _s; [_s.rmtree(ep / x, ignore_errors=True) for x in ("out/audio",)]
print("fixture built in %s s (approved, locked plan includes the audio cues); fixture audio %s s" % (TB, TA), flush=True)
env = {k: v for k, v in os.environ.items() if k != "RICKS_UNAPPROVED_TEST_RUN"}; env["RICKS_REGISTRY"] = str(tmp / "registry.json")
t0 = time.time(); r = subprocess.run([sys.executable, str(ROOT / "tools/pipeline.py"), str(ep), "--renderer", "cpu"], capture_output=True, text=True, env=env); TP = round(time.time() - t0, 1)
(tmp / "pipeline.log").write_text(r.stdout + r.stderr); print(r.stdout[-2500:])
S = {s["stage"]: s for s in json.load(open(ep / "out/pipeline/stages.json"))}
t("the production pipeline PASSES end to end (exit 0) with audio", r.returncode == 0)
t("order: G9 approval -> 6 lock -> 7 base (the ONE expensive render) -> 9 final -> 10 qa -> 11 sound -> 12 delivery qa", all(k in S for k in ("G9", "6 lock", "7 base", "9 final", "10 qa", "11 sound", "12 delivery qa")) and [x for x in S if x in ("G9", "6 lock", "7 base", "9 final", "10 qa", "11 sound", "12 delivery qa")] == ["G9", "6 lock", "7 base", "9 final", "10 qa", "11 sound", "12 delivery qa"])
t("11 sound PASS: %s" % S.get("11 sound", {}).get("note"), S.get("11 sound", {}).get("status") == "PASS")
t("12 delivery qa PASS on the decoded MP4: %s" % S.get("12 delivery qa", {}).get("note"), S.get("12 delivery qa", {}).get("status") == "PASS")
import audio as AU
R = AU.qa(ep); [print("   " + ("PASS " if ok else "FAIL ") + k + (" | " + d if d else "")) for k, ok, d in R]; t("independent re-run of the delivery QA: %d/%d checks PASS" % (sum(ok for _, ok, _ in R), len(R)), all(ok for _, ok, _ in R))
M = json.load(open(ep / "out/final/final_manifest.json")); A = M.get("audio") or {"inputs": {}, "gated": None, "production": None, "delivery": {}}
t("the manifest names every audio input with its sha1, the mix, the delivery and the config; production:false (TEST_FIXTURE_ONLY) though gated by the real approval + lock", len(A["inputs"]) == 6 and A["gated"] is True and A["production"] is False and A["delivery"]["sha1"])
t("the visual render ran ONCE: %s" % S.get("7 base", {}).get("status"), S.get("7 base", {}).get("status") in ("PASS", "CACHE"))
TS = {k: S[k]["seconds"] for k in ("7 base", "9 final", "10 qa", "11 sound", "12 delivery qa") if k in S}
print("\nE2E TIMES:", json.dumps(dict(fixture_build_s=TB, fixture_audio_s=TA, pipeline_total_s=TP, **TS)))
# approval safety on the real approved fixture: change the approved sound plan -> the mux is refused
orig = (ep / "film.json").read_bytes(); F = json.load(open(ep / "film.json")); F["sound"][3]["gain"] = -3; json.dump(F, open(ep / "film.json", "w"), indent=1)
r = subprocess.run([sys.executable, str(ROOT / "tools/audio.py"), "mux", str(ep)], capture_output=True, text=True, env=env)
t("approval safety: editing a sound cue after approval makes the approval STALE and the mux is REFUSED", r.returncode != 0 and "REFUSED" in r.stdout + r.stderr and "STALE" in r.stdout + r.stderr)
(ep / "film.json").write_bytes(orig)   # restore the approved plan (the episode stays resumable)
print("\n%d FAIL" % len(fails)); sys.exit(1 if fails else 0)
