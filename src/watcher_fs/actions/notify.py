from pathlib import Path

def action(changes):
    if type(changes) == list:
        for change in changes:
            notify(*change)
    else:
        # in this case it's just a tuple (file, event)
        notify(changes[0], event_type=changes[1])


def notify(file:Path, event_type:str):
    print(f"File {file} has been {event_type}")
