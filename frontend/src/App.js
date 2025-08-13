import React, { useState, useEffect } from 'react';
import Login from './Login';
import Chat from './Chat';
import Documents from './Documents';
import Settings from './Settings';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('login');
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
      setCurrentPage('chat');
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setCurrentPage('chat');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setCurrentPage('login');
  };

  const renderPage = () => {
    if (!user && currentPage !== 'login') {
      return <Login onLogin={handleLogin} />;
    }

    switch (currentPage) {
      case 'login':
        return <Login onLogin={handleLogin} />;
      case 'chat':
        return <Chat user={user} />;
      case 'documents':
        return <Documents user={user} />;
      case 'settings':
        return <Settings user={user} />;
      default:
        return <Chat user={user} />;
    }
  };

  return (
    <div className="app">
      {user && (
        <nav className="navbar">
          <div className="nav-brand">
            <h2>🤖 RAG Chatbot</h2>
          </div>
          <div className="nav-links">
            <button 
              className={currentPage === 'chat' ? 'nav-btn active' : 'nav-btn'}
              onClick={() => setCurrentPage('chat')}
            >
              💬 Chat
            </button>
            <button 
              className={currentPage === 'documents' ? 'nav-btn active' : 'nav-btn'}
              onClick={() => setCurrentPage('documents')}
            >
              📁 Documents
            </button>
            <button 
              className={currentPage === 'settings' ? 'nav-btn active' : 'nav-btn'}
              onClick={() => setCurrentPage('settings')}
            >
              ⚙️ Settings
            </button>
            <button 
              className="nav-btn logout"
              onClick={handleLogout}
            >
              🚪 Logout
            </button>
          </div>
          <div className="user-info">
            👤 {user.username}
          </div>
        </nav>
      )}
      
      <main className="main-content">
        {renderPage()}
      </main>

    </div>
  );
}

export default App;
