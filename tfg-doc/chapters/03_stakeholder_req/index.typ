// chapters/03_stakeholder_req/index.typ
#import "../../template.typ": guia, req, req-group

= Stakeholder Requirements

#guia[The purpose is to provide an initial definition of the requirements for a system
that can provide the services needed by users and other stakeholders. This involves a
preliminary description of what the system to be developed should include.

As a guideline, the content of this chapter corresponds to the results of the
"Stakeholder Requirements Definition" process in ISO/IEC 15288 or the "System
Feasibility Study (EVS)" process in the Métrica Version 3 methodology.]

== System Scope

#guia[Identify the users and other stakeholders in the system and briefly describe
their objectives and needs. It may also include a description of the system's
operation and/or processes as they are currently performed.]

#pagebreak()

== Stakeholder Requirements

#guia[This will include the identified requirements, usually organized in a structured
way using a hierarchical list. It will address both functional and non-functional
requirements and other constraints that condition the final product. Note that these
requirements should be written from the user's point of view and must be brief and
concise. As a guideline, they may occupy two or three pages.]

=== Functional Requirements

#req-group("SR-F")

#req("Authentication", [
  The system shall provide mechanisms for users to register, access, and leave the
  system securely.
])

#req("User Registration", [
  The system shall allow new users to create an account.
], indent: 1)

#req("Registration Form", [
  The system shall require the following fields to create an account: username, email
  address, and password.
], indent: 2)

#req("Username Uniqueness", [
  The system shall reject a registration attempt if the provided username is already
  associated with an existing account.
], indent: 2)

#req("Email Uniqueness", [
  The system shall reject a registration attempt if the provided email address is
  already associated with an existing account.
], indent: 2)

#req("Password Policy", [
  The system shall reject a registration attempt if the provided password contains
  fewer than 8 characters.
], indent: 2)

#req("Password Hashing", [
  The system shall hash every password using bcrypt before persisting it in the
  database. Plain-text passwords shall never be stored.
], indent: 2)

#req("User Login", [
  The system shall allow registered users to authenticate and obtain access to
  protected resources.
], indent: 1)

#req("Login Credentials", [
  The system shall accept either the username or the email address, combined with the
  password, as valid login credentials.
], indent: 2)

#req("Credential Validation", [
  The system shall verify the provided password against the stored bcrypt hash and
  reject the login if they do not match.
], indent: 2)

#req("JWT Issuance", [
  Upon successful login, the system shall issue a signed JSON Web Token (JWT) to the
  client to be used in subsequent authenticated requests.
], indent: 2)

#req("Failed Login Feedback", [
  The system shall return an error message on failed login attempts without revealing
  whether the username, the email, or the password was incorrect.
], indent: 2)

#req("Session Management", [
  The system shall manage authenticated sessions through JWT.
], indent: 1)

#req("Token Validation", [
  The system shall validate the JWT on every request to a protected resource.
], indent: 2)

#req("Token Rejection", [
  The system shall reject requests carrying a missing, malformed, or expired token,
  returning an appropriate error response.
], indent: 2)

#req("User Logout", [
  The system shall allow authenticated users to terminate their session.
], indent: 1)

#req("Token Invalidation", [
  Upon logout, the system shall invalidate the user's current JWT so that it cannot be
  reused in subsequent requests.
], indent: 2)

#req("Client-Side Cleanup", [
  Upon logout, the client shall remove any locally stored copy of the JWT.
], indent: 2)

=== Non-Functional Requirements

#req-group("SR-NF")

#req("Performance", [
  The system shall respond to any user interaction within 3 seconds under normal load
  conditions (100 concurrent users).
])

#req("Availability", [
  The system shall be available at least [99.5]% of the time, measured on a monthly
  basis, excluding scheduled maintenance windows.
])

#req("Security", [
  The system shall authenticate every user before granting access to the registered
  users' functionalities.
])

#req("Maintainability", [
  The system shall be designed in a modular way so that any individual component can
  be updated or replaced with minimal impact on the rest of the system.
])

#req("Usability", [
  A new user with basic computer skills shall be able to complete the main tasks
  without prior training in less than 5 minutes.
])

#req("Portability", [
  The system shall operate correctly on the following web browsers: Chrome, Firefox.
  No client-side installation shall be required beyond a standard web browser.
])

#req("Legal & Regulatory Compliance", [
  The system shall comply with applicable regulations, including GDPR / LOPD-GDD for
  personal data protection.
])

#pagebreak()

== Alternatives

#guia[When there is freedom to choose between several alternatives (both functional
and technical) to comply with the user requirements, a description of their pros and
cons and the justification for the selected alternative should be included.]

=== Solution Alternatives

#guia[Here, describe the different solutions presented for this project (web app,
desktop app (with Python or with a `.exe` file), a mobile app...). Expose the pros and
cons of each one and why the final solution was a web app (public access for everyone
from a web browser).]

=== Technology Alternatives

#guia[Describe the different technical alternatives considered to build the project,
the selected programming language (Python) for the frontend (used Python Shiny as a
constraint from the stakeholder), backend (FastAPI), the database selection (relational
Postgres database), the migration technology, and the ORM used.]
