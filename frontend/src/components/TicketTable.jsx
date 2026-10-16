import { priorityLabels, statusLabels } from '../api';

export default function TicketTable({ tickets, onEdit, onDelete, busy }) {
  return <div className="table-wrap"><table>
    <thead><tr><th>Ticket / requester</th><th>Priority</th><th>Status</th><th>Assigned to</th><th>Actions</th></tr></thead>
    <tbody>{tickets.map(ticket => <tr key={ticket.id}>
      <td><button className="ticket-link" onClick={() => onEdit(ticket)}><span className="ticket-id">#{String(ticket.id).padStart(4, '0')}</span> {ticket.subject}</button><small>{ticket.requester_email}</small>{ticket.description && <details><summary>Description</summary><p>{ticket.description}</p></details>}</td>
      <td data-label="Priority"><span className={`badge priority-${ticket.priority.toLowerCase()}`}>{priorityLabels[ticket.priority]}</span></td>
      <td data-label="Status"><span className={`badge status-${ticket.status.toLowerCase()}`}>{statusLabels[ticket.status]}</span></td>
      <td data-label="Assigned to">{ticket.assignee}</td>
      <td data-label="Actions"><button className="text-button" onClick={() => onEdit(ticket)} aria-label={`Edit ticket ${ticket.id}`}>Edit</button><button className="text-button danger" disabled={busy} onClick={() => onDelete(ticket)} aria-label={`Delete ticket ${ticket.id}`}>Delete</button></td>
    </tr>)}</tbody>
  </table></div>;
}
