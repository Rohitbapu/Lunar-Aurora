"""
Generates glTF 2.0 binary (.glb) 3D heritage exhibits compatible with Sony Spatial Reality Display Player.
Includes PBR materials (sandstone, dark granite, metallic gold, emissive cyan), accurate face normals,
and compliant min/max bounds scaled for the 15.6-inch ELF-SR1 volumetric prism.
"""
import json
import math
import os
import struct
from typing import List, Tuple, Dict


class GlbBuilder:
    def __init__(self, name: str):
        self.name = name
        self.materials: List[dict] = []
        self.meshes: List[dict] = []
        self.nodes: List[dict] = []
        self.accessors: List[dict] = []
        self.buffer_views: List[dict] = []
        self.bin_data = bytearray()

    def add_material(
        self,
        name: str,
        rgba: Tuple[float, float, float, float],
        metallic: float = 0.05,
        roughness: float = 0.75,
        emissive: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> int:
        mat = {
            "name": name,
            "pbrMetallicRoughness": {
                "baseColorFactor": list(rgba),
                "metallicFactor": metallic,
                "roughnessFactor": roughness,
            },
        }
        if any(e > 0 for e in emissive):
            mat["emissiveFactor"] = list(emissive)
        idx = len(self.materials)
        self.materials.append(mat)
        return idx

    def _pad4(self):
        while len(self.bin_data) % 4 != 0:
            self.bin_data.append(0)

    def _add_buffer_view(self, raw_bytes: bytes, target: int) -> int:
        self._pad4()
        offset = len(self.bin_data)
        self.bin_data.extend(raw_bytes)
        bv_idx = len(self.buffer_views)
        self.buffer_views.append(
            {
                "buffer": 0,
                "byteOffset": offset,
                "byteLength": len(raw_bytes),
                "target": target,
            }
        )
        return bv_idx

    def add_mesh(
        self,
        name: str,
        positions: List[Tuple[float, float, float]],
        normals: List[Tuple[float, float, float]],
        indices: List[int],
        material_idx: int,
        translation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation_euler_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        pos_bytes = b"".join(struct.pack("<3f", *p) for p in positions)
        norm_bytes = b"".join(struct.pack("<3f", *n) for n in normals)
        idx_bytes = b"".join(struct.pack("<H", i) for i in indices)

        bv_pos = self._add_buffer_view(pos_bytes, 34962)
        bv_norm = self._add_buffer_view(norm_bytes, 34962)
        bv_idx = self._add_buffer_view(idx_bytes, 34963)

        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        zs = [p[2] for p in positions]

        acc_pos = len(self.accessors)
        self.accessors.append(
            {
                "bufferView": bv_pos,
                "componentType": 5126,
                "count": len(positions),
                "type": "VEC3",
                "min": [min(xs), min(ys), min(zs)],
                "max": [max(xs), max(ys), max(zs)],
            }
        )

        acc_norm = len(self.accessors)
        self.accessors.append(
            {
                "bufferView": bv_norm,
                "componentType": 5126,
                "count": len(normals),
                "type": "VEC3",
            }
        )

        acc_idx = len(self.accessors)
        self.accessors.append(
            {
                "bufferView": bv_idx,
                "componentType": 5123,
                "count": len(indices),
                "type": "SCALAR",
            }
        )

        mesh_idx = len(self.meshes)
        self.meshes.append(
            {
                "name": name,
                "primitives": [
                    {
                        "attributes": {"POSITION": acc_pos, "NORMAL": acc_norm},
                        "indices": acc_idx,
                        "material": material_idx,
                    }
                ],
            }
        )

        node = {"name": name, "mesh": mesh_idx, "translation": list(translation)}
        if any(abs(a) > 1e-5 for a in rotation_euler_deg):
            node["rotation"] = list(_euler_deg_to_quat(*rotation_euler_deg))
        self.nodes.append(node)

    def add_box(
        self,
        name: str,
        pos: Tuple[float, float, float],
        size: Tuple[float, float, float],
        material_idx: int,
        rot_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        hx, hy, hz = size[0] * 0.5, size[1] * 0.5, size[2] * 0.5
        faces = [
            ((0, 0, 1), [(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]),
            ((0, 0, -1), [(hx, -hy, -hz), (-hx, -hy, -hz), (-hx, hy, -hz), (hx, hy, -hz)]),
            ((1, 0, 0), [(hx, -hy, hz), (hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz)]),
            ((-1, 0, 0), [(-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz)]),
            ((0, 1, 0), [(-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz), (-hx, hy, -hz)]),
            ((0, -1, 0), [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz)]),
        ]
        positions, normals, indices = [], [], []
        for f_idx, (normal, verts) in enumerate(faces):
            base = f_idx * 4
            positions.extend(verts)
            normals.extend([normal] * 4)
            indices.extend([base, base + 1, base + 2, base, base + 2, base + 3])
        self.add_mesh(name, positions, normals, indices, material_idx, pos, rot_deg)

    def add_cylinder(
        self,
        name: str,
        pos: Tuple[float, float, float],
        radius: float,
        height: float,
        material_idx: int,
        segments: int = 20,
        rot_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        hy = height * 0.5
        positions, normals, indices = [], [], []

        # Side quads
        for i in range(segments):
            a0 = 2.0 * math.pi * i / segments
            a1 = 2.0 * math.pi * (i + 1) / segments
            c0, s0 = math.cos(a0), math.sin(a0)
            c1, s1 = math.cos(a1), math.sin(a1)
            base = len(positions)
            positions.extend([
                (radius * c0, -hy, radius * s0),
                (radius * c1, -hy, radius * s1),
                (radius * c1, hy, radius * s1),
                (radius * c0, hy, radius * s0),
            ])
            normals.extend([(c0, 0.0, s0), (c1, 0.0, s1), (c1, 0.0, s1), (c0, 0.0, s0)])
            indices.extend([base, base + 2, base + 1, base, base + 3, base + 2])

        # Top & Bottom caps
        for sign, ny in ((1, 1.0), (-1, -1.0)):
            center_idx = len(positions)
            positions.append((0.0, sign * hy, 0.0))
            normals.append((0.0, ny, 0.0))
            ring_start = len(positions)
            for i in range(segments):
                a = 2.0 * math.pi * i / segments
                positions.append((radius * math.cos(a), sign * hy, radius * math.sin(a)))
                normals.append((0.0, ny, 0.0))
            for i in range(segments):
                n_i = (i + 1) % segments
                if sign > 0:
                    indices.extend([center_idx, ring_start + n_i, ring_start + i])
                else:
                    indices.extend([center_idx, ring_start + i, ring_start + n_i])

        self.add_mesh(name, positions, normals, indices, material_idx, pos, rot_deg)

    def add_sphere(
        self,
        name: str,
        pos: Tuple[float, float, float],
        scale: Tuple[float, float, float],
        material_idx: int,
        rings: int = 14,
        sectors: int = 20,
    ):
        rx, ry, rz = scale[0] * 0.5, scale[1] * 0.5, scale[2] * 0.5
        positions, normals, indices = [], [], []
        for r in range(rings + 1):
            phi = math.pi * r / rings
            sp, cp = math.sin(phi), math.cos(phi)
            for s in range(sectors + 1):
                theta = 2.0 * math.pi * s / sectors
                st, ct = math.sin(theta), math.cos(theta)
                nx, ny, nz = ct * sp, cp, st * sp
                positions.append((rx * nx, ry * ny, rz * nz))
                # Normalize scaled normal
                ln = math.sqrt((nx / max(rx, 1e-6)) ** 2 + (ny / max(ry, 1e-6)) ** 2 + (nz / max(rz, 1e-6)) ** 2)
                normals.append((nx / max(rx, 1e-6) / ln, ny / max(ry, 1e-6) / ln, nz / max(rz, 1e-6) / ln))

        stride = sectors + 1
        for r in range(rings):
            for s in range(sectors):
                a = r * stride + s
                b = (r + 1) * stride + s
                c = b + 1
                d = a + 1
                indices.extend([a, b, c, a, c, d])

        self.add_mesh(name, positions, normals, indices, material_idx, pos)

    def save_glb(self, out_path: str):
        self._pad4()
        root_indices = list(range(len(self.nodes)))
        gltf = {
            "asset": {"version": "2.0", "generator": "Lunar Aurora Heritage Exporter"},
            "scene": 0,
            "scenes": [{"name": self.name, "nodes": root_indices}],
            "nodes": self.nodes,
            "meshes": self.meshes,
            "materials": self.materials,
            "accessors": self.accessors,
            "bufferViews": self.buffer_views,
            "buffers": [{"byteLength": len(self.bin_data)}],
        }
        json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
        while len(json_bytes) % 4 != 0:
            json_bytes += b" "

        total_length = 12 + 8 + len(json_bytes) + 8 + len(self.bin_data)
        with open(out_path, "wb") as f:
            f.write(struct.pack("<3I", 0x46546C67, 2, total_length))
            f.write(struct.pack("<2I", len(json_bytes), 0x4E4F534A))
            f.write(json_bytes)
            f.write(struct.pack("<2I", len(self.bin_data), 0x004E4942))
            f.write(self.bin_data)


def _euler_deg_to_quat(rx_d: float, ry_d: float, rz_d: float) -> Tuple[float, float, float, float]:
    rx, ry, rz = math.radians(rx_d) * 0.5, math.radians(ry_d) * 0.5, math.radians(rz_d) * 0.5
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    return (
        sx * cy * cz - cx * sy * sz,
        cx * sy * cz + sx * cy * sz,
        cx * cy * sz - sx * sy * cz,
        cx * cy * cz + sx * sy * sz,
    )


def _setup_palette(b: GlbBuilder) -> Dict[str, int]:
    return {
        "sandstone": b.add_material("Sandstone", (0.80, 0.66, 0.48, 1.0), 0.05, 0.85),
        "granite": b.add_material("DarkGranite", (0.24, 0.27, 0.32, 1.0), 0.1, 0.8),
        "gold": b.add_material("ImperialGold", (0.95, 0.76, 0.20, 1.0), 0.88, 0.28),
        "cyan": b.add_material("GlowingCyan", (0.05, 0.88, 1.0, 1.0), 0.1, 0.2, (0.0, 0.55, 0.7)),
    }


def export_sun_temple(out_path: str):
    b = GlbBuilder("Grand_Solstice_Sun_Temple")
    m = _setup_palette(b)
    # Stepped Jagati Terrace
    b.add_box("JagatiTier1", (0, -0.055, 0), (0.22, 0.012, 0.22), m["granite"])
    b.add_box("JagatiTier2", (0, -0.043, 0), (0.19, 0.012, 0.19), m["sandstone"])
    b.add_box("JagatiTier3", (0, -0.031, 0), (0.16, 0.010, 0.16), m["granite"])
    # Sanctum
    b.add_box("SanctumWalls", (0, -0.004, 0), (0.105, 0.044, 0.105), m["sandstone"])
    # Vimana Spire Tiers
    for i, w in enumerate((0.095, 0.080, 0.065, 0.050, 0.036)):
        b.add_box(f"SpireTier_{i}", (0, 0.025 + i * 0.014, 0), (w, 0.013, w), m["sandstone"] if i % 2 == 0 else m["granite"])
    b.add_cylinder("AmalakaDisc", (0, 0.096, 0), 0.019, 0.008, m["gold"])
    b.add_sphere("KalashaFinial", (0, 0.108, 0), (0.014, 0.020, 0.014), m["gold"])
    # Perimeter Colonnade Pillars
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            if i == 0 and j == 0:
                continue
            b.add_cylinder(f"Pillar_{i}_{j}", (i * 0.068, -0.005, j * 0.068), 0.006, 0.044, m["sandstone"])
    # Dual Solar Chariot Wheels
    for side in (-1, 1):
        b.add_cylinder(f"ChariotWheel_{side}", (side * 0.088, -0.026, 0), 0.021, 0.007, m["gold"], 24, (0, 0, 90))
        b.add_sphere(f"WheelAxle_{side}", (side * 0.088, -0.026, 0), (0.012, 0.012, 0.012), m["granite"])
    b.save_glb(out_path)


def export_airavata(out_path: str):
    b = GlbBuilder("Celestial_Airavata_Sculpture")
    m = _setup_palette(b)
    b.add_box("Plinth", (0, -0.048, 0), (0.18, 0.018, 0.14), m["granite"])
    b.add_box("LotusTrim", (0, -0.036, 0), (0.16, 0.008, 0.12), m["gold"])
    b.add_sphere("Torso", (0, 0.012, 0), (0.085, 0.068, 0.115), m["sandstone"])
    b.add_sphere("Head", (0, 0.028, 0.062), (0.058, 0.056, 0.058), m["sandstone"])
    b.add_cylinder("Crown", (0, 0.062, 0.060), 0.014, 0.024, m["gold"])
    b.add_box("Caparison", (0, 0.028, -0.005), (0.088, 0.025, 0.055), m["gold"])
    b.add_box("EarL", (-0.036, 0.032, 0.050), (0.008, 0.038, 0.028), m["sandstone"], (0, -20, 0))
    b.add_box("EarR", (0.036, 0.032, 0.050), (0.008, 0.038, 0.028), m["sandstone"], (0, 20, 0))
    b.add_cylinder("TuskL", (-0.018, 0.014, 0.095), 0.0035, 0.040, m["gold"], 12, (65, 0, 0))
    b.add_cylinder("TuskR", (0.018, 0.014, 0.095), 0.0035, 0.040, m["gold"], 12, (65, 0, 0))
    b.add_cylinder("Trunk", (0, 0.002, 0.092), 0.008, 0.044, m["sandstone"], 14, (15, 0, 0))
    b.add_sphere("LotusBud", (0, -0.018, 0.105), (0.018, 0.018, 0.018), m["cyan"])
    for lx in (-0.024, 0.024):
        for lz in (-0.035, 0.032):
            b.add_cylinder(f"Leg_{lx}_{lz}", (lx, -0.018, lz), 0.011, 0.040, m["sandstone"])
    b.save_glb(out_path)


def export_lotus_gnomon(out_path: str):
    b = GlbBuilder("Solstitial_Lotus_Gnomon")
    m = _setup_palette(b)
    b.add_cylinder("OuterBasin", (0, -0.045, 0), 0.100, 0.024, m["granite"], 28)
    b.add_cylinder("CoolingWater", (0, -0.032, 0), 0.088, 0.008, m["cyan"], 28)
    for i in range(8):
        ang = math.radians(i * 45.0)
        b.add_box(
            f"LotusPetal_{i}",
            (math.cos(ang) * 0.055, -0.022, math.sin(ang) * 0.055),
            (0.032, 0.010, 0.020),
            m["sandstone"],
            (0, -i * 45.0, 20.0),
        )
    b.add_cylinder("ChronoPillar", (0, 0.035, 0), 0.012, 0.136, m["sandstone"], 20)
    b.add_box("BrassMeridian", (0, -0.028, 0), (0.004, 0.003, 0.17), m["gold"])
    b.add_sphere("SolarApex", (0, 0.106, 0), (0.022, 0.022, 0.022), m["gold"])
    b.save_glb(out_path)


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SonyPlayer_3DAssets")
    os.makedirs(out_dir, exist_ok=True)
    exports = [
        ("Grand_Solstice_Sun_Temple.glb", export_sun_temple),
        ("Celestial_Airavata_Sculpture.glb", export_airavata),
        ("Solstitial_Lotus_Gnomon.glb", export_lotus_gnomon),
    ]
    for filename, fn in exports:
        path = os.path.join(out_dir, filename)
        fn(path)
        size_kb = os.path.getsize(path) / 1024.0
        print(f"[GLB Export] Generated {filename} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
