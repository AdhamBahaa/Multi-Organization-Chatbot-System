import React, { useEffect, useMemo, useRef, useState } from "react";
import cytoscape from "cytoscape";
import dagre from "cytoscape-dagre";
import "./GraphExplorer.css";

// Register dagre layout for fast, readable graph
cytoscape.use(dagre);
const defaultLayout = {
  name: "dagre",
  // Left-to-right layout; change to TB for top-to-bottom
  rankDir: "LR",
  nodeSep: 40,
  edgeSep: 20,
  rankSep: 60,
  fit: true,
  padding: 30,
  animate: false,
};

const cyStyles = [
  {
    selector: "node",
    style: {
      "background-color": (ele) =>
        ele.data("type") === "Entity"
          ? "#6c8ef5"
          : ele.data("type") === "Chunk"
          ? "#f5a623"
          : ele.data("type") === "Document"
          ? "#7bd389"
          : ele.data("type") === "document"
          ? "#7bd389"
          : ele.data("type") === "context"
          ? "#1c7ed6"
          : "#888",
      label: "data(label)",
      color: "#222",
      "font-size": 10,
      "text-wrap": "wrap",
      "text-max-width": 120,
      "border-width": 1,
      "border-color": "#ddd",
    },
  },
  {
    selector: "edge",
    style: {
      width: 1.5,
      "line-color": "#bbb",
      "target-arrow-color": "#bbb",
      "target-arrow-shape": "triangle",
      label: "data(label)",
      "font-size": 8,
      "text-rotation": "autorotate",
      "curve-style": "bezier",
    },
  },
];

function toElements(graph) {
  const nodes = (graph?.nodes || []).map((n) => ({ data: { ...n } }));
  const edges = (graph?.edges || []).map((e) => {
    const sid = String(e.source);
    const tid = String(e.target);
    const lab = e.label ?? "";
    // stable deterministic id for edges to prevent excessive re-adding
    const id = e.id || `e:${sid}|${tid}|${lab}`;
    return { data: { id, source: sid, target: tid, label: lab } };
  });
  return { nodes, edges };
}

export default function GraphExplorer({
  graph,
  onSearch,
  onExpandEntities,
  onExpandChunks,
  loading = false,
  title = "Graph",
}) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const countsRef = useRef({ nodes: 0, edges: 0 });
  const memoElements = useMemo(() => toElements(graph), [graph]);
  const [query, setQuery] = useState("");
  const [selectedIds, setSelectedIds] = useState([]);

  // Initialize Cytoscape on mount
  useEffect(() => {
    if (!containerRef.current) return;
    const cy = cytoscape({
      container: containerRef.current,
      elements: [],
      style: cyStyles,
      layout: defaultLayout,
      // perf tuning
      pixelRatio: 1,
      wheelSensitivity: 0.2,
      textureOnViewport: true,
      motionBlur: false,
    });
    cy.on("select unselect", "node", () => {
      const ids = cy.$("node:selected").map((n) => n.data("id"));
      setSelectedIds(ids);
    });
    cyRef.current = cy;
    return () => {
      try {
        cy.destroy();
      } catch (e) {
        // ignore
      }
    };
  }, []);

  // Update graph when data changes (diff-based, batched)
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    const { nodes, edges } = memoElements;
    const newNodeIds = new Set(nodes.map((n) => n.data.id));
    const newEdgeIds = new Set(edges.map((e) => e.data.id));

    cy.startBatch();
    // Remove missing nodes/edges
    cy.nodes()
      .filter((n) => !newNodeIds.has(n.id()))
      .remove();
    cy.edges()
      .filter((e) => !newEdgeIds.has(e.id()))
      .remove();
    // Add new nodes
    const toAdd = [];
    for (const n of nodes) {
      if (cy.getElementById(n.data.id).empty()) toAdd.push(n);
    }
    for (const e of edges) {
      if (cy.getElementById(e.data.id).empty()) toAdd.push(e);
    }
    if (toAdd.length) cy.add(toAdd);
    cy.endBatch();

    // Run layout only when graph grows (prevents excessive relayouts)
    const prev = countsRef.current;
    const grew = nodes.length > prev.nodes || edges.length > prev.edges;
    countsRef.current = { nodes: nodes.length, edges: edges.length };
    if (grew) {
      cy.layout(defaultLayout).run();
    }
  }, [memoElements]);

  return (
    <div className="graph-explorer">
      <div className="toolbar">
        <strong style={{ marginRight: 8 }}>{title}</strong>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search entities..."
        />
        <button
          onClick={() => onSearch && onSearch(query)}
          disabled={!query || loading}
        >
          Search
        </button>
        <button
          onClick={() => {
            const cy = cyRef.current;
            if (cy) {
              cy.fit(undefined, 30);
            }
          }}
          title="Fit graph to view"
        >
          Fit
        </button>
        <button
          onClick={() => onExpandEntities && onExpandEntities(selectedIds)}
          disabled={!selectedIds.length || loading}
          title="Expand selected entities"
        >
          Expand Entities
        </button>
        <button
          onClick={() => onExpandChunks && onExpandChunks(selectedIds)}
          disabled={!selectedIds.length || loading}
          title="Expand selected chunks"
        >
          Expand Chunks
        </button>
      </div>
      <div className="graph-legend">
        <div>
          <span className="dot" style={{ background: "#6c8ef5" }} />
          Entity
        </div>
        <div>
          <span className="dot" style={{ background: "#f5a623" }} />
          Chunk
        </div>
        <div>
          <span className="dot" style={{ background: "#7bd389" }} />
          Document
        </div>
      </div>
      <div className="cy-container" ref={containerRef} />
    </div>
  );
}
