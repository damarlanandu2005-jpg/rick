"""PHASE 1B composite + criteria numbers (numpy/PIL). Rule unchanged from Phase 1: out = base + layer_rgb * layer_alpha (display space, straight alpha).
python3 compose_1b.py --base <stills> --layer <dir with layer_/idmask_ PNGs> --align <align png> --camera <align_camera.json> --out <dir> --frames 201-210"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phase1"))
from compose_compare import load, lum, sobel, phase_corr, ncc, checker, u8

def dilate(m, n=1):
    o = m.copy()
    for _ in range(n):
        p = np.pad(o, 1); o = p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:] | p[:-2, :-2] | p[2:, 2:] | p[:-2, 2:] | p[2:, :-2]
    return o

def main():
    ap = argparse.ArgumentParser(); [ap.add_argument("--" + k) for k in ("base", "layer", "align", "camera", "out", "frames")]; a = ap.parse_args()
    f0, f1 = map(int, a.frames.split("-")); os.makedirs(a.out, exist_ok=True); R = {}; rows = []; stats = []
    base0 = load(os.path.join(a.base, "f_%05d.png" % f0)); R["dims"] = dict(base=list(base0.shape[1::-1]), layer=list(load(os.path.join(a.layer, "layer_%05d.png" % f0)).shape[1::-1]))
    outside_max = 0; outside_px = 0
    for f in range(f0, f1 + 1):
        bimg = np.asarray(Image.open(os.path.join(a.base, "f_%05d.png" % f)).convert("RGB")); b = bimg.astype(np.float32) / 255
        L = load(os.path.join(a.layer, "layer_%05d.png" % f)); al = L[..., 3:4]; comp = np.clip(b + L[..., :3] * al, 0, 1); cimg = (comp * 255 + .5).astype(np.uint8)
        Image.fromarray(cimg).save(os.path.join(a.out, "composite_%05d.png" % f))
        idm = load(os.path.join(a.layer, "idmask_%05d.png" % f))[..., 3] > 0; intended = dilate(idm, 1)
        dif = np.abs(cimg.astype(np.int16) - bimg.astype(np.int16)).max(axis=2); out_d = dif[~intended]; om = int(out_d.max()) if out_d.size else 0; outside_max = max(outside_max, om); outside_px += int((out_d > 0).sum())
        m = al[..., 0] > .5; d = comp - b; lb, lc = lum(b), lum(comp); ys, xs = np.where(m)
        st = dict(f=f, mask_px=int(m.sum()), mask_frac=round(float(m.mean()), 5), idmask_px=int(idm.sum()), outside_intended_max_diff_8bit=om, outside_changed_px=int((out_d > 0).sum()), layer_alpha_outside_intended_px=int(((al[..., 0] > 0) & ~intended).sum()))
        if m.any():
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1; st["bbox"] = [int(x0), int(y0), int(x1), int(y1)]
            st["mean_lum_added_in_mask"] = round(float((lc - lb)[m].mean()), 4); st["max_lum_added"] = round(float((lc - lb).max()), 3); st["mean_lum_base_in_mask"] = round(float(lb[m].mean()), 4); st["mean_lum_comp_in_mask"] = round(float(lc[m].mean()), 4)
            st["lum_std_base_in_mask"] = round(float(lb[m].std()), 4); st["lum_std_comp_in_mask"] = round(float(lc[m].std()), 4)
            lap = lambda g: (g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]); mm = m[1:-1, 1:-1]
            st["hf_energy_base"] = round(float(np.abs(lap(lb))[mm].mean()), 5); st["hf_energy_comp"] = round(float(np.abs(lap(lc))[mm].mean()), 5); st["hf_ratio"] = round(st["hf_energy_comp"] / max(st["hf_energy_base"], 1e-9), 3)
            st["frac_mask_added_gt_0.10"] = round(float(((lc - lb)[m] > .10).mean()), 4); st["mean_added_rgb_in_mask"] = [round(float(d[..., c][m].mean()), 4) for c in range(3)]
        stats.append(st); rows.append((f, b, L, comp, st))
    R["per_frame"] = stats; R["A_max_outside_diff_8bit_all_frames"] = outside_max; R["A_outside_changed_px_total"] = outside_px
    ms = [s["mean_lum_added_in_mask"] for s in stats if "mean_lum_added_in_mask" in s]; R["B_mean_lum_added_in_mask_max_over_frames"] = max(ms) if ms else None; R["B_mean_over_frames"] = round(float(np.mean(ms)), 4) if ms else None
    # ---- E alignment ----
    cam = json.load(open(a.camera)); fm = cam["frame"]; base = load(os.path.join(a.base, "f_%05d.png" % fm)); al_ = load(a.align)
    R["camera"] = {k: cam[k] for k in cam if k != "frame"}; R["camera"]["fov_diff_deg"] = round(abs(cam["blender_fov_v_deg"] - cam["baked_fov_v_deg"]), 4)
    eb, ea = sobel(lum(base[..., :3])), sobel(lum(al_[..., :3])); H, W = eb.shape; st_mid = [s for s in stats if s["f"] == fm and "bbox" in s][0]; x0, y0, x1, y1 = st_mid["bbox"]; pad = 30
    hx0, hy0, hx1, hy1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    reg = {"hero_bbox": (hx0, hy0, hx1, hy1), "full": (0, 0, W, H), "right_half": (W // 2, 0, W, H)}; R["E_align_pass_edge_shift_px"] = {}; R["E_align_pass_ncc0"] = {}
    for k, (a0, b0, a1, b1) in reg.items(): R["E_align_pass_edge_shift_px"][k] = phase_corr(eb[b0:b1, a0:a1], ea[b0:b1, a0:a1]); R["E_align_pass_ncc0"][k] = round(ncc(eb[b0:b1, a0:a1], ea[b0:b1, a0:a1]), 3)
    Lm = load(os.path.join(a.layer, "layer_%05d.png" % fm)); eal = sobel(Lm[..., 3]); R["E_layer_alpha_edges_vs_base_edges_hero_bbox_shift_px"] = phase_corr(eb[hy0:hy1, hx0:hx1], eal[hy0:hy1, hx0:hx1]); R["E_layer_alpha_vs_base_ncc0"] = round(ncc(eb[hy0:hy1, hx0:hx1], eal[hy0:hy1, hx0:hx1]), 3)
    ov = np.zeros((H, W, 3), np.float32); ov[..., 0] = np.clip(eb * 1.4, 0, 1); ov[..., 1] = np.clip(eal * 1.4, 0, 1); u8(ov[hy0:hy1, hx0:hx1]).resize(((hx1 - hx0) * 2, (hy1 - hy0) * 2), Image.NEAREST).save(os.path.join(a.out, "align_layer_alpha_edges_green_vs_base_red_hero.png"))
    # ---- sheet: 3 frames, hero crop enlarged ----
    pick = [rows[0], rows[len(rows) // 2], rows[-1]]; cw = 260; tiles = []
    for f, b, L, comp, st in pick:
        x0, y0, x1, y1 = st["bbox"]; pad = 30; x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(b.shape[1], x1 + pad), min(b.shape[0], y1 + pad)
        lay = L[..., :3] * L[..., 3:4] + checker(*L.shape[:2], 16) * (1 - L[..., 3:4]); diff = np.clip(np.abs(comp - b) * 6, 0, 1)
        ims = [u8(x[y0:y1, x0:x1]) for x in (b, lay, comp, diff)]; ch = int(cw * (y1 - y0) / (x1 - x0)); tiles.append((f, [i.resize((cw, ch), Image.LANCZOS) for i in ims]))
    Wt = 4 * cw + 5 * 8; Ht = sum(t[1][0].size[1] + 30 for t in tiles) + 40; sheet = Image.new("RGB", (Wt, Ht), (245, 242, 235)); dr = ImageDraw.Draw(sheet); y = 6
    for i, h in enumerate(("THREE.JS BASE 720x1280", "BLENDER REFLECTION LAYER", "BASE + LAYER", "DIFFERENCE x6")): dr.text((8 + i * (cw + 8), y), h, fill=(20, 20, 20))
    y += 20
    for f, ims in tiles:
        dr.text((8, y), "frame %d" % f, fill=(120, 20, 20)); y += 14
        for i, im in enumerate(ims): sheet.paste(im, (8 + i * (cw + 8), y))
        y += ims[0].size[1] + 16
    sheet.save(os.path.join(a.out, "before_after_sheet.png")); f, b, L, comp, st = rows[len(rows) // 2]
    full = Image.new("RGB", (W * 2 + 8, H)); full.paste(u8(b), (0, 0)); full.paste(u8(comp), (W + 8, 0)); full.save(os.path.join(a.out, "full_frame_%d_base_vs_composite.png" % f))
    json.dump(R, open(os.path.join(a.out, "compose_report.json"), "w"), indent=1); print(json.dumps({k: R[k] for k in R if k != "per_frame"}))

if __name__ == "__main__": main()
