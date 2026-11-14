import random
import threading
import time

NUM_TELLERS = 3
NUM_CUSTOMERS = 10   # test with 5, then 10

print_lock = threading.Semaphore(1)
mutex = threading.Semaphore(1)

ready_tellers = []                      # ids of tellers waiting for a customer
teller_ready = threading.Semaphore(0)   # counts ready tellers; customers wait here (the "line")

# One set of semaphores per teller, one for each step of the conversation
customer_arrived = [threading.Semaphore(0) for _ in range(NUM_TELLERS)]  # customer -> teller: "I'm here"
ask_txn = [threading.Semaphore(0) for _ in range(NUM_TELLERS)]           # teller -> customer: "what do you want?"
txn_given = [threading.Semaphore(0) for _ in range(NUM_TELLERS)]         # customer -> teller: "here it is"
txn_done = [threading.Semaphore(0) for _ in range(NUM_TELLERS)]          # teller -> customer: "finished"
customer_left = [threading.Semaphore(0) for _ in range(NUM_TELLERS)]     # customer -> teller: "I'm leaving"

# Per-teller shared slots, written by the customer currently at that teller
current_customer = [None] * NUM_TELLERS
current_transaction = [None] * NUM_TELLERS

served = threading.Semaphore(0)         # lets main know a customer is completely finished
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
        teller_ready.release()              # announce: one more teller is free
        customer_arrived[tid].acquire()     # wait for a customer (or for closing time)
        if closing:
            say("Teller", tid, "", "leaving for the day")
            return
        cid = current_customer[tid]
        who = f"Customer {cid}"
        say("Teller", tid, who, "serving a customer")
        say("Teller", tid, who, "asks for transaction")
        ask_txn[tid].release()              # tell the customer to speak
        txn_given[tid].acquire()            # wait until the customer has answered
        txn = current_transaction[tid]
        say("Teller", tid, who, f"handling {txn} transaction")
        # Session 3: manager (withdrawals only), safe, and sleeps go here
        say("Teller", tid, who, f"finishes {txn} transaction.")
        say("Teller", tid, who, "wait for customer to leave.")
        txn_done[tid].release()             # tell the customer it's finished
        customer_left[tid].acquire()        # wait until the customer has left
        served.release()


def customer(cid):
    transaction = random.choice(["deposit", "withdrawal"])
    say("Customer", cid, "", f"wants to perform a {transaction} transaction")
    time.sleep(random.randint(0, 100) / 1000)
    say("Customer", cid, "", "going to bank.")
    say("Customer", cid, "", "entering bank.")
    say("Customer", cid, "", "getting in line.")
    teller_ready.acquire()                  # blocks here until some teller is free
    mutex.acquire()
    tid = ready_tellers.pop(0)
    mutex.release()
    me = f"Teller {tid}"
    say("Customer", cid, "", "selecting a teller.")
    say("Customer", cid, me, "selects teller")
    current_customer[tid] = cid
    say("Customer", cid, me, "introduces itself")
    customer_arrived[tid].release()
    ask_txn[tid].acquire()                  # wait for the teller to ask
    current_transaction[tid] = transaction
    say("Customer", cid, me, f"asks for {transaction} transaction")
    txn_given[tid].release()
    txn_done[tid].acquire()                 # wait for the teller to finish
    say("Customer", cid, me, "leaves teller")
    customer_left[tid].release()
    say("Customer", cid, "", "goes to door")
    say("Customer", cid, "", "leaves the bank")


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
    for _ in range(NUM_CUSTOMERS):          # wait until every customer was fully served
        served.acquire()

    closing = True                          # tell tellers the day is over
    for t in range(NUM_TELLERS):
        customer_arrived[t].release()       # wake each one so it sees the flag
    for th in tellers:
        th.join()
    print("The bank closes for the day.")


if __name__ == "__main__":
    main()