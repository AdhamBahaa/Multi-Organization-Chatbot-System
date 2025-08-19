import React, { useState, useEffect } from "react";
import { uploadDocument, getDocuments, deleteDocument } from "./api";
import "./Documents.css";

function Documents({ user }) {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const isAdmin = user && user.role === "admin";

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const docs = await getDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error("Failed to load documents:", error);
      if (!isAdmin) {
        setError("Document access restricted to admin users.");
      } else {
        setError("Failed to load documents. Please check your connection.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFiles = async (files) => {
    if (!isAdmin) {
      setError("Document upload is restricted to admin users only.");
      return;
    }

    const fileArray = Array.from(files);
    setUploading(true);
    setError(null);

    try {
      for (const file of fileArray) {
        // Validate file size
        if (file.size > 50 * 1024 * 1024) {
          // 50MB limit
          setError(`${file.name} is too large (max 50MB)`);
          continue;
        }

        // Validate file type
        const allowedTypes = [
          ".pdf",
          ".txt",
          ".csv",
          ".docx",
          ".doc",
          ".xlsx",
          ".xls",
          ".md",
        ];
        const fileExt = "." + file.name.split(".").pop().toLowerCase();
        if (!allowedTypes.includes(fileExt)) {
          setError(
            `${
              file.name
            } - File type not supported. Allowed: ${allowedTypes.join(", ")}`
          );
          continue;
        }

        console.log("Uploading file:", file.name);
        const result = await uploadDocument(file);
        console.log("Upload result:", result);

        // Add to documents list
        const newDoc = {
          id: result.id || Date.now(),
          filename: result.filename || file.name,
          original_filename: result.original_filename || file.name,
          file_type: result.file_type || file.type,
          file_size: result.file_size || file.size,
          processed: result.processed || false,
          chunk_count: result.chunk_count || 0,
          content_preview: result.content_preview || "",
          created_at: result.created_at || new Date().toISOString(),
        };
        setDocuments((prev) => [...prev, newDoc]);
      }

      // Reload documents to get the latest from server
      await loadDocuments();
    } catch (error) {
      console.error("Upload error:", error);
      setError(`Upload failed: ${error.message || "Please try again."}`);
    } finally {
      setUploading(false);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!isAdmin) {
      setError("Document deletion is restricted to admin users only.");
      return;
    }

    if (!window.confirm("Are you sure you want to delete this document?")) {
      return;
    }

    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((doc) => doc.id !== docId));
      setError(null); // Clear any previous errors
    } catch (error) {
      console.error("Delete error:", error);
      setError(`Delete failed: ${error.message || "Please try again."}`);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getFileIcon = (fileType) => {
    const type = fileType?.toLowerCase();
    if (type?.includes("pdf")) return "📄";
    if (type?.includes("word") || type?.includes("docx")) return "📝";
    if (type?.includes("excel") || type?.includes("xlsx")) return "📊";
    if (type?.includes("text") || type?.includes("txt")) return "📋";
    if (type?.includes("csv")) return "🗂️";
    return "📁";
  };

  if (loading) {
    return (
      <div className="documents-container">
        <h2>📁 Document Management</h2>
        <div style={{ textAlign: "center", padding: "40px" }}>
          Loading documents...
        </div>
      </div>
    );
  }

  // Non-admin users see view-only interface
  if (!isAdmin) {
    return (
      <div className="documents-container">
        <h2>📁 Document Library</h2>

        <div
          style={{
            background: "#fef3c7",
            color: "#92400e",
            padding: "15px",
            borderRadius: "8px",
            marginBottom: "20px",
            fontSize: "14px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <span style={{ fontSize: "18px" }}>ℹ️</span>
          <div>
            <strong>View Only Access</strong>
            <br />
            Document upload and management is restricted to admin users. You can
            view available documents and chat about them.
          </div>
        </div>

        {documents.length > 0 ? (
          <div>
            <h3>Available Documents ({documents.length})</h3>
            <div style={{ maxHeight: "400px", overflowY: "auto" }}>
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    padding: "15px",
                    backgroundColor: "#f9fafb",
                    borderRadius: "8px",
                    marginBottom: "10px",
                    border: "1px solid #e5e7eb",
                  }}
                >
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        marginBottom: "8px",
                      }}
                    >
                      <span style={{ fontSize: "20px", marginRight: "8px" }}>
                        {getFileIcon(doc.file_type)}
                      </span>
                      <div style={{ fontWeight: "500", color: "#374151" }}>
                        {doc.original_filename}
                      </div>
                    </div>

                    <div
                      style={{
                        fontSize: "14px",
                        color: "#6b7280",
                        marginBottom: "8px",
                      }}
                    >
                      Size: {formatFileSize(doc.file_size)} • Type:{" "}
                      {doc.file_type}
                      {doc.chunk_count > 0 &&
                        ` • ${doc.chunk_count} text chunks`}
                    </div>

                    {doc.content_preview && (
                      <div
                        style={{
                          fontSize: "12px",
                          color: "#6b7280",
                          fontStyle: "italic",
                          lineHeight: "1.4",
                          maxWidth: "400px",
                        }}
                      >
                        Preview: {doc.content_preview.substring(0, 100)}
                        {doc.content_preview.length > 100 && "..."}
                      </div>
                    )}

                    <div
                      style={{
                        fontSize: "12px",
                        color: "#9ca3af",
                        marginTop: "8px",
                      }}
                    >
                      Available since:{" "}
                      {new Date(doc.created_at).toLocaleString()}
                    </div>
                  </div>

                  <div
                    style={{
                      padding: "4px 8px",
                      backgroundColor: doc.processed ? "#dcfce7" : "#fef3c7",
                      color: doc.processed ? "#166534" : "#92400e",
                      borderRadius: "4px",
                      fontSize: "12px",
                    }}
                  >
                    {doc.processed
                      ? "✅ Available for Chat"
                      : "⏳ Processing..."}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div
            style={{
              textAlign: "center",
              padding: "30px",
              color: "#6b7280",
              fontSize: "14px",
            }}
          >
            No documents available yet. Contact your admin to upload documents
            for the knowledge base.
          </div>
        )}

        <div
          style={{
            marginTop: "20px",
            padding: "15px",
            backgroundColor: "#eff6ff",
            borderRadius: "8px",
            fontSize: "14px",
            color: "#1e40af",
          }}
        >
          💡 <strong>Tip:</strong> You can ask questions about these documents
          in the Chat section. The AI will search through the uploaded content
          to provide relevant answers.
        </div>
      </div>
    );
  }

  return (
    <div className="documents-container">
      <h2>📁 Document Management (Admin)</h2>

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

      <div
        style={{
          border: `2px dashed ${dragActive ? "#2563eb" : "#d1d5db"}`,
          borderRadius: "8px",
          padding: "40px",
          textAlign: "center",
          backgroundColor: dragActive ? "#eff6ff" : "#fafafa",
          marginBottom: "20px",
          position: "relative",
          cursor: "pointer",
        }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => isAdmin && document.getElementById("fileInput").click()}
      >
        <input
          id="fileInput"
          type="file"
          multiple
          onChange={handleFileInput}
          accept=".pdf,.txt,.csv,.docx,.doc,.xlsx,.xls,.md"
          style={{ display: "none" }}
          disabled={uploading || !isAdmin}
        />

        <div>
          <div style={{ fontSize: "48px", marginBottom: "15px" }}>
            {isAdmin ? "📁" : "🔒"}
          </div>
          <h3 style={{ margin: "0 0 10px 0", color: "#374151" }}>
            {dragActive
              ? "Drop files here!"
              : isAdmin
              ? "Upload Documents"
              : "Admin Access Required"}
          </h3>
          <p style={{ margin: "0 0 15px 0", color: "#6b7280" }}>
            {isAdmin
              ? "Drag and drop files here, or click to browse"
              : "Only admin users can upload documents"}
          </p>
          {isAdmin && (
            <button type="button" className="submit-btn" disabled={uploading}>
              {uploading ? "⏳ Uploading..." : "📤 Choose Files"}
            </button>
          )}
          <p
            style={{ margin: "15px 0 0 0", fontSize: "14px", color: "#9ca3af" }}
          >
            Supported: PDF, TXT, CSV, DOCX, XLSX, MD • Max 50MB per file
            {isAdmin && " • Admin access confirmed"}
          </p>
        </div>
      </div>

      {documents.length > 0 && isAdmin && (
        <div>
          <h3>📋 Uploaded Documents ({documents.length})</h3>
          <div style={{ maxHeight: "400px", overflowY: "auto" }}>
            {documents.map((doc) => (
              <div
                key={doc.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  padding: "15px",
                  backgroundColor: "#f9fafb",
                  borderRadius: "8px",
                  marginBottom: "10px",
                  border: "1px solid #e5e7eb",
                }}
              >
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      marginBottom: "8px",
                    }}
                  >
                    <span style={{ fontSize: "20px", marginRight: "8px" }}>
                      {getFileIcon(doc.file_type)}
                    </span>
                    <div style={{ fontWeight: "500", color: "#374151" }}>
                      {doc.original_filename}
                    </div>
                  </div>

                  <div
                    style={{
                      fontSize: "14px",
                      color: "#6b7280",
                      marginBottom: "8px",
                    }}
                  >
                    Size: {formatFileSize(doc.file_size)} • Type:{" "}
                    {doc.file_type}
                    {doc.chunk_count > 0 && ` • ${doc.chunk_count} text chunks`}
                  </div>

                  {doc.content_preview && (
                    <div
                      style={{
                        fontSize: "12px",
                        color: "#6b7280",
                        fontStyle: "italic",
                        lineHeight: "1.4",
                        maxWidth: "400px",
                      }}
                    >
                      Preview: {doc.content_preview.substring(0, 100)}
                      {doc.content_preview.length > 100 && "..."}
                    </div>
                  )}

                  <div
                    style={{
                      fontSize: "12px",
                      color: "#9ca3af",
                      marginTop: "8px",
                    }}
                  >
                    Uploaded: {new Date(doc.created_at).toLocaleString()}
                  </div>
                </div>

                <div
                  style={{ display: "flex", alignItems: "center", gap: "10px" }}
                >
                  <div
                    style={{
                      padding: "4px 8px",
                      backgroundColor: doc.processed ? "#dcfce7" : "#fef3c7",
                      color: doc.processed ? "#166534" : "#92400e",
                      borderRadius: "4px",
                      fontSize: "12px",
                    }}
                  >
                    {doc.processed ? "✅ Processed" : "⏳ Processing..."}
                  </div>

                  <button
                    onClick={() => handleDeleteDocument(doc.id)}
                    style={{
                      background: "rgba(239, 68, 68, 0.1)",
                      color: "#dc2626",
                      border: "1px solid rgba(239, 68, 68, 0.2)",
                      padding: "4px 8px",
                      borderRadius: "4px",
                      fontSize: "12px",
                      cursor: "pointer",
                    }}
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {documents.length === 0 && !loading && isAdmin && (
        <div
          style={{
            textAlign: "center",
            padding: "30px",
            color: "#6b7280",
            fontSize: "14px",
          }}
        >
          No documents uploaded yet. Upload some documents to get started!
        </div>
      )}
    </div>
  );
}

export default Documents;
