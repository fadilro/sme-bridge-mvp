import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import './Layout.css';

const Layout: React.FC = () => {
  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo-icon">SB</div>
          <span className="logo-text">SME Bridge</span>
        </div>
        
        <nav className="nav-menu">
          <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
            <span className="icon">📊</span>
            Dashboard
          </NavLink>
          <NavLink to="/review" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="icon">🔍</span>
            Bill Review
          </NavLink>
          <NavLink to="/exports" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="icon">📥</span>
            Exports
          </NavLink>
        </nav>
        
        <div className="sidebar-footer">
          <div className="sme-badge">
            <span className="sme-name">TechCorp SME</span>
            <span className="sme-id">ID: sme_123</span>
          </div>
        </div>
      </aside>
      
      <main className="main-content">
        <header className="page-header">
          <div className="header-search">
            {/* Placeholder for search if needed */}
          </div>
          <div className="user-profile">
            <div className="avatar">JD</div>
          </div>
        </header>
        
        <div className="content-inner fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
