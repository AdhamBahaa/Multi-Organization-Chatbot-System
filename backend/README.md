# RAG Chatbot Backend

A modular FastAPI backend for a RAG (Retrieval-Augmented Generation) chatbot system.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration settings
│   ├── models.py            # Pydantic models
│   ├── auth.py              # Authentication logic
│   ├── chat.py              # Chat and AI functionality
│   ├── documents.py         # Document management
│   ├── routes.py            # API routes
│   ├── utils.py             # Utility functions
│   ├── vector_db.py         # ChromaDB vector database
│   ├── document_store.py    # Persistent document registry
│   └── cleanup.py           # System cleanup utilities
├── shared_uploads/          # Team documents (version controlled)
│   ├── README.md           # Team guidelines
│   ├── document_registry.json
│   ├── chroma_db/
│   └── [team_documents]
├── main.py                  # Main application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Modules Overview

### `config.py`

- Environment variables and configuration settings
- API keys, CORS settings, file type configurations
- Demo user data (for development)

### `models.py`

- Pydantic models for request/response validation
- Login, chat, document, and system stats models

### `auth.py`

- User authentication logic
- Login endpoint handlers
- User information retrieval

### `chat.py`

- AI chat functionality using Google Gemini
- RAG (Retrieval-Augmented Generation) implementation
- Document search and context building

### `documents.py`

- Document upload, retrieval, and deletion
- File processing and text extraction
- System statistics

### `routes.py`

- All API endpoint definitions
- Route handlers and request/response mapping

### `utils.py`

- File processing utilities
- Text extraction from various file formats
- Document search functionality (now uses ChromaDB)
- File system operations

### `vector_db.py`

- ChromaDB vector database integration
- Document embedding and storage
- Semantic search functionality
- Vector similarity search

### `document_store.py`

- Persistent document registry
- JSON-based document metadata storage
- Automatic loading of existing documents on startup
- Data consistency management

### `cleanup.py`

- System cleanup utilities
- Orphaned file detection and removal
- ChromaDB entry validation
- Registry consistency checks

## Getting Started

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
# Create a .env file with:
GOOGLE_API_KEY=your_gemini_api_key_here
```

3. Run the application:

```bash
python main.py
```

**🔗 Team Mode**: This project is configured for shared team development. All team members see the same documents.

## API Endpoints

- `POST /api/login` - User authentication
- `GET /api/me` - Get current user info
- `POST /api/chat` - Send chat message
- `GET /api/sessions` - Get chat sessions
- `GET /api/documents` - Get all documents
- `POST /api/documents/upload` - Upload document
- `DELETE /api/documents/{id}` - Delete document
- `GET /api/system/stats` - Get system statistics
- `GET /health` - Health check

## Benefits of This Structure

1. **Modularity**: Each concern is separated into its own module
2. **Maintainability**: Easy to locate and modify specific functionality
3. **Testability**: Individual modules can be tested in isolation
4. **Scalability**: Easy to add new features or modify existing ones
5. **Readability**: Clear separation of concerns makes code easier to understand
6. **Reusability**: Utility functions and models can be reused across modules
7. **Vector Search**: ChromaDB integration provides semantic search capabilities

## Development

To add new features:

1. Add new models to `models.py`
2. Create business logic in appropriate module
3. Add routes to `routes.py`
4. Update configuration in `config.py` if needed

## File Processing

The system supports:

- PDF files (using PyPDF2)
- Word documents (DOC/DOCX using python-docx)
- Text files (TXT)
- CSV files

Text extraction is handled automatically during upload, and the extracted text is used for RAG functionality.

## Vector Database (ChromaDB)

The system now uses ChromaDB for:

- **Semantic Search**: Documents are embedded and stored as vectors
- **Chunking**: Documents are automatically split into manageable chunks
- **Similarity Search**: Queries are matched using vector similarity
- **Persistent Storage**: Vector embeddings are stored persistently
- **Metadata Storage**: Document metadata is stored alongside embeddings

This provides much more accurate and contextually relevant search results compared to simple keyword matching.

## Document Persistence

The system provides robust document persistence with team collaboration:

- **Persistent Registry**: Documents are stored in a JSON registry file
- **Automatic Loading**: Existing documents are loaded on server startup
- **Data Consistency**: Automatic cleanup of orphaned files and entries
- **Complete Deletion**: When documents are deleted, they're removed from:
  - File system (actual files)
  - Document registry (metadata)
  - ChromaDB (vector embeddings)
- **Team Sharing**: All documents are shared across team members

### Data Storage Structure

```
backend/shared_uploads/
├── document_registry.json    # Document metadata registry
├── chroma_db/               # ChromaDB vector database
└── [document_files]         # Actual uploaded files
```

The `shared_uploads/` directory is version controlled, ensuring all team members have the same documents.

## Team Development Guide

### 🔗 Shared Team Development

This project is configured for **shared team development only**. All team members work with the same document set, making collaboration seamless and consistent.

### Team Workflow

#### For Feature Development:

1. **Upload Test Documents**: Use consistent naming (e.g., `test_feature_x.pdf`)
2. **Test as Team**: Everyone can see and interact with the same documents
3. **Coordinate Changes**: Communicate before deleting or modifying documents

#### For Bug Fixing:

1. **Reproduce in Shared Environment**: Upload the problematic document
2. **Debug Together**: All team members can see the issue
3. **Test Fix**: Everyone can verify the solution works
4. **Document the Fix**: Add notes about the solution

#### For Testing:

1. **Create Test Suite**: Upload a standard set of test documents
2. **Share Test Cases**: Everyone has the same test data
3. **Run Tests**: All team members can run the same test scenarios

### Team Guidelines

#### Document Management:

- ✅ Use descriptive file names: `test_feature_x.pdf`, `bug_reproduction.docx`
- ✅ Communicate before deleting documents
- ✅ Keep test documents organized
- ✅ Document what each test document is for
- ⚠️ Don't upload sensitive or personal documents
- ⚠️ Coordinate document management with team

#### Team Coordination:

- Always check which documents are available before uploading
- Use clear naming conventions for test documents
- Coordinate document management with team
- Consider creating a team convention for document organization

### Version Control

The `shared_uploads/` directory is **NOT** gitignored, so:

- Documents will be committed to the repository
- All team members will have the same documents
- Changes are tracked in version control
- Team can see document history and changes
