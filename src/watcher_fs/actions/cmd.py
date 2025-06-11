import sys
import shlex
import subprocess
from pathlib import Path

# ANSI color codes
CON_TEAL = "\033[1;96m"
CON_RESET = "\033[0m"       # Reset to default
CON_HEAD = f"{CON_TEAL}[cmd]{CON_RESET}"

def action(changes, **kwargs):
    """Process file changes and execute the cmd function for each change."""
    # print(f"CMD called with {changes}")
    if type(changes) == list:
        for change in changes:
            cmd(change[0], event_type=change[1], **kwargs)
    else:
        # in this case it's just a tuple (file, event)
        cmd(changes[0], event_type=changes[1], **kwargs)


def cmd(file: Path, event_type: str, **kwargs):
    """
        Execute a command in the console for a file change event.

        Args:
            file: Path object representing the changed file.
            event_type: String describing the event (e.g., 'created', 'modified').
            **kwargs: Additional parameters, must include 'cmd' with the command template.

        Raises:
            RuntimeError: If 'cmd' is not defined in kwargs.
            subprocess.CalledProcessError: If the command execution fails.
    """
    print(f"{CON_HEAD} File {file} ({event_type}), kwargs: {kwargs}")
    cmd_str: str = kwargs.get('cmd', "")
    if not cmd_str:
        raise RuntimeError(f"Cmd is not defined properly")

    # Replace {0} with the file path
    cmd_str = cmd_str.replace("{0}", f"{file}")

    print(f"{CON_HEAD} {cmd_str}")

    try:
        # Split the command string into a list for subprocess
        # Split the command string safely using shlex
        cmd_args = shlex.split(cmd_str)

        # Start the process with pipes for stdout and stderr
        process = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line-buffered
            universal_newlines=True
        )

        # Stream output in real-time
        while True:
            stdout_line = process.stdout.readline()
            stderr_line = process.stderr.readline()
            if stdout_line:
                print(stdout_line, end="", flush=True)
            if stderr_line:
                print(stderr_line, file=sys.stderr, end="", flush=True)
            # Check if process has finished and no more output
            if process.poll() is not None and not (stdout_line or stderr_line):
                break

        # Ensure all output is flushed before checking return code
        sys.stdout.flush()
        sys.stderr.flush()

        # Get final return code
        return_code = process.wait()
        if return_code != 0:
            raise RuntimeError(f"Command failed with exit code {return_code}")


    except FileNotFoundError:
        # Ensure output is flushed before raising exception
        sys.stdout.flush()
        sys.stderr.flush()
        raise RuntimeError(f"Command not found: {cmd_str}")
    except Exception as e:
        # Ensure output is flushed before raising exception
        sys.stdout.flush()
        sys.stderr.flush()
        raise RuntimeError(f"Command execution failed: {e}")
