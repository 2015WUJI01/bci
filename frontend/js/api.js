async function apiPost(path, body) {
  const headers = { 'Content-Type': 'application/json' };
  if (authToken) headers['x-auth-token'] = authToken;
  const res = await fetch(API_URL + path, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || '请求失败');
  }
  return res.json();
}

async function apiGet(path) {
  const headers = {};
  if (authToken) headers['x-auth-token'] = authToken;
  const res = await fetch(API_URL + path, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || '请求失败');
  }
  return res.json();
}
