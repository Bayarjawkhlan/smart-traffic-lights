# The Controller proposes, the Safety Guard decides

No Controller (Fixed-time, Max-pressure or RL) ever sets a signal. Each one proposes the next Phase; the Safety Guard approves it, delays it or replaces it, and is the only code that changes signals. Pedestrian and vehicle wait caps, minimum green, yellow, all-red and pedestrian clearance live in the Safety Guard, so a learned or buggy Controller cannot break them, and every Override is logged with the rule that forced it.

## Considered Options

- Rules inside each Controller: rejected, because the RL Controller would have to learn them and every Controller would re-implement them.
- An LLM choosing Phases: rejected as too slow and unpredictable. An LLM may explain decisions after the fact but never takes part in them.
