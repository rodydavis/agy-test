#!/usr/bin/env python3
"""
issue_helper.py - GitHub Issue Management Helper for rodydavis/agy-test.
Enforces repository isolation and provides convenience commands for task
checkbox toggling, media attachments, and commit-linked closures.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TARGET_REPO = "rodydavis/agy-test"


def run_gh(cmd_args, capture_output=True, text=True):
    """Execute gh command scoped to TARGET_REPO."""
    base_cmd = ["gh"] + cmd_args
    # Ensure -R is present
    if "-R" not in base_cmd and "--repo" not in base_cmd:
        base_cmd.extend(["-R", TARGET_REPO])

    res = subprocess.run(base_cmd, capture_output=capture_output, text=text)
    if res.returncode != 0:
        err_msg = res.stderr.strip() if res.stderr else "Unknown error"
        print(f"Error executing {' '.join(base_cmd)}:\n{err_msg}", file=sys.stderr)
        sys.exit(res.returncode)
    return res.stdout


def cmd_list(args):
    """List issues with task completion summary."""
    output = run_gh(["issue", "list", "--json", "number,title,state,body"])
    issues = json.loads(output)
    if not issues:
        print(f"No open issues found in {TARGET_REPO}.")
        return

    print(f"Issues in {TARGET_REPO}:")
    for issue in issues:
        body = issue.get("body", "")
        tasks = re.findall(r"-\s*\[([ xX])\]\s*(.+)", body)
        task_str = ""
        if tasks:
            done = sum(1 for t in tasks if t[0] in ("x", "X"))
            task_str = f" [{done}/{len(tasks)} tasks completed]"
        print(f"#{issue['number']}: {issue['title']}{task_str}")


def cmd_view(args):
    """View issue details and numbered tasks."""
    output = run_gh(["issue", "view", str(args.issue_number), "--json", "number,title,state,body,url"])
    data = json.loads(output)
    print(f"Issue #{data['number']}: {data['title']}")
    print(f"State: {data['state']}")
    print(f"URL: {data['url']}")
    print("\n--- Body ---")
    body = data.get("body", "")
    print(body)

    tasks = list(re.finditer(r"^(\s*-\s*\[([ xX])\]\s*(.+))$", body, flags=re.MULTILINE))
    if tasks:
        print("\n--- Identified Tasks ---")
        for idx, match in enumerate(tasks, start=1):
            status = "DONE" if match.group(2) in ("x", "X") else "TODO"
            print(f"  [{idx}] [{status}] {match.group(3)}")


def cmd_create(args):
    """Create an issue with standard template and optional media."""
    cmd = ["issue", "create", "--title", args.title]
    if args.body_file:
        cmd.extend(["--body-file", args.body_file])
    elif args.body:
        cmd.extend(["--body", args.body])
    else:
        # Default template
        template_path = Path(__file__).resolve().parent.parent / "templates" / "issue_template.md"
        if template_path.exists():
            cmd.extend(["--body-file", str(template_path)])
        else:
            cmd.extend(["--body", "## Overview\n\n## Tasks\n- [ ] Task 1"])

    if args.attach:
        for att in args.attach:
            cmd.extend(["--attach", att])

    if args.label:
        for lbl in args.label:
            cmd.extend(["--label", lbl])

    out = run_gh(cmd)
    print(out.strip())


def cmd_check_task(args):
    """Toggle a task checkbox from [ ] to [x] in an issue body."""
    output = run_gh(["issue", "view", str(args.issue_number), "--json", "body"])
    body = json.loads(output).get("body", "")

    # Match lines like - [ ] task
    task_matches = list(re.finditer(r"^(\s*-\s*\[([ xX])\]\s*(.+))$", body, flags=re.MULTILINE))
    if not task_matches:
        print(f"No task checkboxes found in issue #{args.issue_number}.")
        return

    target_match = None
    # Check if target is integer index (1-based)
    if args.task.isdigit():
        idx = int(args.task) - 1
        if 0 <= idx < len(task_matches):
            target_match = task_matches[idx]
        else:
            print(f"Task index {args.task} out of range (1-{len(task_matches)}).")
            return
    else:
        # Search by substring
        for tm in task_matches:
            if args.task.lower() in tm.group(3).lower():
                target_match = tm
                break

    if not target_match:
        print(f"Could not find task matching: '{args.task}'")
        return

    old_line = target_match.group(1)
    # Replace [ ] with [x]
    new_line = re.sub(r"\[[ ]\]", "[x]", old_line, count=1)
    if old_line == new_line:
        print(f"Task already completed: {target_match.group(3)}")
        return

    updated_body = body[:target_match.start(1)] + new_line + body[target_match.end(1):]

    # Save to temp file and update
    import tempfile
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".md") as tf:
        tf.write(updated_body)
        temp_name = tf.name

    try:
        run_gh(["issue", "edit", str(args.issue_number), "--body-file", temp_name])
        print(f"Checked task in issue #{args.issue_number}: {target_match.group(3)}")
    finally:
        Path(temp_name).unlink(missing_ok=True)


def cmd_attach(args):
    """Attach media file to an existing issue."""
    attach_spec = args.file
    if args.alt:
        attach_spec = f"{args.file}#{args.alt}"
    run_gh(["issue", "edit", str(args.issue_number), "--attach", attach_spec])
    print(f"Attached {args.file} to issue #{args.issue_number}.")


def cmd_comment(args):
    """Add a comment (and optional media) to an issue."""
    cmd = ["issue", "comment", str(args.issue_number)]
    if args.body_file:
        cmd.extend(["--body-file", args.body_file])
    elif args.body:
        cmd.extend(["--body", args.body])
    else:
        print("Must supply either --body or --body-file.", file=sys.stderr)
        sys.exit(1)

    if args.attach:
        for att in args.attach:
            cmd.extend(["--attach", att])

    out = run_gh(cmd)
    print(out.strip())


def cmd_close(args):
    """Close issue referencing git commit."""
    # Obtain current commit hash
    git_hash_res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    commit_sha = git_hash_res.stdout.strip() if git_hash_res.returncode == 0 else "HEAD"

    comment = args.comment or f"Resolved and completed in commit {commit_sha}. Pushed to origin."
    cmd = ["issue", "close", str(args.issue_number), "--reason", "completed", "--comment", comment]
    out = run_gh(cmd)
    print(out.strip())
    print(f"Issue #{args.issue_number} successfully closed as completed.")


def main():
    parser = argparse.ArgumentParser(description=f"GitHub Issue Helper for {TARGET_REPO}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    subparsers.add_parser("list", help="List open issues and task status")

    # view
    p_view = subparsers.add_parser("view", help="View issue details and numbered tasks")
    p_view.add_argument("issue_number", type=int, help="Issue number")

    # create
    p_create = subparsers.add_parser("create", help="Create a new issue")
    p_create.add_argument("--title", required=True, help="Issue title")
    p_create.add_argument("--body", help="Issue body text")
    p_create.add_argument("--body-file", help="Path to markdown body file")
    p_create.add_argument("--attach", action="append", help="Media file to attach (<path>[#alt])")
    p_create.add_argument("--label", action="append", help="Issue label")

    # check-task
    p_check = subparsers.add_parser("check-task", help="Check off a task in issue body")
    p_check.add_argument("issue_number", type=int, help="Issue number")
    p_check.add_argument("task", help="Task 1-based index or search substring")

    # attach
    p_attach = subparsers.add_parser("attach", help="Attach media to issue")
    p_attach.add_argument("issue_number", type=int, help="Issue number")
    p_attach.add_argument("file", help="Path to image or video")
    p_attach.add_argument("--alt", help="Alt text for media")

    # comment
    p_comment = subparsers.add_parser("comment", help="Add comment to issue")
    p_comment.add_argument("issue_number", type=int, help="Issue number")
    p_comment.add_argument("--body", help="Comment body text")
    p_comment.add_argument("--body-file", help="Comment body file")
    p_comment.add_argument("--attach", action="append", help="Media file to attach")

    # close
    p_close = subparsers.add_parser("close", help="Close issue as completed linked to commit")
    p_close.add_argument("issue_number", type=int, help="Issue number")
    p_close.add_argument("--comment", help="Closing comment")

    args = parser.parse_args()

    commands = {
        "list": cmd_list,
        "view": cmd_view,
        "create": cmd_create,
        "check-task": cmd_check_task,
        "attach": cmd_attach,
        "comment": cmd_comment,
        "close": cmd_close,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
