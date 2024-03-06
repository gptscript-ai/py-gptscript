import os
import sys

from gptscript.exec_utils import exec_cmd, stream_exec_cmd

optToArg = {
    "cache": "--cache=",
    "cacheDir": "--cache-dir=",
}


def _get_command():
    python_bin_dir = os.path.dirname(sys.executable)
    return os.path.join(python_bin_dir, "gptscript")


def list_tools():
    cmd = _get_command()
    out, _ = exec_cmd(cmd, ["--list-tools"])
    return out


def list_models():
    cmd = _get_command()
    try:
        models, _ = exec_cmd(cmd, ["--list-models"])
        return models.strip().split("\n")
    except Exception as e:
        raise e


def exec(tool, opts={}):
    cmd = _get_command()
    args = toArgs(opts)
    args.append("-")
    try:
        out, err = exec_cmd(cmd, args, input=str(tool))
        print(err)
        return out
    except Exception as e:
        raise e


def stream_exec(tool, opts={}):
    cmd = _get_command()
    args = toArgs(opts)
    args.append("-")
    try:
        process = stream_exec_cmd(cmd, args, input=str(tool))
        return process.stdout, process.stderr, process.wait
    except Exception as e:
        raise e


def exec_file(tool_path, input="", opts={}):
    cmd = _get_command()
    args = toArgs(opts)

    args.append(tool_path)

    if input != "":
        args.append(input)
    try:
        out, _ = exec_cmd(cmd, args)
        return out
    except Exception as e:
        raise e


def stream_exec_file(tool_path, input="", opts={}):
    cmd = _get_command()
    args = toArgs(opts)

    args.append(tool_path)

    if input != "":
        args.append(input)
    try:
        process = stream_exec_cmd(cmd, args)

        return process.stdout, process.stderr, process.wait
    except Exception as e:
        raise e


def toArgs(opts):
    args = ["--quiet=false"]
    for opt, val in opts.items():
        if optToArg.get(opt):
            args.append(optToArg[opt] + val)
    return args
