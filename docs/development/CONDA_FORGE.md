# Conda-forge Recipes

Rhiza **generates** a conda-forge recipe for each public PyPI release. It does **not
publish** anything to conda-forge. A package reaches conda-forge only through a
*feedstock*, a repository in the `conda-forge` organisation that conda-forge's
infrastructure builds and uploads from. Changes to a feedstock are reviewed and merged by
its maintainers. The recipe Rhiza produces is an input to that process: the first
submission of a new package, or a reference when you review an update.

| Step | Who does it | Where |
| --- | --- | --- |
| Generate `meta.yaml` with grayskull, verified against the PyPI sdist | Rhiza (`rhiza_release.yml`, or `rhiza_conda_recipe.yml` on demand) | `conda-recipe` workflow artifact |
| Submit the first recipe | You | PR to [conda-forge/staged-recipes](https://github.com/conda-forge/staged-recipes) |
| Review and merge the first recipe | conda-forge reviewers | `staged-recipes` |
| Propose each later version | conda-forge's autotick bot (`regro-cf-autotick-bot`) | PR to `conda-forge/<name>-feedstock` |
| Review and merge updates | Feedstock maintainers (you) | `<name>-feedstock` |
| Build and upload packages | conda-forge CI | the `conda-forge` channel |

## What the release workflow does

The `conda` job in `.github/workflows/rhiza_release.yml` runs after the package was
published to **public PyPI**. It is skipped when:

- the repository variable `PUBLISH_CONDA` is set to anything other than `true` (unset means `true`),
- `RELEASE_PUBLISHER` is `custom` or `none`, or `PYPI_REPOSITORY_URL` points at another index, or
- the PyPI upload failed.

The job runs `.rhiza/scripts/conda_recipe.py`, which:

1. asks grayskull (pinned, `meta.yaml` format) for exactly `<name>==<tag version>`, never
   for whatever PyPI currently calls "latest";
2. retries for up to five attempts, a minute apart, while PyPI's metadata for the
   just-published version propagates (a grayskull crash is not retried);
3. verifies the recipe's `version`, source filename and `sha256` against PyPI's record of
   that release. A recipe for an older release fails here, it does not count as success;
4. uploads `conda-recipe/meta.yaml` as the `conda-recipe` artifact of the run.

The job never blocks the release. When it fails, the GitHub release is still published
and its notes say that recipe generation failed and how to regenerate it. When it
succeeds, the notes say where the recipe is and that it has not been published.

## Regenerating the recipe for an existing release

To regenerate a recipe without rebuilding, re-tagging or republishing the package, run
`.github/workflows/rhiza_conda_recipe.yml`. For example, when the `conda` job failed, was
skipped, or its artifact has expired:

```bash
gh workflow run rhiza_conda_recipe.yml -f tag=v1.2.3
gh run list --workflow rhiza_conda_recipe.yml --limit 1   # find the run id
gh run download <run-id> -n conda-recipe
```

or **Actions → (RHIZA) CONDA RECIPE → Run workflow** in the GitHub UI.

The tag must exist and its version must already be on PyPI. The workflow runs the same
script as the release, with the same checks. Its only permission is `contents: read`, so
it cannot publish, tag or edit a release. It reads the script from the commit you run the
workflow from, not from the tag. You can therefore regenerate a recipe for a release
that was tagged before the script was synced into your repository.

## First release: submitting to `staged-recipes`

A package that is not on conda-forge yet is added once, by pull request:

1. Download the `conda-recipe` artifact for the release you want to submit.
2. Fork [conda-forge/staged-recipes](https://github.com/conda-forge/staged-recipes) and
   copy the file to `recipes/<name>/meta.yaml`.
3. Review what grayskull produced. It is a draft, not a finished recipe:
    - `extra.recipe-maintainers` lists the GitHub handles who will maintain the
      feedstock. Add yourself and any co-maintainers.
    - Check `requirements` against `pyproject.toml`. Optional dependencies, extras and
      platform markers often need adjusting.
    - Check that `license` and `license_file` name the licence file that is actually in the
      sdist.
    - Keep the `test` section meaningful: `imports` plus `pip check` at minimum.
4. Open the pull request and follow the staged-recipes checklist. conda-forge reviewers
   will comment, and the recipe is merged once they approve.
5. On merge, conda-forge creates `conda-forge/<name>-feedstock` and grants the listed
   maintainers access. That feedstock is the recipe's home from then on.

## Later releases: the feedstock's bot

After the feedstock exists you do not need to submit Rhiza's recipe again. conda-forge's
autotick bot watches PyPI. When a new version appears, it opens a pull request on the
feedstock that bumps `version`, updates `sha256` and resets the build number to 0.

Review that PR as a maintainer before merging:

- **Version and checksum.** Compare with the `conda-recipe` artifact from your release
  run, whose `version` and `sha256` were checked against PyPI. They should agree.
- **Dependencies.** The bot does not always update `requirements`. Diff the artifact's
  `requirements` against the feedstock's recipe and port any new, removed or re-pinned
  dependency to the bot's branch.
- **Rerender.** If conda-forge's linter or CI asks for it, comment
  `@conda-forge-admin, please rerender` on the PR.

### Preserve feedstock-specific changes

The feedstock's recipe is the source of truth for conda-forge, not Rhiza's artifact. Over
time it collects changes grayskull cannot know about: patches, `skip` selectors, extra
test commands, `noarch` choices, extra maintainers and feedstock settings in
`conda-forge.yml`. **Never overwrite the feedstock's `meta.yaml` with a regenerated
recipe.** Treat the artifact as a reference. Diff it, and carry over only what actually
changed upstream, usually version, checksum and dependencies.

## Not covered yet

Optional conda build or install checks, and the newer v1 `recipe.yaml` format built with
`rattler-build`, are possible follow-ups. Rhiza currently generates the `meta.yaml`
format, which `staged-recipes` and existing feedstocks accept.
