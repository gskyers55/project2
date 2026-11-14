"""Run project2.py many times and check every run against the spec's rules.

Usage: python check_runs.py [number_of_runs]
"""
import re
import subprocess
import sys

RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 50
TIMEOUT = 20  # seconds; a run longer than this is treated as a hang

CUSTOMER_STEPS = [
    "wants to perform a", "going to bank.", "entering bank.",
    "getting in line.", "selecting a teller.", "selects teller",
    "introduces itself", "asks for", "leaves teller",
    "goes to door", "leaves the bank",
]
TELLER_STEPS = [
    "ready to serve", "waiting for a customer", "serving a customer",
    "asks for transaction", "handling", "finishes", "wait for customer to leave.",
]


def check(lines):
    """Return a list of problems found in one run's output (empty = good)."""
    problems = []
    parsed = []
    for line in lines:
        m = re.match(r"(Teller|Customer) (\d+) \[([^\]]*)\]: (.*)$", line)
        if m:
            parsed.append((m.group(1), int(m.group(2)), m.group(3), m.group(4)))
        elif line != "The bank closes for the day.":
            problems.append(f"unparseable line (interleaved?): {line!r}")

    if not lines or lines[-1] != "The bank closes for the day.":
        problems.append("last line is not 'The bank closes for the day.'")

    # Customers
    cust_ids = sorted({i for k, i, _, _ in parsed if k == "Customer"})
    n = len(cust_ids)
    wanted = {}
    cust_teller = {}
    for cid in cust_ids:
        mine = [(p, msg) for k, i, p, msg in parsed if k == "Customer" and i == cid]
        if len(mine) != len(CUSTOMER_STEPS) or not all(
            m.startswith(s) for (_, m), s in zip(mine, CUSTOMER_STEPS)
        ):
            problems.append(f"Customer {cid}: wrong sequence")
            continue
        wanted[cid] = re.search(r"a (\w+) transaction", mine[0][1]).group(1)
        tellers = {p for p, _ in mine if p}
        if len(tellers) != 1:
            problems.append(f"Customer {cid}: used more than one teller {tellers}")
        else:
            cust_teller[cid] = tellers.pop()

    # Tellers
    for tid in range(3):
        mine = [(p, msg) for k, i, p, msg in parsed if k == "Teller" and i == tid]
        if not mine or mine[-1][1] != "leaving for the day":
            problems.append(f"Teller {tid}: did not leave for the day")
            continue
        body = mine[:-1]
        # every customer visit = 7 lines; the final loop adds 2 more (ready, waiting)
        if (len(body) - 2) % len(TELLER_STEPS) != 0:
            problems.append(f"Teller {tid}: odd number of lines ({len(body)})")
            continue
        for start in range(0, len(body) - 2, len(TELLER_STEPS)):
            chunk = body[start:start + len(TELLER_STEPS)]
            if not all(m.startswith(s) for (_, m), s in zip(chunk, TELLER_STEPS)):
                problems.append(f"Teller {tid}: out-of-order lines near visit {start // 7}")
                break
            who = chunk[2][0]
            cid = int(who.split()[1])
            if cust_teller.get(cid) != f"Teller {tid}":
                problems.append(f"Teller {tid} served {who} but that customer named {cust_teller.get(cid)}")
            kind = re.search(r"handling (\w+)", chunk[4][1]).group(1)
            if wanted.get(cid) != kind:
                problems.append(f"{who}: wanted {wanted.get(cid)} but teller handled {kind}")

    # Cross-thread order: the teller and its customer must hand off in the right order
    def index_of(kind, ident, startswith, after=-1):
        for pos, line in enumerate(lines):
            if pos > after and line.startswith(f"{kind} {ident} [") and line.split("]: ", 1)[1].startswith(startswith):
                return pos
        return None

    for cid in cust_ids:
        if cid not in cust_teller:
            continue
        tid = int(cust_teller[cid].split()[1])
        intro = index_of("Customer", cid, "introduces itself")
        serving = index_of("Teller", tid, "serving a customer", after=intro - 1)
        asks_t = index_of("Teller", tid, "asks for transaction", after=intro)
        asks_c = index_of("Customer", cid, "asks for")
        handling = index_of("Teller", tid, "handling", after=intro)
        finishes = index_of("Teller", tid, "finishes", after=intro)
        leaves_t = index_of("Customer", cid, "leaves teller")
        next_ready = index_of("Teller", tid, "ready to serve", after=serving)
        checks = [
            ("teller got ready again before customer left it", leaves_t, next_ready),
            ("teller served before customer introduced itself", intro, serving),
            ("customer answered before teller asked", asks_t, asks_c),
            ("teller handled before customer gave transaction", asks_c, handling),
            ("customer left teller before teller finished", finishes, leaves_t),
        ]
        for name, first, second in checks:
            if first is None or second is None or not first < second:
                problems.append(f"Customer {cid}/Teller {tid}: {name}")

    # Totals
    def count(text):
        return sum(1 for *_, msg in parsed if msg == text)
    if count("ready to serve") != n + 3:
        problems.append(f"'ready to serve' count {count('ready to serve')} != {n + 3}")
    if count("leaving for the day") != 3:
        problems.append("expected 3 'leaving for the day' lines")
    if count("serving a customer") != n:
        problems.append("'serving a customer' count != number of customers")
    return problems, n


bad = 0
for r in range(1, RUNS + 1):
    try:
        result = subprocess.run(
            [sys.executable, "project2.py"],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired as e:
        print(f"run {r}: HANG (no exit after {TIMEOUT}s)")
        bad += 1
        continue
    lines = result.stdout.splitlines()
    problems, n = check(lines)
    if result.returncode != 0:
        problems.append(f"exit code {result.returncode}")
    if result.stderr.strip():
        problems.append("stderr: " + result.stderr.strip().splitlines()[-1])
    if problems:
        bad += 1
        print(f"run {r}: FAIL")
        for p in problems[:5]:
            print("   ", p)
    elif RUNS <= 10:
        print(f"run {r}: ok ({n} customers, {len(lines)} lines)")

print(f"\n{RUNS - bad}/{RUNS} runs passed")
