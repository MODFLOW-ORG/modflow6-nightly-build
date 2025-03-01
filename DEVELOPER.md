# Developing the MODFLOW 6 nightly build

This repository exists solely to orchestrate bleeding-edge MODFLOW 6 development version releases independently of the [main MODFLOW 6 repository](https://github.com/MODFLOW-ORG/modflow6). It contains no source code or scripts, only GitHub Actions workflows and a `requirements.txt` file specifying Python dependencies. All scripts related to MODFLOW 6 distribution/release are contained in the `distribution` folder in the MODFLOW 6 repository.

## Workflows

This repository contains two workflows:

- `dev.yml`
- `full.yml`

### Development distribution

The `dev.yml` workflow builds a minimal development distribution of MODFLOW 6 and posts it on this repository's [releases page](https://github.com/MODFLOW-ORG/modflow6-nightly-build/releases). Assets include only binaries and the MODFLOW 6 input/output PDF documentation. This workflow is triggered each night, as well as whenever new code is merged into the MODFLOW 6 repo's `develop` branch. If a release already exists for a given date, assets are updated on the existing release. Binaries from the same date can be distinguished by compile timestamps emitted in the header info block at runtime.

### Full distribution test

Each night, the `full.yml` workflow tests the full, official MODFLOW 6 release procedure and posts the created distribution as an artifact. This distribution is identical to that produced in a [real release](https://github.com/MODFLOW-ORG/modflow6/blob/develop/distribution/README.md), with the exception of version numbers. This permits regular inspection of the distribution, allowing more confidence at release time.