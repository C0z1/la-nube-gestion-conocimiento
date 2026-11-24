# Usability test (≈10 minutes per person)

Give each tester the app link and these three tasks. Do not help them. Write down the time and whether they finished.

| # | Task | Done when |
|---|------|-----------|
| T1 | "A customer wants to pay part of their credit. Find the document that explains how to register it." | They open D03 or D30 |
| T2 | "Ask the assistant how long the store keeps old backups." | The answer says 30 days |
| T3 | "In the knowledge graph, find which documents are about cash closing." | They name at least 2 (e.g. D04, D13, D99) |

Then they answer the **SUS questionnaire** (1 = strongly disagree … 5 = strongly agree). A Google Form with these 10 items works:

1. I think that I would like to use this system frequently.
2. I found the system unnecessarily complex.
3. I thought the system was easy to use.
4. I think that I would need the support of a technical person to be able to use this system.
5. I found the various functions in this system were well integrated.
6. I thought there was too much inconsistency in this system.
7. I would imagine that most people would learn to use this system very quickly.
8. I found the system very cumbersome to use.
9. I felt very confident using the system.
10. I needed to learn a lot of things before I could get going with this system.

Plus one open question: *"What was the most confusing part?"*

## Recording results

Fill `responses.csv` (one row per tester: role, the 10 answers, task times in seconds or empty if not finished, comment) and run:

```bash
python usability/score.py
```

It writes `outputs/usability.json`, which the app's Evaluation tab shows. SUS above 68 is above average; above 80 is good.
