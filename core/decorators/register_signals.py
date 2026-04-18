# # core/apps.py
# import importlib
# import logging
# import os
# import pkgutil
# import sys
# from typing import Optional
# from django.apps import AppConfig

# from core.utils import formattedError


# # class BaseAppConfig(AppConfig):
# #     """
# #     A custom reusable AppConfig base that handles safe signal importing,
# #     skipping during management commands or autoreloader phases.
# #     """

# #     default_auto_field = "django.db.models.BigAutoField"
# #     name = None

# #     #: Path to the signals module to import during `ready()`.
# #     #: e.g: "app.signals"
# #     signals = None

# #     def ready(self):
# #         # Skip signal registration during management commands
# #         skip_commands = {"migrate", "makemigrations", "test", "qcluster"}
# #         if any(cmd in sys.argv for cmd in skip_commands):
# #             print(f"🟡 Skipping <{self.name}> signals during: {sys.argv}")
# #             return

# #         # Skip during autoreloader startup (runserver)
# #         if os.environ.get("RUN_MAIN") != "true":
# #             print(f"🟡 Skipping <{self.name}> signals during autoreloader phase")
# #             return

# #         print(self.signals)

# #         # Load signal handlers if module is defined
# #         if self.signals:
# #             try:
# #                 __import__(self.signals)
# #                 print(f"✅ <{self.name}> signals imported successfully")
# #             except Exception as e:
# #                 print(f"❌ Failed to import <{self.name}> signals:", e)

# #         super().ready()


# # core/decorators.py
# import os
# import sys
# from functools import wraps

# logger = logging.getLogger(__name__)


# def register_signals(module: str = "signals"):
#     """
#     Decorator for Django's AppConfig.ready() method that automatically loads
#     signal handlers for a given app.

#     Features:
#     ----------
#     - Automatically detects and imports:
#         • A `signals.py` file, or
#         • All `.py` modules inside a `signals/` package.
#     - Skips signal loading during specific management commands such as:
#         migrate, makemigrations, test, or qcluster.
#     - Prints informative logs to show which signal files or packages were registered.

#     Parameters
#     ----------
#     module : str, optional
#         The name of the signals module or package to import (default: "signals").

#     Usage
#     -----
#     In your app’s AppConfig (apps.py):

#         from django.apps import AppConfig
#         from core.decorators.register_signals import register_signals

#         class StoreConfig(AppConfig):
#             name = "store"

#             @register_signals()
#             def ready(self):
#                 # Optional additional startup logic
#                 pass

#     Behavior
#     --------
#     - If your app contains `store/signals.py`, it will import it automatically.
#     - If your app contains `store/signals/` as a package, it will import
#       every `.py` file inside that folder.
#     - If neither exists, it will silently skip.

#     Example log output:
#     -------------------
#         🟢 Loaded store.signals
#         🟢 Loaded store.signals.orders
#         🟢 Loaded store.signals.payments
#         🟡 Skipping <store> signals registering (e.g. during migration)
#     """

#     def decorator(func):
#         @wraps(func)
#         def wrapper(self, *args, **kwargs):
#             skip_commands = {"migrate", "makemigrations", "test", "qcluster"}
#             if any(cmd in sys.argv for cmd in skip_commands):
#                 print(f"🟡 Skipping < {self.name} > signals registering")
#                 return
#             base_name = f"{self.name}.{module}"
#             if module:  # Load signal handlers
#                 try:
#                     mod = importlib.import_module(base_name)

#                     # If it's a package, import all its submodules
#                     if hasattr(mod, "__path__"):
#                         loaded_any = False
#                         for _, name, is_pkg in pkgutil.iter_modules(mod.__path__):
#                             if not is_pkg:
#                                 submodule = f"{base_name}.{name}"
#                                 importlib.import_module(submodule)
#                                 print(f"🟢 Loaded {submodule}")
#                                 loaded_any = True
#                         # If the folder exists but has no submodules
#                         if not loaded_any:
#                             print(f"🟡 Loaded empty package {base_name}")
#                     else:
#                         # It's a single signals.py file
#                         print(f"🟢 Loaded {base_name}")

#                 # except ModuleNotFoundError:
#                 #     pass  # no signals package — silently ignore
#                 except Exception as e:
#                     print(f">>> ❌ Failed to import <{base_name}>: {formattedError(e)}")
#                     # clean, intentional failure to allow systemd to restart
#                     sys.exit(1)

#             # Run the original ready() logic if any
#             return func(self, *args, **kwargs)

#         return wrapper

#     return decorator
