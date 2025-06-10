from pathlib import Path

# ANSI color codes
CON_GREEN = "\033[1;32m"
CON_RESET = "\033[0m"       # Reset to default
CON_HEAD = f"{CON_GREEN}[notify]{CON_RESET}"

def action(changes):
    """Process file changes and execute the notify function for each change."""
    if type(changes) == list:
        for change in changes:
            notify(*change)
    else:
        # in this case it's just a tuple (file, event)
        notify(changes[0], event_type=changes[1])


def notify(file:Path, event_type:str):
    print(f"{CON_HEAD} File {file} has been {event_type}")
