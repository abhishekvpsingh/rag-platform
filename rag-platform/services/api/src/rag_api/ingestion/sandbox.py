"""No-network parser child with OS resource limits and fail-closed isolation."""

import codecs
import ctypes
import errno
import json
import platform
import resource
import subprocess
import sys
import tempfile
from pathlib import Path

from rag_api.ingestion.parsing import MAX_FILE, MAX_TEXT, Parsed, ParseFailure, parse

OUTPUT_LIMIT = MAX_TEXT * 4


def restrict_linux() -> None:
    """Deny by default after imports; no file opens, sockets, exec or child creation."""
    lib = ctypes.CDLL("libseccomp.so.2")
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    context = lib.seccomp_init(0x00050000 | errno.EPERM)
    if not context:
        raise RuntimeError("sandbox_unavailable")
    try:
        for name in (
            "read",
            "write",
            "close",
            "fstat",
            "newfstatat",
            "lseek",
            "mmap",
            "mprotect",
            "munmap",
            "brk",
            "mremap",
            "madvise",
            "futex",
            "rt_sigaction",
            "rt_sigprocmask",
            "rt_sigreturn",
            "sigaltstack",
            "clock_gettime",
            "gettimeofday",
            "getpid",
            "gettid",
            "getrandom",
            "exit",
            "exit_group",
            "sched_yield",
            "fcntl",
        ):
            number = lib.seccomp_syscall_resolve_name(name.encode())
            if number >= 0 and lib.seccomp_rule_add(context, 0x7FFF0000, number, 0) != 0:
                raise RuntimeError("sandbox_unavailable")
        if lib.seccomp_load(context) != 0:
            raise RuntimeError("sandbox_unavailable")
    finally:
        lib.seccomp_release(context)


def child() -> None:
    for encoding in ("utf-8-sig", "utf-16", "utf-16-be", "utf-16-le", "cp1252", "cp437", "latin1"):
        codecs.lookup(encoding)
    resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
    resource.setrlimit(resource.RLIMIT_FSIZE, (OUTPUT_LIMIT, OUTPUT_LIMIT))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if platform.system() == "Linux":
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        restrict_linux()
    else:
        raise RuntimeError("sandbox_unavailable")
    try:
        data = sys.stdin.buffer.read(MAX_FILE + 1)
        parsed = parse(data, sys.argv[1])
        encoded = parsed.model_dump_json().encode()
        if len(encoded) > OUTPUT_LIMIT:
            raise ParseFailure("extracted_size_limit")
        sys.stdout.buffer.write(encoded)
    except ParseFailure as exc:
        sys.stdout.write(json.dumps({"error": str(exc)}))


def isolated_parse(data: bytes, format: str) -> Parsed:
    if not data or len(data) > MAX_FILE:
        raise ParseFailure("file_size_limit")
    if format not in {"txt", "md", "html", "csv", "docx", "xlsx", "pdf"}:
        raise ParseFailure("unsupported_format")
    source = Path(__file__).resolve().parents[2]
    command = [sys.executable, "-m", "rag_api.ingestion.sandbox", format]
    env = {"PYTHONPATH": str(source), "PYTHONDONTWRITEBYTECODE": "1", "LANG": "C.UTF-8"}
    if platform.system() != "Linux":
        raise ParseFailure("sandbox_requires_linux_container")
    # File output is limited by RLIMIT_FSIZE; avoid unbounded communicate() stdout buffering.
    with tempfile.TemporaryFile() as output:
        try:
            result = subprocess.run(
                command,
                input=data,
                stdout=output,
                stderr=subprocess.DEVNULL,
                env=env,
                timeout=15,
                close_fds=True,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise ParseFailure("parser_unavailable_or_timeout") from None
        if result.returncode:
            raise ParseFailure("parser_resource_or_sandbox_failure")
        output.seek(0)
        raw = output.read(OUTPUT_LIMIT + 1)
        if len(raw) > OUTPUT_LIMIT:
            raise ParseFailure("extracted_size_limit")
        try:
            value = json.loads(raw)
            if isinstance(value, dict) and "error" in value:
                raise ParseFailure(str(value["error"]))
            return Parsed.model_validate(value)
        except (ValueError, TypeError):
            raise ParseFailure("invalid_parser_output") from None


if __name__ == "__main__":
    child()
