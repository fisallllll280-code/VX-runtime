# VX Marketplace, Creator Wallets, Commission, and Payouts

Status: SPECIFIED / PROPOSAL — payment-provider integration and live money movement are not implemented by this document.
Scope: VX Runtime. No changes to `project.genome` or `Ω.000`.

## Product rule

Every verified creator gets a marketplace profile and a ledger-backed wallet view. Every listed product has an owner, version, price, currency, license, supported markets, refund terms, and release evidence. A product cannot be listed as purchasable until the required validation, ownership/provenance, policy, and store checks pass.

The dashboard must show:
- gross sales, completed orders, refunds, chargebacks, platform commission, payment processing fees, taxes where applicable, net creator earnings;
- pending, available, reserved, paid-out, and disputed balances separately;
- per-product and per-market performance, currency, date range, and last-updated timestamp;
- payout status, destination verification status, and transaction-level evidence references;
- exportable statements and reconciliation totals.

Do not show fabricated or estimated values as actual money. Demo data must be visibly labeled.

## Payment and payout invariants

1. A checkout attempt is not a sale. A browser redirect or client-supplied success flag is not payment evidence.
2. Only a verified provider webhook/API status with signature verification, idempotency, amount/currency/order matching, and reconciliation can move an order into a paid state.
3. Funds are allocated only after the provider-confirmed event required by the selected payment method and provider contract.
4. The platform commission is calculated from an explicit, versioned seller agreement and stored with each order. Do not hard-code an unspecified commission percentage.
5. Payment processing fees, applicable taxes, refunds, chargebacks, reserves, and FX costs are recorded separately; do not silently subtract them from a different party's share.
6. Creator earnings remain pending until the provider's settlement and platform risk rules allow availability. A displayed balance is a ledger liability, not proof that funds are held in a VX bank account.
7. A payout requires verified creator identity/business details, verified bank destination, sufficient available balance, applicable compliance checks, and an explicit payout authorization or configured schedule.
8. A payout is not marked paid until provider evidence confirms it. Failed or reversed payouts return to the appropriate ledger state with an audit event.
9. Refunds and chargebacks generate compensating ledger entries; historical sale entries are never deleted or silently rewritten.
10. All money is represented in integer minor units (e.g., halalas/cents), with explicit ISO currency. Never use binary floating point for financial calculations.
11. Every financial transition is idempotent and linked to a stable order, provider event, ledger entry, and audit record.
12. No actual money movement is simulated by a test fixture and represented as real. Sandbox/test/live environments are strictly separated.

## Illustrative order allocation

For a hypothetical settled sale of 100.00 currency units, an illustrative 10% platform commission would be 10.00 before any separately agreed fee/tax treatment. The creator's net cannot be stated until processing fees, taxes, refunds/reserves, and the contract's allocation rules are known. This example is not a proposed final commission rate.

Recommended configurable formula, subject to the payment contract and jurisdiction:
- `gross_minor`: amount paid by customer.
- `platform_commission_minor`: calculated under the versioned seller agreement.
- `processing_fee_minor`: actual provider fee.
- `tax_minor`: separately assessed where applicable.
- `refund_or_reserve_minor`: explicit hold/refund/chargeback liability.
- `creator_net_minor`: derived from the agreed allocation policy; never inferred from gross alone.

## Wallet model

Wallet views are ledger projections, not arbitrary mutable balances:
- `pending`: earned in a provider-confirmed state but not yet eligible for payout.
- `available`: settled and cleared for payout.
- `reserved`: held for refunds, disputes, risk review, or provider requirements.
- `paid_out`: payout confirmed by provider.
- `disputed`: amounts under dispute/chargeback handling.

The append-only ledger is authoritative. Cached dashboard totals must be rebuildable from ledger events and reconcile to the payment provider's reports.

## Global marketplace

Each market configuration must define:
- supported countries and seller eligibility;
- product category and prohibited-content rules;
- currency, pricing, localized listing, language, and tax treatment;
- payment methods and payout availability confirmed by the selected provider;
- seller verification, sanctions/fraud screening where required, consumer protection, refunds, and dispute workflow;
- software licensing, IP/provenance declarations, vulnerability/security scans, and malware checks where applicable.

“Global” means only the country/currency/payment combinations that have been reviewed, configured, and tested. Never claim worldwide availability from a provider's general marketing statement alone.

## Provider integration

Use a marketplace-capable licensed payment provider that explicitly supports the intended seller countries, currency routes, split/commission handling, refunds, disputes, and payouts. Candidate providers to assess include Stripe Connect and Adyen for Platforms; availability and onboarding for the platform's legal entity and each seller country must be confirmed directly with the provider. VX must not hold or transfer customer funds itself unless the operating model is legally authorized to do so.

Use provider-hosted onboarding where possible. Keep API secrets server-side in a secret manager; never store bank credentials, card data, identity documents, or raw secrets in source code or general-purpose logs. Verify webhook signatures, use idempotency keys, reconcile settlement reports, and implement refund/chargeback paths before launch.

## Proposed state machine

`DRAFT → VALIDATING → APPROVED_FOR_LISTING → LISTED → CHECKOUT_PENDING → PAYMENT_CONFIRMED → SETTLEMENT_PENDING → EARNINGS_AVAILABLE → PAYOUT_PENDING → PAID_OUT`

Exception states include `REJECTED`, `PAYMENT_FAILED`, `REFUND_PENDING`, `REFUNDED`, `DISPUTED`, `PAYOUT_FAILED`, and `COMPLIANCE_HOLD`. Transitions require provider/validation evidence; clients cannot set them directly.

## Creator's end-to-end journey

1. Sign up and verify identity/business and payout destination through the provider's approved onboarding.
2. Create a product using VX Builder; attach version, license, provenance, and build/test evidence.
3. Pass security, policy, ownership, and market eligibility checks.
4. Publish to selected supported marketplaces.
5. Track views, conversion, paid orders, refunds, commission, and net proceeds per currency.
6. After settlement and required checks, request a payout or receive it under the configured schedule.
7. Receive a payout receipt and statement; reconcile it against ledger and provider evidence.

## Required acceptance tests before live launch

- Forged or unsigned webhook cannot mark an order paid.
- Duplicate webhook/order event does not duplicate a sale or commission.
- Amount/currency/order mismatch is rejected and raises an alert.
- Payment authorization without capture/settlement does not become available earnings.
- Commission is calculated from the agreement version active for the order.
- Refund and chargeback create compensating entries and update payout eligibility.
- Unverified seller or bank destination cannot receive a payout.
- Payout exceeding available balance is rejected.
- Failed payout is not reported as paid.
- Currency rounding and boundary cases are tested in integer minor units.
- Provider settlement report reconciles to the ledger; unexplained differences raise a hold.
- Sandbox and live credentials/data cannot be mixed.
- Product cannot be listed before required provenance/security/policy gates pass.

## Regulatory and operational gate

Before processing real payments, confirm the platform's legal entity, merchant-of-record/marketplace role, seller terms, consumer/refund terms, tax/accounting responsibilities, data protection obligations, and payment-services requirements for Saudi Arabia and every target market. Obtain qualified legal/compliance advice and provider approval. The design must not imply that a UI wallet is a bank account or that VX can independently provide regulated payment services.
