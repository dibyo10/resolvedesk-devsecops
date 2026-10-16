import React, { useCallback, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { request, statusLabels } from './api';
import TicketForm from './components/TicketForm';
import TicketTable from './components/TicketTable';
import './styles.css';

function App() {
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [editor, setEditor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [page, setPage] = useState(0);
  const [refresh, setRefresh] = useState(0);
  const pageSize = 25;

  const reload = useCallback(() => setRefresh(value => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setLoading(true);
      setError('');
      const query = new URLSearchParams({ limit: pageSize, offset: page * pageSize });
      if (filter !== 'ALL') query.set('status', filter);
      if (search.trim()) query.set('search', search.trim());
      try {
        const [items, counts] = await Promise.all([
          request(`/tickets?${query}`, { signal: controller.signal }),
          request('/tickets/stats', { signal: controller.signal }),
        ]);
        setTickets(items);
        setStats(counts);
      } catch (failure) {
        if (failure.name !== 'AbortError') setError('We could not load the queue. Check your connection and retry.');
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 150);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [filter, search, page, refresh]);

  async function save(payload) {
    await request(editor.ticket ? `/tickets/${editor.ticket.id}` : '/tickets', {
      method: editor.ticket ? 'PUT' : 'POST', body: JSON.stringify(payload),
    });
    setNotice(editor.ticket ? 'Ticket updated.' : 'Ticket created.');
    setEditor(null);
    reload();
  }

  async function remove(ticket) {
    if (!window.confirm(`Delete ticket #${ticket.id}: ${ticket.subject}? This cannot be undone.`)) return;
    setBusy(true);
    try {
      await request(`/tickets/${ticket.id}`, { method: 'DELETE' });
      setNotice(`Ticket #${ticket.id} deleted.`);
      if (tickets.length === 1 && page > 0) setPage(page - 1);
      else reload();
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  }

  return <div className="app">
    <a className="skip-link" href="#queue">Skip to tickets</a>
    <aside className="sidebar"><div className="brand"><span className="brand-mark">R</span><div><b>ResolveDesk</b><small>Support workspace</small></div></div><nav aria-label="Ticket queues">{[['ALL', 'All tickets'], ...Object.entries(statusLabels)].map(([value, label]) => <button key={value} className={filter === value ? 'active' : ''} aria-pressed={filter === value} onClick={() => { setFilter(value); setPage(0); }}>{label}</button>)}</nav><div className="side-bottom"><p>Clear queues.<br />Better support.</p><small>Internal demonstration workspace</small></div></aside>
    <main className="main" id="queue"><header><div><h1>Support queue</h1><p className="muted">Give every request a clear next step.</p></div><button className="primary" onClick={() => setEditor({ ticket: null })}>New ticket</button></header>
      {error && <div className="alert" role="alert">{error} <button onClick={reload}>Retry</button></div>}
      <p className="notice" role="status">{notice}</p>
      <section className="stats" aria-label="Queue summary">{[['Open', 'open'], ['In progress', 'inProgress'], ['Resolved', 'resolved'], ['Urgent unresolved', 'urgent']].map(([label, key]) => <div className="stat" key={key}><small>{label}</small><strong>{stats?.[key] ?? '—'}</strong></div>)}</section>
      {editor ? <TicketForm key={editor.ticket?.id ?? 'new'} ticket={editor.ticket} onSave={save} onCancel={() => setEditor(null)} /> : <section className="panel"><div className="panel-head"><div><h2>{filter === 'ALL' ? 'All tickets' : statusLabels[filter]}</h2><p className="muted">{stats ? `${stats.total} tickets across the workspace` : 'Connecting to your workspace'}</p></div><label className="search">Search tickets<input type="search" value={search} maxLength={200} onChange={event => { setSearch(event.target.value); setPage(0); }} placeholder="Subject, requester or description" /></label></div>
        {loading ? <p className="empty" role="status">Loading tickets…</p> : !tickets.length ? <div className="empty"><h3>{search || filter !== 'ALL' ? 'No matching tickets' : 'Your queue is clear'}</h3><p>{search || filter !== 'ALL' ? 'Try another search or queue.' : 'Create your first ticket to start supporting your team.'}</p></div> : <TicketTable tickets={tickets} onEdit={ticket => setEditor({ ticket })} onDelete={remove} busy={busy} />}
        <div className="pagination"><button disabled={page === 0 || loading} onClick={() => setPage(page - 1)}>Previous</button><span>Page {page + 1}</span><button disabled={tickets.length < pageSize || loading} onClick={() => setPage(page + 1)}>Next</button></div>
      </section>}
      <footer>ResolveDesk · A little structure for every request.</footer>
    </main>
  </div>;
}

createRoot(document.getElementById('root')).render(<App />);
