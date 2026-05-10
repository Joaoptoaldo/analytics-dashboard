import os
import sys

# Set minimal envs for dev import
os.environ.setdefault('ENV', 'development')
os.environ.setdefault('DATABASE_URL', 'sqlite:///./backend.db')
os.environ.setdefault('CORS_ORIGINS', 'http://localhost:3000')

print('ENV=', os.environ.get('ENV'))
print('DATABASE_URL=', os.environ.get('DATABASE_URL'))
print('CORS_ORIGINS=', os.environ.get('CORS_ORIGINS'))

try:
    # Ensure project root is on sys.path
    project_root = os.path.dirname(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    import backend.main
    print('IMPORT_OK')
except SystemExit as e:
    print('SYSTEMEXIT', e)
    sys.exit(2)
except Exception as e:
    import traceback
    traceback.print_exc()
    print('IMPORT_ERROR', e)
    sys.exit(1)
