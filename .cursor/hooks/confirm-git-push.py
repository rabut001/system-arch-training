#!/usr/bin/env python3
"""git push を含むシェルコマンドに、Cursor の確認を要求する。

判定だけを行い、許可するかはセッションの可否確認に任せる。
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys

ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "ash"}
GIT_VALUE_OPTIONS = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--super-prefix",
    "--config-env",
    "--list-cmds",
}
GIT_EQUALS_PREFIXES = (
    "--git-dir=",
    "--work-tree=",
    "--namespace=",
    "--exec-path=",
    "--super-prefix=",
    "--config-env=",
    "--list-cmds=",
)
SUBTREE_VALUE_OPTIONS = {"-P", "--prefix", "-b", "--branch", "-m", "--message", "--annotate"}
SUDO_VALUE_OPTIONS = {
    "-u",
    "-g",
    "-h",
    "-p",
    "-C",
    "-T",
    "-r",
    "-U",
    "--user",
    "--group",
    "--host",
    "--prompt",
    "--chdir",
    "--role",
    "--other-user",
    "--command-timeout",
    "--close-from",
}
ENV_VALUE_OPTIONS = {
    "-u",
    "-C",
    "-S",
    "--unset",
    "--chdir",
    "--split-string",
    "--default-signal",
    "--ignore-signal",
    "--block-signal",
}
XARGS_VALUE_OPTIONS = {
    "-I",
    "-J",
    "-L",
    "-n",
    "-P",
    "-s",
    "-E",
    "-a",
    "-d",
    "--replace",
    "--max-lines",
    "--max-args",
    "--max-procs",
    "--max-chars",
    "--eof",
    "--arg-file",
    "--delimiter",
}


def command_has_git_push(source: str) -> bool:
    if "git" not in source:
        return False
    cleaned, inners = extract_substitutions(source)
    for inner in inners:
        if command_has_git_push(inner):
            return True
    for segment in split_commands(cleaned):
        if segment_pushes(segment):
            return True
    return False


def extract_substitutions(source: str) -> tuple[str, list[str]]:
    out: list[str] = []
    inners: list[str] = []
    i = 0
    n = len(source)
    in_single = False
    in_double = False
    while i < n:
        char = source[i]
        if in_single:
            out.append(char)
            if char == "'":
                in_single = False
            i += 1
            continue
        if char == "\\" and i + 1 < n:
            out.append(char)
            out.append(source[i + 1])
            i += 2
            continue
        if char == "'" and not in_double:
            in_single = True
            out.append(char)
            i += 1
            continue
        if char == '"':
            in_double = not in_double
            out.append(char)
            i += 1
            continue
        if char == "`":
            end = find_backtick(source, i + 1)
            if end is None:
                out.append(char)
                i += 1
                continue
            inners.append(source[i + 1 : end])
            out.append('""')
            i = end + 1
            continue
        if char == "$" and i + 1 < n and source[i + 1] == "(":
            end = find_paren_end(source, i + 2)
            if end is None:
                out.append(char)
                i += 1
                continue
            inners.append(source[i + 2 : end])
            out.append('""')
            i = end + 1
            continue
        if char in "<>" and i + 1 < n and source[i + 1] == "(":
            end = find_paren_end(source, i + 2)
            if end is None:
                out.append(char)
                i += 1
                continue
            inners.append(source[i + 2 : end])
            out.append('""')
            i = end + 1
            continue
        out.append(char)
        i += 1
    return "".join(out), inners


def find_paren_end(source: str, start: int) -> int | None:
    depth = 1
    i = start
    n = len(source)
    in_single = False
    in_double = False
    while i < n:
        char = source[i]
        if in_single:
            if char == "'":
                in_single = False
            i += 1
            continue
        if char == "\\" and i + 1 < n:
            i += 2
            continue
        if char == "'" and not in_double:
            in_single = True
            i += 1
            continue
        if char == '"':
            in_double = not in_double
            i += 1
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def find_backtick(source: str, start: int) -> int | None:
    i = start
    n = len(source)
    while i < n:
        if source[i] == "\\" and i + 1 < n:
            i += 2
            continue
        if source[i] == "`":
            return i
        i += 1
    return None


def split_commands(source: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(source)
    in_single = False
    in_double = False

    def finish() -> None:
        text = "".join(buf).strip()
        if text:
            parts.append(text)
        buf.clear()

    while i < n:
        char = source[i]
        if in_single:
            buf.append(char)
            if char == "'":
                in_single = False
            i += 1
            continue
        if char == "\\" and i + 1 < n:
            buf.append(char)
            buf.append(source[i + 1])
            i += 2
            continue
        if char == "'" and not in_double:
            in_single = True
            buf.append(char)
            i += 1
            continue
        if char == '"':
            in_double = not in_double
            buf.append(char)
            i += 1
            continue
        if char == "#" and is_comment_start(source, i):
            while i < n and source[i] != "\n":
                i += 1
            continue
        if char == "\n":
            finish()
            i += 1
            continue
        if source.startswith("&&", i) or source.startswith("||", i):
            finish()
            i += 2
            continue
        if char == ";":
            finish()
            i += 1
            continue
        if char in "|&":
            previous = source[i - 1] if i else ""
            if previous in "<>":
                buf.append(char)
                i += 1
                continue
            finish()
            i += 1
            continue
        buf.append(char)
        i += 1
    finish()
    return parts


def is_comment_start(source: str, index: int) -> bool:
    if index == 0:
        return True
    return source[index - 1] in " \t\n;&|()"


def segment_pushes(segment: str) -> bool:
    try:
        words = shlex.split(segment, posix=True)
    except ValueError:
        return loose_git_push(segment)
    return words_run_git_push(words)


def loose_git_push(segment: str) -> bool:
    return re.search(
        r"(?:^|[\s;&|(])(?:[\w./+-]*/)?git(?:\.exe)?\s+(?:-\S+\s+)*push\b",
        segment,
    ) is not None


def words_run_git_push(words: list[str]) -> bool:
    words = skip_wrappers(words)
    if not words:
        return False
    base = os.path.basename(words[0])
    if base in {"git", "git.exe"}:
        return git_invokes_push(words[1:])
    if base in SHELLS or base == "busybox":
        return shell_inline_script_pushes(words)
    if base == "eval":
        return command_has_git_push(" ".join(words[1:]))
    if base == "xargs":
        return xargs_pushes(words[1:])
    return False


def skip_wrappers(words: list[str]) -> list[str]:
    index = 0
    while index < len(words):
        word = words[index]
        if ASSIGNMENT.match(word):
            index += 1
            continue
        base = os.path.basename(word)
        if base == "sudo":
            index = skip_options(words, index + 1, SUDO_VALUE_OPTIONS)
            continue
        if base == "env":
            index += 1
            while index < len(words):
                if words[index].startswith("-"):
                    index = skip_one_option(words, index, ENV_VALUE_OPTIONS)
                    continue
                if ASSIGNMENT.match(words[index]):
                    index += 1
                    continue
                break
            continue
        if base == "command":
            index += 1
            while index < len(words) and words[index] in {"-p", "-v", "-V"}:
                index += 1
            continue
        if base in {"exec", "time", "nohup", "nice"}:
            index += 1
            if base in {"time", "nice"} and index < len(words) and words[index].startswith("-"):
                index += 1
            continue
        break
    return words[index:]


def skip_options(words: list[str], index: int, value_options: set[str]) -> int:
    while index < len(words) and words[index].startswith("-"):
        index = skip_one_option(words, index, value_options)
    return index


def skip_one_option(words: list[str], index: int, value_options: set[str]) -> int:
    option = words[index]
    index += 1
    if option in value_options and index < len(words):
        index += 1
    return index


def shell_inline_script_pushes(words: list[str]) -> bool:
    args = words[1:]
    if words and os.path.basename(words[0]) == "busybox":
        if not args:
            return False
        if os.path.basename(args[0]) not in SHELLS:
            return False
        args = args[1:]
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "-c" or (
            arg.startswith("-") and not arg.startswith("--") and "c" in arg[1:]
        ):
            if index + 1 >= len(args):
                return False
            return command_has_git_push(args[index + 1])
        if arg.startswith("-"):
            index += 1
            continue
        return False
    return False


def xargs_pushes(args: list[str]) -> bool:
    index = 0
    while index < len(args) and args[index].startswith("-"):
        index = skip_one_option(args, index, XARGS_VALUE_OPTIONS)
    return words_run_git_push(args[index:])


def git_invokes_push(args: list[str]) -> bool:
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            return False
        if arg.startswith("-"):
            if arg in GIT_VALUE_OPTIONS:
                index += 2
                continue
            if arg.startswith(GIT_EQUALS_PREFIXES) or (
                (arg.startswith("-c") or arg.startswith("-C")) and len(arg) > 2
            ):
                index += 1
                continue
            index += 1
            continue
        if arg == "push":
            return True
        if arg == "subtree":
            return subtree_pushes(args[index + 1 :])
        return False
    return False


def subtree_pushes(args: list[str]) -> bool:
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            return False
        if arg.startswith("-"):
            if arg in SUBTREE_VALUE_OPTIONS:
                index += 2
                continue
            if any(arg.startswith(prefix + "=") for prefix in ("--prefix", "--branch", "--message", "--annotate")):
                index += 1
                continue
            index += 1
            continue
        return arg == "push"
    return False


def decide(command: str) -> dict:
    if not command_has_git_push(command):
        return {"permission": "allow"}
    return {
        "permission": "ask",
        "user_message": "git push を実行する前に確認してください。",
        "agent_message": "git push は利用者の確認が必要です。拒否された場合は再実行しないこと。",
    }


def read_command(payload: dict) -> str:
    command = payload.get("command")
    if isinstance(command, str):
        return command
    return ""


def emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        return run_self_test()
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        if "git" in raw and command_has_git_push(raw):
            emit(decide("git push"))
            return 0
        emit({"permission": "allow"})
        return 0
    if not isinstance(payload, dict):
        emit({"permission": "allow"})
        return 0
    emit(decide(read_command(payload)))
    return 0


def run_self_test() -> int:
    positives = [
        "git push",
        "git push origin main",
        "git push --force",
        "git -C /tmp/repo push",
        "git -C /tmp/repo -c user.name=a push origin",
        "git --git-dir=/tmp/r/.git push",
        "git --no-pager push",
        "command git push",
        "sudo git push",
        "sudo -u root git push",
        "FOO=1 git push",
        "git status && git push",
        "git status; git push",
        "git status || git push",
        "git status\ngit push",
        "echo ok | git push",
        "bash -c 'git push'",
        "bash -lc 'git push origin HEAD'",
        'sh -c "git push"',
        "eval 'git push'",
        'echo "$(git push)"',
        "echo `git push`",
        "exec git push",
        "env git push",
        "env FOO=bar git push",
        "/usr/bin/git push",
        "git.exe push",
        "git subtree push --prefix=lib origin main",
        "git subtree --prefix lib push origin main",
        "  git   push  ",
        "git push > /tmp/out",
        "git commit -m 'fix && git push' && git push",
        "diff <(git push)",
    ]
    negatives = [
        "git status",
        "git log --grep=push",
        "git log -S push",
        "echo git push",
        'echo "git push"',
        "echo 'git push'",
        'git commit -m "do not push"',
        'git commit -m "do not push" && git status',
        "# git push",
        "echo hello # git push",
        "echo '$(git push)'",
        "git",
        "git stash push",
        "git diff",
        "ls",
        "python3 script.py",
        "git -c foo=bar status",
    ]
    failed = False
    for command in positives:
        if not command_has_git_push(command):
            print(f"MISS {command!r}", file=sys.stderr)
            failed = True
        if decide(command).get("permission") != "ask":
            print(f"ASK {command!r}", file=sys.stderr)
            failed = True
    for command in negatives:
        if command_has_git_push(command):
            print(f"FALSE {command!r}", file=sys.stderr)
            failed = True
        if decide(command) != {"permission": "allow"}:
            print(f"BLOCKED {command!r}", file=sys.stderr)
            failed = True
    if failed:
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
