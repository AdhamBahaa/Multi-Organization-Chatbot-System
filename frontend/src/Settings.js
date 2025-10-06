import React, { useState, useEffect } from "react";
import {
  getSystemStats,
  getUsers,
  getOrganizationStats,
  debugOrganizationDocuments,
  getDocumentChunks,
  getGraphHealth,
  reindexGraph,
  startGraphReindexBackground,
  getGraphReindexStatus,
  getGraphDocumentSummary,
} from "./api";

function Settings() {
  const [stats, setStats] = useState({
    total_documents: 0,
    total_chunks: 0,
    vector_db_status: "unknown",
    ai_configured: false,
    organization_id: null,
    documents: [],
  });
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [debugInfo, setDebugInfo] = useState(null);
  const [debugLoading, setDebugLoading] = useState(false);
  const [openChunks, setOpenChunks] = useState({});
  // chunksCache shape: { [docId]: { [engine]: { chunks, chunk_count, ... } } }
  const [chunksCache, setChunksCache] = useState({});
  const [chunksLoading, setChunksLoading] = useState({});
  const [engineChoice, setEngineChoice] = useState({});
  const [graphHealth, setGraphHealth] = useState(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphActionMsg, setGraphActionMsg] = useState("");
  const [graphJob, setGraphJob] = useState(null);
  const [docSummaries, setDocSummaries] = useState({});

  useEffect(() => {
    loadSystemData();
    // Load graph health in parallel
    (async () => {
      try {
        const h = await getGraphHealth();
        setGraphHealth(h);
      } catch (e) {
        setGraphHealth({ enabled: false, status: "error", error: e.message });
      }
    })();
  }, []);

  const loadSystemData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Load organization-specific stats instead of system-wide stats
      try {
        const orgStats = await getOrganizationStats();
        setStats((prevStats) => ({
          ...prevStats,
          total_documents: orgStats.total_documents || 0,
          organization_id: orgStats.organization_id || null,
          documents: orgStats.documents || [],
        }));
      } catch (orgError) {
        console.log(
          "Organization stats not available, falling back to system stats"
        );
        // Fallback to system stats if organization stats fail
        const systemStats = await getSystemStats();
        setStats(systemStats);
      }

      // Try to load users (admin only)
      try {
        const userList = await getUsers();
        setUsers(userList);
      } catch (userError) {
        console.log("User list not available (admin access required)");
      }
    } catch (error) {
      console.error("Failed to load system data:", error);
      setError("Failed to load system settings");
    } finally {
      setLoading(false);
    }
  };

  const debugOrganization = async () => {
    setDebugLoading(true);
    try {
      const debugData = await debugOrganizationDocuments();
      setDebugInfo(debugData);
      console.log("Debug info:", debugData);
    } catch (error) {
      console.error("Debug failed:", error);
      setError("Debug failed");
    } finally {
      setDebugLoading(false);
    }
  };

  const toggleChunks = async (docId) => {
    setOpenChunks((prev) => ({ ...prev, [docId]: !prev[docId] }));
    const willOpen = !openChunks[docId];
    const engine = engineChoice[docId] || "docling";
    if (willOpen && !(chunksCache[docId] && chunksCache[docId][engine])) {
      setChunksLoading((p) => ({ ...p, [docId]: true }));
      try {
        const data = await getDocumentChunks(docId, engine);
        setChunksCache((p) => ({
          ...p,
          [docId]: { ...(p[docId] || {}), [engine]: data },
        }));
      } catch (e) {
        setChunksCache((p) => ({
          ...p,
          [docId]: { ...(p[docId] || {}), [engine]: { error: e.message } },
        }));
      } finally {
        setChunksLoading((p) => ({ ...p, [docId]: false }));
      }
    }
  };

  const changeEngine = async (docId, newEngine) => {
    setEngineChoice((p) => ({ ...p, [docId]: newEngine }));
    // If the panel is open and we don't have cache for the new engine, fetch it
    if (
      openChunks[docId] &&
      !(chunksCache[docId] && chunksCache[docId][newEngine])
    ) {
      setChunksLoading((p) => ({ ...p, [docId]: true }));
      try {
        const data = await getDocumentChunks(docId, newEngine);
        setChunksCache((p) => ({
          ...p,
          [docId]: { ...(p[docId] || {}), [newEngine]: data },
        }));
      } catch (e) {
        setChunksCache((p) => ({
          ...p,
          [docId]: { ...(p[docId] || {}), [newEngine]: { error: e.message } },
        }));
      } finally {
        setChunksLoading((p) => ({ ...p, [docId]: false }));
      }
    }
  };

  const triggerGraphReindex = async () => {
    setGraphLoading(true);
    setGraphActionMsg("");
    try {
      // Prefer background job to avoid UI blocking
      const start = await startGraphReindexBackground();
      setGraphJob(start);
      setGraphActionMsg(`Reindex started (job: ${start.job_id}).`);

      // Poll status until done/error
      const poll = async () => {
        try {
          const s = await getGraphReindexStatus(start.job_id);
          setGraphJob(s);
          if (s.state === "done") {
            setGraphActionMsg(
              `Reindex completed: indexed ${s.indexed ?? 0} document(s).`
            );
          } else if (s.state === "error") {
            setGraphActionMsg(`Reindex failed: ${s.error || "Unknown error"}`);
          } else {
            setGraphActionMsg(
              `Reindex ${s.state}... ${s.indexed ?? 0} document(s) processed`
            );
            setTimeout(poll, 2000);
          }
        } catch (e) {
          setGraphActionMsg(`Status error: ${e.message}`);
        }
      };
      setTimeout(poll, 1500);
    } catch (e) {
      setGraphActionMsg(`Reindex failed: ${e.message}`);
    } finally {
      setGraphLoading(false);
    }
  };

  const loadDocSummary = async (docId) => {
    setDocSummaries((p) => ({ ...p, [docId]: { loading: true } }));
    try {
      const s = await getGraphDocumentSummary(docId);
      setDocSummaries((p) => ({ ...p, [docId]: { ...s, loading: false } }));
    } catch (e) {
      setDocSummaries((p) => ({
        ...p,
        [docId]: { error: e.message, loading: false },
      }));
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "connected":
      case "healthy":
        return { bg: "#dcfce7", color: "#166534" };
      case "error":
      case "disconnected":
        return { bg: "#fef2f2", color: "#dc2626" };
      default:
        return { bg: "#fef3c7", color: "#92400e" };
    }
  };

  const pill = (text, color) => (
    <span
      style={{
        background: color || "#f1f5f9",
        color: "#0f172a",
        padding: "2px 8px",
        borderRadius: 999,
        fontSize: 12,
        marginLeft: 6,
      }}
    >
      {text}
    </span>
  );

  if (loading) {
    return (
      <div className="card">
        <h2>System Settings</h2>
        <div style={{ textAlign: "center", padding: "40px" }}>
          Loading system information...
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>System Settings & Status</h2>

      {error && (
        <div
          style={{
            background: "rgba(239, 68, 68, 0.1)",
            color: "#dc2626",
            padding: "10px",
            borderRadius: "6px",
            marginBottom: "20px",
            fontSize: "14px",
          }}
        >
          {error}
        </div>
      )}

      {/* Graph DB Status */}
      <div style={{ marginBottom: 20 }}>
        <h3>Graph Database</h3>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ fontSize: 12, color: "#334155" }}>Status:</div>
          {graphHealth ? (
            <>
              {pill(
                graphHealth.status || (graphHealth.enabled ? "ok" : "disabled"),
                graphHealth.status === "ok"
                  ? "#dcfce7"
                  : graphHealth.status === "error"
                  ? "#fee2e2"
                  : "#fde68a"
              )}
              {graphHealth.error && (
                <span style={{ fontSize: 12, color: "#b91c1c" }}>
                  {graphHealth.error}
                </span>
              )}
            </>
          ) : (
            <span style={{ fontSize: 12, color: "#64748b" }}>Loading...</span>
          )}
        </div>
        <div style={{ marginTop: 10 }}>
          <button
            onClick={triggerGraphReindex}
            disabled={graphLoading}
            style={{
              padding: "6px 10px",
              backgroundColor: graphLoading ? "#93c5fd" : "#3b82f6",
              color: "white",
              border: "none",
              borderRadius: 4,
              cursor: graphLoading ? "default" : "pointer",
              fontSize: 12,
            }}
          >
            {graphLoading ? "Reindexing..." : "Reindex Graph (Org)"}
          </button>
          {graphActionMsg && (
            <div style={{ fontSize: 12, color: "#334155", marginTop: 6 }}>
              {graphActionMsg}
            </div>
          )}
        </div>
      </div>

      {/* Document Statistics */}
      <div style={{ marginBottom: "30px" }}>
        <h3>Document Statistics</h3>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "15px",
            marginTop: "15px",
          }}
        >
          <div
            style={{
              padding: "20px",
              backgroundColor: "#eff6ff",
              borderRadius: "8px",
              textAlign: "center",
            }}
          >
            <div
              style={{ fontSize: "32px", fontWeight: "bold", color: "#2563eb" }}
            >
              {stats.total_documents}
            </div>
            <div
              style={{ fontSize: "14px", color: "#1e40af", marginTop: "5px" }}
            >
              Organization Documents
            </div>
          </div>

          <div
            style={{
              padding: "20px",
              backgroundColor: "#f0fdf4",
              borderRadius: "8px",
              textAlign: "center",
            }}
          >
            <div
              style={{ fontSize: "32px", fontWeight: "bold", color: "#16a34a" }}
            >
              {stats.total_chunks}
            </div>
            <div
              style={{ fontSize: "14px", color: "#15803d", marginTop: "5px" }}
            >
              Text Chunks
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Document Information */}
      {stats.documents && stats.documents.length > 0 && (
        <div style={{ marginBottom: "30px" }}>
          <h3>Document Details</h3>
          <div
            style={{
              padding: "15px",
              backgroundColor: "#f8fafc",
              borderRadius: "8px",
            }}
          >
            <div
              style={{
                marginBottom: "10px",
                fontSize: "14px",
                color: "#64748b",
              }}
            >
              Organization ID: {stats.organization_id}
            </div>
            {stats.documents.map((doc, index) => (
              <div
                key={doc.id}
                style={{
                  padding: "12px",
                  backgroundColor: "white",
                  borderRadius: "6px",
                  marginBottom: "8px",
                  border: "1px solid #e2e8f0",
                }}
              >
                <div
                  style={{
                    fontWeight: "500",
                    color: "#374151",
                    marginBottom: "4px",
                  }}
                >
                  {doc.filename}
                </div>
                <div style={{ fontSize: 12, color: "#6b7280" }}>
                  ID: {doc.id} • Organization: {doc.organization_id}
                </div>
                <div style={{ fontSize: 12, color: "#6b7280" }}>
                  Text:{" "}
                  {doc.has_extracted_text ? "✅ Extracted" : "❌ Not extracted"}{" "}
                  • Length: {doc.text_length} chars • Chunks: {doc.chunk_count}
                </div>

                {/* Graph summary */}
                <div style={{ marginTop: 6 }}>
                  <button
                    onClick={() => loadDocSummary(doc.id)}
                    style={{
                      padding: "4px 8px",
                      backgroundColor: "#10b981",
                      color: "white",
                      border: "none",
                      borderRadius: 4,
                      cursor: "pointer",
                      fontSize: 12,
                      marginRight: 8,
                    }}
                  >
                    Graph Summary
                  </button>
                  {docSummaries[doc.id]?.loading && (
                    <span style={{ fontSize: 12, color: "#64748b" }}>
                      Loading...
                    </span>
                  )}
                  {docSummaries[doc.id]?.error && (
                    <span style={{ fontSize: 12, color: "#b91c1c" }}>
                      {docSummaries[doc.id].error}
                    </span>
                  )}
                  {docSummaries[doc.id] &&
                    !docSummaries[doc.id].loading &&
                    !docSummaries[doc.id].error && (
                      <span style={{ fontSize: 12, color: "#334155" }}>
                        Chunks: {docSummaries[doc.id].chunks} • Entities:{" "}
                        {docSummaries[doc.id].entities}
                      </span>
                    )}
                </div>

                {doc.has_extracted_text && (
                  <div style={{ marginTop: "8px" }}>
                    <button
                      onClick={() => toggleChunks(doc.id)}
                      style={{
                        padding: "6px 10px",
                        backgroundColor: "#2563eb",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        fontSize: "12px",
                      }}
                    >
                      {openChunks[doc.id]
                        ? "Hide chunks"
                        : "View chunks (Docling)"}
                    </button>
                    <span
                      style={{
                        marginLeft: "10px",
                        fontSize: "12px",
                        color: "#475569",
                      }}
                    >
                      Engine:{" "}
                    </span>
                    <select
                      value={engineChoice[doc.id] || "docling"}
                      onChange={(e) => changeEngine(doc.id, e.target.value)}
                      style={{
                        padding: "4px 6px",
                        fontSize: "12px",
                        borderRadius: "4px",
                        border: "1px solid #cbd5e1",
                        marginLeft: "6px",
                      }}
                    >
                      <option value="docling">Docling</option>
                      <option value="docling-hierarchical">
                        Docling Hierarchical
                      </option>
                      <option value="simple">Simple</option>
                    </select>
                  </div>
                )}

                {openChunks[doc.id] && (
                  <div
                    style={{
                      marginTop: "10px",
                      backgroundColor: "#f8fafc",
                      padding: "10px",
                      borderRadius: "6px",
                      border: "1px solid #e2e8f0",
                    }}
                  >
                    {chunksLoading[doc.id] ? (
                      <div style={{ fontSize: "12px", color: "#64748b" }}>
                        Loading chunks...
                      </div>
                    ) : (
                      <div>
                        {(() => {
                          const engine = engineChoice[doc.id] || "docling";
                          const data = chunksCache[doc.id]?.[engine];
                          if (!data) return null;
                          if (data.error)
                            return (
                              <div style={{ fontSize: 12, color: "#b91c1c" }}>
                                {data.error}
                              </div>
                            );
                          return (
                            <div>
                              <div
                                style={{
                                  fontSize: 12,
                                  color: "#334155",
                                  marginBottom: 6,
                                }}
                              >
                                Used Engine:{" "}
                                {data.used_engine || data.engine || engine} •
                                Chunks: {data.chunk_count}
                              </div>
                              <div
                                style={{
                                  maxHeight: 220,
                                  overflowY: "auto",
                                  fontSize: 12,
                                  color: "#0f172a",
                                }}
                              >
                                <ol style={{ margin: 0, paddingLeft: 18 }}>
                                  {data.chunks?.map((c, i) => (
                                    <li key={i} style={{ marginBottom: 6 }}>
                                      {c}
                                    </li>
                                  ))}
                                </ol>
                              </div>
                            </div>
                          );
                        })()}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Model Settings */}
      <div style={{ marginBottom: "30px" }}>
        <h3>AI Model Configuration</h3>
        <div
          style={{
            padding: "15px",
            backgroundColor: "#f9fafb",
            borderRadius: "8px",
          }}
        >
          <div style={{ marginBottom: "15px" }}>
            <label
              style={{
                display: "block",
                marginBottom: "5px",
                fontWeight: "500",
              }}
            >
              Model: Google Gemini 1.5 Flash
            </label>
            <div style={{ fontSize: "14px", color: "#6b7280" }}>
              Fast and efficient model for RAG applications
            </div>
          </div>

          <div style={{ marginBottom: "15px" }}>
            <label
              style={{
                display: "block",
                marginBottom: "5px",
                fontWeight: "500",
              }}
            >
              Temperature: 0.1
            </label>
            <div style={{ fontSize: "14px", color: "#6b7280" }}>
              Low temperature for consistent, factual responses
            </div>
          </div>

          <div style={{ marginBottom: "15px" }}>
            <label
              style={{
                display: "block",
                marginBottom: "5px",
                fontWeight: "500",
              }}
            >
              Max Tokens: 500
            </label>
            <div style={{ fontSize: "14px", color: "#6b7280" }}>
              Maximum response length
            </div>
          </div>
        </div>
      </div>

      {/* Debug Section */}
      <div style={{ marginBottom: "30px" }}>
        <h3>Debug & Troubleshooting</h3>
        <div
          style={{
            padding: "15px",
            backgroundColor: "#fef3c7",
            borderRadius: "8px",
          }}
        >
          <div style={{ marginBottom: "15px" }}>
            <button
              onClick={debugOrganization}
              disabled={debugLoading}
              style={{
                padding: "10px 20px",
                backgroundColor: "#f59e0b",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "14px",
              }}
            >
              {debugLoading ? "Loading..." : "Debug Organization Filtering"}
            </button>
            <div
              style={{ fontSize: "12px", color: "#92400e", marginTop: "5px" }}
            >
              Click to see detailed information about your organization's
              documents
            </div>
          </div>

          {debugInfo && (
            <div style={{ marginTop: "15px", fontSize: "12px" }}>
              <h4 style={{ margin: "0 0 10px 0", color: "#92400e" }}>
                Debug Information:
              </h4>
              <pre
                style={{
                  backgroundColor: "#fef3c7",
                  padding: "10px",
                  borderRadius: "4px",
                  overflow: "auto",
                  fontSize: "11px",
                }}
              >
                {JSON.stringify(debugInfo, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* User Management (Admin Only) */}
      {users.length > 0 && (
        <div style={{ marginBottom: "30px" }}>
          <h3>User Management</h3>
          <div style={{ maxHeight: "200px", overflowY: "auto" }}>
            {users.map((user) => (
              <div
                key={user.user_id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "12px",
                  backgroundColor: "#f9fafb",
                  borderRadius: "6px",
                  marginBottom: "8px",
                }}
              >
                <div>
                  <div style={{ fontWeight: "500", color: "#374151" }}>
                    {user.full_name}
                  </div>
                  <div style={{ fontSize: "14px", color: "#6b7280" }}>
                    {user.email} • Role: {user.role}
                  </div>
                </div>
                <div
                  style={{
                    padding: "4px 8px",
                    backgroundColor: user.password_hash ? "#dcfce7" : "#fef2f2",
                    color: user.password_hash ? "#166534" : "#dc2626",
                    borderRadius: "4px",
                    fontSize: "12px",
                  }}
                >
                  {user.password_hash ? "Active" : "Setup Required"}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Refresh Button */}
      <div style={{ textAlign: "center" }}>
        <button onClick={loadSystemData} className="button" disabled={loading}>
          {loading ? "Refreshing..." : "Refresh Status"}
        </button>
      </div>

      <div
        style={{
          fontSize: "12px",
          color: "#6b7280",
          textAlign: "center",
          marginTop: "20px",
          padding: "15px",
          backgroundColor: "#f9fafb",
          borderRadius: "6px",
        }}
      >
        <div style={{ marginBottom: "8px" }}>
          <strong>API Endpoint:</strong> http://localhost:8002/api
        </div>
        <div style={{ marginBottom: "8px" }}>
          <strong>Frontend:</strong> http://localhost:3000
        </div>
        <div>
          <strong>Documentation:</strong>{" "}
          <a
            href="http://localhost:8002/docs"
            target="_blank"
            rel="noopener noreferrer"
          >
            API Docs
          </a>
        </div>
      </div>
    </div>
  );
}

export default Settings;
