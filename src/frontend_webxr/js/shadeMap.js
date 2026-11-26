/**
 * ShadeMap.js - Renders Mahabalipuram 2D/Spatial Sanctuary Graph with Dual Solar vs. Shaded Routes,
 * Live Tourist Beacon, Active Visitor Crowd Badges, and Heat Exposure Saved (%) Readout.
 */
class ShadeMapRenderer {
    constructor(svgElement, badgeElement) {
        this.svg = svgElement;
        this.badge = badgeElement;
        this.nodes = [];
        this.edges = [];
        this.telemetry = null;
        this.visitedSteps = new Set([1]);
        this.currentStep = 1;
        this.playerPos = { x: 0, y: 0 };
        this.onNodeClick = null;
    }

    setSiteGeometry(nodes, edges) {
        this.nodes = Array.isArray(nodes) ? nodes : [];
        this.edges = Array.isArray(edges) ? edges : [];
        this.render();
    }

    setTelemetry(telemetry) {
        this.telemetry = telemetry;
        if (this.badge && telemetry) {
            const saved = telemetry.heat_exposure_saved_pct ?? 0;
            const sunDeg = telemetry.solar_elevation_deg ?? 0;
            const deltaM = telemetry.route_distance_delta_meters ?? 0;
            this.badge.innerHTML =
                `<span style="color:#ff5252;">● Sun</span> vs ` +
                `<span style="color:#00e676;">● Shaded</span> ` +
                `| <strong>Heat Saved: ${saved}%</strong> ` +
                `(${deltaM >= 0 ? "+" : ""}${deltaM}m, Sun ${sunDeg}°)`;
        }
        this.render();
    }

    setProgress({ currentStep, visitedSteps, playerPos }) {
        if (currentStep) this.currentStep = currentStep;
        if (Array.isArray(visitedSteps)) this.visitedSteps = new Set(visitedSteps);
        if (playerPos && Number.isFinite(playerPos.x) && Number.isFinite(playerPos.y)) {
            this.playerPos = playerPos;
        }
        this.render();
    }

    _project(x, y) {
        // World bounds: x in [-55, 90], y in [-15, 155] -> SVG viewBox 0..320 x 0..240
        const px = 42 + ((x + 55) / 145) * 236;
        const py = 212 - ((y + 15) / 170) * 184;
        return { px, py };
    }

    render() {
        if (!this.svg || this.nodes.length === 0) return;

        const nodeById = {};
        for (const n of this.nodes) nodeById[n.id] = n;

        const ns = "http://www.w3.org/2000/svg";
        this.svg.setAttribute("viewBox", "0 0 320 240");
        this.svg.innerHTML = "";

        // Background ambient courtyard grid
        const bg = document.createElementNS(ns, "rect");
        bg.setAttribute("x", "0");
        bg.setAttribute("y", "0");
        bg.setAttribute("width", "320");
        bg.setAttribute("height", "240");
        bg.setAttribute("rx", "14");
        bg.setAttribute("fill", "rgba(7, 12, 22, 0.92)");
        this.svg.appendChild(bg);

        // Draw base stone pathways
        for (const e of this.edges) {
            const a = nodeById[e.source_id];
            const b = nodeById[e.target_id];
            if (!a || !b) continue;
            const p1 = this._project(a.x, a.y);
            const p2 = this._project(b.x, b.y);
            const line = document.createElementNS(ns, "line");
            line.setAttribute("x1", p1.px);
            line.setAttribute("y1", p1.py);
            line.setAttribute("x2", p2.px);
            line.setAttribute("y2", p2.py);
            line.setAttribute("stroke", "rgba(139, 162, 189, 0.25)");
            line.setAttribute("stroke-width", "2");
            this.svg.appendChild(line);
        }

        // Draw Red Shortest (Direct Sun) Route
        const drawRoute = (ids, color, width, dash) => {
            if (!Array.isArray(ids) || ids.length < 2) return;
            const pts = [];
            for (const id of ids) {
                const n = nodeById[id];
                if (!n) continue;
                const p = this._project(n.x, n.y);
                pts.push(`${p.px.toFixed(1)},${p.py.toFixed(1)}`);
            }
            if (pts.length < 2) return;
            const poly = document.createElementNS(ns, "polyline");
            poly.setAttribute("points", pts.join(" "));
            poly.setAttribute("fill", "none");
            poly.setAttribute("stroke", color);
            poly.setAttribute("stroke-width", String(width));
            poly.setAttribute("stroke-linecap", "round");
            poly.setAttribute("stroke-linejoin", "round");
            if (dash) poly.setAttribute("stroke-dasharray", dash);
            this.svg.appendChild(poly);
        };

        if (this.telemetry) {
            drawRoute(this.telemetry.shortest_path?.path_node_ids, "#ff5252", 3, "5,4");
            drawRoute(this.telemetry.shaded_path?.path_node_ids, "#00e676", 4.5, null);
        }

        // Draw Stop Nodes + Active Crowd Telemetry Badges
        const crowd = (this.telemetry && this.telemetry.active_visitor_nodes) || {};
        for (const n of this.nodes) {
            const p = this._project(n.x, n.y);
            const g = document.createElementNS(ns, "g");
            g.style.cursor = "pointer";
            g.addEventListener("click", () => {
                if (typeof this.onNodeClick === "function") this.onNodeClick(n);
            });

            const isCurrent = n.id === this.currentStep;
            const isVisited = this.visitedSteps.has(n.id);
            const isRest = n.category === "shade_rest" || n.has_tree_shade;

            if (isCurrent) {
                const halo = document.createElementNS(ns, "circle");
                halo.setAttribute("cx", p.px);
                halo.setAttribute("cy", p.py);
                halo.setAttribute("r", "12");
                halo.setAttribute("fill", "rgba(0, 229, 255, 0.22)");
                halo.setAttribute("stroke", "#00e5ff");
                halo.setAttribute("stroke-width", "1.5");
                g.appendChild(halo);
            }

            const dot = document.createElementNS(ns, "circle");
            dot.setAttribute("cx", p.px);
            dot.setAttribute("cy", p.py);
            dot.setAttribute("r", isCurrent ? "7.5" : "6");
            dot.setAttribute("fill", isCurrent ? "#00e5ff" : (isRest ? "#00e676" : (isVisited ? "#f4c430" : "#3a4b63")));
            dot.setAttribute("stroke", "#08101c");
            dot.setAttribute("stroke-width", "1.8");
            g.appendChild(dot);

            const num = document.createElementNS(ns, "text");
            num.setAttribute("x", p.px);
            num.setAttribute("y", p.py + 3.2);
            num.setAttribute("text-anchor", "middle");
            num.setAttribute("font-size", "8.5");
            num.setAttribute("font-weight", "700");
            num.setAttribute("fill", "#050911");
            num.textContent = String(n.id);
            g.appendChild(num);

            const label = document.createElementNS(ns, "text");
            label.setAttribute("x", p.px);
            label.setAttribute("y", p.py + 16);
            label.setAttribute("text-anchor", "middle");
            label.setAttribute("font-size", "7.2");
            label.setAttribute("fill", isCurrent ? "#ffffff" : "#9db4cc");
            label.textContent = n.name.split(" ")[0] + (n.name.split(" ")[1] ? " " + n.name.split(" ")[1] : "");
            g.appendChild(label);

            const crowdCount = crowd[String(n.id)] || 0;
            if (crowdCount > 0) {
                const pill = document.createElementNS(ns, "circle");
                pill.setAttribute("cx", p.px + 9);
                pill.setAttribute("cy", p.py - 8);
                pill.setAttribute("r", "5");
                pill.setAttribute("fill", "#f4c430");
                g.appendChild(pill);

                const ct = document.createElementNS(ns, "text");
                ct.setAttribute("x", p.px + 9);
                ct.setAttribute("y", p.py - 5.5);
                ct.setAttribute("text-anchor", "middle");
                ct.setAttribute("font-size", "6.5");
                ct.setAttribute("font-weight", "800");
                ct.setAttribute("fill", "#050911");
                ct.textContent = String(crowdCount);
                g.appendChild(ct);
            }

            this.svg.appendChild(g);
        }

        // Player live beacon
        const player = this._project(this.playerPos.x, this.playerPos.y);
        const beacon = document.createElementNS(ns, "circle");
        beacon.setAttribute("cx", player.px);
        beacon.setAttribute("cy", player.py);
        beacon.setAttribute("r", "4.5");
        beacon.setAttribute("fill", "#ffea00");
        beacon.setAttribute("stroke", "#ffffff");
        beacon.setAttribute("stroke-width", "1.5");
        this.svg.appendChild(beacon);
    }
}

window.ShadeMapRenderer = ShadeMapRenderer;
