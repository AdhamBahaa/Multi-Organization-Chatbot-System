# Team Documents

This directory contains documents that are shared across all team members.

## Purpose

All uploaded documents are stored here and are visible to all team members. This is the **only** document storage location for the team.

## How to Use

1. **Start the server:**

   ```bash
   python main.py
   ```

2. **Upload documents** through the web interface
3. **All team members** will see the same documents
4. **Coordinate** with your team before deleting documents

## Directory Structure

```
shared_uploads/
├── document_registry.json    # Document metadata (shared)
├── chroma_db/               # Vector database (shared)
└── [uploaded_files]         # Actual document files (shared)
```

## Team Guidelines

- ✅ Use descriptive file names: `test_feature_x.pdf`, `bug_reproduction.docx`
- ✅ Communicate before deleting documents
- ✅ Keep test documents organized
- ⚠️ Don't upload sensitive or personal documents
- ⚠️ Coordinate document management with team

## Team Collaboration

This project is configured for **shared team development only**. There is no individual mode - all team members work with the same document set.

## Version Control

This directory is **NOT** gitignored, so:

- Documents will be committed to the repository
- All team members will have the same documents
- Changes are tracked in version control
