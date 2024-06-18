import os
import subprocess
import sys

if sys.platform == "win32":
    import msvcrt
    import win32api
    import win32con


def exec_cmd(cmd, args=[], input=None):
    try:
        process = subprocess.Popen(
            [cmd] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

        return process.communicate(input=input)
    except Exception as e:
        raise e


def stream_exec_cmd(cmd, args=[], input=None):
    return _stream_cmd(cmd, args, input)


def stream_exec_cmd_with_events(cmd, args=[], input=None):
    events_out, events_in = os.pipe()
    close_fds = True
    fds = (events_in,)

    if sys.platform == "win32":
        # Can't close fds on Windows
        close_fds = False
        # Can't pass fds on Windows
        fds = tuple()

        # Convert the writable file descriptor to a handle
        w_handle = msvcrt.get_osfhandle(events_in)

        # Duplicate the handle to make it inheritable
        proc_handle = win32api.GetCurrentProcess()
        dup_handle = win32api.DuplicateHandle(
            proc_handle,  # Source process handle
            w_handle,  # Source handle
            proc_handle,  # Target process handle
            0,  # Desired access (0 defaults to same as source)
            1,  # Inherit handle
            win32con.DUPLICATE_SAME_ACCESS  # Options
        )
        args = ["--events-stream-to=fd://" + str(int(dup_handle))] + args
    else:
        args = ["--events-stream-to=fd://" + str(events_in)] + args

    proc = _stream_cmd(cmd, args, input, fds=fds, close_fds=close_fds)
    os.close(events_in)
    if sys.platform == "win32":
        win32api.CloseHandle(dup_handle)

    return proc, os.fdopen(events_out, "r", encoding="utf-8")


def _stream_cmd(cmd, args=[], input=None, fds=tuple(), close_fds=True):
    try:
        process = subprocess.Popen(
            [cmd] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            pass_fds=fds,
            close_fds=close_fds,
            encoding="utf-8",
        )

        if input:
            process.stdin.write(input)
            process.stdin.close()

        return process
    except Exception as e:
        raise e
