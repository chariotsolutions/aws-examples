This directory contains polices -- both IAM and SCP -- that we use at Chariot to manage our
developer sandboxes. They're saved here as general examples, referenced from
[this blog post](https://chariotsolutions.com/blog/post/building-developer-sandboxes-on-aws/)
but also form part of our infrastructure-as-code codebase.

* `BasicUserPolicy` (IAM) 

  This policy is granted to all users in the root account. It allows them to log in, change
  their password, and assign a virtual MFA device. We also have a very permissive read-only
  policy that grants access to other IAM information.

* `PreventAdminRoleDeletion` (SCP) 

  Each of our sandbox accounts has a role that grants administrator access. This role must
  be protected against changes, because the only alternative for managing these accounts is
  to log in as the account root user.

  One quirk of our particular implementation is that we protect two different role names.
  `OrganizationAccountAccessRole` is the default name for child accounts created via the
  AWS console. `OrganizationAccessRole` is a Chariot-specific name that was used by
  accident when creating a large number of workshop accounts. Rather than replace the
  latter with the former, it was easier to just protect both.

* `SandboxGuardrail` (SCP) 

  The basic execution limits for our sandbox accounts. This prevents the creation of
  expensive EC2 and RDS instance types, limits creation actions to the US regions, and
  prevents any use of a private certificate manager (which costs $400/month).

  In the blog post I specify the "non-blessed region" statement as a simple "deny all
  actions on all services" rule. For this policy I get a little more selective, denying
  actions that will cost us money, while still allowing reads and free-service creates.
  This bloats the policy, perhaps without any real benefit; it would be nice if AWS
  allowed a wildcard service name in the actions (so we could use "*:Create*").
