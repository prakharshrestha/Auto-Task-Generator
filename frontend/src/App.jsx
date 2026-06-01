import React, { useState, useEffect } from 'react';
import { api } from './api';
import logoImg from './assets/logo.png';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Connection / Auth State
  const [isConnected, setIsConnected] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [checkingStatus, setCheckingStatus] = useState(true);


  
  // Data State
  const [tasks, setTasks] = useState([]);
  const [emailData, setEmailData] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [selectedEmail, setSelectedEmail] = useState(null);
  
  // UI State
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState(null);
  const [hiddenItems, setHiddenItems] = useState(() => {
    return JSON.parse(localStorage.getItem('hiddenItems') || '[]');
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [hoveredSection, setHoveredSection] = useState(null);

  const hideItem = (id) => {
    const newHidden = [...hiddenItems, id];
    setHiddenItems(newHidden);
    localStorage.setItem('hiddenItems', JSON.stringify(newHidden));
  };

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const data = await api.getTasks();
      setTasks(data.tasks || []);
    } catch (err) {
      if (err.message === "Gmail authentication required" || err.message.includes("401")) {
        setIsConnected(false);
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const data = await api.getUnreadCount();
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      console.error("Failed to fetch unread count:", err);
    }
  };

  const checkStatus = async () => {
    try {
      setCheckingStatus(true);
      const status = await api.getLoginStatus();
      if (status.connected) {
        setIsConnected(true);
        setUserEmail(status.email);
        fetchTasks();
        fetchUnreadCount();
      } else {
        setIsConnected(false);
        setUserEmail('');
      }
    } catch (err) {
      console.error("Failed to fetch connection status:", err);
      setIsConnected(false);
    } finally {
      setCheckingStatus(false);
    }
  };

  const handleLogout = async () => {
    try {
      setLoading(true);
      await api.logout();
    } catch (err) {
      console.error("Failed to disconnect from server:", err);
    } finally {
      setIsConnected(false);
      setUserEmail('');
      setTasks([]);
      setEmailData(null);
      setError(null);
      setLoading(false);
      // Clean redirect to root page
      window.location.href = window.location.origin + window.location.pathname;
    }
  };

  const handleExtractEmails = async () => {
    try {
      setExtracting(true);
      setError(null);
      // Fast fetch of raw emails
      const rawData = await api.getRawRecentEmails(15);
      setEmailData(rawData);
      setExtracting(false); // UI becomes responsive instantly

      // Async extract tasks for each important email
      rawData.senders.forEach(sender => {
        sender.emails.forEach(async (email) => {
          try {
            const result = await api.extractTasksForEmail(email.subject, email.body, sender.from_raw);
            if (result.tasks && result.tasks.length > 0) {
              setEmailData(prevData => {
                if (!prevData) return prevData;
                const newData = JSON.parse(JSON.stringify(prevData));
                newData.senders.forEach(s => {
                  s.emails.forEach(e => {
                    if (e.id === email.id) {
                      e.tasks = result.tasks;
                    }
                  });
                });
                return newData;
              });
              fetchTasks(); // Refresh total tasks in DB
            }
          } catch (e) {
            console.error("Extraction failed for email:", email.id, e);
          }
        });
      });
    } catch (err) {
      if (err.message === "Gmail authentication required" || err.message.includes("401")) {
        setIsConnected(false);
      }
      setError(err.message);
      setExtracting(false);
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const loginStatus = params.get('login');
    const emailParam = params.get('email');
    const errorParam = params.get('error');

    if (loginStatus === 'success' && emailParam) {
      setIsConnected(true);
      setUserEmail(emailParam);
      setCheckingStatus(false);
      window.history.replaceState({}, document.title, window.location.pathname);
      fetchTasks();
      fetchUnreadCount();
    } else if (loginStatus === 'error' && errorParam) {
      setError(`Google Login failed: ${decodeURIComponent(errorParam)}`);
      setCheckingStatus(false);
      window.history.replaceState({}, document.title, window.location.pathname);
    } else {
      checkStatus();
    }
  }, []);



  // Automatically extract tasks once logged in
  useEffect(() => {
    if (isConnected) {
      handleExtractEmails();
      fetchUnreadCount();
    }
  }, [isConnected]);

  // Compute Statistics of recent 15 mails
  let allRecentEmails = [];
  let importantEmails = [];
  let spamEmails = [];
  let unreadCountRecent = 0;

  if (emailData) {
    // Flatten grouped emails
    emailData.senders.forEach(sender => {
      sender.emails.forEach(email => {
        const fullEmail = {
          ...email,
          senderName: sender.sender_name || sender.sender_email,
          senderEmail: sender.sender_email
        };
        allRecentEmails.push(fullEmail);
        
        // Count unread
        const isUnread = email.labels && email.labels.includes("UNREAD");
        if (isUnread) {
          unreadCountRecent++;
        }

        if (email.is_spam) {
          spamEmails.push(fullEmail);
        } else {
          importantEmails.push(fullEmail);
        }
      });
    });
  }

  // Categorize emails for Pie Chart
  let spamCountPie = spamEmails.length;
  let importantCountPie = 0;
  let modImportantCountPie = 0;

  if (emailData) {
    importantEmails.forEach(email => {
      const hasHighPriority = email.tasks && email.tasks.some(t => t.priority === 'high' || t.priority === 'urgent');
      if (hasHighPriority) {
        importantCountPie++;
      } else {
        modImportantCountPie++;
      }
    });
  } else {
    // Beautiful default placeholders for empty states
    spamCountPie = 5;
    importantCountPie = 6;
    modImportantCountPie = 4;
  }

  const totalPie = spamCountPie + importantCountPie + modImportantCountPie;
  const spamPercent = totalPie > 0 ? (spamCountPie / totalPie) * 100 : 0;
  const importantPercent = totalPie > 0 ? (importantCountPie / totalPie) * 100 : 0;
  const modPercent = totalPie > 0 ? (modImportantCountPie / totalPie) * 100 : 0;

  const visibleTasks = tasks.filter(t => {
    if (hiddenItems.includes(t.id)) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (t.title && t.title.toLowerCase().includes(q)) || 
             (t.description && t.description.toLowerCase().includes(q));
    }
    return true;
  });

  const visibleEmails = importantEmails.filter(e => {
    if (hiddenItems.includes(e.id)) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (e.subject && e.subject.toLowerCase().includes(q)) || 
             (e.body && e.body.toLowerCase().includes(q)) ||
             (e.senderName && e.senderName.toLowerCase().includes(q));
    }
    return true;
  });

  const visibleRecentEmails = allRecentEmails.filter(e => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (e.subject && e.subject.toLowerCase().includes(q)) || 
             (e.body && e.body.toLowerCase().includes(q)) ||
             (e.senderName && e.senderName.toLowerCase().includes(q));
    }
    return true;
  });

  if (checkingStatus) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', width: '100vw', background: 'var(--bg-color)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <div className="loader loader-dark" style={{ width: '40px', height: '40px', borderWidth: '4px' }}></div>
          <p style={{ color: 'var(--text-muted)', fontWeight: 500 }}>Initializing AutoTask AI...</p>
        </div>
      </div>
    );
  }

  if (!isConnected) {
    return (
      <div className="login-page-container">
        <div className="envelope-wrapper">
          <div className="envelope">
            <div className="envelope-flap"></div>
            <div className="envelope-left"></div>
            <div className="envelope-right"></div>
            <div className="envelope-bottom"></div>
            <div className="envelope-letter">
              <div className="login-logo">
                <img src={logoImg} alt="AutoTask Logo" />
              </div>
              <h1 className="login-title">AutoTask AI</h1>
              <p className="login-subtitle">
                Sign in with Google to automatically extract tasks and coordinate your email workflows.
              </p>

              {error && (
                <div style={{ 
                  width: '100%', 
                  padding: '12px 16px', 
                  background: 'var(--danger-light)', 
                  color: 'var(--danger)', 
                  borderRadius: '12px', 
                  fontSize: '0.85rem', 
                  marginBottom: '24px',
                  textAlign: 'left'
                }}>
                  ⚠️ {error}
                </div>
              )}

              <a 
                href="/api/auth/google/login"
                className="google-btn"
              >
                <svg className="google-icon" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v3.92h6.69a5.74 5.74 0 0 1-2.48 3.77v3.08h3.99c2.34-2.16 3.68-5.32 3.68-8.7z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.99-3.08c-1.11.75-2.53 1.19-3.94 1.19-3.07 0-5.67-2.08-6.6-4.88H1.31v3.19A12.02 12.02 0 0 0 12 24z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.4 14.32a7.16 7.16 0 0 1 0-4.64V6.49H1.31a12.02 12.02 0 0 0 0 11.02L5.4 14.32z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42A11.95 11.95 0 0 0 12 0 12.02 12.02 0 0 0 1.31 6.49l4.09 3.19c.93-2.8 3.53-4.88 6.6-4.88z"
                  />
                </svg>
                <span>Sign in with Google</span>
              </a>

              <div className="login-footer">
                <span>Secure OAuth 2.0 Connection</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
        {/* Sidebar */}
        <div className="sidebar">
          <div className="sidebar-logo">
            <img src={logoImg} alt="Logo" className="logo-img" />
            AutoTask AI
          </div>
        
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div 
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Dashboard
          </div>
          <div 
            className={`nav-item ${activeTab === 'emails' ? 'active' : ''}`}
            onClick={() => setActiveTab('emails')}
          >
            📧 Important Mails
          </div>
          <div 
            className={`nav-item ${activeTab === 'tasks' ? 'active' : ''}`}
            onClick={() => setActiveTab('tasks')}
          >
            📋 All Tasks
          </div>
        </nav>

        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {isConnected && (
            <div className="connection-status" style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '12px', borderRadius: '12px', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--panel-border)', alignItems: 'center', textAlign: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className={`status-dot ${extracting ? 'status-dot-animating' : ''}`}></span>
                <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '180px', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-main)' }}>
                  {userEmail}
                </span>
              </div>
              {extracting && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <div className="loader loader-dark" style={{ width: '12px', height: '12px', borderWidth: '2px' }}></div>
                  Syncing tasks...
                </div>
              )}
            </div>
          )}

          {isConnected && (
            <button 
              className="btn-logout" 
              onClick={handleLogout}
              disabled={loading}
            >
               Logout
            </button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <div className="page-header">
          <h1 className="page-title">
            {activeTab === 'dashboard' && 'Dashboard'}
            {activeTab === 'emails' && 'Important Mails'}
            {activeTab === 'tasks' && 'Database Tasks'}
          </h1>
          <div className="header-actions">
            <input 
              type="text" 
              className="search-bar" 
              placeholder="Search mail..." 
              value={searchInput}
              onChange={(e) => {
                setSearchInput(e.target.value);
                setSearchQuery(e.target.value);
              }}
            />
          </div>
        </div>

        {error && (
          error === "Gmail authentication required" ? (
            <div className="bento-card" style={{ 
              background: 'linear-gradient(135deg, #eff6ff, #dbeafe)', 
              borderColor: '#bfdbfe',
              padding: '32px', 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              textAlign: 'center',
              gap: '16px',
              maxWidth: '600px',
              margin: '20px auto'
            }}>
              <div style={{ fontSize: '3rem' }}>🔑</div>
              <h3 style={{ color: '#1e3a8a', fontSize: '1.25rem', fontWeight: 600 }}>Google Account Connection Required</h3>
              <p style={{ color: '#1e40af', fontSize: '0.95rem', maxWidth: '400px' }}>
                AutoTask AI needs permission to read your Gmail inbox in order to automatically extract tasks and build workflow plans.
              </p>
              <a 
                href="/api/auth/google/login" 
                className="btn btn-primary"
                style={{ 
                  background: '#2563eb', 
                  color: 'white', 
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 24px',
                  borderRadius: '100px',
                  fontWeight: 600,
                  boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.2)'
                }}
              >
                <span>Connect Google Account</span>
              </a>
            </div>
          ) : (
            <div style={{ padding: '16px', background: 'var(--danger-light)', color: 'var(--danger)', borderRadius: '12px' }}>
              Error: {error}
            </div>
          )
        )}

        {/* Dashboard View */}
        {activeTab === 'dashboard' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            <div className="bento-card" style={{ padding: '32px' }}>
              <h3 style={{ marginBottom: '24px', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                Overview
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 400 }}>(last 15 mails)</span>
              </h3>
              <div className="stats-grid">
                
                <div className="stat-card">
                  <div className="stat-header">
                    <span>Unread Mails</span>
                  </div>
                  <div className="stat-body">
                    <span className="stat-value">{unreadCountRecent}</span>
                    <span className="stat-trend trend-up" style={{ backgroundColor: 'var(--success-light)', color: 'var(--success)' }}>
                      ✉️ Unread
                    </span>
                  </div>
                </div>

                <div className="stat-card" style={{ borderLeft: '1px solid var(--panel-border)', paddingLeft: '24px' }}>
                  <div className="stat-header">
                    <span>Important Mails</span>
                  </div>
                  <div className="stat-body">
                    <span className="stat-value">{importantEmails.length}</span>
                    <span className="stat-trend trend-up">Filtered</span>
                  </div>
                </div>

                <div className="stat-card" style={{ borderLeft: '1px solid var(--panel-border)', paddingLeft: '24px' }}>
                  <div className="stat-header">
                    <span>Spam Blocked</span>
                  </div>
                  <div className="stat-body">
                    <span className="stat-value">{spamEmails.length}</span>
                    <span className="stat-trend trend-down">Skipped</span>
                  </div>
                </div>

              </div>
            </div>

            <div className="stats-grid">
               <div className="bento-card" style={{ flex: 2 }}>
                  <h3 style={{ marginBottom: '16px', fontSize: '1.1rem' }}>Recent Extractions</h3>
                  {visibleEmails.slice(0, 3).map(email => (
                    <div key={email.id} className="list-item" style={{ padding: '12px 0', cursor: 'pointer' }} onClick={() => setSelectedEmail(email)} title="Click to read email">
                      <div className="item-icon">📧</div>
                      <div className="item-content">
                        <div className="item-title">{email.subject}</div>
                        <div className="item-desc">From: {email.senderName}</div>
                      </div>
                      <div className="item-actions">
                        <span className="badge badge-active">{email.tasks?.length || 0} tasks</span>
                      </div>
                    </div>
                  ))}
                  {visibleEmails.length === 0 && <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No recent extractions.</p>}
               </div>
               <div className="bento-card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                 <h3 style={{ marginBottom: '20px', fontSize: '1.1rem' }}>Mail Distribution</h3>
                 <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px', flex: 1, justifyContent: 'center' }}>
                   <div style={{
                     position: 'relative',
                     width: '130px',
                     height: '130px',
                     display: 'flex',
                     alignItems: 'center',
                     justifyContent: 'center'
                   }}>
                     <svg width="130" height="130" viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
                       {/* Background circle */}
                       <circle
                         cx="50"
                         cy="50"
                         r="40"
                         fill="transparent"
                         stroke="rgba(255, 255, 255, 0.05)"
                         strokeWidth="10"
                       />
                       
                       {/* Spams */}
                       {spamPercent > 0 && (
                         <circle
                           cx="50"
                           cy="50"
                           r="40"
                           fill="transparent"
                           stroke="#ef4444"
                           strokeWidth={hoveredSection === 'Spam' ? '12' : '10'}
                           strokeDasharray={`${(spamPercent / 100) * 2 * Math.PI * 40} ${2 * Math.PI * 40}`}
                           strokeDashoffset={0}
                           style={{ transition: 'stroke-width 0.2s', cursor: 'pointer' }}
                           onMouseEnter={() => setHoveredSection('Spam')}
                           onMouseLeave={() => setHoveredSection(null)}
                         />
                       )}

                       {/* Moderately Important */}
                       {modPercent > 0 && (
                         <circle
                           cx="50"
                           cy="50"
                           r="40"
                           fill="transparent"
                           stroke="#f59e0b"
                           strokeWidth={hoveredSection === 'Medium' ? '12' : '10'}
                           strokeDasharray={`${(modPercent / 100) * 2 * Math.PI * 40} ${2 * Math.PI * 40}`}
                           strokeDashoffset={-((spamPercent / 100) * 2 * Math.PI * 40)}
                           style={{ transition: 'stroke-width 0.2s', cursor: 'pointer' }}
                           onMouseEnter={() => setHoveredSection('Medium')}
                           onMouseLeave={() => setHoveredSection(null)}
                         />
                       )}

                       {/* Important Mails */}
                       {importantPercent > 0 && (
                         <circle
                           cx="50"
                           cy="50"
                           r="40"
                           fill="transparent"
                           stroke="#10b981"
                           strokeWidth={hoveredSection === 'Important' ? '12' : '10'}
                           strokeDasharray={`${(importantPercent / 100) * 2 * Math.PI * 40} ${2 * Math.PI * 40}`}
                           strokeDashoffset={-(((spamPercent + modPercent) / 100) * 2 * Math.PI * 40)}
                           style={{ transition: 'stroke-width 0.2s', cursor: 'pointer' }}
                           onMouseEnter={() => setHoveredSection('Important')}
                           onMouseLeave={() => setHoveredSection(null)}
                         />
                       )}
                     </svg>
                     
                     {/* Center text overlay */}
                     <div style={{
                       position: 'absolute',
                       width: '68px',
                       height: '68px',
                       borderRadius: '50%',
                       backgroundColor: '#0f172a',
                       display: 'flex',
                       flexDirection: 'column',
                       alignItems: 'center',
                       justifyContent: 'center',
                       boxShadow: 'inset 0 2px 8px rgba(0, 0, 0, 0.4)',
                       pointerEvents: 'none'
                     }}>
                       <span style={{ fontSize: hoveredSection ? '0.75rem' : '1.3rem', fontWeight: '700', color: 'var(--text-main)', textAlign: 'center', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', width: '100%', padding: '0 2px' }}>
                         {hoveredSection ? hoveredSection : totalPie}
                       </span>
                       <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>
                         {hoveredSection ? `${Math.round(hoveredSection === 'Spam' ? spamPercent : hoveredSection === 'Medium' ? modPercent : importantPercent)}%` : 'Total Mails'}
                       </span>
                     </div>
                   </div>

                   {/* Legend */}
                   <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%' }}>
                     <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', cursor: 'pointer', padding: '4px', borderRadius: '6px', background: hoveredSection === 'Spam' ? 'rgba(239, 68, 68, 0.1)' : 'transparent' }} onMouseEnter={() => setHoveredSection('Spam')} onMouseLeave={() => setHoveredSection(null)}>
                       <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                         <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: '#ef4444' }}></span>
                         <span style={{ color: 'var(--text-muted)' }}>Spams</span>
                       </div>
                       <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{spamCountPie} ({totalPie > 0 ? Math.round(spamPercent) : 0}%)</span>
                     </div>
                     <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', cursor: 'pointer', padding: '4px', borderRadius: '6px', background: hoveredSection === 'Medium' ? 'rgba(245, 158, 11, 0.1)' : 'transparent' }} onMouseEnter={() => setHoveredSection('Medium')} onMouseLeave={() => setHoveredSection(null)}>
                       <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                         <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: '#f59e0b' }}></span>
                         <span style={{ color: 'var(--text-muted)' }}>Moderately Important</span>
                       </div>
                       <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{modImportantCountPie} ({totalPie > 0 ? Math.round(modPercent) : 0}%)</span>
                     </div>
                     <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', cursor: 'pointer', padding: '4px', borderRadius: '6px', background: hoveredSection === 'Important' ? 'rgba(16, 185, 129, 0.1)' : 'transparent' }} onMouseEnter={() => setHoveredSection('Important')} onMouseLeave={() => setHoveredSection(null)}>
                       <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                         <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: '#10b981' }}></span>
                         <span style={{ color: 'var(--text-muted)' }}>Important Mails</span>
                       </div>
                       <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{importantCountPie} ({totalPie > 0 ? Math.round(importantPercent) : 0}%)</span>
                     </div>
                   </div>
                 </div>
               </div>
            </div>
          </div>
        )}

        {/* Emails View */}
        {activeTab === 'emails' && (
          <div className="bento-card" style={{ flex: 1, overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
              <h3 style={{ fontSize: '1.1rem' }}>Filtered Mails & Tasks</h3>
              <span className="badge badge-active">{spamEmails.length} spam hidden</span>
            </div>

            {visibleEmails.length === 0 ? (
               <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No important emails found.
               </div>
            ) : (
               <div className="list-container">
                 {visibleEmails.map(email => (
                   <div key={email.id} className="list-item" style={{ flexDirection: 'column' }}>
                     <div style={{ display: 'flex', width: '100%', gap: '16px' }}>
                        <div className="item-icon" style={{ background: 'var(--success-light)', color: 'var(--success)' }}>✉️</div>
                        <div className="item-content" style={{ cursor: 'pointer' }} onClick={() => setSelectedEmail(email)} title="Click to read email">
                          <div className="item-title">{email.subject}</div>
                          <div className="item-desc"><strong>{email.senderName}</strong> • {new Date(email.date).toLocaleDateString()}</div>
                          <div className="item-desc" style={{ marginTop: '4px', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '650px' }}>{email.body}</div>
                        </div>
                        <div className="item-actions">
                          <button className="btn btn-secondary btn-icon" onClick={() => hideItem(email.id)} title="Hide Mail">
                            🗑️
                          </button>
                        </div>
                     </div>
                     
                     {/* Render extracted tasks beneath the email */}
                     {email.tasks && email.tasks.length > 0 && (
                        <div className="nested-tasks">
                           <h4>🤖 AI Extracted Tasks</h4>
                           <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                             {email.tasks.map((task, idx) => (
                                <div key={idx} style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '12px', borderRadius: '8px', border: '1px solid var(--panel-border)', display: 'flex', justifyContent: 'space-between' }}>
                                   <div>
                                      <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>{task.title}</div>
                                      <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Priority: {task.priority}</div>
                                   </div>
                                </div>
                             ))}
                           </div>
                        </div>
                     )}
                   </div>
                 ))}
               </div>
            )}
          </div>
        )}

        {/* Tasks View */}
        {activeTab === 'tasks' && (
          <div style={{ display: 'flex', gap: '24px', flex: 1, minHeight: 0 }}>
             {/* Left Panel: Tasks */}
             <div className="bento-card" style={{ flex: 1, overflowY: 'auto' }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '24px' }}>All Saved Tasks</h3>
                <div className="list-container">
                  {visibleTasks.length === 0 ? (
                     <p style={{ color: 'var(--text-muted)' }}>No tasks available.</p>
                  ) : (
                     visibleTasks.map(task => (
                       <div key={task.id} className="list-item">
                         <div className="item-icon" style={{ 
                           background: `var(--priority-${task.priority}Light, #f1f5f9)`, 
                           color: `var(--priority-${task.priority})` 
                         }}>
                           📋
                         </div>
                         <div className="item-content">
                           <div className="item-title">{task.title}</div>
                           <div className="item-desc">{task.description}</div>
                           <div className="item-meta">
                              {task.status !== 'pending' && (
                                <span className={`badge badge-${task.status === 'completed' ? 'active' : 'warning'}`}>
                                  {task.status.replace('_', ' ')}
                                </span>
                              )}
                              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{task.source_email}</span>
                           </div>
                         </div>
                         <div className="item-actions">
                           <button className="btn btn-secondary btn-icon" onClick={() => hideItem(task.id)} title="Hide Task">
                             🗑️
                           </button>
                         </div>
                       </div>
                     ))
                  )}
                </div>
             </div>

             {/* Right Panel: Recent Mails */}
             <div className="bento-card" style={{ flex: 1, overflowY: 'auto' }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '24px' }}>Recent 15 Inbox Mails</h3>
                <div className="list-container">
                  {visibleRecentEmails.length === 0 ? (
                     <p style={{ color: 'var(--text-muted)' }}>{searchQuery ? 'No matching emails found.' : 'No recent emails found.'}</p>
                  ) : (
                     visibleRecentEmails.map(email => (
                       <div key={email.id} className="list-item" style={{ opacity: email.is_spam ? 0.6 : 1, cursor: 'pointer' }} onClick={() => setSelectedEmail(email)} title="Click to read email">
                         <div className="item-icon" style={{ 
                           background: email.is_spam ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)', 
                           color: email.is_spam ? '#ef4444' : '#10b981' 
                         }}>
                           {email.is_spam ? '🚫' : '✉️'}
                         </div>
                         <div className="item-content">
                           <div className="item-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-main)' }}>
                             {email.subject}
                             {email.labels && email.labels.includes('UNREAD') && (
                               <span className="badge" style={{ backgroundColor: '#6366f1', color: 'white', padding: '2px 6px', fontSize: '0.65rem' }}>UNREAD</span>
                             )}
                             {email.is_spam && (
                               <span className="badge" style={{ backgroundColor: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', padding: '2px 6px', fontSize: '0.65rem' }}>SPAM</span>
                             )}
                           </div>
                           <div className="item-desc"><strong>{email.senderName}</strong> • {new Date(email.date).toLocaleDateString()}</div>
                           <div className="item-desc" style={{ fontSize: '0.8rem', marginTop: '4px', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '320px' }}>{email.body}</div>
                         </div>
                       </div>
                     ))
                  )}
                </div>
             </div>
          </div>
        )}

      </div>

      {/* Email Reader Modal */}
      {selectedEmail && (
        <div className="modal-overlay" onClick={() => setSelectedEmail(null)}>
          <div className="modal-content bento-card" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedEmail(null)}>✕</button>
            <div className="modal-header">
              <span className="modal-icon">📧</span>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <h2 className="modal-subject">{selectedEmail.subject}</h2>
                <span className="modal-meta">From: <strong>{selectedEmail.senderName || selectedEmail.senderEmail}</strong> • {new Date(selectedEmail.date).toLocaleString()}</span>
              </div>
            </div>
            <hr style={{ border: '0', borderTop: '1px solid var(--panel-border)', margin: '20px 0' }} />
            <div className="modal-body">
              <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', color: 'var(--text-main)', fontSize: '0.95rem' }}>{selectedEmail.body}</p>
            </div>
            {selectedEmail.tasks && selectedEmail.tasks.length > 0 && (
              <div className="modal-footer" style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid var(--panel-border)' }}>
                <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '12px', letterSpacing: '0.5px' }}>🤖 Associated Tasks</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {selectedEmail.tasks.map((task, idx) => (
                    <div key={idx} style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '12px', borderRadius: '8px', border: '1px solid var(--panel-border)' }}>
                      <div style={{ fontWeight: 500, fontSize: '0.9rem', color: 'var(--text-main)' }}>{task.title}</div>
                      {task.description && <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>{task.description}</div>}
                      <div style={{ fontSize: '0.8rem', color: `var(--priority-${task.priority}, var(--text-muted))`, marginTop: '4px', fontWeight: 600 }}>Priority: {task.priority}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
