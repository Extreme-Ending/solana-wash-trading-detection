# Submission materials

This directory contains the editable and rendered public project report.

- `solana_wallet_risk_project_report.md`: editable report source.
- `solana_wallet_risk_project_report.docx`: editable word-processing version.
- `solana_wallet_risk_project_report.pdf`: rendered review copy.
- `assets/`: verified diagrams and charts generated from repository evidence.

The presentation is submitted separately and is not a public-repository deliverable. The older tracked `solana_wallet_risk_presentation.pptx` and `solana_wallet_risk_presentation_outline.md` should be removed by the student before the final public commit. The final report satisfies the repository's report-or-slide-deck requirement.

Regenerate the binary files with:

```bash
python -m pip install -e '.[submission]'
python -c "from scripts.generate_submission_assets import markdown_to_docx, render_pdf; markdown_to_docx(); render_pdf()"
```

The report uses an author-date reference list because no institutional template or required citation style is present in the repository. The student should confirm cover-page fields, word limit, citation style and submission format before submitting.
