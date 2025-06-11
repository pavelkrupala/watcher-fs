from pathlib import Path

# ANSI color codes
CON_GREEN = "\033[1;32m"
CON_RESET = "\033[0m"       # Reset to default
CON_HEAD = f"{CON_GREEN}[notify]{CON_RESET}"

def action(changes):
    """Process file changes and execute the notify function for each change."""
    if type(changes) == list:
        for change in changes:
            notify(change[0], event_type=change[1])
    else:
        # in this case it's just a tuple (file, event)
        notify(changes[0], event_type=changes[1])


def notify(file:Path, event_type:str):
    """Notify Action implementation

    Args:
        file: `Path` of the file which was changed/created/deleted
        event_type: `str` of the event which happened: changed/created/deleted
    """
    print(f"{CON_HEAD} File {file} has been {event_type}")
