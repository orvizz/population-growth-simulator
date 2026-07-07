// chapters/03_stakeholder_req/alternatives/deployment_alternatives.typ

=== Deployment Alternatives

Two cloud platforms were evaluated for hosting the three-service stack (PostgreSQL, FastAPI,
Python Shiny): *Microsoft Azure* and *Railway*. Both can host containerised web applications
and managed databases, but they differ substantially in setup complexity, developer
experience, and cost at academic scale.

==== Microsoft Azure

Azure is Microsoft's enterprise cloud platform. Deploying this project on Azure would
require provisioning several independent resources: an *Azure App Service Plan* for the
compute layer, two *Web App* instances (one for the API, one for the frontend), an
*Azure Database for PostgreSQL – Flexible Server* for the database, and *Azure Key Vault*
for secret management. Each resource must be configured separately, linked by connection
strings, and protected by network security rules. Continuous deployment from GitHub
requires either *Azure DevOps Pipelines* or a manually crafted GitHub Actions workflow
targeting each service individually. Staging and production environments are not
first-class concepts in App Service (they are implemented as *deployment slots*, available
only on Standard tier or above).

The main strengths of Azure are its enterprise maturity, globally distributed regions,
strong SLAs, and its integration with the wider Microsoft ecosystem (Active Directory,
Teams, Office 365). These advantages matter for large-scale institutional deployments,
but they also require institutional credentials and introduce operational overhead that
is disproportionate for an academic TFG project.

==== Railway

Railway is a modern Platform-as-a-Service designed around the developer-experience
principle of minimal configuration. Deployment consists of connecting a GitHub repository
to a Railway project; Railway detects the Dockerfiles automatically and builds each
service on every push to the tracked branch. A managed PostgreSQL instance is added as a
plugin with a single click, and its connection string is injected into the other services
via Railway's built-in variable interpolation. Multiple isolated environments
(e.g. `production` tracking `main`, `staging` tracking `dev`) are a first-class feature
of every project, with no tier restrictions.

Railway's Hobby plan provides sufficient compute and database storage for the traffic
expected during development, demonstration, and initial classroom use, without requiring
an institutional subscription or per-resource billing setup.

==== Comparison and Justification

#figure(
  {
    set text(size: 8pt)
    table(
      columns: (1.6fr, 2fr, 2fr),
      stroke: 0.5pt + luma(160),
      align: (left + horizon, left + horizon, left + horizon),
      inset: (x: 6pt, y: 5pt),
      table.header(
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Dimension]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Azure]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Railway]],
      ),
      [Setup complexity],
        [High — resource groups, App Service plans, managed DB, Key Vault, networking rules],
        [Low — connect GitHub repo, add PostgreSQL plugin, set environment variables],
      [GitHub integration],
        [Requires Azure DevOps or a custom GitHub Actions workflow per service],
        [Native — redeploy on push, branch-per-environment built in],
      [Environments],
        [Deployment slots (Standard tier+); not built in on free/basic plans],
        [First-class multi-environment support on all plans],
      [Cost at academic scale],
        [Free tier limited; production pricing per vCPU, RAM, and DB storage],
        [Hobby plan sufficient; simple credit-based billing],
      [Vendor maturity],
        [Enterprise-grade, globally distributed, strong SLAs],
        [PaaS focused on developer experience; smaller ecosystem],
      [Academic fit],
        [Overkill; requires institutional Azure subscription],
        [Self-contained; free tier adequate; minimal operational overhead],
    )
  },
  caption: [Deployment platform comparison: Azure vs Railway],
) <tab:deployment-alternatives>

Railway is selected as the deployment platform. Its GitHub-native continuous deployment,
built-in multi-environment support, and zero-configuration PostgreSQL provisioning match
the scale and operational constraints of this project without requiring an institutional
cloud subscription or dedicated DevOps infrastructure. The live deployment is accessible
at #link("https://popgrowthsim.marioorviz.dev") and is described in detail in
@sec:railway-deployment.
