Nov 12, 2026 22:47 

## Session 1 start 

This is the start of project 2 and this devlog, this project is a bank simulation involving 3 teller threads and 50 customer threads, where the threads will use semapohres to synchronize their actions and control access to shared resources.

From project 1, I am bringing the experience of process and pipes, where the main difference is that they share memory, and they can communicate through shared variables rather than pipes. However, this also introduces the possbility of race conditions when multiple threads try to access or modify the same data. 

lang im using again is python because it supports multithreading through its threading module and has module.Semaphore 

### Shared Resources 

- The door: Only 2 customers should be allowed inside at a time. A semaphore will control access.

- The safe: Only 2 tellers can use the safe simultaneously, so it will also need a semaphore.

- The manager: Only 1 teller can interact with the manager at a time, and only withdrawals require permission.

- Ready teller list: Since multiple customers may try to access or modify this list, it needs a mutex to prevent race conditions.

- Output: Multiple threads printing simultaneously could make the output confusing or interleaved. A lock may be needed to keep messages organized.

### My First Design Thoughts 

I'm starting by figuring out how customers and tellers will communicate. If no teller is available, customers will need some way to wait until one becomes ready. A semaphore initialized to 0 might help with this.

I also need to figure out how a teller identifies which customer selected it and how they coordinate their interactions. Each teller will likely need its own set of semaphores to handle communication with its assigned customer.

The hardest part will probably be coordinating the customer and teller threads without causing race conditions or having threads wait indefinitely.

### Questions Im not sure about yet

- How will tellers know when to stop after all 50 customers have been served?

- What prevents two customers from selecting the same teller?

- How will the bank wait for all three tellers to be ready before opening?

### plans for this session

- Set up the repository and Python files.

- Start with only the first interaction, where customers introduce themselves to tellers, as suggested by the assignment.

- Begin with 3 customer threads to make the output easier to follow.

- Test with 10 customers once the initial interaction works.

Things I expect to go wrong: Customers might select the same teller, threads might get stuck waiting for signals, or the output might appear out of order. I'll use the smaller tests to identify these problems before moving on to the full simulation.



> Nov 12 23:45 

The 3 teller threads and the customer threads are now done for the introduction handshake and the process goes: a customer waits in line, picks a ready teller, introduces itself, and the teller prints that it is serving that customer. I tested this with 3 customers first, and then with 10, and ran those 10 times each, all of which finished and printed with the closing lines. 

The first run I did do with 3 customeres printed the correct output but it ended up exiting with a fatal python error about not being able to acquire the lock for stdout at interpreter shutdown, possibly due to daemon threads. Initially I thought that the print lock was broke, but reading the output, the last line said that Teller 2 was "ready to serve" meaning that the teller was still running when the program ended and what I did to cause that was that I had made the tellers daemon threads as a shortcut, and main stopped waiting as soon as every customer had been served. Python then shut down while a teller was in the middle of a print and the daemon threads got killed wherever they are, and I fixed that issue with a shared closing flag so that when all customers have been served, the main sets the flag and releases each teller's own customer_arrived semaphore. Then, the teller wakes up and sees the flag instead of a customer and prints "leaving for the day", and returns, main then joins the tellers, so nothing is killed mid print, which also gave the the same kind of shutdown behavior the sample output shows, which is part of the main plan for what I have in a future session. 

What I understand better about semaphores: teller_ready starts at 0, so
a customer who calls acquire() blocks until a teller releases it. That
one semaphore covers both cases in the spec, going straight to a free
teller and waiting in line. The list of ready tellers is a shared
variable, so I guard it with a mutex, because two customers popping at
once could take the same teller. Each teller also has its own
customer_arrived semaphore, so a customer wakes only the teller it
chose.

Plans for next session:

rest of the conversation, being that the teller asks for the transaction, customer tells it, teller completes it, and tells the customer, and customer leaves. Hopefully get that working with 5 to 10 customers before adding the door, safe, and manager.

### Session 1 End


### Session 2 Begin

> Nov 12 11:22

to start, the thing that is missing from the handshake is that the teller currently moves on without the customer ever saying what it wants, and the teller has to wait for the customer to give the transaction, and the customer has to wait for the teller to finish. So I need to expand it to have the teller ask for the transaction type, then the customer responds, and then the tellers completes the interaction before the customer leaves 

Ill need to add some additional semaphores to coordinate a few things
- Transaction Request: Signals that the teller is ready to receive the customer's transaction
- Transaction response: Signals that the customer has provided their transaction type
- Transaction completion: Signals that the teller has finished and the customer can leave. 

The customer and teller must wait for the appropriate signals so neither moves ahead too early

Semaphores aren't enough by themselves because they only signal when something can happen, and the actual transaction type (deposit or withdrawal) needs to be stored in a shared variable. Each teller should have its own transaction variable so customers assigned to different tellers don't overwrite each other's information, and since the assigned customer communicates through that teller's handshake, the information stays separate. 

**Plans**

- Complete the full customer-teller conversation
- Keep the dorr, safe, manager, and simulated processing delays for Session 3
- Test with 5 customers, then increase to 10
- Check that every customer prints their complete sequence, from entering the interaction to leaving, without missing or overlapping steps. 

> Nov 12 13:18 

Finished Session 2 with the teller and customer now have the full conversation, where the customer introduces itself, the teller asks for the transaction, the customer answers, the teller finishes and tells the customer, and the customer leaves before the teller calls the next one. All of which was tested with 3, 10, and 50 customers. 

This took five semaphores per teller, each starting at 0 and each
standing for one step: customer_arrived, ask_txn, txn_given, txn_done, and customer_left. The side that needs something calls acquire() and blocks, and the other side releases it when that step is done. Before writing it I predicted that without the last one, customer_left, the teller could print "ready to serve" and take a new customer while the old one was still leaving. The transaction type is passed through a shared slot per teller, current_transaction[tid]. I decided it needs no mutex because a teller only goes back on the ready list after customer_left,
so only one customer can write to that slot at a time.

I also changed when `served` is released. In Sesson 1 it fired right after the introduction, but now it fires after the customer leaves, so main cannot start closing the bank while someone is mid-transaction.

I read one customer's lines in order and they went from "wants to perform" to "leaves the bank" with the teller's lines in between. Then I counted the lines in my output file: 10 each of "serving a customer", "finishes", and "leaves the bank", and 13 "ready to serve" for 10 customers plus 3 tellers. 

I was initally reading output by eye which 190 some lines repeatedly was very slow and kinda hurting my eyes, so I made a checker script `check_runs.py` that runs the program many times and checks each run for hangs, crashes, each thread's sequence of lines, and the order between a customer and its teller. It passed 50 out of 50 runs for 10 customers, then 20/20 for 50 customers. The first version missed a deliberately broken handshake because it only check each thread's own lines, the the order between the threads, so adding cross-thread checks fixed that, and a pass only means no problem showed up in those runs, since it is still possible for a race race to exist. 

**Plans** 

next session i will add the sleeps, the door (2 at a time), the safe (2 tellers), and the manager, (1 teller, withdrawals only), plus the three line patterm for each shared resource in which i expect the safe and manager to be where deadlock risk comes in, so I want to take into consideration the order the tellers acquire them. 

### Session 2 End

### Session 3 Begin

> Nov 12 14:17

the goal for today is to add the sleeps, the three shared resources and the opening gate

door, safe, and manager are semaphores starting at 2, 2, and 1. The opening gate is a semaphore starting at 0 that the third ready teller releases.

A teller may need both the manager and the safe, so acquiring them in the wrong order could cause deadlock if tellers hold one resource while waiting for another. To avoid this, I'll have tellers acquire the manager first (when needed) and release it before acquiring the safe. This prevents them from holding one resource while waiting for the other

Customers should not hold the door semaphore while waiting in line. Doing so could prevent other customers from entering or leaving the bank, creating unnecessary congestion. They should release the door after entering

The maximum number of tellers inside the safe at once should be two, because the safe semaphore starts at 2.

Withdrawals should take longer overall than deposits because withdrawals require an additional interaction with the manager, while deposits can go directly to the safe.

The bank can wait for all three tellers using a counter that tracks how many tellers are ready. Once the counter reaches three, the third teller releases the opening gate, allowing customers to enter.

 > Nov 12 5:47

 I finished implementing the shared resources and synchronization. The bank now has a door (2 customers at a time), safe (2 tellers at a time), manager (1 teller at a time for withdrawals), random processing delays, and an opening gate that prevents customers from entering until all three tellers are ready.

I tested the program with 3, 10, and 50 customers. The checker reported for 50 runs 50/50 and 20 for 20/20. It also confirmed that the maximum number of tellers using the safe was 2 and the maximum using the manager was 1.

The biggest design concern was deadlock. I avoided this by making tellers release the manager before requesting the safe, preventing them from holding one resource while waiting for another.

For the opening gate, I used a semaphore starting at 0 and a shared counter protected by a mutex. Once the third teller becomes ready, it releases the gate. Customers wait on the gate before entering. The door is only held while passing through, not while waiting in line.

I expected withdrawals to take longer because they require an additional manager interaction, although I did somewhat measure this directly. One thing I noticed was that the order of printed messages changes between runs because the threads execute concurrently.

I also identified some testing limitations: the opening gate and door limits cannot be fully verified through the current checker output, so I watched their implementation directly.

Next session: Run more tests with 50 customers, compare the output with the sample run, write the README, and complete the final repository checks and zip.

### Session 3 End


### Session 4 Begin 

> Nov 12 20:02

The main goal of this session is to make sure the complete bank simulation works as expected and follows the project specifications. I'll focus on running the program with all 50 customers multiple times to check for synchronization issues, deadlocks, or customers and tellers getting stuck.

I'll also compare my program's output against the sample run provided with the assignment to make sure the messages follow the expected format and that the interactions happen in the correct order. I'll pay particular attention to the shared resources, making sure the safe and manager limits are never exceeded.

Once testing is complete, I'll write the README explaining the project, how to run it, and how the threading and semaphore synchronization work.

Finally, I'll review the repository against the assignment rubric, check that all required source files are included, remove any unnecessary files, and make sure the program can be run without additional setup issues.

**Final goal:** Have a working, tested, and properly documented project ready to zip and submit. 

