export function safeReturnTo(value) {
  if (typeof value !== 'string' || !value.startsWith('/')) return '/catalogo';
  try {
    const url = new URL(value, 'https://neifit.invalid');
    if (url.origin !== 'https://neifit.invalid' || /^\/(login|registro|auth|recuperar-contrasena|restablecer-contrasena)(\/|$)/.test(url.pathname)) return '/catalogo';
    return url.pathname + url.search + url.hash;
  } catch { return '/catalogo'; }
}

export function loginDestination(destination, role) {
  const next = safeReturnTo(destination);
  if (role === 'mensajeria') return '/mensajeria';
  if (next.startsWith('/admin') && role !== 'admin') return '/catalogo';
  if (next.startsWith('/mensajeria') && role !== 'admin') return '/catalogo';
  return next;
}

export function loginLink(destination) {
  return '/login?next=' + encodeURIComponent(safeReturnTo(destination));
}
