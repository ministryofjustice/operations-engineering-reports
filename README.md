# MoJ Operations Engineering Reports

[![repo standards badge](https://img.shields.io/badge/dynamic/json?color=blue&style=for-the-badge&logo=github&label=MoJ%20Compliant&query=%24.data%5B%3F%28%40.name%20%3D%3D%20%22operations-engineering-reports%22%29%5D.status&url=https%3A%2F%2Foperations-engineering-reports.cloud-platform.service.justice.gov.uk%2Fgithub_repositories)](https://operations-engineering-reports.cloud-platform.service.justice.gov.uk/github_repositories#operations-engineering-reports "Link to report")

A web application to receive JSON data and publish various reports based on it.

The live site is published [here].

Similar to the MoJ Cloud Platform team's [reporting app](https://reports.cloud-platform.service.justice.gov.uk/dashboard)

## Reports

This is the current list of reports, with links to the source repositories:

* [GitHub External Collaborators](https://github.com/ministryofjustice/github-collaborators)
* [GitHub Repository Standards](https://github.com/ministryofjustice/github-repository-standards)

## Updating

Any changes merged to the `main` branch will be deployed via github actions.

See `.github/workflows/cd.yaml` for details.

[here]: https://operations-engineering-reports.cloud-platform.service.justice.gov.uk/
