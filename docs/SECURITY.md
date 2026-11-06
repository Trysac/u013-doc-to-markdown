# Security notes

## Threat model

`trysac-doc-to-markdown` is a pure conversion library. It reads only the input it is given and performs no network access.

Defended:

- **Script and active content**: `script`, `style`, `noscript`, `template`, `iframe`, `object` and `nav` are dropped; raw `<` in text is escaped as `&lt;`.
- **Unsafe URL schemes**: `javascript:`, `vbscript:` and `data:` are removed after stripping whitespace and control characters and decoding entities. Only `http`, `https`, `mailto` and relative URLs pass.
- **Markdown injection**: link text and URLs escape brackets and parentheses; text escapes Markdown syntax characters where they would start syntax.
- **Zip bombs**: DOCX parts are read in 64 KiB chunks with a running total across all members, checked against `max_bytes`; declared sizes are ignored. Archives with more than `max_members` entries are rejected.
- **XML entity attacks**: any part containing `<!DOCTYPE` or `<!ENTITY` is rejected before parsing. Only UTF-8 and UTF-16 detection is applied to this check.
- **Deep nesting and large input**: HTML over `max_chars` or nested deeper than `max_depth` is rejected.

Not defended:

- The DOCX entity check is a substring check on the raw bytes. It is not a full XML parser hardening; `xml.etree.ElementTree` is used as-is for the remaining content.
- Size limits are caller-configurable defaults; a caller who raises them accepts the larger memory use.
- Ordered list numbering and images from DOCX are not resolved, so output does not reflect every source feature.
- Memory use is not bounded beyond the size limits; the output string is built fully in memory.
- Images are kept by default (`keep_images=True`); their URLs are not fetched by this library.

## Publishing

Releases are published to PyPI with trusted publishing (OIDC) when available, never with a long-lived token stored in the repository.

To report a vulnerability, see [SECURITY.md](../SECURITY.md).
