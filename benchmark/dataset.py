"""Grow the demo data with deterministic filler projects, so the benchmark can run at several sizes.

The filler never contains P1 tasks, paused projects with open tasks or text that the benchmark questions ask about.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import demo_seed as d  # noqa: E402

KINDS = ["Shop", "Portal", "Landing page", "Booking tool", "Intranet", "Newsletter", "Dashboard", "Importer", "API", "App"]
CLIENTS = ["Weber", "Lindner", "Albrecht", "Seitz", "Moser", "Brandt", "Vogel", "Kaiser", "Roth", "Engel", "Fuchs", "Graf",
           "Horn", "Jäger", "Koch", "Lang", "Maier", "Neumann", "Otto", "Pfeiffer", "Quast", "Reiter", "Sauer", "Thiel"]
TASKS = ["Update the {x} dependencies", "Write tests for the {x} export", "Review the {x} error pages",
         "Add a sitemap for {x}", "Speed up the {x} start page", "Check the {x} backups", "Document the {x} deployment",
         "Move the {x} settings into the admin area", "Clean up the {x} database", "Improve the {x} mobile layout"]
THINGS = ["login", "search", "invoice", "newsletter", "calendar", "upload", "report", "checkout", "profile", "import"]
NOTES = ["The customer prefers a short call on Monday mornings, not e-mail.",
         "Hosting contract renews in spring. Check the price before extending.",
         "Staging and live use different mail accounts. Never test with real addresses.",
         "Last deploy took longer than planned because of a cache that was not cleared.",
         "The logo files in the old folder are outdated, use the ones from the brand guide.",
         "Decision: keep the current framework, a rewrite is not worth the effort this year."]
LOGS = ["Deployed a small fix to live", "Updated dependencies, tests green", "Customer sent new texts, added to the site",
        "Checked the backup, restore works", "Fixed a layout bug on small screens", "Renewed the TLS certificate"]
DOC = ("# Runbook\n\n## Deploy\n\n1. Pull the latest version\n2. Run the tests\n3. Restart the service\n4. Check the start "
       "page and the contact form\n\n## Contacts\n\n- Customer: ask for the project owner, not the front desk\n- Hosting "
       "support: ticket system, answers within one working day\n\n## Known problems\n\n- Images above 5 MB are rejected by "
       "the proxy\n- The nightly job logs to a file that is rotated weekly\n\n## Monitoring\n\nA simple HTTP check runs "
       "every five minutes. Failures are sent by e-mail to the maintainer.\n")


def extend(extra):
    rnd = random.Random(7)
    areas = d.AREAS
    for i in range(extra):
        slug = f"client-{i + 1:03d}"
        name = f"{rnd.choice(CLIENTS)} {rnd.choice(KINDS)}"
        status = "archiv" if i % 6 == 5 else "aktiv"
        d.PROJECTS.append((slug, name, rnd.choice(areas), status, rnd.choice(["VPS", "Shared hosting", "Docker on the NAS"]),
                           rnd.choice(["PHP, MariaDB", "FastAPI, SQLite", "Django, PostgreSQL", "Node, SQLite"]),
                           f"{name}: maintenance and small changes."))
        for _ in range(rnd.randint(3, 5)):
            d.TODOS.append((slug, rnd.choice(TASKS).format(x=rnd.choice(THINGS)), rnd.choice([2, 3, 3]), "todo", None))
        for _ in range(rnd.randint(1, 2)):
            d.NOTES.append((slug, rnd.choice(NOTES), rnd.choice(["user", "agent"]), rnd.choice([0, 1]), rnd.randint(2, 60)))
        for _ in range(rnd.randint(2, 4)):
            d.ACTIVITY.append((slug, rnd.choice(LOGS), rnd.randint(1, 90)))
        if i % 3 == 0:
            d.DOCS.append((slug, "Runbook", DOC))


if __name__ == "__main__":
    extend(int(sys.argv[1]))
    d.main()
