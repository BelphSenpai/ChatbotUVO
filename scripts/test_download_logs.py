import importlib.util
import os
import sys

# Cargar app desde ruta (sin requerir paquete)
project_root = os.path.dirname(os.path.dirname(__file__))
app_path = os.path.join(project_root, 'www', 'app.py')

spec = importlib.util.spec_from_file_location('webapp', app_path)
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)
app = web.app

print('App loaded:', app)

with app.test_client() as client:
    # Simular sesión con rol admin
    with client.session_transaction() as sess:
        sess['usuario'] = 'admin'
        sess['rol'] = 'admin'

    print('Requesting /admin/download-logs...')
    resp = client.get('/admin/download-logs')
    print('Status:', resp.status_code)
    print('Content-Type:', resp.headers.get('Content-Type'))

    out_path = os.path.join(project_root, 'logs_all_test.zip')
    with open(out_path, 'wb') as f:
        f.write(resp.data)

    print('Wrote:', out_path, 'size=', os.path.getsize(out_path))
