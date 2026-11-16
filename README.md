# Project 2: Bank Simulation

A multithreaded bank simulation in Python. Three teller threads and 50
customer threads coordinate with threading.Semaphore and shared
variables.

## Run

python project2.py

## Design summary

- door: Semaphore(2), two customers through at a time
- safe: Semaphore(2), two tellers inside at a time
- manager: Semaphore(1), one teller at a time, withdrawals only
- bank_open: opens once all three tellers are ready
- per-teller semaphores carry the customer-teller conversation

## Testing

python check_runs.py 50 runs the program repeatedly and checks each run.