import random
import threading
import time

NUM_TELLERS = 3
NUM_CUSTOMERS = 10   # start small, scale up in later sessions

print_lock = threading.Semaphore(1)
mutex = threading.Semaphore(1)

ready_tellers = []                      # ids of tellers waiting for a customer
teller_ready = threading.Semaphore(0)   # counts ready tellers; customers wait here (the "line")
customer_arrived = [threading.Semaphore(0) for _ in range(NUM_TELLERS)]
current_customer = [None] * NUM_TELLERS
served = threading.Semaphore(0)         # lets main know a customer was handled
closing = False                         # set by main when the day is over


def say(kind, ident, partner, msg):
    """Print one whole line, never interleaved with another thread's."""
    print_lock.acquire()
    print(f"{kind} {ident} [{partner}]: {msg}")
    print_lock.release()


def teller(tid):
    while True:
        say("Teller", tid, "", "ready to serve")
        say("Teller", tid, "", "waiting for a customer")
        mutex.acquire()
        ready_tellers.append(tid)
        mutex.release()
        teller_ready.release()          # announce: one more teller is free
        customer_arrived[tid].acquire() # wait for a customer (or for closing time)
        if closing:
            say("Teller", tid, "", "leaving for the day")
            return
        cid = current_customer[tid]
        say("Teller", tid, f"Customer {cid}", "serving a customer")
        served.release()


def customer(cid):
    transaction = random.choice(["deposit", "withdrawal"])
    say("Customer", cid, "", f"wants to perform a {transaction} transaction")
    time.sleep(random.randint(0, 100) / 1000)
    say("Customer", cid, "", "going to bank.")
    say("Customer", cid, "", "entering bank.")
    say("Customer", cid, "", "getting in line.")
    teller_ready.acquire()              # blocks here until some teller is free
    mutex.acquire()
    tid = ready_tellers.pop(0)
    mutex.release()
    say("Customer", cid, "", "selecting a teller.")
    say("Customer", cid, f"Teller {tid}", "selects teller")
    current_customer[tid] = cid
    say("Customer", cid, f"Teller {tid}", "introduces itself")
    customer_arrived[tid].release()


def main():
    global closing

    tellers = [threading.Thread(target=teller, args=(t,)) for t in range(NUM_TELLERS)]
    for th in tellers:
        th.start()

    threads = [threading.Thread(target=customer, args=(c,)) for c in range(NUM_CUSTOMERS)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    for _ in range(NUM_CUSTOMERS):      # wait until every customer was actually served
        served.acquire()

    closing = True                      # tell tellers the day is over
    for t in range(NUM_TELLERS):
        customer_arrived[t].release()   # wake each one so it sees the flag
    for th in tellers:
        th.join()
    print("The bank closes for the day.")


if __name__ == "__main__":
    main()