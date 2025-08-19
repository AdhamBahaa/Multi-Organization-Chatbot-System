# Frontend Dashboard

A modern React dashboard with role-based access control for managing organizations, admins, and users.

## 🚀 Quick Start

### Prerequisites

- Node.js (version 14 or higher)
- npm (comes with Node.js)

### Installation

1. **Navigate to the frontend directory:**

   ```bash
   cd frontend
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Start the development server:**

   ```bash
   npm start
   ```

4. **Open your browser** and go to `http://localhost:3000`

## 🔐 Login Credentials

### Super Admin (Default)

- **Email:** `superadmin@system.com`
- **Password:** `superadmin123`

## 🎯 Features

### Super Admin Dashboard

- ✅ Create, read, update, delete organizations
- ✅ Create, read, update, delete admins
- ✅ View statistics
- ✅ Assign admins to organizations

### Admin Dashboard

- ✅ Create, read, update, delete users
- ✅ View organization information
- ✅ Users automatically assigned to admin's organization

### User Dashboard

- ✅ View profile information
- ✅ See organization details
- ✅ See admin information

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── OrganizationManager.js
│   │   ├── AdminManager.js
│   │   ├── UserManager.js
│   │   ├── UserProfile.js
│   │   └── OrganizationInfo.js
│   ├── dashboards/          # Role-specific dashboards
│   │   ├── SuperAdminDashboard.js
│   │   ├── AdminDashboard.js
│   │   └── UserDashboard.js
│   ├── api.js              # API functions
│   ├── App.js              # Main app component
│   ├── Dashboard.js        # Dashboard router
│   ├── Login.js            # Login component
│   └── index.js            # App entry point
├── package.json            # Dependencies and scripts
└── README.md              # This file
```

## 🔧 Available Scripts

- `npm start` - Runs the app in development mode
- `npm build` - Builds the app for production
- `npm test` - Launches the test runner
- `npm eject` - Ejects from Create React App (one-way operation)

## 🌐 Backend Connection

Make sure your backend server is running on `http://localhost:8002` before testing the dashboard functionality.

## 🎨 Styling

The dashboard uses modern CSS with:

- Responsive design
- Beautiful gradients
- Card-based layouts
- Hover effects and animations
- Mobile-friendly interface

## 🔒 Security Features

- Role-based access control
- JWT token authentication
- Secure API communication
- Protected routes based on user roles

## 📱 Responsive Design

The dashboard is fully responsive and works on:

- Desktop computers
- Tablets
- Mobile phones

## 🐛 Troubleshooting

If you encounter any issues:

1. **Make sure all dependencies are installed:**

   ```bash
   npm install
   ```

2. **Clear npm cache if needed:**

   ```bash
   npm cache clean --force
   ```

3. **Check if the backend is running** on the correct port

4. **Verify your Node.js version** is 14 or higher

## 📞 Support

If you need help, check the backend README for API documentation or contact the development team.
