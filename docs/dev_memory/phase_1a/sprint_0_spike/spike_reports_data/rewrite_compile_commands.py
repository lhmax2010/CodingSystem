"""Rewrite compile_commands.json from chroot paths to host paths.

This spike helper lets host clangd index the long-lived host checkout under
codes/pkgmgr-info while reusing compile commands produced inside GBS chroot.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_GBS_ROOT = "/home/linhao/GBS-ROOT-TIZEN-LLVM/local/BUILD-ROOTS/scratch.x86_64.0"
DEFAULT_CHROOT_BUILD_PREFIX = "/home/abuild/rpmbuild/BUILD/pkgmgr-info-0.37.0"


def rewrite_commands(
    input_path: str,
    output_path: str,
    host_codes_path: str,
    gbs_root: str = DEFAULT_GBS_ROOT,
    chroot_build_prefix: str = DEFAULT_CHROOT_BUILD_PREFIX,
) -> dict[str, Any]:
    """Rewrite chroot-view compile commands for host-view clangd."""

    with open(input_path, encoding="utf-8") as stream:
        cc = json.load(stream)

    rules = [
        (chroot_build_prefix, host_codes_path),
        ("/usr/include", f"{gbs_root}/usr/include"),
        ("/usr/lib64", f"{gbs_root}/usr/lib64"),
        ("/usr/lib", f"{gbs_root}/usr/lib"),
        ("/bin/x86_64-tizen-linux-gnu-clang++", "/usr/bin/clang++"),
        ("/bin/x86_64-tizen-linux-gnu-clang", "/usr/bin/clang"),
        ("/bin/x86_64-tizen-linux-gnu-g++", "/usr/bin/g++"),
        ("/bin/x86_64-tizen-linux-gnu-gcc", "/usr/bin/gcc"),
    ]

    def apply_rules(value: str) -> str:
        if not isinstance(value, str):
            return value
        rewritten = value
        placeholders: list[tuple[str, str]] = []
        for index, (old, new) in enumerate(rules):
            placeholder = f"__CODING_SYSTEM_REWRITE_{index}__"
            rewritten = rewritten.replace(old, placeholder)
            placeholders.append((placeholder, new))
        for placeholder, new in placeholders:
            rewritten = rewritten.replace(placeholder, new)
        return rewritten

    def filter_pseudo_includes(command: str) -> str:
        """Remove CMake SYSTEM pseudo include flags before clangd/LLM use.

        CMake can produce -I<path>/SYSTEM as an artifact of SYSTEM include
        handling. clangd ignores the missing path, but evidence packets should
        not show it to the LLM as if it were a real source directory.
        """

        command = re.sub(r"\s-I\S*/SYSTEM(?=\s|$)", "", command)
        command = re.sub(r"\s-isystem\s+\S*/SYSTEM(?=\s|$)", "", command)
        return command

    def filter_pseudo_include_args(arguments: list[str]) -> list[str]:
        filtered: list[str] = []
        skip_next = False
        for index, argument in enumerate(arguments):
            if skip_next:
                skip_next = False
                continue
            if argument.startswith("-I") and argument.endswith("/SYSTEM"):
                continue
            if argument == "-isystem" and index + 1 < len(arguments) and arguments[index + 1].endswith("/SYSTEM"):
                skip_next = True
                continue
            filtered.append(argument)
        return filtered

    rewritten_entries = 0
    for entry in cc:
        before = json.dumps(entry, sort_keys=True)
        if "file" in entry:
            entry["file"] = apply_rules(entry["file"])
        if "directory" in entry:
            entry["directory"] = apply_rules(entry["directory"])
        if "command" in entry:
            entry["command"] = filter_pseudo_includes(apply_rules(entry["command"]))
        if "arguments" in entry:
            entry["arguments"] = filter_pseudo_include_args([apply_rules(arg) for arg in entry["arguments"]])
        after = json.dumps(entry, sort_keys=True)
        if after != before:
            rewritten_entries += 1

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as stream:
        json.dump(cc, stream, indent=2)
        stream.write("\n")

    return {
        "total": len(cc),
        "rewritten": rewritten_entries,
        "output_path": str(output),
        "sample_first_entry_file": cc[0].get("file") if cc else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--host-codes", required=True, help="Host codes/pkgmgr-info absolute path")
    parser.add_argument("--gbs-root", default=DEFAULT_GBS_ROOT)
    parser.add_argument("--chroot-build-prefix", default=DEFAULT_CHROOT_BUILD_PREFIX)
    args = parser.parse_args()

    result = rewrite_commands(
        args.input,
        args.output,
        args.host_codes,
        args.gbs_root,
        args.chroot_build_prefix,
    )
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
