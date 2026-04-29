SAYC Bridge
===========

A Python library and web app for bidding bridge hands using Standard American
Yellow Card (SAYC) conventions. The bidder is built on top of
[Microsoft Research's Z3 theorem prover](https://github.com/Z3Prover/z3).

> **Note:** This project was dormant for many years and has been updated to
> Python 3 + Flask. There is a known memory leak in the Z3 bidder that should
> be fixed before running this in production under load.


Requirements
------------

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip


Setup
-----

Install dependencies from `src/`:

    cd src
    uv sync

This installs `z3-solver`, `networkx`, and `flask` into a local `.venv`.


Running the Web App
-------------------

    cd src
    uv run python ../dist/gae/app.py           # production mode
    DEBUG=1 uv run python ../dist/gae/app.py   # dev mode (auto-reload, detailed errors)

Then open http://localhost:19883/

Useful URLs once running:

- `/` — Main bidder UI
- `/explore` — Walk the bidder's decision tree, call by call
- `/unittests` — HTML view of the current `z3b_baseline.txt` regression file
- `/json/autobid` — JSON endpoint: auto-bid a full hand
- `/json/interpret` — JSON endpoint: interpret a bidding sequence


Deploying on a VPS
------------------

**1. Install dependencies:**

    git clone <your-repo-url> saycbridge
    cd saycbridge/src
    uv sync

**2. Pre-compile CoffeeScript** (requires Node.js + CoffeeScript; avoids runtime compilation):

Install CoffeeScript if you haven't already:

    npm install -g coffeescript

Then compile the scripts:

    dist/gae/build-js

**3. Run as a systemd service:**

Create `/etc/systemd/system/saycbridge.service`:

    [Unit]
    Description=SAYCBridge
    After=network.target

    [Service]
    WorkingDirectory=/path/to/saycbridge/src
    ExecStart=/path/to/saycbridge/src/.venv/bin/python /path/to/saycbridge/dist/gae/app.py
    Restart=on-failure
    Environment=PORT=19883

    [Install]
    WantedBy=multi-user.target

Then enable and start it:

    sudo systemctl enable --now saycbridge

**4. (Optional) Nginx reverse proxy** for port 80/443:

    location / {
        proxy_pass http://127.0.0.1:19883;
    }

> **Note:** There is a known Z3 memory leak — the process will grow memory under
> load. Consider adding memory limits in the systemd unit or wrapping the app in
> the `production.sh` restart loop.


Running the Tests
-----------------

Unit tests (fast, no Z3 required):

    cd src
    uv run python -m unittest discover -s . -p "test_*.py"

Full bidding regression suite (uses Z3, takes a few minutes):

    cd src
    uv run python -m unittest tests.test_sayc

Or via the helper script:

    scripts/test-sayc

Performance profiling:

    scripts/test-sayc -p


Debugging Scripts
-----------------

Test a single hand against an expected call:

    scripts/test-hand [EXPECTED_CALL] HAND_STRING [HISTORY_STRING]
    # e.g. scripts/test-hand 1N AKQ.432.765.9876 ""

Explain what the bidder sees at a given auction:

    scripts/explain HISTORY_STRING
    # e.g. scripts/explain "1S P"

Interactive command-line bidder:

    scripts/saycbot.py          # manual mode
    scripts/saycbot.py -a       # auto-bid all hands (useful for finding crashes)


Development Workflow
--------------------

    # Edit bidding rules in src/z3b/rules.py
    scripts/test-sayc                         # run regression suite, output to z3b_baseline.txt
    # Review diffs in z3b_baseline.txt, accept when happy
    git commit


Code Layout
-----------

    src/
      core/          # Bridge domain models: Hand, Board, Deal, Call, CallHistory, etc.
      z3b/           # Z3-based bidder (main bidder)
        model.py     # Z3 integer variables for suit lengths and honor cards
        constraints.py # Bid constraint expressions
        rules.py     # All SAYC bidding rules (~3300 lines)
        bidder.py    # Solver: selects bids by checking Z3 satisfiability
      gib/           # Alternative GIB bidder (legacy)
      tests/         # Regression test harness and test_sayc.py

    dist/gae/
      app.py         # Flask application entry point
      handlers/      # One module per route group
      templates/     # Jinja2 HTML templates
      scripts/       # CoffeeScript frontend (compiled to JS)
      app.py         # Flask app + entry point (DEBUG=1 for dev mode)
      build-js       # Pre-compile CoffeeScript to JS for production
      production.sh  # Production deploy loop

    scripts/         # CLI utilities (test-sayc, test-hand, explain, saycbot, etc.)
