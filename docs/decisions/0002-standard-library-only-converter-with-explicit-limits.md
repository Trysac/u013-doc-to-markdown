# Standard-library only converter with explicit limits

Status: accepted (generated, pending human review)

## Context

RAG pipelines need safe Markdown from HTML and DOCX without heavy dependencies.

## Decision

Use html.parser and zipfile with ElementTree, reject DOCTYPE/ENTITY before parsing, count decompressed bytes in 64 KiB chunks and enforce depth limits, with one typed ConversionError.

## Consequences

Small and auditable, but features such as ordered DOCX numbering and footnotes are out of scope.
