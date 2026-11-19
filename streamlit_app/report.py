"""Build a shareable Markdown report from a chat session."""


def build_report(filename: str, messages: list) -> str:
    lines = [f"# Analysis report: {filename}", ""]
    for message in messages:
        if message.get("role") == "user":
            lines += [f"## Question: {message['content']}", ""]
            continue
        lines += [message.get("content", ""), ""]
        if message.get("code_output"):
            lines += ["Output:", "", "```text", message["code_output"].rstrip(), "```", ""]
        charts = len(message.get("charts", []))
        if charts:
            lines += [f"_{charts} chart(s) were shown in the app._", ""]
    return "\n".join(lines).rstrip() + "\n"
