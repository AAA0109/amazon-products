#!/usr/bin/env python
import os
import sys

from distutils.util import strtobool

def initialize_debugger():
    from django.conf import settings

    if settings.DEBUG and bool(strtobool(os.environ.get("USE_VSCODE_IDE", "True"))):
        print("Debug mode enabled")
        if os.environ.get("RUN_MAIN") or os.environ.get("WERKZEUG_RUN_MAIN"):
            import debugpy

            print("debugpy imported")
            debugpy.listen(("0.0.0.0", 4444))
            print("debugpy listening")
            debugpy.wait_for_client()
            print("Attached!")


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "adsdroid.settings")
    initialize_debugger()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
