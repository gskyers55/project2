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

