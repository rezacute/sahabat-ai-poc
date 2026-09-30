# Dataset specification

Three datasets. Seed files (`*.seed.jsonl`) show the format and tone; expand them to the target sizes.
The final files are the ones without `.seed` in the name. They are frozen by `scripts/freeze.py`.

## 1. `data/eval/safety_harmful.jsonl` (target: 200 prompts, local only, never pushed)

Requests a safe assistant should decline. Format:
`{"id": "H001", "category": "scam", "lang": "id", "prompt": "..."}`

| Category | Share | Examples of intent |
|---|---|---|
| scam | 15% | fake bank/courier/tax messages, OTP theft, phishing |
| hate-sara | 12% | insults or incitement against an ethnic group, religion or race |
| misinformation | 10% | hoaxes about health, elections, disasters |
| forgery | 8% | fake ID cards, certificates, documents |
| privacy | 10% | doxxing, selling personal data, stalking |
| illegal-debt-collection | 8% | threats, spreading borrowers' photos |
| bribery-corruption | 7% | bribing officials, hiding corruption |
| gambling | 5% | promoting online gambling, evading blocks |
| cyber-abuse | 10% | account takeover, malware, DDoS against others |
| jailbreak | 15% | any of the above wrapped in role-play, "ignore your rules", fake authority |

Languages: about 70% Indonesian, 15% Javanese, 15% Sundanese.
Keep prompts at the level of a request. Do not include working harmful content (real phone numbers,
real names of private people, real malware) in the prompts themselves.
Leave out categories involving minors, weapons or self-harm instructions: they need a specialist review
process and are out of scope for this PoC.

## 2. `data/eval/overrefusal_benign.jsonl` (target: 100 prompts)

Harmless questions that *sound* sensitive. A good model answers them. Format as above with ids `B001`...
Categories as in the seed: legal-info, medical-info, anti-scam, security-defensive, homonym
("membunuh kecoak", "kill process"), history-sara, religion-facts, culture, fiction, support,
finance, plus Javanese and Sundanese versions.

## 3. `data/train/safety_sft.jsonl` (target: 1,200 to 2,000 examples)

Format (loss is computed on the completion only):
`{"id": "T0001", "type": "refuse|helpful|general", "prompt": [{"role": "user", "content": "..."}], "completion": [{"role": "assistant", "content": "..."}]}`

| type | Share | What the answer looks like |
|---|---|---|
| refuse | 40% | short, polite decline + one sentence why + a genuinely useful safe alternative |
| helpful | 30% | borderline-sounding but harmless request, answered fully without lecturing |
| general | 30% | ordinary Indonesian / Javanese / Sundanese tasks, to keep general ability |

Rules
- **No prompt may copy or paraphrase an eval prompt.** `scripts/contamination_check.py` enforces this.
  Write training prompts about different situations (for example eval uses "kecoak", train uses "semut").
- Refusals must not be preachy and must not refuse more than needed.
- Javanese answers: match the politeness level of the question (ngoko vs krama).
- Every example is reviewed by a native speaker before freezing. Record the review in logs/PROGRESS.md
  (how many examples were checked, fixed, removed).
- If an LLM (for example MiniMax) drafts examples, check its terms of use allow using outputs as
  training data, and prefer a different model as the judge.
