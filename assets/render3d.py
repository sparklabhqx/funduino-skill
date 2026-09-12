#!/usr/bin/env python3
"""
render3d.py — turn a CAD/STEP part into a looping "sway" sprite sequence for the
green Schematik scenes, with NO GPU/Blender (pure-CPU software rasterizer).

Run with the 3D venv (see SKILL.md for setup):
    .venv3d/bin/python render3d.py --step "part.stp" --out-dir model/frames --mode loop
Modes:
    grid  : 5 candidate angles -> out/ang_*.png (pick a hero yaw)
    hero  : one angle -> --out
    loop  : seamless ±sway loop of N frames -> --out-dir/f_00.png ..  (composite with draw_model)

Deps in the venv:  cascadio  trimesh  numpy  pillow
"""
import sys, math, argparse, os
import numpy as np
import trimesh
from PIL import Image

def step_to_glb(step, glb, tol_lin=0.05, tol_ang=0.25):
    import cascadio
    print("converting STEP -> glb ...")
    cascadio.step_to_glb(step, glb, tol_linear=tol_lin, tol_angular=tol_ang)

def load_world(glb):
    scene = trimesh.load(glb)
    V, F, C, off = [], [], [], 0
    for node in scene.graph.nodes_geometry:
        T, gname = scene.graph[node]; g = scene.geometry[gname]
        v = trimesh.transformations.transform_points(g.vertices, T)
        base = (180, 180, 180, 255)
        mat = getattr(g.visual, "material", None)
        if mat is not None and getattr(mat, "baseColorFactor", None) is not None:
            base = tuple(int(x) for x in mat.baseColorFactor)
        V.append(v); F.append(np.asarray(g.faces) + off)
        C.append(np.tile(np.array(base[:3], float)/255.0, (len(g.faces), 1)))
        off += len(v)
    return np.vstack(V), np.vstack(F), np.vstack(C)

def render(V, F, C, yaw, pitch, res=820, light=(-0.45, 0.8, 0.55), roll=0.0):
    center = (V.min(0)+V.max(0))/2
    radius = 0.5*np.linalg.norm(V.max(0)-V.min(0))
    up0 = np.array([0, 0, 1.0])
    az, el = math.radians(yaw), math.radians(pitch)
    d2c = np.array([math.cos(el)*math.sin(az), math.cos(el)*math.cos(az), math.sin(el)])
    campos = center + d2c*radius*3.4
    f = -d2c
    right = np.cross(f, up0)
    if np.linalg.norm(right) < 1e-6: right = np.array([1.0, 0, 0])
    right /= np.linalg.norm(right); upv = np.cross(right, f)
    if roll:
        cr, sr = math.cos(roll), math.sin(roll)
        right, upv = right*cr + upv*sr, -right*sr + upv*cr
    relc = V - campos
    zv = relc @ f; xv = relc @ right; yv = relc @ upv
    proj = np.stack([xv/zv, yv/zv], 1)
    scale = (res*0.40)/np.abs(proj).max()
    sx = res/2 + proj[:, 0]*scale; sy = res/2 - proj[:, 1]*scale; depth = zv

    v0, v1, v2 = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(v1-v0, v2-v0); nl = np.linalg.norm(n, axis=1); nl[nl == 0] = 1; n /= nl[:, None]
    n[(n @ f) > 0] *= -1
    L = np.array(light, float); L /= np.linalg.norm(L)
    diff = np.clip(n @ L, 0, 1)
    half = (-f + L); half /= np.linalg.norm(half)
    spec = np.clip(n @ half, 0, 1)**24
    shade = np.clip((0.30 + 0.72*diff)[:, None]*C + spec[:, None]*0.35, 0, 1)

    img = np.zeros((res, res, 3)); zb = np.full((res, res), np.inf); alpha = np.zeros((res, res))
    P = np.stack([sx, sy], 1)
    for i in range(len(F)):
        a, b, cc = F[i]; x0, y0 = P[a]; x1, y1 = P[b]; x2, y2 = P[cc]
        minx = int(max(0, math.floor(min(x0, x1, x2)))); maxx = int(min(res-1, math.ceil(max(x0, x1, x2))))
        miny = int(max(0, math.floor(min(y0, y1, y2)))); maxy = int(min(res-1, math.ceil(max(y0, y1, y2))))
        if minx > maxx or miny > maxy: continue
        area = (x1-x0)*(y2-y0) - (x2-x0)*(y1-y0)
        if abs(area) < 1e-9: continue
        gx, gy = np.meshgrid(np.arange(minx, maxx+1), np.arange(miny, maxy+1))
        w0 = ((x1-gx)*(y2-gy) - (x2-gx)*(y1-gy))/area
        w1 = ((x2-gx)*(y0-gy) - (x0-gx)*(y2-gy))/area
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any(): continue
        zz = w0*depth[a] + w1*depth[b] + w2*depth[cc]
        sub = zb[miny:maxy+1, minx:maxx+1]; win = inside & (zz < sub)
        if not win.any(): continue
        sub[win] = zz[win]
        img[miny:maxy+1, minx:maxx+1][win] = shade[i]
        alpha[miny:maxy+1, minx:maxx+1][win] = 1.0
    return (np.clip(np.dstack([img, alpha]), 0, 1)*255).astype(np.uint8)

def save(rgba, path, down=None):
    im = Image.fromarray(rgba, "RGBA")
    if down: im = im.resize((down, down), Image.LANCZOS)
    im.save(path); print("wrote", path)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--step"); ap.add_argument("--glb", default="model.glb")
    ap.add_argument("--out", default="hero.png"); ap.add_argument("--out-dir", default="model/frames")
    ap.add_argument("--mode", default="loop", choices=["grid", "hero", "loop"])
    ap.add_argument("--yaw", type=float, default=22); ap.add_argument("--pitch", type=float, default=30)
    ap.add_argument("--frames", type=int, default=48); ap.add_argument("--sway", type=float, default=24)
    ap.add_argument("--res", type=int, default=820); ap.add_argument("--down", type=int, default=540)
    a = ap.parse_args()
    if a.step and (not os.path.exists(a.glb)): step_to_glb(a.step, a.glb)
    V, F, C = load_world(a.glb)
    print("faces", len(F), "extent", np.round(V.max(0)-V.min(0), 3).tolist())
    if a.mode == "grid":
        for yaw in (0, 30, 60, 90, 135):
            save(render(V, F, C, yaw, a.pitch, res=a.res), f"ang_{yaw}.png", down=a.down)
    elif a.mode == "hero":
        save(render(V, F, C, a.yaw, a.pitch, res=a.res), a.out, down=a.down)
    else:
        os.makedirs(a.out_dir, exist_ok=True)
        for i in range(a.frames):
            yaw = a.yaw + a.sway*math.sin(2*math.pi*i/a.frames)
            save(render(V, F, C, yaw, a.pitch, res=a.res), f"{a.out_dir}/f_{i:02d}.png", down=a.down)
