# Test fixtures

Fixture governance is defined by:

- [`catalog.v1.json`](catalog.v1.json),
- [`../schemas/fixture-manifest.schema.json`](../schemas/fixture-manifest.schema.json),
- [`../docs/fixture-governance.md`](../docs/fixture-governance.md),
- [`../docs/adr/0003-fixture-consent-and-usage-governance.md`](../docs/adr/0003-fixture-consent-and-usage-governance.md).

The current catalog is metadata-only. It covers digital PDF, scanned PDF, hybrid PDF, JPG/JPEG, PNG, phone photos, staff notation, guitar TAB, combined systems, and every approved degradation category without adding document bytes.

No real score, TAB, student, teacher, copyrighted, private, training, or phone-photo artifact may be committed merely because it has a catalog entry. Artifact availability requires approved provenance, rights, privacy, permission, retention, checksum, and review metadata.

Private and incoming material remains outside Git under `fixtures/private/` or `fixtures/incoming/`.

Validate the catalog with:

```bash
python tools/validate_fixture_catalog.py
python -m unittest discover -s tests -p "test_*.py" -v
```
