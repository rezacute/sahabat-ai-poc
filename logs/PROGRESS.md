# Progress log

## Stage 0 — environment (in progress)

**2026-09-28 12:25 UTC — scaffold extracted**

- Source: `/home/ubuntu/.hermes/cache/documents/doc_15cec3e2e72d_sahabat-safety-poc.zip`
- Extracted to `~/projects/sahabat-safety-poc`, renamed to `sahabat-ai-poc`
- 23 files, no internal references to the old name (`grep` clean)
- `git init` + first commit `ca25b2c stage 0: scaffold (renamed from sahabat-safety-poc)`

**GitHub remote: BLOCKED**

- `~/.bashrc GITHUB_TOKEN` = literal placeholder `github...De6C` (not a real PAT)
- `~/.git-credentials` entries are all placeholders (`github...fjVa`)
- `git push` to a fresh repo fails with "could not read Username" — the credential store has no working token
- Existing `~/qml-lab` repo's `git fetch` from origin appears to work in some configurations, but no PAT is available for `POST /user/repos` to create `sahabat-ai-poc` on github.com

**Need from Riza:** a real GitHub PAT (scope: `repo`) — paste it here or export `GITHUB_TOKEN=...` in the next shell turn so I can:
1. `POST /user/repos` to create `sahabat-ai-poc` (private, auto_init=false)
2. `git remote add origin` and push `master`

If no remote is wanted (local-only repo is fine for the PoC), say so and I'll proceed without it.

**2026-09-28 12:35 UTC — github auth resolved, pushed to origin**

- Replaced placeholder `github...De6C` in `~/.bashrc:126` with real fine-grained PAT (Riza-supplied)
- Token: `rezacute` / id 4646258, perms on `sahabat-ai-poc`: `admin, maintain, push, triage, pull`
- Embedded token in remote URL: `https://<token>@github.com/rezacute/sahabat-ai-poc.git`
- Pushed both stage-0 commits: `ca25b2c`, `2c8fc1d` → `origin/master`
- Verified via REST: top commit on remote is `2c8fc1d stage 0: log github auth blocker`

Note for next session: `GITHUB_TOKEN` in `~/.bashrc` is now real; `source ~/.bashrc` returns early in non-interactive shells — extract with `export $(grep '^export GITHUB_TOKEN=' ~/.bashrc)` if needed.

**2026-09-28 12:50 UTC — github + hf tokens ready**

- `~/.bashrc:126` GITHUB_TOKEN restored to real PAT (Riza re-supplied; previous value got clobbered when patch tool re-read a tokenised file with offset/limit pagination — display layer returned the masked placeholder which I copied back). Restored via Python regex sub to bypass display redaction.
- `~/.bashrc:128-129` HF_TOKEN added (37 chars, fine-grained PAT, Riza-supplied).
- Auth checks:
  - `curl /api.github.com/user` → 200, login `rezacute`
  - `curl /api/whoami-v2` → 200, name `riza-alaudin`, model `GoToCompany/gemma2-9b-cpt-sahabatai-v1-instruct` accessible (HTTP 200, not gated, 13 sibling files)

**Lesson recorded:** never use `read_file(offset,limit)` + `patch` to edit `~/.bashrc` while it contains real tokens — the display layer redacts tokens on read, and any `new_string` constructed from that display will replace bytes with the placeholder. Use `python3` regex sub for credential-line edits.

**2026-09-30 22:55 UTC — switch to main, Stage 0 verified**

- Switched from `master` to `main` (pristine scaffold) per Riza's choice.
- `master` branch retained locally with full v3 work; uncommitted v3 SFT edits stashed as `v3 SFT edits (uncommitted)`.
- Re-verified Stage 0 env (carried over from `master`'s stage 0 run; venvs persist on disk):
  - nvidia-smi: NVIDIA RTX PRO 6000 Blackwell Server Edition, 595.71.05, 97887 MiB
  - `.venv-train`: torch 2.11.0+cu128, compute capability (12, 0) ✓
  - `.venv-infer`: torch 2.13.0+cu130, vllm 0.30.0
  - `third_party/SEA-HELM`: cloned
- `setup.sh` not re-run (no need; venvs are functional).
- Untracked working-tree leftovers from `master`: `results/general_base_greedy.jsonl`, `review/pilot_review.csv`, `review/pilot_review_prereviewed.csv`. Not committed; clean up if not needed.

Stage 0 complete. Ready to start Stage 1 on pristine main.
