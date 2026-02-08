#!/usr/bin/env python3
"""repliclaude: lightweight git checkpoint and status tool."""

import subprocess
import sys
from datetime import datetime, timezone

PHASES = ["understand", "replicate", "report"]


def run_git(*args):
    result = subprocess.run(["git"] + list(args), capture_output=True, text=True)
    if result.returncode != 0 and "fatal" in result.stderr:
        print(f"git error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def cmd_checkpoint(message):
    """Stage all changes and commit with a consistent format."""
    run_git("add", "-A")
    # Check if there's anything to commit
    status = run_git("status", "--porcelain")
    if not status:
        print("Nothing to commit.")
        return
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    full_message = f"[replic] {message}\n\nTimestamp: {timestamp}"
    run_git("commit", "-m", full_message)
    print(f"Checkpoint: {message}")


def cmd_tag(phase):
    """Tag current commit as phase completion."""
    if phase not in PHASES:
        print(f"Unknown phase: {phase}. Valid: {', '.join(PHASES)}", file=sys.stderr)
        sys.exit(1)
    tag_name = f"{phase}-complete"
    # Remove existing tag if present (allows re-tagging)
    run_git("tag", "-d", tag_name)
    run_git("tag", tag_name)
    print(f"Tagged: {tag_name}")


def cmd_status():
    """Show which phases are complete based on git tags."""
    print("\nrepliclaude Status")
    for phase in PHASES:
        tag = f"{phase}-complete"
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ai", tag],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            date = result.stdout.strip()[:10]
            print(f"  {phase:<15} COMPLETE ({date})")
        else:
            # Check if there are commits mentioning this phase
            log = run_git("log", "--oneline", "--grep", f"[replic] {phase}:")
            if log:
                count = len(log.strip().split("\n"))
                print(f"  {phase:<15} IN PROGRESS ({count} checkpoint{'s' if count > 1 else ''})")
            else:
                print(f"  {phase:<15} PENDING")
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  replic.py checkpoint 'message'   # git commit with consistent format")
        print("  replic.py tag <phase>             # mark phase complete")
        print("  replic.py status                  # show pipeline status")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "checkpoint":
        if len(sys.argv) < 3:
            print("Usage: replic.py checkpoint 'message'", file=sys.stderr)
            sys.exit(1)
        cmd_checkpoint(sys.argv[2])
    elif cmd == "tag":
        if len(sys.argv) < 3:
            print("Usage: replic.py tag <phase>", file=sys.stderr)
            sys.exit(1)
        cmd_tag(sys.argv[2])
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
