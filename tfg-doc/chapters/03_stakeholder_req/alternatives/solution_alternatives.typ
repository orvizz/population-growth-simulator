#import "../tables.typ": solution-comparison-table

=== Solution Alternatives

Before committing to a specific delivery format, four plausible approaches were
evaluated: distributing a plain Python script or Jupyter notebook, packaging the
application as a platform-native compiled executable, running the tool as a local
desktop application with a graphical interface, and hosting it as a web application
accessible through a browser. Each alternative was assessed against the project's
primary goals: universal accessibility, integration with the COMPADRE database,
multi-user collaboration, and zero installation friction.

==== Plain Python Script / Jupyter Notebook

The simplest possible delivery format would be a Python script (`.py`) or an
interactive Jupyter notebook (`.ipynb`) that users download and run locally.
The simulation mathematics - matrix multiplication with NumPy @numpy - are a natural fit
for this environment, and the barrier to _development_ is minimal.

However, this approach places the entire setup burden on the end user. Every
person wanting to run a simulation must first install Python at the correct version,
create a virtual environment, resolve dependency conflicts between NumPy, SciPy @scipy,
and any visualisation library, and keep everything up to date. In an academic
context where target users are biology students and researchers - not software
engineers - this friction is a significant deterrent. There is also no graphical
interface: the user interacts through a terminal or a notebook cell, which is
unsuitable for an audience unfamiliar with command-line tools.

Beyond usability, the model offers no persistence or sharing. Each user maintains
their own disconnected copy of any saved matrices or simulation results. Integrating
the COMPADRE Plant Matrix Database @compadre (6,000+ matrices) would require either bundling
a large static file with every distribution or asking users to fetch and manage it
themselves - both unacceptable for a tool meant to serve a broad, non-technical
audience. Dependency conflicts (Python version mismatches, `pip` environment
pollution) are a recurring source of failure in academic computing environments,
making this option fragile in practice.

==== Standalone Desktop Application (.exe)

Packaging the application as a compiled, platform-native executable using tools
such as PyInstaller @pyinstaller or cx\_Freeze removes the requirement for users to have Python
installed. The runtime is bundled into the binary, and the user's experience
resembles installing any conventional desktop software.

The appeal here is real: a single double-click gets the tool running, with no
environment setup and no command line. However, the practical drawbacks are
substantial. Because the Python interpreter is bundled, the resulting executable
is large - typically 150-300 MB for a moderately complex application. More
critically, compiled executables are platform-specific: separate build artefacts
must be produced and maintained for Windows, macOS, and Linux, each requiring
its own signing and distribution pipeline.

Updates present a further problem. There is no mechanism to push a fix or a new
COMPADRE snapshot to installed copies; every user must manually download and
reinstall the application. University and corporate IT environments frequently
block or quarantine unsigned executables, making deployment to the most common
user environment - a university workstation - unreliable. Finally, every installed
instance is isolated: there is no shared database, no user accounts, and no way
to share a custom matrix between two colleagues running the tool on different
machines.

==== Local Desktop Application (Python)

A richer alternative to a raw script is a locally-hosted graphical application
built with a Python GUI framework such as Python Shiny @shiny (running on localhost),
tkinter, or PyQt6. This preserves the use of the Python ecosystem while providing
a reactive, point-and-click interface close in feel to the final product.

Python Shiny in particular is attractive because it shares the same programming
model as the chosen solution and could, in principle, reuse large portions of
the application code. The tool would work offline once installed, and the
simulation logic would remain entirely on the user's machine.

In practice, however, this approach still requires the user to install Python,
Shiny, NumPy, matplotlib, and all transitive dependencies - precisely the
environment setup problem identified above. Python Shiny's local mode launches
a local HTTP server and opens a browser tab, but it is not a true desktop
application: it depends on available ports, can be disrupted by firewalls, and
produces an experience indistinguishable from a web app - without any of the
distribution benefits of one. Each user's data remains local, collaborative
features are impossible, and the live COMPADRE database still requires a network
connection regardless of the "offline" framing. In effect, this alternative
inherits all the drawbacks of the script approach while adding the complexity of
a GUI framework.

==== Web Application

The chosen solution is a three-tier web application: a Python Shiny frontend
served at port 8080, a FastAPI REST API at port 8000, and a PostgreSQL database
- all orchestrated with Docker Compose @docker and accessible from any modern browser.

This architecture directly satisfies every constraint the other alternatives
failed to meet. The user requires nothing beyond Chrome or Firefox; there is no
installation, no version management, and no environment to maintain. The
COMPADRE database is seeded once on the server and is immediately available to
all users, always up to date. Authentication and access controls enable multiple
users to own their own matrices and simulations, share matrices with colleagues
by username, and persist simulation workspaces across sessions and devices.
Deploying a new version of the application - whether a bug fix, a new COMPADRE
snapshot, or a new feature - propagates to every user the moment the container
restarts, with no client action required.

The API-first design (`/v1/` REST endpoints) means the simulation logic is
decoupled from any particular interface, leaving the door open for future
clients - a mobile application, a third-party integration, or a command-line
tool - without duplicating any business logic. Security practices that are
impractical in a distributed desktop application (centralised JWT @rfc7519 authentication,
automated SAST with Bandit and CodeQL, dependency vulnerability scanning with
pip-audit and Trivy) become straightforward in a server-hosted architecture.

The main trade-off is infrastructure dependency: the application requires an
internet connection and a running server. For a public educational tool targeting
university students and researchers worldwide, this is an acceptable and expected
constraint - far less disruptive than requiring every user to manage a local
Python environment.

==== Comparison and Justification

#solution-comparison-table

The table makes the outcome clear: the web application is the only alternative
that satisfies all ten criteria simultaneously. The non-functional requirement
SR-NF-Portability (@req:sr-nf-06) explicitly mandates "Chrome, Firefox, no client installation",
which eliminates the script and local desktop options outright. The
non-functional requirement SR-NF-Availability (@req:sr-nf-02)  demands 99.5% monthly uptime,
which requires infrastructure-level guarantees rather than per-user processes.
The integration of the COMPADRE database as a shared, always-current resource
is only practical when the data lives on a server accessible to all users
concurrently. Collaboration features - matrix sharing, simulation persistence
across devices, and future team workspaces - are architecturally impossible in
any isolated, single-user deployment model.

The additional complexity of the three-tier architecture - compared to a script
or a compiled binary - is justified by the breadth of capabilities it unlocks
and is itself a demonstration of the full range of software engineering
competencies expected of a Final Degree Project: API design, relational database
modelling, containerisation, continuous integration, and automated security
scanning.
