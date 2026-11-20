"""fulltest/shotmath.py -- pure Python (no Blender). The ONE place that turns a shot spec into camera numbers and projects points to the frame.
blender_full.py renders with these functions and validate_plan.py checks with the same ones, so a plan that validates is a plan that renders as checked."""
import math
ASPECT = 720 / 1280.0      # frame width / height (portrait)
SENSOR_H = 24.0            # vertical sensor (mm), matches the camera built in blender_full.py
def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def mul(a, k): return (a[0]*k, a[1]*k, a[2]*k)
def dot(a, b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a): l = math.sqrt(dot(a, a)) or 1.0; return (a[0]/l, a[1]/l, a[2]/l)
def tan_v(lens): return (SENSOR_H / 2.0) / lens
def tan_h(lens): return tan_v(lens) * ASPECT
def vfov(lens): return 2 * math.atan(tan_v(lens))
def basis(pos, aim):
    f = norm(sub(aim, pos)); r = norm(cross(f, (0, 0, 1))); u = cross(r, f); return f, r, u
def project(p, pos, aim, lens):
    """-> (x, y, depth): x,y in -1..1 across the frame (None if behind the camera)"""
    f, r, u = basis(pos, aim); v = sub(p, pos); z = dot(v, f)
    if z <= 1e-6: return None
    return (dot(v, r) / (z * tan_h(lens)), dot(v, u) / (z * tan_v(lens)), z)
def screen_to_world(pos, aim, lens, sx, sy, depth):
    f, r, u = basis(pos, aim); return add(add(add(pos, mul(f, depth)), mul(r, sx * depth * tan_h(lens))), mul(u, sy * depth * tan_v(lens)))
def fit_camera(spec, shot_chars, cast):
    """-> dict(pos0, aim0, pos1, aim1, lens, dist, mode). Target mode frames a character by visible_frac / center_frac of its height."""
    lens = float(spec.get("lens", 30)); push = float(spec.get("push", 0)); dz = float(spec.get("aim_dz", 0)); adx = float(spec.get("aim_dx", 0))
    if "target" in spec:
        c = next((x for x in shot_chars if x["id"] == spec["target"]), None)
        if c is None: raise ValueError("camera target '%s' is not in this shot's chars" % spec["target"])
        H = cast[c["id"]].get("height_m", 1.8); az, el = math.radians(spec.get("az", 0)), math.radians(spec.get("el", 0))
        A0 = (c["pos"][0] + math.cos(az) * adx, c["pos"][1] + math.sin(az) * adx, spec.get("center_frac", .6) * H)
        d0 = spec.get("visible_frac", .8) * H / (2 * tan_v(lens)); v = (math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))
        A1 = (A0[0], A0[1], A0[2] + dz * H); d1 = d0 * (1 - push)
        return dict(pos0=add(A0, mul(v, d0)), aim0=A0, pos1=add(A1, mul(v, d1)), aim1=A1, lens=lens, dist=d0, mode="target")
    if "pos" in spec and "aim" in spec:
        p, a = tuple(spec["pos"]), tuple(spec["aim"]); f = norm(sub(a, p))
        return dict(pos0=p, aim0=a, pos1=add(p, mul(f, push)), aim1=(a[0], a[1], a[2] + dz), lens=lens, dist=None, mode="free")
    raise ValueError("camera spec needs 'target' or both 'pos' and 'aim': %s" % spec)
def place_by_screen(cam_spec, sx, depth):
    """world (x, y) of a character placed at screen x (-1..1) and depth m in front of a pos/aim camera"""
    p, a = tuple(cam_spec["pos"]), tuple(cam_spec["aim"]); fwd = norm((a[0]-p[0], a[1]-p[1], 0)); right = (fwd[1], -fwd[0], 0)
    th = tan_h(float(cam_spec.get("lens", 30))); return (p[0] + fwd[0]*depth + right[0]*sx*depth*th, p[1] + fwd[1]*depth + right[1]*sx*depth*th)
def resolve_screen_chars(shots):
    for sh in shots:
        for c in sh.get("chars", []):
            if "screen" in c:
                if "pos" not in sh["cam"]: raise ValueError("shot %s: char 'screen' placement needs the shot camera in pos/aim mode" % sh["id"])
                c["pos"] = list(place_by_screen(sh["cam"], c["screen"][0], c["screen"][1]))
