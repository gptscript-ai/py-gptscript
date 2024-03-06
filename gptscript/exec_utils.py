import subprocess


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

        if input is None:
            return process.communicate()
        else:
            return process.communicate(input=input)
    except Exception as e:
        raise e


def stream_exec_cmd(cmd, args=[], input=None):
    try:
        process = subprocess.Popen(
            [cmd] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )

        if input:
            process.stdin.write(input)
            process.stdin.close()

        return process
    except Exception as e:
        raise e
