# Deviations log (append only)

Record every change to the plan after freezing: what changed, why, when, and who approved it.
Never delete or edit earlier entries.

| Date (UTC) | Stage | What changed | Why | Approved by |
|---|---|---|---|---|
| 2026-09-28 | 0 | `~/.bashrc:126` GITHUB_TOKEN briefly clobbered by patch tool re-reading tokenised file with offset/limit pagination (display layer returned masked placeholder, copied back to disk). Restored same session via Python regex sub. HF_TOKEN added on line 129 in the same edit. | Tool-layer display redaction is write-side lossy when the edit source is a paginated read. | Riza approved restoration with re-pasted PAT. |
