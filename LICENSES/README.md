# Third-party license records

Every runtime library, development tool, model adapter and model weight must
have a review record before it is introduced.

A review includes package/model name and exact version, canonical source,
license, redistribution terms, transitive obligations, native components,
security considerations, removal plan and approval record.

Approved runtime graph:

- `numpy==2.3.5`
- `opencv-python-headless==4.13.0.92`

Approved offline validation/test graph:

- `attrs==26.1.0`
- `jsonschema==4.26.0`
- `jsonschema-specifications==2025.9.1`
- `referencing==0.37.0`
- `rpds-py==2026.5.1`
- `typing-extensions==4.15.0`

The validation graph is not part of restoration runtime behavior and cannot
read document artifacts or external custody storage.
