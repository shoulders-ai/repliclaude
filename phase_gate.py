#!/usr/bin/env python3
"""
phase_gate.py — Lightweight phase transition manager for REPLIC-AI.

Enforces sequential phase completion with audit trail.
Each phase transition: snapshots conversation, hashes outputs, commits to git.

Usage:
    python phase_gate.py start <phase_number>    # Validate prerequisites, create phase dir
    python phase_gate.py complete <phase_number>  # Lock phase, snapshot conversation, commit
    python phase_gate.py status                   # Show current state
    python phase_gate.py validate <phase_number>  # Check if phase can start (dry run)
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from glob import glob
from pathlib import Path

# --- Configuration ---

PROJECT_ROOT = Path(__file__).parent
LEDGER_FILE = PROJECT_ROOT / "LEDGER.md"
STATUS_FILE = PROJECT_ROOT / "STATUS.md"

PHASE_NAMES = {
    1: "Comprehension",
    2: "Planning",
    3: "Data Acquisition",
    4: "Implementation",
    5: "Comparison",
    6: "Final Report",
}

PHASE_DIRS = {
    1: "phase1_comprehension",
    2: "phase2_planning",
    3: "phase3_data",
    4: "phase4_implementation",
    5: "phase5_comparison",
    6: "phase6_report",
}

# Claude Code conversation storage
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def get_project_conversation_dir():
    """Find the Claude conversation directory for this project."""
    # Claude encodes the project path by replacing / with -
    project_path = str(PROJECT_ROOT).replace("/", "-")
    if project_path.startswith("-"):
        pass  # keep leading dash
    conv_dir = CLAUDE_PROJECTS_DIR / project_path
    if conv_dir.exists():
        return conv_dir
    return None


def extract_conversation_log(output_path: Path):
    """Extract conversation from Claude's JSONL files into readable markdown."""
    conv_dir = get_project_conversation_dir()
    if not conv_dir:
        print("WARNING: Could not find Claude conversation directory.")
        output_path.write_text("# Conversation Log\n\nNo conversation data found.\n")
        return

    # Find the most recent session file
    sessions_index = conv_dir / "sessions-index.json"
    if not sessions_index.exists():
        print("WARNING: No sessions index found.")
        output_path.write_text("# Conversation Log\n\nNo session index found.\n")
        return

    with open(sessions_index) as f:
        index = json.load(f)

    if not index.get("entries"):
        output_path.write_text("# Conversation Log\n\nNo sessions found.\n")
        return

    # Use the most recent session (last modified)
    entries = sorted(index["entries"], key=lambda e: e.get("fileMtime", 0), reverse=True)
    session_file = Path(entries[0]["fullPath"])

    if not session_file.exists():
        output_path.write_text("# Conversation Log\n\nSession file not found.\n")
        return

    lines = []
    lines.append("# Conversation Log")
    lines.append(f"\nExtracted: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Session: {entries[0]['sessionId']}")
    lines.append("")

    with open(session_file) as f:
        for raw_line in f:
            try:
                obj = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            msg_type = obj.get("type")
            if msg_type not in ("user", "assistant"):
                continue

            timestamp = obj.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                    ts_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                except (ValueError, TypeError, OSError):
                    ts_str = str(timestamp)
            else:
                ts_str = "unknown"

            message = obj.get("message", {})
            role = message.get("role", msg_type).upper()
            content = message.get("content", "")

            # Content can be string or list of content blocks
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            text_parts.append(f"[Tool call: {block.get('name', 'unknown')}]")
                        elif block.get("type") == "tool_result":
                            text_parts.append("[Tool result received]")
                    elif isinstance(block, str):
                        text_parts.append(block)
                content = "\n".join(text_parts)
            elif not isinstance(content, str):
                content = str(content)

            # Truncate very long messages
            if len(content) > 3000:
                content = content[:3000] + "\n\n[... truncated ...]"

            lines.append(f"---\n### {role} ({ts_str})\n")
            lines.append(content)
            lines.append("")

    output_path.write_text("\n".join(lines))
    print(f"Conversation log saved to {output_path}")


def hash_file(path: Path) -> str:
    """SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]  # short hash for readability


def hash_directory(dir_path: Path) -> dict:
    """Hash all files in a directory (excluding MANIFEST.json and conversation_log.md)."""
    hashes = {}
    if not dir_path.exists():
        return hashes
    for fpath in sorted(dir_path.rglob("*")):
        if fpath.is_file() and fpath.name not in ("MANIFEST.json", "conversation_log.md"):
            rel = str(fpath.relative_to(PROJECT_ROOT))
            hashes[rel] = hash_file(fpath)
    return hashes


def read_manifest(phase_num: int) -> dict | None:
    """Read a phase's MANIFEST.json if it exists."""
    manifest_path = PROJECT_ROOT / PHASE_DIRS[phase_num] / "MANIFEST.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return None


def write_manifest(phase_num: int, input_hashes: dict):
    """Write MANIFEST.json for a phase."""
    phase_dir = PROJECT_ROOT / PHASE_DIRS[phase_num]
    manifest = {
        "phase": phase_num,
        "phase_name": PHASE_NAMES[phase_num],
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "input_hashes": input_hashes,
        "output_hashes": hash_directory(phase_dir),
    }
    manifest_path = phase_dir / "MANIFEST.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest written: {manifest_path}")


def validate_upstream(phase_num: int) -> tuple[bool, list[str]]:
    """Check that all upstream phases are complete and unchanged."""
    issues = []

    if phase_num == 1:
        return True, []  # No upstream dependency

    # Check that previous phase is complete
    prev = phase_num - 1
    prev_manifest = read_manifest(prev)
    if prev_manifest is None:
        issues.append(f"Phase {prev} ({PHASE_NAMES[prev]}) has not been completed.")
        return False, issues

    # Check that all phases before prev are also complete
    for p in range(1, prev):
        m = read_manifest(p)
        if m is None:
            issues.append(f"Phase {p} ({PHASE_NAMES[p]}) has not been completed.")

    # Check that upstream outputs haven't changed since they were consumed
    # (i.e., the previous phase's inputs still match their manifests)
    for p in range(1, phase_num):
        m = read_manifest(p)
        if m is None:
            continue
        # Verify the output files haven't been modified since completion
        current_hashes = hash_directory(PROJECT_ROOT / PHASE_DIRS[p])
        recorded_hashes = m.get("output_hashes", {})
        for fpath, recorded_hash in recorded_hashes.items():
            current_hash = current_hashes.get(fpath)
            if current_hash is None:
                issues.append(f"STALE: {fpath} was deleted since Phase {p} completed.")
            elif current_hash != recorded_hash:
                issues.append(f"STALE: {fpath} was modified since Phase {p} completed. Phase {p} must be re-run.")

    return len(issues) == 0, issues


def update_status(phase_num: int, status: str):
    """Update STATUS.md."""
    lines = ["# Replication Status\n"]

    # Read paper info from README if available
    lines.append(f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
    lines.append("| Phase | Status | Completed |")
    lines.append("|-------|--------|-----------|")

    for p in range(1, 8):
        m = read_manifest(p)
        if p == phase_num:
            p_status = status
        elif m:
            p_status = "COMPLETE"
        else:
            p_status = "PENDING"

        completed = m["completed_at"][:10] if m else "—"
        lines.append(f"| {p}. {PHASE_NAMES[p]} | {p_status} | {completed} |")

    STATUS_FILE.write_text("\n".join(lines) + "\n")


def update_ledger(phase_num: int, action: str, note: str = ""):
    """Append entry to LEDGER.md."""
    if not LEDGER_FILE.exists():
        LEDGER_FILE.write_text("# Phase Ledger\n\nAppend-only log of phase transitions.\n\n")

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"- **{ts}** | Phase {phase_num} ({PHASE_NAMES[phase_num]}) | {action}"
    if note:
        entry += f" | {note}"
    entry += "\n"

    with open(LEDGER_FILE, "a") as f:
        f.write(entry)


def git_commit(message: str):
    """Stage all changes and commit."""
    try:
        subprocess.run(["git", "add", "-A"], cwd=PROJECT_ROOT, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
        )
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        commit_hash = result.stdout.strip()
        print(f"Committed: {commit_hash} — {message}")
        return commit_hash
    except subprocess.CalledProcessError as e:
        print(f"Git commit failed: {e.stderr.decode() if e.stderr else e}")
        return None


# --- Commands ---


def cmd_start(phase_num: int):
    """Validate and prepare to start a phase."""
    print(f"\n=== Starting Phase {phase_num}: {PHASE_NAMES[phase_num]} ===\n")

    ok, issues = validate_upstream(phase_num)
    if not ok:
        print("BLOCKED: Cannot start this phase.\n")
        for issue in issues:
            print(f"  - {issue}")
        print("\nResolve these issues before proceeding.")
        sys.exit(1)

    # Create phase directory
    phase_dir = PROJECT_ROOT / PHASE_DIRS[phase_num]
    phase_dir.mkdir(parents=True, exist_ok=True)

    update_status(phase_num, "IN PROGRESS")
    update_ledger(phase_num, "STARTED")

    print(f"Phase directory: {phase_dir}")
    print("Upstream validation: PASSED")
    print(f"\nPhase {phase_num} is ready to begin.\n")


def cmd_commit(phase_num: int, note: str = ""):
    """Freeze sub-agent work: git commit outputs + GATE.md, record hashes."""
    print(f"\n=== Committing Phase {phase_num}: {PHASE_NAMES[phase_num]} (sub-agent snapshot) ===\n")

    phase_dir = PROJECT_ROOT / PHASE_DIRS[phase_num]
    if not phase_dir.exists():
        print(f"ERROR: Phase directory {phase_dir} does not exist. Run 'start' first.")
        sys.exit(1)

    # Check that GATE.md exists
    gate_file = phase_dir / "GATE.md"
    if not gate_file.exists():
        print(f"WARNING: No GATE.md found. The orchestrator should write GATE.md before committing.")

    # Update status and ledger
    update_status(phase_num, "REVIEW")
    update_ledger(phase_num, "COMMITTED (awaiting human review)", note)

    # Git commit sub-agent work
    commit_msg = f"phase {phase_num} commit: {PHASE_NAMES[phase_num]}"
    if note:
        commit_msg += f" — {note}"
    commit_hash = git_commit(commit_msg)

    if commit_hash:
        print(f"Sub-agent work committed: {commit_hash}")
        update_ledger(phase_num, f"git commit {commit_hash}")

    print(f"\nPhase {phase_num} sub-agent work frozen. Awaiting human review of GATE.md.\n")


def cmd_complete(phase_num: int, note: str = ""):
    """Lock a phase after human approval: snapshot conversation, final commit."""
    print(f"\n=== Completing Phase {phase_num}: {PHASE_NAMES[phase_num]} (human approved) ===\n")

    phase_dir = PROJECT_ROOT / PHASE_DIRS[phase_num]
    if not phase_dir.exists():
        print(f"ERROR: Phase directory {phase_dir} does not exist.")
        sys.exit(1)

    # Check that GATE.md exists
    gate_file = phase_dir / "GATE.md"
    if not gate_file.exists():
        print(f"WARNING: No GATE.md found in {phase_dir}.")

    # Snapshot conversation
    conv_log = phase_dir / "conversation_log.md"
    extract_conversation_log(conv_log)

    # Hash upstream outputs as our inputs
    input_hashes = {}
    if phase_num > 1:
        for p in range(1, phase_num):
            dir_hashes = hash_directory(PROJECT_ROOT / PHASE_DIRS[p])
            input_hashes.update(dir_hashes)

    # Write manifest (locks the phase)
    write_manifest(phase_num, input_hashes)

    # Update status and ledger
    update_status(phase_num, "COMPLETE")
    update_ledger(phase_num, "COMPLETED (human approved)", note)

    # Git commit (human additions + conversation log + manifest)
    commit_msg = f"phase {phase_num} complete: {PHASE_NAMES[phase_num]}"
    if note:
        commit_msg += f" — {note}"
    commit_hash = git_commit(commit_msg)

    if commit_hash:
        update_ledger(phase_num, f"LOCKED as git commit {commit_hash}")

    print(f"\nPhase {phase_num} locked. Downstream phases can now start.\n")


def cmd_status():
    """Show current pipeline status."""
    print("\n=== REPLIC-AI Pipeline Status ===\n")
    for p in range(1, 8):
        m = read_manifest(p)
        if m:
            print(f"  Phase {p}: {PHASE_NAMES[p]:20s} COMPLETE ({m['completed_at'][:10]})")
        else:
            phase_dir = PROJECT_ROOT / PHASE_DIRS[p]
            if phase_dir.exists():
                print(f"  Phase {p}: {PHASE_NAMES[p]:20s} IN PROGRESS")
            else:
                print(f"  Phase {p}: {PHASE_NAMES[p]:20s} PENDING")

    # Check for staleness — both self-modification and upstream changes
    print("\n--- Staleness Check ---")
    any_stale = False
    for p in range(1, 8):
        m = read_manifest(p)
        if m is None:
            continue
        # Check if this phase's own outputs were modified after completion
        current_hashes = hash_directory(PROJECT_ROOT / PHASE_DIRS[p])
        recorded_hashes = m.get("output_hashes", {})
        for fpath, recorded_hash in recorded_hashes.items():
            current_hash = current_hashes.get(fpath)
            if current_hash is None:
                any_stale = True
                print(f"  STALE: Phase {p} — {fpath} was deleted after completion.")
            elif current_hash != recorded_hash:
                any_stale = True
                print(f"  STALE: Phase {p} — {fpath} was modified after completion.")
        # Check upstream validity for phases > 1
        if p > 1:
            ok, issues = validate_upstream(p)
            if not ok:
                any_stale = True
                for issue in issues:
                    print(f"  {issue}")
    if not any_stale:
        print("  All completed phases are current.")
    print()


def cmd_validate(phase_num: int):
    """Dry-run validation for starting a phase."""
    ok, issues = validate_upstream(phase_num)
    if ok:
        print(f"Phase {phase_num} ({PHASE_NAMES[phase_num]}): READY to start.")
    else:
        print(f"Phase {phase_num} ({PHASE_NAMES[phase_num]}): BLOCKED.")
        for issue in issues:
            print(f"  - {issue}")


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="REPLIC-AI phase gate manager")
    parser.add_argument("command", choices=["start", "commit", "complete", "status", "validate"])
    parser.add_argument("phase", nargs="?", type=int, help="Phase number (1-6)")
    parser.add_argument("--note", default="", help="Optional note for the ledger")
    args = parser.parse_args()

    if args.command in ("start", "commit", "complete", "validate") and args.phase is None:
        parser.error(f"'{args.command}' requires a phase number.")

    if args.phase and args.phase not in PHASE_NAMES:
        parser.error(f"Phase must be 1-6, got {args.phase}")

    if args.command == "start":
        cmd_start(args.phase)
    elif args.command == "commit":
        cmd_commit(args.phase, args.note)
    elif args.command == "complete":
        cmd_complete(args.phase, args.note)
    elif args.command == "status":
        cmd_status()
    elif args.command == "validate":
        cmd_validate(args.phase)


if __name__ == "__main__":
    main()
