# Project record

## Objective

Convert HTML and DOCX into safe, structure-preserving Markdown for RAG pipelines, using only the standard library and under explicit size and depth limits.

## Scope

- In scope: `html_to_markdown`, `docx_to_markdown`, `convert` and the `doc-to-markdown` CLI, typed and tested. HTML rules cover hidden content, scripts, unsafe URL schemes, headings, lists, tables, links and images. DOCX rules cover headings, numbered paragraphs, external hyperlinks and tables.
- Out of scope: PDF, OCR, footnotes, comments, tracked changes, PPTX, XLSX, runtime dependencies, and any I/O beyond reading the input path and writing the output path.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 293649 / 275175 |
| Hours (human) | pending measurement |
| Cost (USD) | 1.5518 |

## Factory run u013 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | claude-sonnet-5-5 | yes | 2466 | 128000 | 0 | 4246 | 0.6429 |
| generation | claude-sonnet-5-5 | yes | 2466 | 128000 | 0 | 4246 | 0.6429 |
| generation | claude-sonnet-5-5 | yes | 2466 | 12008 | 0 | 4246 | 0.0629 |
| fix-1 | claude-sonnet-5-5 | no | 6 | 1085 | 17236 | 32545 | 0.0572 |
| fix-2 | claude-sonnet-5-5 | no | 6 | 958 | 7679 | 41071 | 0.0329 |
| fix-3 | claude-sonnet-5-5 | no | 8 | 728 | 6769 | 55417 | 0.0298 |
| audit | claude-sonnet-5-5 | no | 0 | 0 | 0 | 0 | 0.0000 |
| docs | claude-haiku-5-5 | no | 144460 | 4396 | 0 | 0 | 0.0832 |

Total: $1.5518. Prices: Anthropic list prices.
