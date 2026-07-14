# Release Checklist

This checklist is the operational gate for each BlackScholesLab release.
No step in this checklist authorises publication by itself; all steps must
be completed and explicitly approved before a version is published.

## 1. Pre-release preparation

- [ ] CI is green on the release branch (Python 3.11 and 3.12).
- [ ] Ruff format and lint pass.
- [ ] Mypy strict passes.
- [ ] Full pytest suite passes with 100% branch coverage for core and demo.
- [ ] The working tree is clean (no uncommitted changes).
- [ ] The release branch is correct and reviewed.
- [ ] No unreviewed dependencies or configuration changes remain.
- [ ] Release documentation (`docs/releasing.md`) has been reviewed.

## 2. Release-candidate verification

- [ ] Wheel builds successfully from a clean checkout.
- [ ] Sdist builds successfully from a clean checkout.
- [ ] Wheel metadata is correct (name, version, description, license, author,
      Python requirement, project URLs, classifiers, keywords).
- [ ] Sdist contains expected documentation, examples, tests, and source files.
- [ ] `py.typed` marker is present in the wheel.
- [ ] Console entry point `blackscholeslab` is present in the wheel.
- [ ] No secrets, caches, or virtual-environment files are in the artifacts.
- [ ] Streamlit is not a mandatory runtime dependency.
- [ ] Demo extra metadata is present.
- [ ] Version consistency test passes (pyproject.toml, `__version__`, wheel
      metadata, sdist metadata).
- [ ] Artifact SHA-256 hashes are computed and recorded.
- [ ] Core wheel installs cleanly into a fresh virtual environment.
- [ ] `import blackscholeslab` succeeds and `__version__` is correct.
- [ ] `blackscholeslab --help` succeeds through the installed entry point.
- [ ] `python -m blackscholeslab.cli --help` succeeds.
- [ ] Streamlit is absent from the core-only environment.
- [ ] TestPyPI rehearsal completed: the exact version installs from TestPyPI in
      isolation (`--index-url https://test.pypi.org/simple/ --no-deps`) and
      verifies artifact integrity; no mixed TestPyPI/PyPI resolver was used.
- [ ] Version consistency confirmed across `pyproject.toml`, `__version__`,
      wheel METADATA, and sdist PKG-INFO (exact, non-development version).
- [ ] Demo extra installs cleanly into a fresh virtual environment.
- [ ] `import demo.app` and `import demo.helpers` succeed in the demo
      environment.
- [ ] Sdist builds wheel, installs, and passes tests.
- [ ] All seven CLI commands exercise success, domain-error, and
      implied-volatility non-convergence exit codes.
- [ ] Markdown links in release documentation resolve.
- [ ] Workflow YAML syntax is valid.
- [ ] Workflow triggers and permissions are correct.

## 3. Explicit human approval

- [ ] A human maintainer has reviewed the release candidate.
- [ ] A human maintainer has approved the version bump.
- [ ] A human maintainer has approved the publication target (TestPyPI or
      production PyPI).
- [ ] The approval is recorded in the release issue, pull request, or
      checklist.

## 4. Version bump

- [ ] `pyproject.toml` version is updated (for example from `0.1.0.dev0` to
      `0.1.0`).
- [ ] `src/blackscholeslab/__init__.py` `__version__` is updated.
- [ ] Version consistency test still passes after the bump.
- [ ] Changelog `## [Unreleased]` section is finalised with a release date.

## 5. Tag creation

- [ ] A Git tag is created whose exact name equals `v<package version>`
      (for example `v0.1.0`), with no other suffixes or deviations.
- [ ] The tag is pushed to the remote repository.
- [ ] The tagged commit is contained in the default `main` history (the release
      workflow verifies this via `git merge-base --is-ancestor`).

## 6. Artifact publication

- [ ] The release workflow triggers on the `v*` tag.
- [ ] The workflow builds artifacts once.
- [ ] The workflow validates the built artifacts.
- [ ] The publishing job uploads to the target index (TestPyPI or PyPI).
- [ ] Trusted Publishing is used; no stored password or API token is involved.
- [ ] The protected environment gate (`pypi` or `pypi-testpypi`) is active.
- [ ] Trusted Publishers configured for the exact repository
      (`sciwiz7/Blackscholes`), workflow (`release.yml`), and environment
      (`pypi` for production, `pypi-testpypi` for TestPyPI).

## 7. GitHub release

- [ ] A GitHub release is created from the tag.
- [ ] Release notes include the changelog section for the version.
- [ ] The wheel, sdist, and SHA-256 hashes are attached as release assets.

## 8. Post-release checks

- [ ] Install from the published index in a fresh virtual environment.
- [ ] Verify `blackscholeslab.__version__` matches the released version.
- [ ] Verify `blackscholeslab --help` works through the installed entry point.
- [ ] Run the core test suite against the installed package.
- [ ] Verify the GitHub release assets are present and correct.
- [ ] Confirm no unintended artifacts were published.

## 9. Rollback / yank response

If a defect is discovered after publication:

- [ ] Assess severity and decide whether to yank.
- [ ] If yanking, yank the release on PyPI.
- [ ] Fix the defect in a new commit.
- [ ] Release a corrected version with a new patch or minor number.
- [ ] Document the yank and replacement in the changelog.
- [ ] Record the incident in the release evidence.

## Notes

- This checklist does not authorise publication by itself.
- Every completed release must retain its own checklist copy as release
  evidence.
- TestPyPI rehearsals follow the same structure but use the `pypi-testpypi`
  environment and target TestPyPI.
- Deleting a Git tag or deleting/withdrawing a GitHub Release does **not**
  remove a PyPI publication. A published version must be yanked on PyPI to
  withdraw it from default installation resolution; users who pin the exact
  version are still affected.
- Production PyPI publication is triggered only by a rigorously validated
  `vMAJOR.MINOR.PATCH` tag; it is not available from a manual
  `workflow_dispatch` run.
