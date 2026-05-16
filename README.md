# MODFLOW 6 nightly build

Nightly development build of MODFLOW 6.

[![Latest tag](https://img.shields.io/github/tag/MODFLOW-ORG/modflow6-nightly-build.svg)](https://github.com/MODFLOW-ORG/modflow6-nightly-build/tags/latest)
[![MODFLOW 6 nightly build](https://github.com/MODFLOW-ORG/modflow6-nightly-build/actions/workflows/nightly-build.yml/badge.svg)](https://github.com/MODFLOW-ORG/modflow6-nightly-build/actions/workflows/nightly-build.yml)
[![MODFLOW 6 full distribution test](https://github.com/MODFLOW-ORG/modflow6-nightly-build/actions/workflows/full-dist-test.yml/badge.svg)](https://github.com/MODFLOW-ORG/modflow6-nightly-build/actions/workflows/full-dist-test.yml)

The `develop` branch of the [MODFLOW 6 repository](https://github.com/MODFLOW-ORG/modflow6) contains bug fixes and new functionality that may be incorporated into the next [approved MODFLOW 6 release](https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model). Minimal development distributions are posted regularly to [nightly build repository](https://github.com/MODFLOW-ORG/modflow6-nightly-build/releases/latest) &mdash; these should be considered preliminary, provisional release candidates for the next version of MODFLOW 6.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Distribution contents](#distribution-contents)
  - [Binaries](#binaries)
  - [Documentation](#documentation)
- [Tags](#tags)
- [Reporting issues](#reporting-issues)
- [Disclaimer](#disclaimer)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Distribution contents

The nightly builds are available as operating-system specific [distributions](https://github.com/MODFLOW-ORG/modflow6-nightly-build/releases/latest) including binaries, MODFLOW 6 input/output documentation, development notes, and a `code.json` metadata file. 

### Binaries

Binaries include `mf6`, `mf5to6`, and `zbud6` executables, and the `libmf6` library. The binaries are built in develop mode, making development options available.

### Documentation

Release notes summarizing the current development cycle's changeset are included in the nightly distribution. The distribution also includes a copy of the *'MODFLOW 6 – Description of Input and Output'* document (`mf6io.pdf`).

## Tags

Release tags are based on the date, with format `YYYYMMDD`. Nightly builds are retained for 30 days in the event that there are issues with the latest release candidate. 

## Reporting issues

Any issues with the nightly build should be posted on the main [MODFLOW 6 GitHub repo](https://github.com/MODFLOW-ORG/modflow6) and flagged with the [nightly build](https://github.com/MODFLOW-ORG/modflow6/labels/nightly%20build) label.

## Disclaimer

This software is preliminary or provisional and is subject to revision. It is
being provided to meet the need for timely best science. The software has not
received final approval by the U.S. Geological Survey (USGS). No warranty,
expressed or implied, is made by the USGS or the U.S. Government as to the
functionality of the software and related material nor shall the fact of release
constitute any such warranty. The software is provided on the condition that
neither the USGS nor the U.S. Government shall be held liable for any damages
resulting from the authorized or unauthorized use of the software.
