"""Run project2.py many times and check every run against the spec's rules.

Usage: python check_runs.py [number_of_runs]
"""
import re
import subprocess
import sys

RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 50
TIMEOUT = 60  # seconds; a run longer than this is treated as a hang

CUSTOMER_STEPS = [
    "wants to perform a", "going to bank.", "entering bank.",
    "getting in line.", "selecting a teller.", "selects teller",
    "introduces itself", "asks for", "leaves teller",
    "goes to door", "leaves the bank",
]
BEFORE_MANAGER = ["serving a customer", "asks for transaction", "handling"]
MANAGER_STEPS = ["going to the manager", "getting manager's permission", "got manager's permission"]
SAFE_STEPS = ["going to safe", "enter safe", "leaving safe"]
AFTER_SAFE = ["finishes", "wait for customer to leave."]


def parse(lines, problems):
    parsed = []
    for line in lines:
        m = re.match(r"(Teller|Customer) (\d+) \[([^\]]*)\]: (.*)$", line)
        if m:
            parsed.append((m.group(1), int(m.group(2)), m.group(3), m.group(4)))
        elif line != "The bank closes for the day.":
            problems.append(f"unparseable line (interleaved?): {line!r}")
    return parsed


def check_teller(tid, mine, wanted, cust_teller, problems):
    """Walk one teller's lines: each visit must follow the full step pattern."""
    pos = 0

    def expect(steps):
        nonlocal pos
        for step in steps:
            if pos >= len(mine) or not mine[pos][1].startswith(step):
                got = mine[pos][1] if pos < len(mine) else "<end>"
                problems.append(f"Teller {tid}: expected '{step}' but got '{got}'")
                return False
            pos += 1
        return True

    while True:
        if not expect(["ready to serve", "waiting for a customer"]):
            return
        if pos < len(mine) and mine[pos][1] == "leaving for the day":
            if pos != len(mine) - 1:
                problems.append(f"Teller {tid}: lines after leaving for the day")
            return
        if not expect(BEFORE_MANAGER):
            return
        who = mine[pos - 3][0]
        cid = int(who.split()[1])
        kind = re.search(r"handling (\w+)", mine[pos - 1][1]).group(1)
        if wanted.get(cid) != kind:
            problems.append(f"{who}: wanted {wanted.get(cid)} but teller handled {kind}")
        if cust_teller.get(cid) != f"Teller {tid}":
            problems.append(f"Teller {tid} served {who} but that customer named {cust_teller.get(cid)}")
        if kind == "withdrawal" and not expect(MANAGER_STEPS):
            return
        if kind == "deposit" and pos < len(mine) and mine[pos][1] == MANAGER_STEPS[0]:
            problems.append(f"Teller {tid}: went to the manager for a deposit ({who})")
            return
        if not expect(SAFE_STEPS) or not expect(AFTER_SAFE):
            return


def max_occupancy(parsed, enter_text, leave_text):
    inside = peak = 0
    for _, _, _, msg in parsed:
        if msg == enter_text:
            inside += 1
            peak = max(peak, inside)
        elif msg == leave_text:
            inside -= 1
    return peak


def check(lines):
    problems = []
    parsed = parse(lines, problems)
    if not lines or lines[-1] != "The bank closes for the day.":
        problems.append("last line is not 'The bank closes for the day.'")

    cust_ids = sorted({i for k, i, _, _ in parsed if k == "Customer"})
    n = len(cust_ids)
    wanted, cust_teller = {}, {}
    for cid in cust_ids:
        mine = [(p, msg) for k, i, p, msg in parsed if k == "Customer" and i == cid]
        if len(mine) != len(CUSTOMER_STEPS) or not all(
            m.startswith(s) for (_, m), s in zip(mine, CUSTOMER_STEPS)
        ):
            problems.append(f"Customer {cid}: wrong sequence")
            continue
        wanted[cid] = re.search(r"a (\w+) transaction", mine[0][1]).group(1)
        names = {p for p, _ in mine if p}
        if len(names) != 1:
            problems.append(f"Customer {cid}: used more than one teller {names}")
        else:
            cust_teller[cid] = names.pop()

    for tid in range(3):
        mine = [(p, msg) for k, i, p, msg in parsed if k == "Teller" and i == tid]
        if not mine or mine[-1][1] != "leaving for the day":
            problems.append(f"Teller {tid}: did not leave for the day")
            continue
        check_teller(tid, mine, wanted, cust_teller, problems)

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
        next_ready = index_of("Teller", tid, "ready to serve", after=serving if serving is not None else 0)
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

    # Bank opening: all three tellers' first "ready to serve" come before any customer enters
    first_ready = []
    for tid in range(3):
        idx = index_of("Teller", tid, "ready to serve")
        first_ready.append(idx)
    first_going = next((p for p, l in enumerate(lines) if "going to bank." in l), None)
    if None in first_ready or first_going is None or max(first_ready) > first_going:
        problems.append("a customer went to the bank before all three tellers were ready")

    # Shared resources never over capacity
    safe_peak = max_occupancy(parsed, "enter safe", "leaving safe")
    mgr_peak = max_occupancy(parsed, "getting manager's permission", "got manager's permission")
    if safe_peak > 2:
        problems.append(f"safe held by {safe_peak} tellers at once (limit 2)")
    if mgr_peak > 1:
        problems.append(f"manager used by {mgr_peak} tellers at once (limit 1)")

    def count(text):
        return sum(1 for *_, msg in parsed if msg == text)
    if count("ready to serve") != n + 3:
        problems.append(f"'ready to serve' count {count('ready to serve')} != {n + 3}")
    if count("leaving for the day") != 3:
        problems.append("expected 3 'leaving for the day' lines")
    if count("serving a customer") != n:
        problems.append("'serving a customer' count != number of customers")
    return problems, n, safe_peak, mgr_peak


bad = 0
best_safe = best_mgr = 0
for r in range(1, RUNS + 1):
    try:
        result = subprocess.run(
            [sys.executable, "project2.py"],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(f"run {r}: HANG (no exit after {TIMEOUT}s)")
        bad += 1
        continue
    lines = result.stdout.splitlines()
    problems, n, safe_peak, mgr_peak = check(lines)
    best_safe, best_mgr = max(best_safe, safe_peak), max(best_mgr, mgr_peak)
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
print(f"most tellers seen in the safe at once: {best_safe} (limit 2)")
print(f"most tellers seen with the manager at once: {best_mgr} (limit 1)")