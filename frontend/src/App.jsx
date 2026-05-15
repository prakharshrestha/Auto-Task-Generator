import React, { useState, useEffect } from 'react';
import { api } from './api';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Data State
  const [tasks, setTasks] = useState([]);
  const [emailData, setEmailData] = useState(null);
  
  // UI State
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState(null);
  const [hiddenItems, setHiddenItems] = useState(() => {
    return JSON.parse(localStorage.getItem('hiddenItems') || '[]');
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');

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
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExtractEmails = async () => {
    try {
      setExtracting(true);
      setError(null);
      // Fast fetch of raw emails
      const rawData = await api.getRawRecentEmails(10);
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
      setError(err.message);
      setExtracting(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    // Fetch initial emails without extracting to just get the list?
    // The backend only has /recent-plans which extracts. We'll just call it once or let user trigger it.
  }, []);

  // Compute Statistics
  let totalEmails = 0;
  let importantEmails = [];
  let spamCount = 0;

  if (emailData) {
    totalEmails = emailData.count; // Total fetched by backend
    
    // Flatten grouped emails
    emailData.senders.forEach(sender => {
      sender.emails.forEach(email => {
        importantEmails.push({
          ...email,
          senderName: sender.sender_name || sender.sender_email
        });
      });
    });

    spamCount = totalEmails - importantEmails.length;
  }

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

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">A</div>
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

        <div style={{ marginTop: 'auto' }}>
          <div className="bento-card" style={{ padding: '16px', textAlign: 'center', background: 'linear-gradient(135deg, #f8fafc, #f1f5f9)' }}>
            <div style={{ fontSize: '2rem', marginBottom: '8px' }}>✨</div>
            <h4 style={{ marginBottom: '8px', fontSize: '0.9rem' }}>AI Auto-Pilot</h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Fetch and auto-extract tasks from latest 10 emails.
            </p>
            <button 
              className="btn btn-primary" 
              style={{ width: '100%' }}
              onClick={handleExtractEmails}
              disabled={extracting}
            >
              {extracting ? <div className="loader loader-dark"></div> : 'Extract Now'}
            </button>
          </div>
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
              placeholder="Search mail (press Enter)..." 
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  setSearchQuery(searchInput);
                }
              }}
            />
          </div>
        </div>

        {error && (
          <div style={{ padding: '16px', background: 'var(--danger-light)', color: 'var(--danger)', borderRadius: '12px' }}>
            Error: {error}
          </div>
        )}

        {/* Dashboard View */}
        {activeTab === 'dashboard' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            <div className="bento-card" style={{ padding: '32px' }}>
              <h3 style={{ marginBottom: '24px', fontSize: '1.1rem' }}>Overview</h3>
              <div className="stats-grid">
                
                <div className="stat-card">
                  <div className="stat-header">
                    <span>Active Tasks</span>
                  </div>
                  <div className="stat-body">
                    <span className="stat-value">{visibleTasks.length}</span>
                    <span className="stat-trend trend-up">↑ Active</span>
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
                    <span className="stat-value">{spamCount}</span>
                    <span className="stat-trend trend-down">Skipped</span>
                  </div>
                </div>

              </div>
            </div>

            <div className="stats-grid">
               <div className="bento-card" style={{ flex: 2 }}>
                  <h3 style={{ marginBottom: '16px', fontSize: '1.1rem' }}>Recent Extractions</h3>
                  {visibleEmails.slice(0, 3).map(email => (
                    <div key={email.id} className="list-item" style={{ padding: '12px 0' }}>
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
               <div className="bento-card" style={{ flex: 1 }}>
                 <h3 style={{ marginBottom: '16px', fontSize: '1.1rem' }}>Priority Flow</h3>
                 <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                   <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Urgent</span>
                      <span style={{ fontWeight: 600 }}>{tasks.filter(t => t.priority === 'urgent').length}</span>
                   </div>
                   <div style={{ width: '100%', height: '8px', background: '#f1f5f9', borderRadius: '4px' }}>
                      <div style={{ width: '20%', height: '100%', background: 'var(--danger)', borderRadius: '4px' }}></div>
                   </div>
                   
                   <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Medium</span>
                      <span style={{ fontWeight: 600 }}>{tasks.filter(t => t.priority === 'medium').length}</span>
                   </div>
                   <div style={{ width: '100%', height: '8px', background: '#f1f5f9', borderRadius: '4px' }}>
                      <div style={{ width: '60%', height: '100%', background: 'var(--warning)', borderRadius: '4px' }}></div>
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
              <span className="badge badge-active">{spamCount} spam hidden</span>
            </div>

            {visibleEmails.length === 0 ? (
               <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No important emails found. Click "Extract Now" to fetch latest 10 emails.
               </div>
            ) : (
               <div className="list-container">
                 {visibleEmails.map(email => (
                   <div key={email.id} className="list-item" style={{ flexDirection: 'column' }}>
                     <div style={{ display: 'flex', width: '100%', gap: '16px' }}>
                        <div className="item-icon" style={{ background: 'var(--success-light)', color: 'var(--success)' }}>✉️</div>
                        <div className="item-content">
                          <div className="item-title">{email.subject}</div>
                          <div className="item-desc"><strong>{email.senderName}</strong> • {new Date(email.date).toLocaleDateString()}</div>
                          <div className="item-desc" style={{ marginTop: '4px' }}>{email.body}</div>
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
                                <div key={idx} style={{ background: 'white', padding: '12px', borderRadius: '8px', border: '1px solid var(--panel-border)', display: 'flex', justifyContent: 'space-between' }}>
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
                           <span className={`badge badge-${task.status === 'completed' ? 'active' : 'warning'}`}>
                             {task.status.replace('_', ' ')}
                           </span>
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
        )}

      </div>
    </div>
  );
}

export default App;
