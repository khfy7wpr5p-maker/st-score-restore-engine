# Development environment

**Status:** Milestone M0 baseline  
**Primary runtime:** Python 3.12  
**Compatibility validation:** Python 3.11 and 3.12

## Reference environment

The reference development and CI environment is a current Linux runner. macOS and supported Windows environments may be used, but changes must still pass the reference CI checks.

Windows 7 is not a supported native development target for this repository. Use a remote Linux environment, GitHub-hosted runner, container or supported machine for project work.

## Initial setup

Milestone M0 has no third-party runtime dependencies.

```bash
python --version
python tools/validate_repository.py
python -m compileall -q src tools
```

Expected validation result:

```text
Repository validation passed.
```

## Dependency installation

`pyproject.toml` is the source of declared project dependencies. The first pull request that introduces a third-party dependency must also:

1. complete the dependency and license review,
2. choose and document the lock generator,
3. add a generated, frozen lock artifact,
4. update CI to install in frozen mode,
5. document the exact setup and verification commands.

Until then, the declared dependency set is intentionally empty.
