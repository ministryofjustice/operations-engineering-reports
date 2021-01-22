# MoJ Operations Engineering Reports

[![Releases](https://img.shields.io/github/release/ministryofjustice/operations-engineering-reports/all.svg?style=flat-square)](https://github.com/ministryofjustice/operations-engineering-reports/releases)

A web application to receive JSON data and publish various reports based on it.

The live site is published [here].

Similar to the MoJ Cloud Platform team's [reporting app](https://reports.apps.live-1.cloud-platform.service.justice.gov.uk/)

## Updating

To update this app.

* Commit and push changes to the code & specs
* Create a new release using the [github ui](https://github.com/ministryofjustice/operations-engineering-reports/releases)
* Edit `kubernetes_deployment/deployment.yaml` to update the docker image version number
* Run `make deploy`

[here]: https://operations-engineering-reports.cloud-platform.service.justice.gov.uk/
