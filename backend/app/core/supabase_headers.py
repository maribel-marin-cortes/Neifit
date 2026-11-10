"""Las claves sb_secret son API keys, no tokens JWT."""
def service_headers(key):
    result = {'apikey': key}
    if not key.startswith('sb_secret_'):
        result['Authorization'] = 'Bearer ' + key
    return result
