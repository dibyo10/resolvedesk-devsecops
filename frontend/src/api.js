export async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Unable to save your changes. Check your connection and try again.');
  }
  return response.status === 204 ? null : response.json();
}

export const statusLabels = { OPEN: 'Open', IN_PROGRESS: 'In progress', RESOLVED: 'Resolved' };
export const priorityLabels = { LOW: 'Low', MEDIUM: 'Medium', HIGH: 'High', URGENT: 'Urgent' };
