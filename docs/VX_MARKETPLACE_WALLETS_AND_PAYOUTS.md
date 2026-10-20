# VX Marketplace, Creator Rewards, and Competitions

Status: SPECIFIED / PROPOSAL. Live payment processing, bank transfers, and live competitions are not implemented. `project.genome` and `Ω.000` remain protected.

## Marketplace commission
- Standard commission: **30%** (3,000 basis points).
- Creator launch commission: **5%** (500 basis points) remains a separate promotional rate only for creators explicitly eligible under published terms. If a creator is eligible, the 5% rate applies instead of 30%; it is not an extra discount stacked on top.
- Payout target: weekly after provider settlement, creator identity/destination verification, and compliance clearance.
- Launch market: Saudi Arabia (`SA`); each additional market requires review.
- Supported product types: `apps`, `agents`, `tools`, `apis`, `workflows`.

For a hypothetical settled sale of SAR 100 before fees, taxes, refunds, or other deductions, standard commission is SAR 30 and creator remainder is SAR 70. For an explicitly eligible launch creator, commission is SAR 5 and remainder SAR 95. Show the applicable rate and deductions before checkout; store the seller agreement version and rate on each order.

## Creator progression
- Explorer: onboarding and first approved artifact.
- Builder: product with passing tests, license/provenance, and support information.
- Verified Creator: identity, ownership, policy, and security gates passed.
- Trusted Creator: sustained reliability, reproducible releases, and good customer outcomes.
- Featured Innovator: independently judged competition placement or measurable impact.

Possible benefits, only after actually enabled: creator badges, featured-listing eligibility, additional sandbox/build quota, beta access, enhanced analytics, priority documentation/support, mentorship, and integration support. Do not show an entitlement as active before it is granted.

## Competitions
Proposed recurring events:
1. VX Build Challenge — useful apps, tools, and workflows.
2. Agent Arena — agents and multi-agent workflows scored on task success, robustness, latency/cost, and reproducible evidence.
3. Safety & Trust Challenge — defensive security, provenance, reproducibility, and responsible behavior.
4. Open Innovation Challenge — novel systems with measurable value.
5. Community Impact Challenge — accessibility, localization, education, and public-interest tools.

Example judging rubric, to be published before each contest opens: 30% correctness/usefulness, 20% reproducibility/evidence, 20% safety/security/privacy/license compliance, 15% reliability/performance, 10% usability/accessibility, 5% originality. Publish dates, eligibility, judge identities or roles, conflict-of-interest rules, tie-breaks, IP terms, prize terms, and appeals process. Do not change the rubric after the contest opens.

## Rewards
Potential rewards include funded cash prizes, platform credits, compute/build quota, badges, featured placements, early access, mentorship, integration support, and validated bug-fix bounties. Prize amounts and budgets are **not yet approved**. Publish the funded prize pool, source, amounts, eligibility, tax treatment, delivery schedule, and appeal rules before advertising any cash award. Marketplace revenue is not automatically a funded prize pool. Reward payment requires its own approval and fulfillment evidence.

## Evidence gates
A submission must have a stable submission and creator ID, artifact version, supported category, ownership/provenance evidence, reproducible evidence reference, passing tests, security review, and policy review. Eligibility is not a winning decision. Ranking requires the published rubric and recorded judging evidence. Submissions missing a gate remain ineligible pending review.

## Safety and operating boundaries
- Run untrusted submissions in isolated sandboxes with least privilege and no default network access or production secrets.
- Verify ownership, licenses, security, and abuse controls before public listing.
- Separate sandbox, staging, and production; never claim live money movement from test fixtures.
- Do not modify `project.genome` or `Ω.000` without explicit authorization.
- Obtain legal/compliance review for Saudi launch and each later market.
