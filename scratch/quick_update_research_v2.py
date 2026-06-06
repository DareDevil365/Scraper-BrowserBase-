import os

REPORTS = {
    "Etsy": """ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): Escrow-like (Etsy Payments)
Who holds the funds?: Etsy
When are funds collected? (Before work / At order / On delivery): At order
KYC & Onboarding Barriers: Etsy Payments requires strict KYC (Stripe-powered in many regions): government photo ID, bank statement, tax ID (SSN/EIN/GSTIN), and credit card on file to prevent bad actors.
Transaction Fee Split & Refund Policy: Seller pays listing fee ($0.20) + transaction fee (6.5%) + payment processing fee (typically 3% + $0.25). If a refund is issued, Etsy refunds the transaction/processing fees, but the listing fee is not refunded.

RELEASE TRIGGERS
What triggers the escrow release?
- Shipment dispatch (tracking status shows "in transit") or scheduled payout interval (daily, weekly, bi-weekly, monthly) after a holding period.
- For shops with a payment reserve, a percentage of funds (e.g., 75%) is held for up to 45 days unless valid tracking is uploaded, which triggers immediate release.
Transit Gating & Delivery Verification: Uses carrier API tracking. Release occurs based on carrier tracking showing "in transit" or "delivered". For reserve accounts, carrier physical scan at origin is the trigger.
Hold Extension Mechanism: Buyers cannot arbitrarily extend the release hold, but opening a "case" freezes the escrow/payment reserve funds instantly.

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: Not delivery-gated (typically 3-7 days post-shipment or up to 45 days if on reserve).
Nuances: For standard sellers, funds become available for deposit next business day after shipment. For reserve accounts, they release as soon as tracking confirms the carrier has scanned the package.
Transit Delay Protection: If carrier tracking shows "in transit" but is delayed, Etsy's Purchase Protection covers the refund cost (up to $250) for the buyer, allowing the seller to keep the payout.

DISPUTE HANDLING
Who decides disputes?: Etsy support specialists
What is the resolution timeline?: 2 to 5 business days once escalated
What evidence does the buyer/seller need to submit?:
- Seller: Proof of shipping (postal receipt, tracking showing delivery to buyer's address), photos of custom dimensions, material verification.
- Buyer: Photos showing item condition, sizing discrepancies measured against a ruler, or custom details mismatches.
Alteration vs. Refund Guidelines: Etsy does not support alterations since it's a marketplace of finished items. Returns/refunds are the only dispute actions, unless the seller voluntarily offers a replacement.
Evidence Standards for Sizing/Fit: For custom sizing disputes, buyers must submit high-resolution photos showing the item measured flat against a hard ruler or measuring tape showing the discrepancy from the listing measurements.
Return Shipping Fee Burden: Determined by seller's return policy. In disputes, if the item is "not as described," Etsy can force the seller to provide a return shipping label, or refund the buyer without return.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes (Etsy Purchase Protection Program)
Any coverage cap on orders (e.g. max ₹X covered)?: Yes, covers qualifying orders up to $250 USD.
What happens to the provider if the buyer disputes unfairly?:
- If the seller meets eligibility criteria (tracking, on-time shipping), Etsy covers the cost of the refund from its own funds and does not penalize the seller.
- Under shipping delays or transit damage, Etsy absorbs the refund cost up to the cap if the seller used Etsy shipping labels.
Review/Rating Protection: Sellers can flag reviews for removal if they violate Etsy policies (e.g., reviews about third-party shipping delays, or retaliatory reviews during open disputes).
Material/Fabric Loss Shield: Etsy has no protection if the buyer sent custom fabric to the seller. Sizing or material issues are treated as seller risk.

DISPUTE NUANCES & ACCOUNT CONTROLS
Dispute Occurrence Pattern:
- High frequency of "Item Not Received" (INR) due to international shipping delays or untracked local mail.
- Sizing discrepancies and color mismatch claims on custom handmade apparel and personalized gifts.
Account Blocking/Suspension Criteria:
- Order Defect Rate (ODR) exceeding 1.0% (measured as cases opened against the shop + negative 1- or 2-star reviews over a 60-day period) triggers automatic review and suspension.
- Multiple intellectual property violations (DMCA notices) lead to permanent account termination.
Platform Bias in Disputes:
- Highly buyer-biased. Etsy often refunds the buyer instantly upon case opening for untracked shipping. However, the $250 purchase protection buffer helps shield eligible sellers from bearing the refund cost.

KEY INSIGHT FOR SILAAI
What is the single most useful thing Silaai should borrow or avoid from this model?
- BORROW: The Purchase Protection Program concept with a coverage cap. Silaai should absorb the cost of disputes for trusted tailors up to a certain limit (e.g., ₹5,000) for issues like transit damage, provided the tailor followed packaging guidelines.
- AVOID: Strict ODR-based automated blocking for custom items. Custom tailoring has high subjective dispute rates (e.g. minor fit complaints) which would unfairly trigger automated bans for high-quality tailors.

SOURCES USED
- https://www.etsy.com/legal/policy/purchase-protection-program-for-sellers/345095853800
- https://www.etsy.com/legal/seller/
- https://help.etsy.com/hc/en-us/articles/115014372467-How-to-Resolve-a-Case-on-Etsy
""",

    "Craftsvilla": """ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): Escrow-like
Who holds the funds?: Craftsvilla
When are funds collected? (Before work / At order / On delivery): At order
KYC & Onboarding Barriers: Requires PAN, Aadhaar/GSTIN, bank account verification (cancelled cheque), and business registration (Proprietorship/LLP/Pvt Ltd).
Transaction Fee Split & Refund Policy: Commission of 20% to 45% + service tax. In returns/refunds, commissions are reversed, but logistics fees (if platform-shipped) are charged to the seller.

RELEASE TRIGGERS
What triggers the escrow release?
- Seller ships the item (normally within 3 working days of order confirmation) and uploads valid tracking.
- The payout clock starts from dispatch, releasing the funds within 15 working days of shipping.
Transit Gating & Delivery Verification: Gated by shipment date (schedule-based). Payout is processed 15 working days post-shipment, regardless of actual delivery status.
Hold Extension Mechanism: Buyers cannot extend the payout release hold; it is hardcoded to 15 working days post-shipment.

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: Not delivery-gated (15 working days post-shipment).
Nuances: Craftsvilla releases the funds on a schedule post-shipment regardless of whether the buyer has confirmed delivery.
Transit Delay Protection: None. If shipment is delayed in transit, Craftsvilla does not pause the 15-day payout cycle unless the buyer proactively logs a dispute.

DISPUTE HANDLING
Who decides disputes?: Craftsvilla customer care team
What is the resolution timeline?: 7 to 10 working days, though historically prone to severe delays
What evidence does the buyer/seller need to submit?:
- Buyer: Must email photos of damaged or incorrect items within 7 days of delivery with the order number.
- Seller: Must provide proof of dispatch and courier manifests to dispute tracking claims.
Alteration vs. Refund Guidelines: Custom items are strictly non-returnable. No alteration flow exists on the platform.
Evidence Standards for Sizing/Fit: Standard items require photos of tags and measurements. Custom tailoring disputes are rejected by default unless severe manufacturing damage is shown.
Return Shipping Fee Burden: Buyer pays for return shipping unless it is a seller mistake, in which case the seller is charged for reverse pickup.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): No
Any coverage cap on orders (e.g. max ₹X covered)?: No stated cap
What happens to the provider if the buyer disputes unfairly?:
- Sellers are highly exposed. Craftsvilla frequently refunds buyers (often only as non-refundable wallet credits) and clawbacks payouts from the seller's account.
- Non-compliance with the 3-day shipping rule removes any seller defense.
Review/Rating Protection: No formal retaliatory review protection; dispute cases do not automatically block reviews.
Material/Fabric Loss Shield: No coverage for fabric/material loss.

DISPUTE NUANCES & ACCOUNT CONTROLS
Dispute Occurrence Pattern:
- Courier tracking disputes where tracking shows "delivered" but the buyer claims non-receipt.
- Material/quality complaints and wrong SKU delivery due to catalog sync errors.
Account Blocking/Suspension Criteria:
- Late dispatch rate (failing to ship within 3 working days) exceeding 15% leads to account suspension.
- Multiple complaints of sending counterfeit/fake items triggers immediate ban.
Platform Bias in Disputes:
- Strongly buyer-biased in refunds, but highly opaque. Craftsvilla's practice of refunding buyers in platform "wallet credits" (excluding shipping fees) caused immense friction for both buyers and sellers, leading to massive seller migration.

KEY INSIGHT FOR SILAAI
What is the single most useful thing Silaai should borrow or avoid from this model?
- AVOID: Schedule-based payout post-shipment without delivery confirmation. Silaai must use OTP-on-delivery or buyer active confirmation before releasing funds, as shipping custom clothes across India can take over 10 days and lead to delivery disputes.
- AVOID: Refunding customers in locked wallet credits. This creates high friction and damages brand credibility.

SOURCES USED
- https://www.indiafilings.com/learn/craftsvilla-seller-registration/
- https://www.localcircles.com/a/public/post/rip-off-by-onlinee-commerce-sites-craftsvillacom-avoid-at-all-costs/8471442cy
- https://www.mouthshut.com/product-reviews/craftsvilla-reviews-925640884
""",

    "Jaypore": """ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): No (Inventory-led / Curated D2C Brand)
Who holds the funds?: Jaypore (Aditya Birla Fashion and Retail Limited)
When are funds collected? (Before work / At order / On delivery): At order
KYC & Onboarding Barriers: Strict corporate vendor onboarding: GST registration, MSME certificates, bank audits, and sample testing of products at Jaypore's warehouse.
Transaction Fee Split & Refund Policy: B2B contract margins (usually 40-50% commission). In case of returns, Jaypore absorbs the retail fee; vendor payout is deducted for defective batches.

RELEASE TRIGGERS
What triggers the escrow release?
- Vendor payout is triggered by inventory procurement invoices and contract terms (e.g., Net 30/45 days post-inventory delivery to the warehouse).
- Not triggered by individual customer purchases or delivery.
Transit Gating & Delivery Verification: B2B terms (Net 30/45). Delivery-gating does not exist at an order level.
Hold Extension Mechanism: Not applicable at order level.

AUTO-RELEASE
Is there an auto-release? (Yes / No): No
If yes, how many days after delivery?: Not applicable (supplier contract terms apply).
Transit Delay Protection: Supplier payment is tied to warehouse inventory receipt date, not customer delivery. Delays in warehouse receipt delay vendor payment.

DISPUTE HANDLING
Who decides disputes?: Jaypore's internal customer care team
What is the resolution timeline?: 7 to 10 business days for refunds
What evidence does the buyer/seller need to submit?:
- Buyer: Must email photos of damaged products showing the barcode and shipping label within 48 hours of delivery.
- Seller: Not applicable (consigned stock is pre-vetted at the warehouse).
Alteration vs. Refund Guidelines: Final Sale for customized sizes. No customer alteration or refund allowed.
Evidence Standards for Sizing/Fit: Customer must show photo of barcode and item within 48 hours for damaged items. Fit issues are pre-empted by warehouse QC measurement checks.
Return Shipping Fee Burden: Jaypore covers customer return shipping. If vendor batch fails QC, vendor pays return logistics to their facility.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes
Any coverage cap on orders (e.g. max ₹X covered)?: Not applicable (Jaypore holds all merchant risk)
What happens to the provider if the buyer disputes unfairly?:
- The artisan supplier is completely shielded from end-customer disputes and chargebacks.
- However, if a batch fails Jaypore's strict warehouse quality checks, the vendor bears the return logistics cost and the stock is sent back without payment.
Review/Rating Protection: Vendor rating is internal to Jaypore's buying team, based on reject rates and delivery SLA compliance.
Material/Fabric Loss Shield: If Jaypore provides raw materials (consignment fabric), the supplier must return unused fabric; shortages are deducted from vendor payouts.

DISPUTE NUANCES & ACCOUNT CONTROLS
Dispute Occurrence Pattern:
- Fit and sizing issues.
- Slight variation in block print colors or handloom weave textures (often disputed by customers unfamiliar with artisanal goods).
Account Blocking/Suspension Criteria:
- Reject rate during warehouse quality checks exceeding 10% on consecutive consignments leads to termination of the vendor contract.
- Delays in bulk delivery timelines.
Platform Bias in Disputes:
- Platform-centric. Jaypore determines all quality/return verdicts. Since they own or consign the inventory, they absorb customer disputes directly while enforcing strict QC on suppliers.

KEY INSIGHT FOR SILAAI
What is the single most useful thing Silaai should borrow or avoid from this model?
- BORROW: Pre-dispatch quality checks. Silaai should require tailors to upload a photo of the completed garment next to a measuring tape before handoff to the courier. This prevents fit disputes before the item is shipped.
- BORROW: Non-returnable custom-size policy. Jaypore marks custom-fit items as "Final Sale" (non-returnable) unless damaged, which protects tailors from change-of-mind return losses.

SOURCES USED
- https://www.jaypore.com/content/faq
- https://www.abfrl.com/
- https://www.jaypore.com/content/cmstermsofuse
""",

    "Glowroad": """ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): Escrow-like (Reseller model)
Who holds the funds?: Glowroad (Amazon)
When are funds collected? (Before work / At order / On delivery): At order
KYC & Onboarding Barriers: GST registration, active bank account verification (via Penny Drop), and PAN verification.
Transaction Fee Split & Refund Policy: Supplier sets transfer price; Glowroad adds reseller margin and platform fee. If refund occurs, platform fee is refunded but return shipping is debited from supplier if it is supplier-fault.

RELEASE TRIGGERS
What triggers the escrow release?
- Expiration of the 7-day customer return window after delivery.
- Settlement payouts are processed weekly (7-10 days post-delivery) directly to the supplier's bank account.
Transit Gating & Delivery Verification: Tied to 3PL API delivery scan. Payout scheduled 7-10 days after confirmed delivery.
Hold Extension Mechanism: Buyers cannot extend the 7-day return window. Once expired, payout is released.

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: 7 to 10 days post-delivery.
Nuances: Once delivery status updates via Glowroad's integrated logistics partner, the payout is queued automatically for the next weekly run.
Transit Delay Protection: If tracking is stuck, payout is held until carrier updates to delivered or declares lost. If lost, Glowroad covers supplier payout.

DISPUTE HANDLING
Who decides disputes?: Glowroad customer care
What is the resolution timeline?: 3 to 5 business days
What evidence does the buyer/seller need to submit?:
- Buyer: Selection of return reason in app (no photos required for basic returns).
- Supplier (for wrong/damaged return claims): Compulsory unboxing video of the returned package showing the shipping label/invoice clearly, followed by the item's condition from all angles. No video = claim rejected.
Alteration vs. Refund Guidelines: Returns/refunds only. No alterations.
Evidence Standards for Sizing/Fit: Dropdown return reason in app for buyer. Suppliers must provide unboxing video of the returned package showing measurement deviations to contest.
Return Shipping Fee Burden: Debited from supplier only if "supplier-fault" (wrong item, size, defect). Free for supplier if "buyer-fault".

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes
Any coverage cap on orders (e.g. max ₹X covered)?: No stated cap
What happens to the provider if the buyer disputes unfairly?:
- If the return is categorized as "buyer's fault" (size fit issues, change of mind), the supplier is not debited.
- Glowroad has a strong RTO protection policy: if a customer cancels before delivery or rejects a COD package, the supplier pays zero logistics/RTO fees.
Review/Rating Protection: Supplier rating is internal. Gold/Silver tiers protect against minor negative rating penalties.
Material/Fabric Loss Shield: None for buyer-supplied fabric.

DISPUTE NUANCES & ACCOUNT CONTROLS
Dispute Occurrence Pattern:
- High volume of COD package rejections at the doorstep (RTO).
- Resellers sharing inaccurate product details or shipping times with customers.
Account Blocking/Suspension Criteria:
- Supplier dispatch delay rate > 10% or cancellation rate > 5% leads to account warning and subsequent block.
- High rate of "supplier-fault" returns (wrong item shipped, defective products) exceeding 15% triggers suspension.
Platform Bias in Disputes:
- Buyer-biased for customer returns, but supplier-protective regarding logistics: the zero-RTO charge policy for rejected COD packages is highly supplier-friendly.

KEY INSIGHT FOR SILAAI
What is the single most useful thing Silaai should borrow or avoid from this model?
- BORROW: Compulsory unboxing videos for returned items. Silaai must require tailors to record an unboxing video of any returned garment to verify claims of customer damage or alterations.
- BORROW: Zero-RTO fee for tailors. Since COD is heavily used in India, tailors should not be penalized with shipping fees if a customer rejects a package at the door.

SOURCES USED
- https://glowroad.com/faq
- https://ecomsprint.com/glowroad-supplier-charges-and-fees/
- https://cointab.net/business/reconciliation/glowroad-reconciliation/
""",

    "Grailed": """ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): Escrow-like (Grailed Payments / PayPal)
Who holds the funds?: Grailed (via Stripe/PayPal)
When are funds collected? (Before work / At order / On delivery): At order
KYC & Onboarding Barriers: Stripe/PayPal identity verification. Stripe requires SSN/EIN or local tax IDs. PayPal requires linked verified bank account.
Transaction Fee Split & Refund Policy: 9% commission + payment processing fee (Stripe: 3.49% + $0.49; PayPal: 4.49% + fixed fee). In case of refund, Grailed commissions are refunded, but payment processor fees are not refunded (absorbed by seller).

RELEASE TRIGGERS
What triggers the escrow release?
- Delivery confirmation from the carrier (payout is released within 3 days of confirmed delivery).
- If tracking is not uploaded, funds are released 21 days after transaction completion, provided no disputes are raised.
Transit Gating & Delivery Verification: Carrier tracking integration. Payout released 3 days after carrier confirms delivery.
Hold Extension Mechanism: A buyer's dispute immediately freezes the transaction funds in escrow.

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: 3 days (for new/untrusted sellers) or immediately upon delivery confirmation (for trusted sellers).
Transit Delay Protection: If tracking is delayed, payout is held up to 21 days post-sale, after which it releases if no dispute is opened.

DISPUTE HANDLING
Who decides disputes?: Grailed support team and PayPal (if PayPal was used)
What is the resolution timeline?: 5 to 10 business days
What evidence does the buyer/seller need to submit?:
- Seller: Active tracking link, package weight receipt, detailed photos of the item's tags, wash labels, zippers, and packaging.
- Buyer: Close-up photos of areas of damage, tag comparison for authenticity, or alignment measurements against a tape.
Alteration vs. Refund Guidelines: P2P used clothing platform; returns/refunds only. No alteration services.
Evidence Standards for Sizing/Fit: Buyers must submit photos of the item laid flat with a tape measure showing width (pit-to-pit) and length (collar-to-hem) to prove size discrepancies.
Return Shipping Fee Burden: Buyer pays return shipping for standard returns. In disputes, Grailed may require the seller to pay, or issue a prepaid label if the seller is at fault.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes (Grailed Seller Protection)
Any coverage cap on orders (e.g. max ₹X covered)?: No coverage cap on eligible items (covers the full sale value).
What happens to the provider if the buyer disputes unfairly?:
- The seller is protected if they shipped to the address on the invoice and uploaded tracking within 7 days.
- If a buyer files a fraudulent chargeback, Grailed covers the seller and handles the dispute with the card issuer.
Review/Rating Protection: Sellers can appeal retaliatory feedback if they win a dispute or if the buyer is proven fraudulent.
Material/Fabric Loss Shield: No coverage for fabric/materials since it is a secondary clothing market.

DISPUTE NUANCES & ACCOUNT CONTROLS
Dispute Occurrence Pattern:
- Authenticity disputes (buyer claiming the high-end streetwear/designer item is fake).
- Sizing discrepancies and condition complaints (e.g. "gently used" vs "heavily worn").
Account Blocking/Suspension Criteria:
- Listing replica/counterfeit items (even once if flagged by automated authentication filters).
- Attempting to take transactions off-platform (detected via chat filters for keywords like "IG", "Venmo", "PayPal invoice").
Platform Bias in Disputes:
- Balanced but authentication-heavy. Grailed relies on digital authentication. If a buyer claims an item is fake, Grailed will run a secondary digital audit. If they rule it authentic, the buyer's dispute is rejected.

KEY INSIGHT FOR SILAAI
What is the single most useful thing Silaai should borrow or avoid from this model?
- BORROW: Digital authentication/verification step. Silaai should have a virtual fit-check step before shipment (e.g. tailor uploads video showing exact measurements of the garment on a mannequin) to act as a definitive authentication against fit disputes.
- AVOID: Broad off-platform transaction bans. Silaai should support communication flexibility while keeping payments strictly in escrow.

SOURCES USED
- https://www.grailed.com/about/seller-protection
- https://help.grailed.com/hc/en-us/articles/115003080774-Seller-Protection
- https://trustpilot.com/review/grailed.com
""",

    "StockX": """ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): Yes (Strict Escrow and Authentication)
Who holds the funds?: StockX
When are funds collected? (Before work / At order / On delivery): At order
KYC & Onboarding Barriers: Hyperwallet registration for payouts. Requires identity verification (KYC), tax registration, and credit card on file to charge penalties.
Transaction Fee Split & Refund Policy: 8% to 10% transaction fee (decreases with seller level) + 3% payment processing fee. If order is cancelled/rejected, seller is charged a 15% penalty fee.

RELEASE TRIGGERS
What triggers the escrow release?
- Item passing StockX's physical inspection/authentication at their facility.
- Payout is initiated immediately after verification, bypassing customer delivery confirmation.
Transit Gating & Delivery Verification: Seller ships to StockX hub within 2 days. Physical verification at the hub is the payout trigger.
Hold Extension Mechanism: Buyer cannot extend the inspection period. Once verified at the hub, payout is immediately released to the seller.

AUTO-RELEASE
Is there an auto-release? (Yes / No): No
If yes, how many days after delivery?: Not applicable (release is gated by physical verification, not delivery).
Transit Delay Protection: If the seller's package is delayed to the hub, the order is cancelled and a late penalty is applied, unless the carrier delay is documented.

DISPUTE HANDLING
Who decides disputes?: StockX authentication specialists
What is the resolution timeline?: 1 to 3 business days for inspection. Customer disputes post-delivery are decided unilaterally by StockX.
What evidence does the buyer/seller need to submit?:
- Buyer: Must submit photos of the StockX green tag attached to the item, the StockX invoice, and detailed photos of the defect within 3 days of delivery.
- Seller: Not applicable (once the item passes physical inspection at the hub, the seller is paid and their liability ends).
Alteration vs. Refund Guidelines: Deadstock (new, unworn) items only. No alterations. Customer disputes post-delivery are generally rejected unless counterfeiting is proven.
Evidence Standards for Sizing/Fit: No sizing returns are allowed as buyers are buying standard brand sizes.
Return Shipping Fee Burden: Not applicable for sellers (no returns post-verification).

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes
Any coverage cap on orders (e.g. max ₹X covered)?: No stated cap
What happens to the provider if the buyer disputes unfairly?:
- The seller is completely protected once the item passes verification. Any subsequent disputes, chargebacks, or courier damage are absorbed fully by StockX.
Review/Rating Protection: No public feedback system; all ratings are internal compliance metrics (Seller Levels).
Material/Fabric Loss Shield: Not applicable.

DISPUTE NUANCES & ACCOUNT CONTROLS
Dispute Occurrence Pattern:
- Failure to pass authentication (replicas, factory flaws).
- Minor transit damage to shoe boxes or packaging.
Account Blocking/Suspension Criteria:
- Failing authentication multiple times.
- Late shipment (failing to ship to the hub within 2 business days) results in a 15% penalty fee of the transaction value; repeated delays result in account suspension.
Platform Bias in Disputes:
- Platform-centric. StockX has total authority. Since the platform physically inspects and certifies every item, there are very few post-delivery disputes between buyers and sellers; the platform absorbs the risk of verification errors.

KEY INSIGHT FOR SILAAI
What is the single most useful thing Silaai should borrow or avoid from this model?
- BORROW: Physical hub verification for high-value orders. Silaai could establish a regional quality checking hub for ultra-high-value bespoke items (e.g., bridal wear above ₹15,000). The tailor ships to the hub, Silaai verifies the measurements, and then ships to the customer, releasing payout instantly.
- AVOID: Strict shipping deadlines for custom work. A 2-day shipping window is impossible for custom tailoring where alterations and design refinements require flexible schedules.

SOURCES USED
- https://stockx.com/help/articles/What-is-the-StockX-Seller-Program
- https://stockx.com/help/articles/How-does-payout-work-for-Sellers
- https://www.reddit.com/r/stockx/
""",

    "Vinted": """ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): Yes (Vinted Wallet)
Who holds the funds?: Vinted (via MangoPay/Adyen)
When are funds collected? (Before work / At order / On delivery): At order
KYC & Onboarding Barriers: MangoPay or Adyen verification. Requires identity documents (KYC) once transactions exceed €1,000 in volume.
Transaction Fee Split & Refund Policy: 0% seller commission. Buyer pays a "Buyer Protection" fee (3-8% of item price + €0.70). Processing fees are wrapped in the buyer protection fee. If refunded, the buyer protection fee is not refunded to the buyer.

RELEASE TRIGGERS
What triggers the escrow release?
- The buyer clicking "Everything is OK" in the app after receiving the package.
- If the buyer does not report an issue within 2 days of delivery, the payout is triggered automatically.
Transit Gating & Delivery Verification: Integrated carrier tracking. Payout is released 48 hours after carrier marks as delivered, unless buyer clicks "I have an issue".
Hold Extension Mechanism: Buyer clicking "I have an issue" suspends the auto-release indefinitely until resolved.

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: 2 days (48 hours) after the package is marked as delivered by the carrier tracking system.
Nuances: If the buyer is inactive, the platform auto-releases the payout exactly 48 hours after tracking confirms delivery.
Transit Delay Protection: If shipping is delayed, Vinted waits up to 15-21 days before marking it lost and refunding the buyer while compensating the seller (up to caps).

DISPUTE HANDLING
Who decides disputes?: Vinted Support
What is the resolution timeline?: 5 to 7 business days
What evidence does the buyer/seller need to submit?:
- Buyer: Detailed photos of the packaging, shipping label, and defects. Must report within 48 hours of delivery.
- Seller: Proof of posting (shipping receipt), photo of the item prior to packing, and measurements if sizing is disputed.
Alteration vs. Refund Guidelines: Returns/refunds only. No alterations.
Evidence Standards for Sizing/Fit: Sizing disputes require photos showing measuring tape on the garment's key dimensions.
Return Shipping Fee Burden: Buyer pays for return shipping by default unless the seller agrees to cover it.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes
Any coverage cap on orders (e.g. max ₹X covered)?: Yes, compensation for lost/damaged packages is capped based on the shipping method selected (typically up to €500 for integrated shipping).
What happens to the provider if the buyer disputes unfairly?:
- If the seller can prove the item matched the description and was shipped correctly, Vinted will release the funds.
- However, if the buyer claims an item is counterfeit and Vinted agrees, Vinted is legally required to refund the buyer, and the seller does not get the item back.
Review/Rating Protection: Mutual rating system. Retaliatory reviews can be flagged to Vinted support for removal if a dispute was resolved in the seller's favor.
Material/Fabric Loss Shield: Not applicable.

DISPUTE NUANCES & ACCOUNT CONTROLS
Dispute Occurrence Pattern:
- Counterfeit/fake brand disputes.
- "Item Not Received" claims when tracking lags.
Account Blocking/Suspension Criteria:
- Commercial selling (Vinted is strictly P2P; selling new items in bulk or operating as a professional business on a standard account is prohibited).
- Listing counterfeits or violating safety rules.
Platform Bias in Disputes:
- Heavily buyer-biased. Vinted's 48-hour return window forces quick action, but buyers are often given refunds with low proof requirements, leaving sellers without their item or money if counterfeit claims are raised.

KEY INSIGHT FOR SILAAI
What is the single most useful thing Silaai should borrow or avoid from this model?
- BORROW: 48-hour auto-release window. Vinted's 48-hour post-delivery window is highly efficient. Silaai should adopt this: buyers must flag fit/alteration issues within 48 hours of delivery, otherwise the funds release to the tailor.
- AVOID: Refunding the buyer without requiring the return of the item. This invites fraud.

SOURCES USED
- https://www.vinted.com/help/
- https://www.vinted.co.uk/help/513-our-refund-policy
- https://www.reddit.com/r/vinted/
""",

    "Depop": """ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): Escrow-like (Depop Payments)
Who holds the funds?: Depop (Stripe)
When are funds collected? (Before work / At order / On delivery): At order
KYC & Onboarding Barriers: Stripe-powered Depop Payments requires identity checks (SSN/passport/bank verification) for sellers.
Transaction Fee Split & Refund Policy: 10% commission + payment processing fee (typically 2.9% + $0.30). In refunds, Depop returns its commission, but Stripe processing fees are not returned.

RELEASE TRIGGERS
What triggers the escrow release?
- Standard release occurs 10 working days after the payment date.
- Accelerated release is triggered 2 days after the integrated shipping tracking status updates to "delivered."
Transit Gating & Delivery Verification: 10 days post-sale (without tracking) or 2 days post-delivery (with integrated tracking).
Hold Extension Mechanism: Buyer opening a "resolution case" immediately suspends the release of escrow funds.

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: 2 days (48 hours) post-delivery or 10 working days post-payment if tracking is not integrated.
Transit Delay Protection: Payout is delayed until tracking updates or 10-day backup is reached.

DISPUTE HANDLING
Who decides disputes?: Depop Support
What is the resolution timeline?: 5 to 7 days
What evidence does the buyer/seller need to submit?:
- Buyer: Must open a case within 180 days of purchase. Photos of defects, measurements, and packaging are required.
- Seller: Proof of postage showing buyer's postcode, tracking information, and photos showing the item's condition prior to shipping.
Alteration vs. Refund Guidelines: Returns/refunds only. No alterations.
Evidence Standards for Sizing/Fit: Buyer must show photo with measuring tape showing chest width and length compared to listing description.
Return Shipping Fee Burden: Buyer pays return shipping unless the item was "significantly not as described," in which case Depop may charge the seller.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes (Depop Seller Protection)
Any coverage cap on orders (e.g. max ₹X covered)?: No coverage cap for eligible sellers.
What happens to the provider if the buyer disputes unfairly?:
- Sellers are covered if they shipped via Depop's integrated label or shipped within 7 days using tracked mail to the address on the receipt.
- If a buyer files an unauthorized transaction chargeback, Depop handles it and covers the seller.
Review/Rating Protection: Support removes reviews that are retaliatory or left by buyers who lost disputes.
Material/Fabric Loss Shield: Not applicable.

DISPUTE NUANCES & ACCOUNT CONTROLS
Dispute Occurrence Pattern:
- Drop-shipping disputes (items taking weeks to arrive from overseas).
- Sizing/sizing tag discrepancies.
Account Blocking/Suspension Criteria:
- Drop-shipping listings without original photos.
- Taking transactions off-platform (e.g. sharing PayPal, Venmo, or cash links in chat).
Platform Bias in Disputes:
- Strongly buyer-biased. Depop requires sellers to provide bulletproof tracking and packaging evidence. If tracking shows "delivered" but the buyer disputes, the seller is usually protected, but other disputes (e.g. condition) favor the buyer.

KEY INSIGHT FOR SILAAI
What is the single most useful thing Silaai should borrow or avoid from this model?
- BORROW: Accelerated release upon tracking delivery. Silaai should link its payouts to 3PL logistics API: once the courier marks the package as "delivered," the tailor's payout window starts.
- AVOID: 180-day dispute window. Allowing buyers to file claims months later is catastrophic for independent tailors who cannot manage deferred financial liabilities.

SOURCES USED
- https://depophelp.zendesk.com/hc/en-gb/articles/360001790827-Seller-Protection-Policy
- https://depophelp.zendesk.com/hc/en-gb/articles/360001827248-How-payouts-work
- https://www.reddit.com/r/depop/
""",

    "Okhai": """ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): No (Direct B2B Procurement / Consignment)
Who holds the funds?: Okhai (Tata Trust / Payment Gateway Razorpay)
When are funds collected? (Before work / At order / On delivery): At order
KYC & Onboarding Barriers: Artisan Self-Help Group (SHG) registration, PAN/Aadhaar of lead artisans, and bank accounts of the SHG.
Transaction Fee Split & Refund Policy: Okhai operates as a D2C retail brand. Customer pays Razorpay gateway fees. Artisans are paid direct design/stitching wages.

RELEASE TRIGGERS
What triggers the escrow release?
- Artisan payments are triggered by product completion and handoff to Okhai's field coordinators.
- Not linked to customer order or delivery triggers.
Transit Gating & Delivery Verification: Handed over to Okhai field coordinators. Wages paid upon quality verification by the field coordinator.
Hold Extension Mechanism: Not applicable at customer order level.

AUTO-RELEASE
Is there an auto-release? (Yes / No): No
If yes, how many days after delivery?: Not applicable.
Transit Delay Protection: Artisan wages are independent of customer transit delays.

DISPUTE HANDLING
Who decides disputes?: Okhai Customer Care
What is the resolution timeline?: 5 to 7 business days for returns/exchanges.
What evidence does the buyer/seller need to submit?:
- Buyer: Must return the product in unused condition with all tags and invoice within 30 days of receipt.
- Seller: Not applicable (handled by Okhai's field coordinators).
Alteration vs. Refund Guidelines: Sells ready-to-wear. Customer returns are refunded; artisans do not alter items post-sale.
Evidence Standards for Sizing/Fit: Standard retail sizes. Returns are accepted within 30 days if unused and tags are intact.
Return Shipping Fee Burden: Okhai covers reverse shipping for customer returns.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes
Any coverage cap on orders (e.g. max ₹X covered)?: Not applicable (Okhai holds all inventory risk).
What happens to the provider if the buyer disputes unfairly?:
- Artisans are 100% shielded. Okhai manages all returns, customer chargebacks, and refund losses.
Review/Rating Protection: Artisan groups are rated internally on delivery time and craft consistency.
Material/Fabric Loss Shield: Okhai provides fabrics to artisans. Any fabric wastage beyond the 5% margin is deducted from the artisan group's payout.

DISPUTE NUANCES & ACCOUNT CONTROLS
Dispute Occurrence Pattern:
- Minor variations in hand block printing, stitching, or embroidery (which customers sometimes mistake for defects).
- Sizing discrepancies.
Account Blocking/Suspension Criteria:
- Consistently failing to meet design and quality specifications set by Okhai designers leads to termination of the artisan group's partnership.
Platform Bias in Disputes:
- Platform-centric. Okhai handles end-customer complaints unilaterally and absorbs the financial loss of returns, shielding the rural artisan.

KEY INSIGHT FOR SILAAI
What is the single most useful thing Silaai should borrow or avoid from this model?
- BORROW: The aggregator model for raw materials. Okhai supplies standardized block-printed fabrics and patterns to artisans. Silaai can supply verified fabrics/linings to tailors to eliminate the risk of "cheap fabric quality" disputes.
- AVOID: Direct B2B inventory buyback. If Silaai has to buy and stock custom clothes, it loses its platform scalability and faces huge inventory risk.

SOURCES USED
- https://okhai.org/pages/refund-and-cancellation-policy
- https://razorpay.com/blog/okhai-empowering-artisans-through-e-commerce/
- https://www.tata.com/newsroom/business/okhai-online-marketplace
""",

    "Meesho": """ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): Escrow-like
Who holds the funds?: Meesho
When are funds collected? (Before work / At order / On delivery): At order
KYC & Onboarding Barriers: GSTIN, bank account, and PAN verification.
Transaction Fee Split & Refund Policy: 0% commission platform, but suppliers pay for shipping and payment gateway costs on returns.

RELEASE TRIGGERS
What triggers the escrow release?
- Expiration of the 7-day customer return window after delivery.
- Payout is released on the 15th day from order delivery, deducting returns and cancellations.
Transit Gating & Delivery Verification: Delivered status from 3PL API. Payout released on the 15th day from order delivery.
Hold Extension Mechanism: Buyers cannot extend the return window (7 days).

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: 15 days post-delivery.
Nuances: Settlement is processed weekly in batches.
Transit Delay Protection: Payout is suspended if tracking is stuck; if carrier loses the item, Meesho reimburses the supplier.

DISPUTE HANDLING
Who decides disputes?: Meesho Support Panel
What is the resolution timeline?: 5 to 7 days
What evidence does the buyer/seller need to submit?:
- Buyer: Simple reason selection in app (no photos required for returns).
- Supplier (for wrong/damaged returns): Compulsory unboxing video showing the outer return label (AWB) and the actual item inside the bag.
Alteration vs. Refund Guidelines: Returns/refunds only. No alterations.
Evidence Standards for Sizing/Fit: Simple return reason select. Supplier must upload unboxing video of returns with tape measure showing correct sizing to claim reimbursement.
Return Shipping Fee Burden: Supplier is debited for return shipping on customer returns, which is a major supplier pain point.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Partial
Any coverage cap on orders (e.g. max ₹X covered)?: No stated cap
What happens to the provider if the buyer disputes unfairly?:
- Meesho has high buyer returns. If a buyer returns a worn/damaged item, the supplier is penalized unless they file a claim with an unboxing video.
- Meesho charges sellers return shipping fees for customer returns, which makes returns highly expensive for sellers.
Review/Rating Protection: Sellers cannot remove negative reviews; low rating leads to automatic search demotion or blocking.
Material/Fabric Loss Shield: None.

DISPUTE NUANCES & ACCOUNT CONTROLS
Dispute Occurrence Pattern:
- Customers returning completely different items (e.g. brick instead of phone, old rags instead of dress) to get a refund.
- High rate of RTO (30-40% for COD orders) where customers reject delivery.
Account Blocking/Suspension Criteria:
- Low product rating (<3.0 stars) over consecutive weeks.
- High seller-fault cancellation rate or sending wrong items repeatedly.
Platform Bias in Disputes:
- Heavily buyer-biased. Meesho has a no-questions-asked return policy. Suppliers face heavy logistics return costs and must constantly defend themselves using video evidence of returns to avoid financial loss.

KEY INSIGHT FOR SILAAI
What is the single most useful thing Silaai should borrow or avoid from this model?
- AVOID: "No-questions-asked" returns on custom clothes. Custom apparel cannot be resold; allowing buyers to return custom garments without high proof of tailor error would bankrupt tailors.
- AVOID: Charging tailors for return shipping if the customer simply changed their mind.

SOURCES USED
- https://supplier.meesho.com/
- https://www.quora.com/Meesho-seller-policies
- https://www.reddit.com/r/Meesho/
"""
}

def main():
    output_dir = "c:/Users/yasha/Desktop/scout/outputs/competitor_research"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Overwriting reports in: {output_dir}")
    
    for company, content in REPORTS.items():
        file_path = os.path.join(output_dir, f"{company}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"  - Written {company}.txt")
        
    print("Done writing all updated reports!")

if __name__ == "__main__":
    main()
