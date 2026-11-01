"""Measure what an agent spends to answer project questions: Markdown files vs. the AgentWorkbench API.

    python benchmark/run_benchmark.py --runs 3 --out benchmark/results.json

Needs the Claude Code CLI (run with --safe-mode, so your own CLAUDE.md, skills and hooks stay out) and a demo server:

    AGENTWORKBENCH_DB=./demo.db python scripts/demo_seed.py
    AGENTWORKBENCH_DB=./demo.db AGENTWORKBENCH_TOKEN=benchtoken uvicorn app:app --port 8791
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHARS_PER_TOKEN = 3.6
SYSTEM = "You answer questions about the user's projects. Use the tools to look things up. Answer in English, in at most four lines."

HINT = {
    "files": ("Project information is kept as Markdown files in the current directory. README.md lists the projects. Each "
              "project folder holds NOTES.md (notes and log), TODO.md (tasks) and a docs folder."),
    "api": ("Project information is kept in a dashboard with an HTTP API at {url}. Send the header "
            "'Authorization: Bearer {token}'. GET /api/overview lists all projects, GET /api/projects/<slug> returns the "
            "briefing of one project. Use curl."),
    "api_todos": ("Project information is kept in a dashboard with an HTTP API at {url}. Send the header "
                  "'Authorization: Bearer {token}'. GET /api/overview lists all projects, GET /api/projects/<slug> returns "
                  "the briefing of one project, GET /api/todos?prio=1 lists the open tasks of all projects (prio is the "
                  "lowest priority to include, optional project=<slug>). Use curl."),
}
TOOLS = {
    "files": ["--tools", "Read,Grep,Glob,Bash", "--allowedTools", "Read,Grep,Glob,Bash(cat:*),Bash(ls:*),Bash(grep:*)"],
    "api": ["--tools", "Bash", "--allowedTools", "Bash(curl:*)"],
    "api_todos": ["--tools", "Bash", "--allowedTools", "Bash(curl:*)"],
}


def text_of(content):
    if isinstance(content, str):
        return content
    return "".join(c.get("text", "") for c in content if isinstance(c, dict))


def run_one(job):
    mode, task, n, cwd, model, url, token = job
    prompt = HINT[mode].format(url=url, token=token) + "\n\nQuestion: " + task["question"]
    cmd = [os.environ.get("CLAUDE_BIN") or shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude.exe"), "-p", prompt, "--output-format", "stream-json", "--verbose", "--model", model,
           "--system-prompt", SYSTEM, "--safe-mode", "--strict-mcp-config", "--no-session-persistence",
           *TOOLS[mode]]
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=600)
    tool_chars, answer, result = 0, "", {}
    for line in proc.stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "user":
            for c in ev["message"]["content"]:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    tool_chars += len(text_of(c.get("content", "")))
        elif ev.get("type") == "result":
            result = ev
            answer = ev.get("result", "")
    u = result.get("usage", {})
    total = sum(u.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens",
                                      "output_tokens"))
    ok = all(k.lower() in answer.lower() for k in task["must_contain"])
    row = dict(mode=mode, task=task["id"], run=n, correct=ok, turns=result.get("num_turns"),
               tool_tokens=round(tool_chars / CHARS_PER_TOKEN), total_tokens=total,
               cost_usd=result.get("total_cost_usd"), seconds=round(result.get("duration_ms", 0) / 1000, 1),
               answer=answer.strip())
    print(f"{mode:5} {task['id']:12} #{n} ok={ok} turns={row['turns']} tool={row['tool_tokens']} "
          f"total={total} ${row['cost_usd']}", flush=True)
    return row


def summarize(rows):
    out = {}
    for mode in HINT:
        r = [x for x in rows if x["mode"] == mode]
        out[mode] = dict(
            runs=len(r),
            correct=sum(x["correct"] for x in r),
            tool_tokens_median=statistics.median(x["tool_tokens"] for x in r),
            total_tokens_median=statistics.median(x["total_tokens"] for x in r),
            turns_median=statistics.median(x["turns"] for x in r),
            cost_usd_mean=round(statistics.mean(x["cost_usd"] for x in r), 4),
            seconds_median=statistics.median(x["seconds"] for x in r),
        )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--url", default="http://127.0.0.1:8791")
    ap.add_argument("--token", default="benchtoken")
    ap.add_argument("--extra", type=int, default=0, help="filler projects added to the 12 demo projects")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out", default=str(HERE / "results.json"))
    a = ap.parse_args()
    tasks = json.loads((HERE / "tasks.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        files_dir, api_dir = Path(tmp, "files"), Path(tmp, "api")
        api_dir.mkdir()
        subprocess.run([sys.executable, str(HERE / "build_fixture.py"), str(files_dir), str(a.extra)], check=True)
        jobs = [(m, t, n, str(files_dir if m == "files" else api_dir), a.model, a.url, a.token)
                for n in range(1, a.runs + 1) for t in tasks for m in HINT]
        with ThreadPoolExecutor(a.workers) as pool:
            rows = list(pool.map(run_one, jobs))
    result = dict(projects=12 + a.extra, model=a.model, runs_per_task=a.runs, tasks=len(tasks), summary=summarize(rows), rows=rows)
    Path(a.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
