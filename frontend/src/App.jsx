import { useEffect, useState } from 'react';
import './App.css';
import {
  FiInbox,
  FiSend,
  FiEdit,
  FiTag,
  FiArchive,
  FiCheckCircle,
  FiLogOut,
  FiTrash2,
  FiX,
  FiRefreshCw,
  FiSearch,
  FiMenu,
} from 'react-icons/fi';
import logo from './assets/logo.png';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';

/* =====================
     HELPERS
===================== */
function getHumanLabel(emailLabels, allLabels) {
  if (!emailLabels || !allLabels) return null;
  const match = allLabels.find((l) => emailLabels.includes(l.id));
  return match ? match.name : null;
}

function App() {
  /* =====================
       STATE
  ===================== */
  const [labels, setLabels] = useState([]);
  const [emails, setEmails] = useState([]);
  const [currentLabel, setCurrentLabel] = useState('INBOX');

  const [searchQuery, setSearchQuery] = useState('');

  const [selectedEmail, setSelectedEmail] = useState(null);
  const [viewerOpen, setViewerOpen] = useState(false);

  const [analysis, setAnalysis] = useState(null);
  const [loadingAI, setLoadingAI] = useState(false);

  const [replyText, setReplyText] = useState('');
  const [sendingReply, setSendingReply] = useState(false);

  const [loadingEmails, setLoadingEmails] = useState(false);

  const [toast, setToast] = useState(null);
  const [userEmail, setUserEmail] = useState('');
  
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  
  // Nuevo estado para controlar la sidebar en móvil
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const unreadCount = emails.filter((e) => e.unread).length;

  /* =====================
       AUTO ANALYZE ON OPEN
  ===================== */
  useEffect(() => {
    if (!viewerOpen || !selectedEmail) return;

    setLoadingAI(true);
    setAnalysis(null);

    fetch(`${API}/emails/${selectedEmail.id}/analyze`, {
      method: 'POST',
    })
      .then((res) => res.json())
      .then((data) => {
        setAnalysis(data);
        if (data.suggested_reply) {
          setReplyText(data.suggested_reply);
        }
      })
      .catch(() => showToast('Error analizando el correo', 'error'))
      .finally(() => setLoadingAI(false));
  }, [viewerOpen, selectedEmail]);

  /* =====================
       LOAD LABELS
  ===================== */
  useEffect(() => {
    fetch(`${API}/gmail/labels`)
      .then((res) => res.json())
      .then((data) => setLabels(data.filter((l) => l.type === 'user')))
      .catch(() => {});
  }, []);

  /* =====================
       LOAD EMAILS (CON AUTO-REFRESH)
  ===================== */
  useEffect(() => {
    let cancelled = false;

    async function loadEmails(resetView = false) {
      if (resetView) setLoadingEmails(true);
      
      try {
        const res = await fetch(`${API}/emails?label=${currentLabel}`);
        const data = await res.json();
        
        if (!cancelled) {
          setEmails(data);
          
          if (resetView) {
            setSelectedEmail(null);
            setViewerOpen(false);
          }
        }
      } catch (error) {
        console.error("Error cargando emails:", error);
      } finally {
        if (!cancelled && resetView) setLoadingEmails(false);
      }
    }

    // 1. Carga inicial
    loadEmails(true);

    // 2. Refresh cada 60s
    const intervalId = setInterval(() => {
      loadEmails(false);
    }, 60000); 

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [currentLabel]);

  /* =====================
       USER
  ===================== */
  useEffect(() => {
    fetch(`${API}/auth/user`, { credentials: 'include' })
      .then((res) => res.json())
      .then((data) => data.email && setUserEmail(data.email))
      .catch(() => {});
  }, []);

  /* =====================
       ACTIONS
  ===================== */
  function formatMeetingDate(isoString, duration) {
    try {
      const date = new Date(isoString);
      const formattedDate = date.toLocaleDateString('es-ES', {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
      });
      const formattedTime = date.toLocaleTimeString('es-ES', {
        hour: '2-digit',
        minute: '2-digit',
      });
      return `${formattedDate}, ${formattedTime}${duration ? ` · ${duration} min` : ''}`;
    } catch {
      return '';
    }
  }

  function addMeetingToCalendar() {
    if (!analysis?.meeting_detected || !analysis?.proposed_datetime) {
      showToast('No se detectó una reunión válida', 'info');
      return;
    }

    showToast('Creando evento en Google Calendar…', 'info');

    fetch(`${API}/calendar/meeting`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: selectedEmail.subject || 'Reunión',
        start_datetime: analysis.proposed_datetime,
        duration_minutes: analysis.duration_minutes || 60,
        attendees: [],
      }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Error al crear el evento");
        }
        return data;
      })
      .then((data) => {
        showToast('Evento creado con éxito');
        if (data.calendar_link) {
          window.open(data.calendar_link, '_blank');
        }
      })
      .catch((err) => {
        console.error(err);
        showToast(err.message, 'error');
      });
  }

  function applySuggestedLabel(label) {
    if (!selectedEmail || !label) return;

    fetch(`${API}/emails/${selectedEmail.id}/add-label?label=${label}`, {
      method: 'POST',
    }).then(() => {
      showToast(`Etiqueta "${label}" aplicada`);
      // No recargamos etiquetas aquí para no cortar el flujo visual
    });
  }

  function archiveEmail() {
    if (!selectedEmail) return;

    fetch(`${API}/archive`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message_id: selectedEmail.id,
        label_name: 'AI-Handled',
      }),
    }).then(() => {
      setEmails((prev) => prev.filter((e) => e.id !== selectedEmail.id));
      setViewerOpen(false);
      setSelectedEmail(null);
      showToast('Correo archivado');
    });
  }

  function sendReply() {
    if (!selectedEmail || !replyText) return;

    setSendingReply(true);

    fetch(`${API}/reply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message_id: selectedEmail.id,
        reply_text: replyText,
      }),
    })
      .then(() => {
        showToast('Respuesta enviada');
        setReplyText('');
      })
      .finally(() => setSendingReply(false));
  }

  function showToast(message, type = 'success') {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }

  function logout() {
    fetch(`${API}/logout`, { credentials: 'include' }).finally(() => {
      window.location.href = '/login';
    });
  }

  /* =====================
       RENDER
  ===================== */
  return (
    <div className="app">
      
      {/* Overlay para cerrar sidebar en móvil al hacer click fuera */}
      <div 
        className={`sidebar-overlay ${sidebarOpen ? 'active' : ''}`}
        onClick={() => setSidebarOpen(false)}
      ></div>

      {/* SIDEBAR con clase dinámica para mostrarse en móvil */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div>
          <div className="logo">
            <img src={logo} alt="Logo" />
          </div>

          <nav>
            <button onClick={() => { setCurrentLabel('INBOX'); setSidebarOpen(false); }}>
              <FiInbox /> Inbox
            </button>
            <button onClick={() => { setCurrentLabel('SENT'); setSidebarOpen(false); }}>
              <FiSend /> Enviados
            </button>
            <button onClick={() => { setCurrentLabel('DRAFT'); setSidebarOpen(false); }}>
              <FiEdit /> Borradores
            </button>
            <button onClick={() => { setCurrentLabel('TRASH'); setSidebarOpen(false); }}>
              <FiTrash2 /> Eliminados
            </button>

            <hr />
            <h4>Etiquetas</h4>

            {labels.map((l) => (
              <button key={l.id} onClick={() => { setCurrentLabel(l.id); setSidebarOpen(false); }}>
                <FiTag /> {l.name}
              </button>
            ))}
          </nav>
        </div>

        <div className="sidebar-footer">
          {userEmail && <div className="user-email">{userEmail}</div>}
          <button
            className="logout-button"
            onClick={() => setShowLogoutModal(true)}
          >
            <FiLogOut /> Cerrar sesión
          </button>
        </div>
      </aside>

      {/* MAIN LIST */}
      <div className="main">
        <section className="list">
          <div className="list-card">
            {/* Header */}
            <div className="list-header">
              <div className="list-title" style={{ display: 'flex', alignItems: 'center' }}>
                
                {/* Botón menú hamburguesa (visible solo en móvil por CSS) */}
                <button 
                  className="menu-toggle" 
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                >
                  <FiMenu />
                </button>

                <h3>{currentLabel}</h3>
                {unreadCount > 0 && (
                  <span className="list-count unread">
                    {unreadCount} sin leer
                  </span>
                )}
              </div>

              <div className="list-actions">
                <div className="list-search">
                  <FiSearch size={14} />
                  <input
                    placeholder="Buscar"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <button
                  className="icon-button"
                  onClick={() => {
                    setLoadingEmails(true);
                    fetch(`${API}/emails?label=${currentLabel}`)
                      .then((res) => res.json())
                      .then((data) => setEmails(data))
                      .finally(() => setLoadingEmails(false));
                  }}
                >
                  <FiRefreshCw />
                </button>
              </div>
            </div>

            {/* Body */}
            <div className="list-body">
              {emails
                .filter((email) => {
                  const q = searchQuery.toLowerCase();
                  return (
                    email.from?.toLowerCase().includes(q) ||
                    email.subject?.toLowerCase().includes(q) ||
                    email.snippet?.toLowerCase().includes(q)
                  );
                })
                .map((email) => {
                  const humanLabel = getHumanLabel(email.labels, labels);

                  return (
                    <div
                      key={email.id}
                      className={`email-item ${email.unread ? 'unread' : ''} ${selectedEmail?.id === email.id ? 'active' : ''}`}
                      onClick={() => {
                        setSelectedEmail(email);
                        setViewerOpen(true);
                        setReplyText('');
                        
                        if (email.unread) {
                          fetch(`${API}/emails/${email.id}/mark-read`, { method: 'POST' });
                          setEmails((prev) =>
                            prev.map((e) => (e.id === email.id ? { ...e, unread: false } : e))
                          );
                        }
                      }}
                    >
                      {/* Punto azul de no leído */}
                      {email.unread && <div className="unread-dot"></div>}

                      <div className="email-content">
                        <div className="email-from">{email.from}</div>
                        {humanLabel && (
                           <span className="email-label-chip" style={{ fontSize: '11px', background: '#e2e8f0', padding: '2px 6px', borderRadius: '4px', marginRight: '6px', color: '#475569', display: 'inline-block', marginBottom: '4px' }}>
                             {humanLabel}
                           </span>
                        )}
                        <div className="email-subject">{email.subject}</div>
                        <div className="email-preview">{email.snippet}</div>
                      </div>

                      <button
                        className="email-delete"
                        title="Mover a papelera"
                        onClick={(e) => {
                          e.stopPropagation();
                          fetch(`${API}/emails/${email.id}/trash`, { method: 'POST' })
                            .then(() => setEmails((prev) => prev.filter((e) => e.id !== email.id)));
                        }}
                      >
                         <svg 
                            xmlns="http://www.w3.org/2000/svg" 
                            width="18" 
                            height="18" 
                            viewBox="0 0 24 24" 
                            fill="none" 
                            stroke="currentColor" 
                            strokeWidth="2" 
                            strokeLinecap="round" 
                            strokeLinejoin="round"
                          >
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            <line x1="10" y1="11" x2="10" y2="17"></line>
                            <line x1="14" y1="11" x2="14" y2="17"></line>
                          </svg>
                      </button>
                    </div>
                  );
                })}
            </div>
          </div>
        </section>
      </div>

      {/* VIEWER */}
      <section className={`viewer ${viewerOpen ? 'viewer-visible' : ''}`}>
        {selectedEmail && (
          <>
            <button className="viewer-close" onClick={() => setViewerOpen(false)}>
              <FiX /> Cerrar
            </button>

            <h3>{selectedEmail.subject}</h3>

            <div className="email-body">{selectedEmail.body}</div>

            <div className="viewer-actions">
              <button className="btn-secondary" onClick={archiveEmail}>
                <FiArchive /> Archivar IA
              </button>

              {analysis && analysis.suggested_label && (
                <button
                  className="btn-soft"
                  onClick={() => applySuggestedLabel(analysis.suggested_label)}
                >
                  <FiTag /> Etiquetar como "{analysis.suggested_label}"
                </button>
              )}
            </div>

            {loadingAI && <p>Analizando correo…</p>}

            {analysis && (
              <div className="analysis-box">
                <h4>Resumen</h4>
                <p>{analysis.summary}</p>

                {analysis.meeting_detected && analysis.proposed_datetime && (
                  <button 
                    className="btn-soft"
                    onClick={addMeetingToCalendar}
                  >
                    <FiCheckCircle /> Crear evento ·{' '}
                    {formatMeetingDate(analysis.proposed_datetime, analysis.duration_minutes)}
                  </button>
                )}
              </div>
            )}

            <div className="reply-box">
              <h4>Respuesta sugerida</h4>
              <textarea
                rows={6}
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
              />
              <button
                className="btn-primary"
                onClick={sendReply}
                disabled={sendingReply}
              >
                {sendingReply ? 'Enviando…' : 'Enviar respuesta'}
              </button>
            </div>
          </>
        )}
      </section>

      {/* MODAL LOGOUT */}
      {showLogoutModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>Cerrar sesión</h3>
            <p>¿Estás seguro de que quieres salir?</p>
            <div className="modal-actions">
              <button 
                className="btn-secondary" 
                onClick={() => setShowLogoutModal(false)}
              >
                Cancelar
              </button>
              <button 
                className="btn-primary" 
                style={{ background: '#dc2626' }} 
                onClick={logout}
              >
                Salir
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && <div className={`toast ${toast.type}`}>{toast.message}</div>}
    </div>
  );
}

export default App;