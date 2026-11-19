# Submission materials

This directory contains the editable and rendered project submission materials.

- `solana_wallet_risk_project_report.md`: editable report source.
- `solana_wallet_risk_project_report.docx`: editable word-processing version.
- `solana_wallet_risk_project_report.pdf`: rendered review copy.
- `solana_wallet_risk_presentation_outline.md`: slide content and speaking notes.
- `solana_wallet_risk_presentation.pptx`: editable 12-slide presentation.
- `assets/`: verified diagrams and charts generated from repository evidence.

Regenerate the binary files with:

```bash
python -m pip install -e '.[submission]'
python scripts/generate_submission_assets.py
```

The report uses an author-date reference list because no institutional template or required citation style is present in the repository. The student should confirm cover-page fields, word limit, citation style and submission format before submitting.
