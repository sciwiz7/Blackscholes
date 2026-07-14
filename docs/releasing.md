# Releasing BlackScholesLab

This document describes the release process for BlackScholesLab. It is
educational and operational guidance; it does not authorise or automate any
publication on its own.

## Version format

BlackScholesLab uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Development versions

Development versions use the format `MAJOR.MINOR.PATCH.devN`, for example
`0.1.0.dev0`. This format:

- is PEP 440 compliant;
- is clearly distinguishable from any published release;
- is never uploaded to PyPI;
- allows repeated local iteration without ambiguity.

### Pre-release versions

Pre-release versions use PEP 440 pre-release segments, for example
`0.1.0rc1` or `0.1.0a1`. Pre-release versions may be uploaded to TestPyPI for
rehearsal but are not promoted to production without explicit approval.

### Stable versions

Stable versions use the bare `MAJOR.MINOR.PATCH` format, for example
`0.1.0`. Only stable versions should be published to production PyPI.

## Proposed first public release: 0.1.0

The current candidate version is `0.1.0`. The likely first public
release is **0.1.0**, not 1.0.0, because:

- `0.1.0.dev0` is the natural predecessor of `0.1.0`.
- The project has not yet accumulated real-world compatibility history.
- A `1.0.0` release conventionally signals a stronger public API stability
  promise.
- Publishing `0.1.0` allows real-world feedback before a higher-signals
  release.

## When would 1.0.0 be justified?

A future `1.0.0` release would be justified when the project has:

- a stable public API with documented compatibility commitments;
- sufficient real-world usage history to support those commitments;
- known downstream consumers relying on the published interface;
- explicit maintainer agreement that the stability bar has been reached.

The mere completion of a checklist is not sufficient justification for 1.0.0.

## Clean-checkout release preparation

Always prepare a release from a clean checkout:

1. Confirm the branch and working tree are clean.
2. Confirm CI is green on the release branch.
3. Confirm the release checklist has been completed.
4. Confirm explicit human approval exists for the version bump and publication.

Do not release from a dirty working tree, from unreviewed local changes, or
from a branch that has not passed CI.

## Changelog finalization

Before releasing:

1. Review the `## [Unreleased]` section of `CHANGELOG.md`.
2. Move entries from `## [Unreleased]` to a new version heading
   (for example `## [0.1.0]`).
3. Add a release date under the new heading.
4. Ensure every change is user-facing and accurately described.
5. Ensure no entry implies that a future task in this release process has
   already been completed.

## Version synchronization

The version string must be consistent in every location where it appears:

| Location | Expected value during development | Example during release |
|---|---|---|
| `pyproject.toml` `version` | `0.1.0.dev0` | `0.1.0` |
| `src/blackscholeslab/__init__.py` `__version__` | `0.1.0.dev0` | `0.1.0` |
| Built wheel metadata | `0.1.0.dev0` | `0.1.0` |
| Built sdist metadata | `0.1.0.dev0` | `0.1.0` |

The existing version-consistency test verifies this alignment. If any
location is out of sync, the test fails and the release must not proceed.

## Release-candidate validation

Before the final publication:

1. Build the wheel and sdist from a clean checkout.
2. Inspect the artifact contents.
3. Validate metadata correctness.
4. Install the wheel into a fresh virtual environment.
5. Verify `import blackscholeslab` and `blackscholeslab.__version__`.
6. Run `blackscholeslab --help` through the installed console entry point.
7. Run the full test suite against the installed package.
8. Optionally install with the `demo` extra and run demonstration tests.
9. If any step fails, fix the issue and repeat.

## Artifact building

Build with a standards-compliant tool:

```bash
python -m pip install build
python -m build
```

Artifacts are written to `dist/`. Always build from a clean checkout with no
uncommitted changes.

## Artifact inspection

After building, inspect:

- `dist/blackscholeslab-*.whl` (wheel)
- `dist/blackscholeslab-*.tar.gz` (sdist)

Checklist items:

- Metadata matches the expected version, name, description, license, and
  author.
- `py.typed` marker is present in the wheel.
- No secrets, caches, virtual environments, or IDE files are included.
- Documentation, examples, and tests are included in the sdist.
- The console entry point `blackscholeslab` is present.
- Streamlit is not a mandatory dependency.
- Demo extra metadata is present.

## TestPyPI rehearsal

A TestPyPI rehearsal is recommended before the first production publication.

### TestPyPI Trusted Publisher configuration

Configure a separate Trusted Publisher on TestPyPI:

- Repository: `sciwiz7/Blackscholes`
- Workflow: `release.yml`
- Environment: `pypi-testpypi`

### TestPyPI protected environment

Use a separate protected GitHub environment (for example `pypi-testpypi`).

### Package-name collision considerations

TestPyPI uses a separate package namespace. If a stale `blackscholeslab`
package exists on TestPyPI, the rehearsal may fail. In that case, contact
TestPyPI support or choose a temporary test package name.

### Safe installation from TestPyPI

When testing the TestPyPI build, install the exact distribution in isolation to
avoid dependency confusion. Because the core package has no mandatory runtime
dependencies, prefer an exact-version, dependency-free rehearsal:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --no-deps \
  "blackscholeslab==<exact-version>"
```

Do **not** use `--extra-index-url https://pypi.org/simple/` as a default
resolver configuration. A mixed TestPyPI/PyPI index lets a same-named package
on production PyPI satisfy a dependency, which is a dependency-confusion risk:
malicious or unexpected packages could be resolved from PyPI instead of TestPyPI.

For the optional `demo` extra (which pulls in `streamlit`), use a safe
two-step process instead of a mixed index:

1. Install the exact BlackScholesLab distribution from TestPyPI with `--no-deps`:

   ```bash
   python -m pip install \
     --index-url https://test.pypi.org/simple/ \
     --no-deps \
     "blackscholeslab[demo]==<exact-version>"
   ```

2. Install the known optional dependency separately from the intended production
   index (or validate the downloaded BlackScholesLab wheel/sdist locally before
   installing):

   ```bash
   python -m pip install streamlit
   ```

### Validating the TestPyPI build

After installation:

1. `python -c "import blackscholeslab; print(blackscholeslab.__version__)"`
2. `blackscholeslab --help`
3. Run the core test suite against the installed package.

Do not promote the TestPyPI release to production. Treat TestPyPI as a
rehearsal only.

## Production PyPI publication

Publication uses GitHub Actions with PyPI Trusted Publishing. The workflow
is defined in `.github/workflows/release.yml`.

### Publication path

1. A `v*` tag is created on a commit that has passed CI.
2. The release workflow builds artifacts once.
3. The workflow validates the exact built artifacts.
4. A protected `pypi` environment gates the publishing job.
5. The publishing job uploads the validated wheel and sdist to production PyPI
   using `pypa/gh-action-pypi-publish`.

### What this workflow does not do

- It does not store a PyPI password or API token.
- It does not run on ordinary pushes or pull requests.
- It does not publish from arbitrary branch names.
- It does not rebuild artifacts before publishing.

## Git tag and GitHub release procedure

After production publication:

1. Create an annotated Git tag matching the version (for example `v0.1.0`).
2. Push the tag.
3. Create a GitHub release from the tag.
4. Attach the published wheel, sdist, and SHA-256 hashes.
5. Copy the relevant changelog section into the release notes.

## Post-publication verification

After publishing:

1. Install from production PyPI in a fresh environment.
2. Verify the version, imports, and CLI entry point.
3. Run the core test suite against the installed package.
4. Verify the GitHub release exists and has the expected assets.
5. Confirm the changelog heading and date are correct.

## Failure, rollback, and package-yank guidance

### Pre-publication failure

If validation fails before publication:

1. Stop the release.
2. Fix the issue.
3. Repeat the affected validation steps.

### Post-publication failure

If a published version is defective after publication:

1. Assess the severity.
2. If the defect is critical, yank the release on PyPI.
3. Fix the issue.
4. Release a corrected version with a new patch or minor number.
5. Document the yank and replacement in the changelog.

### Yanking

PyPI yanking removes a version from default installation resolution without
deleting the release. Users who pin the exact version are still affected.
Always prefer a new corrected release over re-uploading the same version.

### When to yank

- The package fails to install.
- The package crashes on import.
- The package contains a security vulnerability.
- The package metadata is materially wrong.

### When not to yank

- Minor documentation issues.
- Non-blocking deprecation warnings.
- Cosmetic formatting differences.

## Maintenance of release evidence and artifact hashes

After each release:

1. Record the SHA-256 hash of the published wheel and sdist.
2. Store the hashes alongside the release notes or checklist.
3. Retain the built artifacts for auditing purposes.
4. Do not modify published artifacts; publish a new version instead.

## Educational / non-advice limitation

This document is operational and educational guidance for maintainers. It
does not constitute financial, legal, or compliance advice. Each release
decision remains the responsibility of the project maintainer.
