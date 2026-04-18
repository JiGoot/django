import importlib
from typing import Any, Callable

def import_function( path: str) -> Callable:
    # Ensure Django is setup

    parts = path.split(".")
    module_path = parts[0]
    remaining_parts = parts[1:]

    # Import the base module
    module = importlib.import_module(module_path)

    # Navigate through the remaining parts
    func = module
    current_path = module_path

    for part in remaining_parts:
        current_path += f".{part}"
        try:
            # Try to get attribute (could be class, function, etc.)
            func = getattr(func, part)
        except AttributeError:
            # If attribute doesn't exist, try to import as submodule
            submodule = importlib.import_module(current_path)
            func = submodule

    if not callable(func):
        raise TypeError(f"{path} is not callable")
    return func



def process_task(path: str, *args, **kwargs) -> Any:
    function = import_function(path)
    return function(*args, **kwargs)