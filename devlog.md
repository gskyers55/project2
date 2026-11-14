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



