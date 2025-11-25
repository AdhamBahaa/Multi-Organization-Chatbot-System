# Multi-Organization RAG Chatbot System

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![React](https://img.shields.io/badge/react-18.2.0-61DAFB.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)

A comprehensive, full-stack RAG (Retrieval-Augmented Generation) chatbot application featuring hierarchical user management, secure authentication, and advanced document processing capabilities.

## 🌟 Key Features

### 🧠 Advanced AI & Data Processing
- **RAG Architecture**: Combines retrieval-based search with generative AI for accurate, context-aware responses.
- **Google Gemini Integration**: Powered by Google's Gemini API for high-quality natural language understanding and generation.
- **Vector Search**: Utilizes **ChromaDB** for efficient semantic search and document embeddings.
- **Graph Knowledge Base** (Optional): Integrates **Neo4j** to map relationships between documents, chunks, and entities.
- **Document Management**: Supports uploading and processing of PDF and DOCX files.

### 🔐 Security & Access Control
- **Hierarchical Role-Based Access Control (RBAC)**:
  - **Super Admin**: System-wide management (Organizations, Admins).
  - **Admin**: Organization-level management (Users, Documents).
  - **User**: End-user access with custom organization-specific roles (e.g., Student, Teacher, Manager).
- **Secure Authentication**: JWT-based stateless authentication.
- **Secure Onboarding**: Email-based password setup flow for new accounts.

### 💻 Modern User Interface
- **Role-Specific Dashboards**: Tailored views for Super Admins, Admins, and Users.
- **Interactive Graph Visualization**: Visual exploration of knowledge graphs using **Cytoscape.js**.
- **Responsive Design**: Fully optimized for desktop, tablet, and mobile devices.
- **Premium Aesthetics**: Modern UI with glassmorphism, gradients, and smooth animations.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQL Server (via ODBC/SQLAlchemy)
- **Vector DB**: ChromaDB
- **Graph DB**: Neo4j
- **AI/LLM**: LangChain, Google Generative AI
- **Auth**: Python-JOSE, Passlib
- **Validation**: Pydantic

### Frontend
- **Framework**: React.js
- **Routing**: React Router
- **State/Network**: Axios
- **Visualization**: Cytoscape.js
- **Styling**: Modern CSS3

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Node.js 14+**
- **SQL Server** (ODBC Driver 17)
- **Google Gemini API Key**
- **Neo4j** (Optional, for graph features)

### 1. Backend Setup
Navigate to the `backend` directory and follow the setup instructions:
```bash
cd backend
pip install -r requirements.txt
# Configure .env file (see backend/README.md)
python main.py
```
*Server runs on `http://localhost:8002`*

### 2. Frontend Setup
Navigate to the `frontend` directory and start the client:
```bash
cd frontend
npm install
npm start
```
*Client runs on `http://localhost:3000`*

---

## 📂 Project Structure

```
root/
├── backend/             # FastAPI Server & Logic
│   ├── app/             # API Endpoints, Models, Services
│   ├── main.py          # Entry point
│   └── requirements.txt # Python dependencies
│
├── frontend/            # React Client Application
│   ├── src/             # Components, Pages, Hooks
│   ├── public/          # Static assets
│   └── package.json     # JS dependencies
│
└── README.md            # This file
```

## 📚 Documentation
For detailed instructions on API endpoints, configuration, and specific features, please refer to the README files in the respective directories:
- [Backend Documentation](./backend/README.md)
- [Frontend Documentation](./frontend/README.md)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

If you have any questions or feedback, please reach out to the development team.
