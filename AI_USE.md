# AI use disclosure

This capstone uses OpenAI Codex as a coding and documentation assistant. AI assistance is disclosed rather than presented as solely student-authored work.

## Phase 0 assistance (2026-11-07 to 2026-11-08)

Codex:

- read the local project instructions and all eight steering documents, including the approved architecture and cost-control direction;
- inspected the lecturer’s public `NUELBUNDI/AML_Book-Data` repository at commit `1ad78cc1ccaa6aa92e081893e3ea0cd380a1f950` as read-only reference material;
- drafted and revised the Phase 0 README, lab traceability, decision log, ignore rules, Python package metadata, package placeholder, and scaffold test;
- documented the student-approved local-ML, FastAPI/Cloud Run, and React/Vite/Firebase Hosting boundaries without implementing or deploying those components; and
- ran the reported local checks without staging, committing, pushing, or changing Git history.

The root `AGENTS.md` and `CODEX_IMPLEMENTATION_PROMPT.md` were absent from this working tree. Codex read matching, byte-identical copies from the locally supplied steering bundle outside the repository. The proposal and rubric primary documents, raw datasets, verified labels, and wallet-counterparty edge data were not available in this working tree and were not invented.

## Boundaries

Codex did not implement data ingestion, preprocessing, feature engineering, model training, evaluation, inference, FastAPI, Docker, React/Vite, Firebase Hosting, or Cloud Run in Phase 0. It did not create results, labels, provenance, cloud resources, or deployment evidence. Any future AI contribution will be added to this file as work occurs.

The student remains responsible for checking the referenced course material, validating every scientific and technical decision, reviewing all generated text and code, running or confirming the work, explaining it during assessment, and personally performing all Git staging, commits, and pushes.

## Git helper assistance (2026-11-09)

At the student’s request, Codex drafted `commit.sh` and its README usage notes. The script is designed for the student to run interactively and includes confirmations, private-file guards, staged-diff validation, ordinary commit creation, and non-force push handling. Codex validated its Bash syntax but did not execute the workflow or run any staging, commit, push, branch, or history-changing operation.
