# Benchmark: what does an agent spend to answer project questions?

English · [Deutsch](#deutsch)

The same five questions, the same data, the same model. Once the agent finds the answer in **Markdown files** (a `README.md` plus `NOTES.md` and `TODO.md` per project, the way many people keep notes), once through the **AgentWorkbench API**.

## Result

Mean per question, 25 runs per row (5 questions, 5 repeats). Model `claude-sonnet-5-5`.

| Projects | Variant | Correct | Tokens | Steps | Cost |
|---|---|---|---|---|---|
| 12 | Markdown files | 24 / 25 | 18,300 | 3.7 | $0.0076 |
| 12 | AgentWorkbench | 25 / 25 | **9,800** (-47 %) | 2.8 | $0.0055 (-28 %) |
| 60 | Markdown files | 25 / 25 | 18,900 | 4.0 | $0.0121 |
| 60 | AgentWorkbench | 25 / 25 | **12,000** (-36 %) | 2.8 | $0.0076 (-37 %) |

- **Tokens** are everything the model processed in that session: input, cached input and output, summed over all steps. About 6,000 of it is the fixed overhead of the system prompt and tool definitions, the same in both variants.
- **AgentWorkbench** here means the briefing API plus `GET /api/todos`. Without that endpoint (briefings and overview only) the saving is smaller: -41 % at 12 projects and -21 % at 60. The benchmark showed that cross-project questions ("which tasks are urgent everywhere?") were the weak spot, so the endpoint was added.
- The saving comes from fewer steps and fewer detours, not from the project text itself being tiny: the text the agent reads through its tools is of the same size in both variants (a few hundred to about 1,300 tokens per question).

Per question, mean tokens at 60 projects:

| Question | Files | AgentWorkbench |
|---|---|---|
| All open P1 tasks across projects | 18,000 | 6,300 |
| Project with the most P1 tasks | 19,300 | 6,300 |
| Paused projects that still have open tasks | 21,700 | 14,000 |
| Why was a decision made (one pinned note) | 10,600 | 13,800 |
| Start of work: where does it run, what must I not do | 25,200 | 19,800 |

Looking up one pinned note ("decision") is a tie, with the files slightly ahead. The biggest gain is in questions that span projects.

## What this does not show

- **The files are tidy.** They are generated from the same data, with a consistent layout and a `(P1)` marker the agent can grep. Real notes are messier, which makes searching them harder, so the real-world gap is likely larger. This is not measured here.
- **Small data.** 12 and 60 projects with short notes. The numbers say nothing about hundreds of projects or very long documents.
- **One model, one agent harness, five questions.** Treat the figures as an indication, not a guarantee. Cost is the list price of that model at the time of the run.
- **Read-only questions.** Ticking off tasks and leaving notes are not part of it.
- The 48 extra projects at the 60-project size are generated filler (`dataset.py`), not real data.

## Reproduce

```bash
# 1. Start two demo servers (12 and 60 projects)
AGENTWORKBENCH_DB=./demo12.db python scripts/demo_seed.py
AGENTWORKBENCH_DB=./demo12.db AGENTWORKBENCH_TOKEN=benchtoken uvicorn app:app --port 8791 &
AGENTWORKBENCH_DB=./demo60.db python benchmark/dataset.py 48
AGENTWORKBENCH_DB=./demo60.db AGENTWORKBENCH_TOKEN=benchtoken uvicorn app:app --port 8792 &

# 2. Run (needs the Claude Code CLI, signed in)
python benchmark/run_benchmark.py --runs 5 --extra 0  --url http://127.0.0.1:8791 --out benchmark/results-12.json
python benchmark/run_benchmark.py --runs 5 --extra 48 --url http://127.0.0.1:8792 --out benchmark/results-60.json
```

The runner starts each agent with `--safe-mode`, so your own `CLAUDE.md`, skills and hooks do not leak in. Answers are checked against keywords in `tasks.json`. `results-*.json` hold every single run including the answer text.

Files: `tasks.json` (questions and expected keywords), `build_fixture.py` (writes the Markdown baseline), `dataset.py` (filler projects), `run_benchmark.py` (runner and summary).

---

## Deutsch

Dieselben fünf Fragen, dieselben Daten, dasselbe Modell. Einmal findet der Agent die Antwort in **Markdown-Dateien** (eine `README.md` sowie `NOTES.md` und `TODO.md` je Projekt, so wie viele ihre Notizen führen), einmal über die **AgentWorkbench-API**.

### Ergebnis

Mittelwert je Frage, 25 Läufe je Zeile (5 Fragen, 5 Wiederholungen). Modell `claude-sonnet-5-5`.

| Projekte | Variante | Richtig | Tokens | Schritte | Kosten |
|---|---|---|---|---|---|
| 12 | Markdown-Dateien | 24 / 25 | 18.300 | 3,7 | 0,0076 $ |
| 12 | AgentWorkbench | 25 / 25 | **9.800** (-47 %) | 2,8 | 0,0055 $ (-28 %) |
| 60 | Markdown-Dateien | 25 / 25 | 18.900 | 4,0 | 0,0121 $ |
| 60 | AgentWorkbench | 25 / 25 | **12.000** (-36 %) | 2,8 | 0,0076 $ (-37 %) |

- **Tokens** ist alles, was das Modell in der Sitzung verarbeitet hat: Eingabe, zwischengespeicherte Eingabe und Ausgabe, über alle Schritte summiert. Rund 6.000 davon sind fester Aufwand für System-Prompt und Werkzeugbeschreibungen, in beiden Varianten gleich.
- **AgentWorkbench** heißt hier Briefing-API plus `GET /api/todos`. Ohne diesen Endpunkt (nur Briefings und Übersicht) ist die Ersparnis kleiner: -41 % bei 12 Projekten und -21 % bei 60. Der Benchmark hat gezeigt, dass Fragen über mehrere Projekte ("welche Aufgaben sind überall dringend?") die Schwachstelle waren, deshalb gibt es den Endpunkt.
- Die Ersparnis kommt aus weniger Schritten und weniger Umwegen, nicht daher, dass der Projekttext selbst winzig wäre: Der Text, den der Agent über seine Werkzeuge liest, ist in beiden Varianten gleich groß (einige hundert bis etwa 1.300 Tokens je Frage).

Beim Nachschlagen einer einzelnen angehefteten Notiz ("Entscheidung") gibt es keinen Vorteil, die Dateien liegen leicht vorn. Der größte Gewinn liegt bei Fragen über mehrere Projekte.

### Was das nicht zeigt

- **Die Dateien sind aufgeräumt.** Sie werden aus denselben Daten erzeugt, mit einheitlichem Aufbau und einer `(P1)`-Markierung, die der Agent durchsuchen kann. Echte Notizen sind unordentlicher und schwerer zu durchsuchen, der Abstand dürfte in der Praxis größer sein. Das ist hier nicht gemessen.
- **Kleine Datenmenge.** 12 und 60 Projekte mit kurzen Notizen. Über Hunderte Projekte oder sehr lange Dokumente sagen die Zahlen nichts.
- **Ein Modell, ein Agent-Werkzeug, fünf Fragen.** Die Werte sind ein Anhaltspunkt, keine Garantie. Die Kosten sind der Listenpreis des Modells zum Zeitpunkt des Laufs.
- **Nur lesende Fragen.** Abhaken und Notizen schreiben sind nicht Teil davon.
- Die 48 zusätzlichen Projekte bei 60 Projekten sind erzeugte Füllung (`dataset.py`), keine echten Daten.

### Nachstellen

Siehe den englischen Abschnitt "Reproduce". Der Runner startet jeden Agenten mit `--safe-mode`, damit deine eigene `CLAUDE.md`, Skills und Hooks nicht hineinwirken.
