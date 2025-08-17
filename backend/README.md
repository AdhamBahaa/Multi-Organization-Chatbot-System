# RAG Chatbot Backend

A FastAPI-based backend for a RAG (Retrieval-Augmented Generation) chatbot with hierarchical user management.

## Features

- **Hierarchical User Management**: Super Admin → Organizations → Admins → Users
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Different permissions for different user types
- **Document Management**: Upload, process, and query documents
- **AI Chat**: Powered by Google Gemini API
- **Vector Database**: ChromaDB for document embeddings

## User Hierarchy

1. **Super Admin** (Only one exists)

   - Can create Organizations
   - Can create Admins for Organizations
   - System-wide access

2. **Admin** (Multiple per Organization)

   - Can create Users within their Organization
   - Manages their Organization's users
   - Organization-scoped access
   - Multiple admins can collaborate within the same organization

3. **User** (Multiple per Organization)

   - Belongs to one Organization
   - Managed by one Admin
   - Has a specific role within the organization
   - Basic access to chat and documents

### User Management

- **Create Users**: Admins can create users in their organization
- **Automatic Organization Assignment**: Users are automatically assigned to the Admin's organization
- **User Roles**: Unlimited custom roles (default: "Member")
- **Password Management**: Users set their own passwords
- **Profile Updates**: Users can update their information

### User Roles

- **Super Admin**: System-wide access, manages organizations and admins
- **Admin**: Organization-level access, manages users within their organization
- **User**: Regular users with customizable roles (e.g., Member, Moderator, Analyst, Developer, Manager, etc.)
- **Default Role**: "Member" (can be changed to any custom role)

Roles are completely customizable - you can use any role name that fits your organization's needs.

## Database Schema

The system uses SQL Server with the following tables:

- **Organizations**: Company/team entities
- **Admins**: Organization administrators (multiple per organization)
- **Users**: Regular users managed by admins

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- SQL Server with ODBC Driver 17
- Google Gemini API key

### 2. Database Setup

Your database schema is already created in SQL Server. The system expects the following tables:

- **Organizations**: Company/team entities
- **Admins**: Organization administrators (multiple per organization)
- **Users**: Regular users managed by admins (with Role column)

The database will remain empty until you manually create organizations, admins, and users through the API endpoints.

### 3. Environment Configuration

Create a `.env` file in the backend directory:

```env
# Database Configuration
DB_USER=sa
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_NAME=chatbot
DB_DRIVER=ODBC+Driver+17+for+SQL+Server

# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here

# JWT Secret Key (change this in production)
SECRET_KEY=your-super-secret-key-here-change-in-production

# API Configuration
API_HOST=0.0.0.0
API_PORT=8002

# CORS Origins
CORS_ORIGINS=["http://localhost:3000"]
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the Application

```bash
python main.py
```

The API will be available at `http://localhost:8002`

## API Endpoints

### Authentication

- `POST /api/login` - User login
- `POST /api/set-password` - Set initial password
- `PUT /api/profile` - Update user profile
- `POST /api/change-password` - Change password

### Super Admin Operations

#### Organizations

- `POST /api/organizations` - Create organization
- `GET /api/organizations` - List all organizations
- `GET /api/organizations/{id}` - Get organization details
- `PUT /api/organizations/{id}` - Update organization
- `DELETE /api/organizations/{id}` - Delete organization

#### Admins

- `POST /api/admins` - Create admin
- `GET /api/admins` - List all admins
- `GET /api/admins/{id}` - Get admin details
- `PUT /api/admins/{id}` - Update admin
- `DELETE /api/admins/{id}` - Delete admin

### Admin Operations

#### Users

- `POST /api/users` - Create user
- `GET /api/users` - List organization users
- `GET /api/users/{id}` - Get user details
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

### User Operations

- `GET /api/profile` - Get user profile
