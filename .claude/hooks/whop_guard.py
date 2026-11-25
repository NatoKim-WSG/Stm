"""PreToolUse guard for the Whop MCP server (mcp__whop__*).

Whop's consent screen required admin scopes (transfers, withdrawals, payout
destinations, crypto swaps, charging payments ...). This hook narrows what
Claude Code may actually call to what the clipping pipeline needs:

  * read-only tools, and
  * three bounty-submission write operations via call_write_operation.

Everything else is denied. Any error inside the guard also denies (fail closed).
To allow something new, add it deliberately to READ_TOOLS or WRITE_OPERATIONS.
"""
import json
import sys

PREFIX = "mcp__whop__"

# Named Whop tools that only read (plus any list_* / get_* tool).
READ_TOOLS = {
    "connection_status",
    "search_operations",
    "describe_operation",
    "call_read_operation",  # server-side: only accepts read_only operations
    "docs_search",
    "docs_query",
    "search",
    "fetch",
}
READ_PREFIXES = ("list_", "get_")

# The only write operations allowed through call_write_operation.
WRITE_OPERATIONS = {
    "create_bounty_submission",  # submit a Short's link to a campaign
    "submit_bounty_submission",  # finish a claimed attempt, if a campaign uses that flow
    "cancel_bounty_submission",  # withdraw a wrong submission
}


def decide(payload):
    """Return a deny reason, or None to let the normal permission flow continue."""
    tool = payload.get("tool_name") or ""
    if not tool.startswith(PREFIX):
        return None
    name = tool[len(PREFIX):]
    if name in READ_TOOLS or name.startswith(READ_PREFIXES):
        return None
    if name == "call_write_operation":
        op = (payload.get("tool_input") or {}).get("name") or ""
        if op in WRITE_OPERATIONS:
            return None
        return (f"Blocked by project guard: Whop write operation '{op}' is not allowed. "
                "Only bounty submissions are (see .claude/hooks/whop_guard.py).")
    return (f"Blocked by project guard: Whop tool '{name}' is not allowed "
            "(see .claude/hooks/whop_guard.py).")


def main():
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        reason = decide(payload)
    except Exception as exc:  # fail closed
        reason = f"Whop guard error ({exc.__class__.__name__}); blocking to be safe."
    if reason:
        sys.stdout.write(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }))
    sys.exit(0)


if __name__ == "__main__":
    main()
