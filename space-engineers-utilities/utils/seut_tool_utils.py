import bpy
import os
import subprocess
import threading

from ..seut_errors          import get_abs_path
from ..seut_utils              import linux_path_to_wine_path

def call_tool(args: list, logfile=None) -> list:
    # check if the tool ends with .exe, if it does run it with wine
    if args[0].endswith('.exe'):
        print(f"SEUT: Running Windows tool with Wine: {args[0]}")
        args = ["wine"] + args

        itterator = 2
        while itterator < len(args):
            if args[itterator].startswith('/home'):
                args[itterator] = linux_path_to_wine_path(args[itterator])
            itterator += 1

    try:
        print(f"SEUT: Executing command: {' '.join(args)}")
        out = subprocess.check_output(args, cwd=None, stderr=subprocess.STDOUT, shell=False)
        if logfile is not None:
            write_to_log(logfile, out, args=args)
        return [0, out, args]

    except subprocess.CalledProcessError as e:
        print(f"SEUT: Command failed with return code {e.returncode}")
        print(f"SEUT: Error output: {e.output}")
        if logfile is not None:
            write_to_log(logfile, e.output, args=args)
        return [e.returncode, e.output, args]

    except Exception as e:
        print(f"SEUT: Exception occurred: {e}")
        print(e)


def call_tool_threaded(commands: list, thread_count: int, logfile=None):

    threads = []
    results = []
    commands_left = commands

    while len(commands_left) > 0:
        if len(threads) < thread_count:
            c = commands_left[0]
            t = threading.Thread(target=threaded_call, args=(c, results,))
            threads.append(t)
            commands_left.remove(c)
            t.start()
        else:
            t = threads[0]
            threads.remove(t)
            t.join()

    for i in threads:
        i.join()

    if logfile is not None:
        output = ""

        for r in results:
            output += r[1].decode("utf-8", "ignore") + '\n'

        write_to_log(logfile, output.encode())

    return results


def threaded_call(c: list, results: list):
    result = call_tool(c)
    results.append(result)


def write_to_log(logfile: str, content: str, args=None, cwd=None):

    with open(get_abs_path(logfile), 'wb') as log:

        if cwd:
            cwd_str = "Running from: " + cwd + '\n'
            log.write(cwd_str.encode('utf-8'))

        if args:
            args_str = "Command: " + str(args) + '\n'
            log.write(args_str.encode('utf-8'))

        log.write(content)


def get_tool_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tools')