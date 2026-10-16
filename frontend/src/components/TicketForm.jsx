import { useState } from 'react';
import { priorityLabels, statusLabels } from '../api';

export default function TicketForm({ ticket, onSave, onCancel }) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(event.currentTarget));
    setSaving(true);
    setError('');
    try {
      await onSave(payload);
    } catch (failure) {
      setError(failure.message);
    } finally {
      setSaving(false);
    }
  }

  return <section className="editor" aria-labelledby="editor-heading">
    <div className="panel-head"><h2 id="editor-heading">{ticket ? `Edit ticket #${ticket.id}` : 'New support ticket'}</h2><button onClick={onCancel} disabled={saving}>Cancel</button></div>
    <form onSubmit={submit}>
      {error && <p role="alert" className="alert">{error}</p>}
      <label>Subject<input autoFocus name="subject" required maxLength={200} defaultValue={ticket?.subject} placeholder="What needs our attention?" /></label>
      <label>Requester email<input name="requester_email" type="email" required maxLength={254} defaultValue={ticket?.requester_email} placeholder="name@example.com" /></label>
      <label>Description<textarea name="description" maxLength={10000} defaultValue={ticket?.description} placeholder="Include the problem and any steps you have already tried." /></label>
      <div className="form-row"><label>Priority<select name="priority" defaultValue={ticket?.priority ?? 'MEDIUM'}>{Object.entries(priorityLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Status<select name="status" defaultValue={ticket?.status ?? 'OPEN'}>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div>
      <label>Assigned to<input name="assignee" maxLength={120} required defaultValue={ticket?.assignee ?? 'Unassigned'} /></label>
      <button className="primary" disabled={saving}>{saving ? 'Saving…' : ticket ? 'Save changes' : 'Create ticket'}</button>
    </form>
  </section>;
}
