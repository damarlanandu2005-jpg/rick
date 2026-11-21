"""PHASE 1: alignment numbers, composite and before/after sheet. numpy + PIL only (no Blender, no GPU).
  python3 compose_compare.py --base <stills dir> --layer <layer dir> --align <align png> --camera <align_camera.json> --out <dir> --frames 201-210
Composite rule (fixed before looking, one rule): out = base + layer_rgb * layer_alpha  (add; it can never darken). Layer PNG is read as straight alpha.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw

def load(p): return np.asarray(Image.open(p).convert("RGBA")).astype(np.float32) / 255
def lum(a): return .2126 * a[..., 0] + .7152 * a[..., 1] + .0722 * a[..., 2]
def sobel(g):
    gx = np.zeros_like(g); gy = np.zeros_like(g); gx[:, 1:-1] = g[:, 2:] - g[:, :-2]; gy[1:-1, :] = g[2:, :] - g[:-2, :]; e = np.hypot(gx, gy); return e / (np.percentile(e, 99.5) + 1e-9)
def phase_corr(a, b):
    """(dx, dy, peak): a(x, y) ~ b(x - dx, y - dy). (0, 0) = registered."""
    h, w = a.shape; win = np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)
    A = np.fft.rfft2((a - a.mean()) * win); B = np.fft.rfft2((b - b.mean()) * win); R = A * np.conj(B); R /= np.abs(R) + 1e-9; r = np.fft.irfft2(R, s=a.shape)
    iy, ix = np.unravel_index(np.argmax(r), r.shape); pk = float(r[iy, ix])
    def sub(v0, v1, v2): d = v0 - 2 * v1 + v2; return 0.0 if abs(d) < 1e-12 else .5 * (v0 - v2) / d
    dy = iy + sub(r[(iy - 1) % h, ix], r[iy, ix], r[(iy + 1) % h, ix]); dx = ix + sub(r[iy, (ix - 1) % w], r[iy, ix], r[iy, (ix + 1) % w])
    if dy > h / 2: dy -= h
    if dx > w / 2: dx -= w
    return round(float(dx), 2), round(float(dy), 2), round(pk, 3)
def ncc(a, b): a = a - a.mean(); b = b - b.mean(); return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-12))

def checker(h, w, s=24):
    y, x = np.mgrid[0:h, 0:w]; c = (((x // s) + (y // s)) % 2).astype(np.float32) * .25 + .35; return np.stack([c, c, c], -1)
def u8(a): return Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--base"); ap.add_argument("--layer"); ap.add_argument("--align"); ap.add_argument("--camera"); ap.add_argument("--out"); ap.add_argument("--frames", default="201-210"); a = ap.parse_args()
    f0, f1 = map(int, a.frames.split("-")); os.makedirs(a.out, exist_ok=True); R = {}
    # ---------- A. alignment ----------
    cam = json.load(open(a.camera)); fm = cam["frame"]; base = load(os.path.join(a.base, "f_%05d.png" % fm)); al = load(a.align)
    R["dims"] = dict(base=list(base.shape[1::-1]), blender_align=list(al.shape[1::-1]), layer=list(load(os.path.join(a.layer, "layer_%05d.png" % f0)).shape[1::-1]), same=bool(base.shape == al.shape))
    R["camera"] = {k: cam[k] for k in ("blender_fov_v_deg", "baked_fov_v_deg", "blender_pos", "baked_pos", "aspect", "aspect_baked", "sensor_fit", "res")}
    R["camera"]["fov_diff_deg"] = round(abs(cam["blender_fov_v_deg"] - cam["baked_fov_v_deg"]), 4); R["camera"]["pos_diff_m"] = round(float(np.linalg.norm(np.array(cam["blender_pos"]) - np.array(cam["baked_pos"]))), 5)
    eb, ea = sobel(lum(base[..., :3])), sobel(lum(al[..., :3])); H, W = eb.shape; reg = {"full": (0, 0, W, H), "left_half(card)": (0, 0, W // 2, H), "right_half(clock)": (W // 2, 0, W, H), "upper_band(sky/roof)": (0, 0, W, H // 2), "lower_band(ground)": (0, H // 2, W, H)}
    R["edge_shift_px"] = {}; R["edge_ncc_at_zero"] = {}
    for k, (x0, y0, x1, y1) in reg.items():
        R["edge_shift_px"][k] = phase_corr(eb[y0:y1, x0:x1], ea[y0:y1, x0:x1]); R["edge_ncc_at_zero"][k] = round(ncc(eb[y0:y1, x0:x1], ea[y0:y1, x0:x1]), 3)
    ov = np.zeros((H, W, 3), np.float32); ov[..., 0] = np.clip(eb * 1.4, 0, 1); ov[..., 1] = np.clip(ea * 1.4, 0, 1); ov[..., 2] = np.clip(ea * .5, 0, 1)
    ck = base[..., :3].copy(); s = 120
    for y in range(0, H, s):
        for x in range(0, W, s):
            if ((x // s) + (y // s)) % 2: ck[y:y + s, x:x + s] = al[y:y + s, x:x + s, :3]
    u8(ov).resize((W // 2, H // 2), Image.LANCZOS).save(os.path.join(a.out, "align_edges_red_base_green_blender.png")); u8(ck).resize((W // 2, H // 2), Image.LANCZOS).save(os.path.join(a.out, "align_checker.png"))
    # ---------- C. composite + metrics ----------
    rows = []; stats = []
    for f in range(f0, f1 + 1):
        b = load(os.path.join(a.base, "f_%05d.png" % f))[..., :3]; L = load(os.path.join(a.layer, "layer_%05d.png" % f)); al_ = L[..., 3:4]; comp = np.clip(b + L[..., :3] * al_, 0, 1)
        m = (al_[..., 0] > .5); d = comp - b; lb, lc = lum(b), lum(comp); ys, xs = np.where(m)
        st = dict(f=f, mask_px=int(m.sum()), mask_frac=round(float(m.mean()), 4), darker_px_gt_1_255=int((lum(d) < -1 / 255).sum()), max_added_lum=round(float(lum(d).max()), 3))
        if m.any():
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1; st["bbox"] = [int(x0), int(y0), int(x1), int(y1)]
            st["mean_lum_base_in_mask"] = round(float(lb[m].mean()), 4); st["mean_lum_comp_in_mask"] = round(float(lc[m].mean()), 4); st["mean_added_lum_in_mask"] = round(float(lum(d)[m].mean()), 4)
            st["lum_std_base_in_mask"] = round(float(lb[m].std()), 4); st["lum_std_comp_in_mask"] = round(float(lc[m].std()), 4)
            lap = lambda g: (g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:])
            mm = m[1:-1, 1:-1]; st["hf_energy_base"] = round(float(np.abs(lap(lb))[mm].mean()), 5); st["hf_energy_comp"] = round(float(np.abs(lap(lc))[mm].mean()), 5)
            st["pixels_with_added_lum_gt_2pct"] = int((lum(d)[m] > .02).sum())
        stats.append(st); Image.fromarray((comp * 255 + .5).astype(np.uint8)).save(os.path.join(a.out, "composite_%05d.png" % f))
        rows.append((f, b, L, comp, st))
    R["per_frame"] = stats
    # temporal flicker of the layer inside the mask (frame-to-frame change of added luminance): a noisy layer would show here
    fl = []
    for (f, b, L, comp, st), (f2, b2, L2, comp2, st2) in zip(rows, rows[1:]):
        mk = (L[..., 3] > .5) & (L2[..., 3] > .5)
        if mk.any(): fl.append(float(np.abs(lum(L[..., :3])[mk] - lum(L2[..., :3])[mk]).mean()))
    R["layer_frame_to_frame_mean_abs_lum_change"] = round(float(np.mean(fl)), 4) if fl else None
    # ---------- sheet ----------
    pick = [rows[0], rows[len(rows) // 2], rows[-1]]; cw = 300; tiles = []
    for f, b, L, comp, st in pick:
        if "bbox" in st:
            x0, y0, x1, y1 = st["bbox"]; pad = 40; x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(b.shape[1], x1 + pad), min(b.shape[0], y1 + pad)
        else: x0, y0, x1, y1 = 0, 0, b.shape[1], b.shape[0]
        lay = L[..., :3] * L[..., 3:4] + checker(*L.shape[:2]) * (1 - L[..., 3:4]); diff = np.clip(np.abs(comp - b) * 6, 0, 1)
        row = [u8(x[y0:y1, x0:x1]) for x in (b, lay, comp, diff)]; ch = int(cw * (y1 - y0) / (x1 - x0)); tiles.append((f, [t.resize((cw, ch), Image.LANCZOS) for t in row]))
    hmax = max(t[1][0].size[1] for t in tiles); Wt = 4 * cw + 5 * 8; Ht = sum(t[1][0].size[1] + 30 for t in tiles) + 40
    sheet = Image.new("RGB", (Wt, Ht), (245, 242, 235)); dr = ImageDraw.Draw(sheet); y = 6
    for i, h in enumerate(("THREE.JS BASE", "BLENDER LAYER (metal only, on checker)", "BASE + LAYER", "DIFFERENCE x6")): dr.text((8 + i * (cw + 8), y), h, fill=(20, 20, 20))
    y += 20
    for f, ims in tiles:
        dr.text((8, y), "frame %d" % f, fill=(120, 20, 20)); y += 14
        for i, im in enumerate(ims): sheet.paste(im, (8 + i * (cw + 8), y))
        y += ims[0].size[1] + 16
    sheet.save(os.path.join(a.out, "before_after_sheet.png"))
    f = rows[len(rows) // 2]; full = Image.new("RGB", (1080 // 2 * 2 + 8, 960)); full.paste(u8(f[1]).resize((540, 960), Image.LANCZOS), (0, 0)); full.paste(u8(f[3]).resize((540, 960), Image.LANCZOS), (548, 0)); full.save(os.path.join(a.out, "full_frame_%d_base_vs_composite.png" % f[0]))
    json.dump(R, open(os.path.join(a.out, "compose_report.json"), "w"), indent=1); print(json.dumps(R["edge_shift_px"]), json.dumps(R["camera"]))

if __name__ == "__main__": main()
