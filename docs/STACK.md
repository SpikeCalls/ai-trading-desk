# The full stack

The repo ships the core desk. Around it, every tool has one job and no two jobs overlap.

![Nine tools, one desk](../assets/stack.png)

## Signals: what's happening right now

- **pump.fun**: the market itself. Every launch, every bonding curve, every graduation.
- **Grok Bot**: reads X around the clock. Narratives, the project's own account, who's talking about a ticker. It reports what it sees and never decides.
- **Grok**: the quick X lookup on one post or one account.
- **REA**: the research seat. When a narrative starts moving, it does the deep dive.

## Brains: who judges

- **Claude Opus 5.5**: the analyst seat in this repo. Fills the typed thesis.
- **ChatGPT**: the second opinion. Same token, same fields, a separate read. When the two disagree, skip.
- **Jev**: typed yes/no gates with probabilities instead of prose. Built for bounded decisions.

## Build + memory: what stays

- **Claude Code**: builds and fixes the desk. Every rule change starts as a prompt and ends as a tested commit.
- **GitHub**: every threshold change is versioned, so you know which rules produced which trades.
- **Obsidian**: the vault. Rules, weekly reviews, the wallet blacklist, every narrative tracked.

**Tools read and judge, code decides, you sign.** No tool holds a key. No tool places an order.

## The research loop

1. Grok Bot flags a narrative picking up on X.
2. REA deep-dives it: origin, the accounts behind it, past coins on the same story and how they died.
3. The findings go into an Obsidian note: narrative, likely tickers, kill conditions.
4. The scanner catches a matching launch on pump.fun.
5. Chain check first. Then Claude scores it, ChatGPT gives the second read, Jev answers the yes/no gates.
6. The risk engine sizes it. You get the alert. You sign or you skip.
7. Every decision lands in the journal. Sunday's review goes back into Obsidian.
8. One rule changes per week. Claude Code makes the edit, GitHub keeps the history.

## Research prompts (copy-paste)

```
NARRATIVE SCAN (Grok Bot / Grok):
Scan X for the last 12 hours. Find 5 narratives that could spawn memecoins today.
For each: the core meme, 3-5 likely tickers, how early it is (1-10), what would kill it.
Rank by early + strong. Report what you saw. Never recommend a buy.

DEEP DIVE (REA):
Research this narrative: [NARRATIVE]. Where did it start, which accounts drive it,
which coins launched on the same story before, how long they lasted, how they died.
A source for every claim. Flag anything you could not verify.

PROJECT CHECK (Grok):
Look at @[HANDLE]. Account age, follower growth, replies on the last 10 posts,
signs of a recycled or renamed account. Facts only.

SECOND OPINION (ChatGPT):
Here is a token's data: [PASTE FIELDS]. Score it 0-10 and list red flags, worst first.
Verdict: SKIP, WATCH or VALID SETUP. Never "buy". A missing number is a red flag.

YES/NO GATES (Jev):
state: the token's fields
questions: holders_look_organic (yes/no), dev_can_dump (yes/no),
           shape (crowd / one_buyer / fading / too_early)
```

## Vault note template (Obsidian)

```markdown
# [NARRATIVE] · [DATE]
Origin:
Accounts driving it:
Likely tickers:
Kill conditions:
Coins that died on it before:
Desk verdicts:
What I learned:
```
