import os

REPORTS = {
    "Etsy": """ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): Escrow-like (Etsy Payments)
Who holds the funds?: Etsy
When are funds collected? (Before work / At order / On delivery): At order

Etsy Payments collects funds from the buyer at checkout. Etsy holds these funds and releases them to the seller's payment account on a scheduled payout basis. For new sellers, funds may be placed in a temporary payment reserve.

RELEASE TRIGGERS
What triggers the escrow release?
- Shipment dispatch (tracking status shows "in transit") or scheduled payout interval (daily, weekly, bi-weekly, monthly) after a holding period.
- For shops with a payment reserve, a percentage of funds (e.g., 75%) is held for up to 45 days unless valid tracking is uploaded, which triggers immediate release.

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: Not delivery-gated (typically 3-7 days post-shipment or up to 45 days if on reserve).
Nuances: For standard sellers, funds become available for deposit next business day after shipment. For reserve accounts, they release as soon as tracking confirms the carrier has scanned the package.

DISPUTE HANDLING
Who decides disputes?: Etsy support specialists
What is the resolution timeline?: 2 to 5 business days once escalated
What evidence does the buyer/seller need to submit?:
- Seller: Proof of shipping (postal receipt, tracking showing delivery to buyer's address), photos of custom dimensions, material verification.
- Buyer: Photos showing item condition, sizing discrepancies measured against a ruler, or custom details mismatches.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes (Etsy Purchase Protection Program)
Any coverage cap on orders (e.g. max ₹X covered)?: Yes, covers qualifying orders up to $250 USD.
What happens to the provider if the buyer disputes unfairly?:
- If the seller meets eligibility criteria (tracking, on-time shipping), Etsy covers the cost of the refund from its own funds and does not penalize the seller.
- Under shipping delays or transit damage, Etsy absorbs the refund cost up to the cap if the seller used Etsy shipping labels.

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

Craftsvilla collects the payment at checkout and holds it. After sale completion, the platform deducts a high commission rate (20% up to 45% based on category) plus service tax/GST and remits the net amount to the seller.

RELEASE TRIGGERS
What triggers the escrow release?
- Seller ships the item (normally within 3 working days of order confirmation) and uploads valid tracking.
- The payout clock starts from dispatch, releasing the funds within 15 working days of shipping.

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: Not delivery-gated (15 working days post-shipment).
Nuances: Craftsvilla releases the funds on a schedule post-shipment regardless of whether the buyer has confirmed delivery.

DISPUTE HANDLING
Who decides disputes?: Craftsvilla customer care team
What is the resolution timeline?: 7 to 10 working days, though historically prone to severe delays
What evidence does the buyer/seller need to submit?:
- Buyer: Must email photos of damaged or incorrect items within 7 days of delivery with the order number.
- Seller: Must provide proof of dispatch and courier manifests to dispute tracking claims.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): No
Any coverage cap on orders (e.g. max ₹X covered)?: No stated cap
What happens to the provider if the buyer disputes unfairly?:
- Sellers are highly exposed. Craftsvilla frequently refunds buyers (often only as non-refundable wallet credits) and clawbacks payouts from the seller's account.
- Non-compliance with the 3-day shipping rule removes any seller defense.

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

Jaypore operates as a curated retail brand under ABFRL. It procures products from artisans/vendors upfront or on consignment, runs 4-5 layers of quality checks, and sells directly. Artisans are paid as suppliers on B2B contractual terms (e.g. Net 30/45).

RELEASE TRIGGERS
What triggers the escrow release?
- Vendor payout is triggered by inventory procurement invoices and contract terms (e.g., Net 30/45 days post-inventory delivery to the warehouse).
- Not triggered by individual customer purchases or delivery.

AUTO-RELEASE
Is there an auto-release? (Yes / No): No
If yes, how many days after delivery?: Not applicable (supplier contract terms apply).

DISPUTE HANDLING
Who decides disputes?: Jaypore's internal customer care team
What is the resolution timeline?: 7 to 10 business days for refunds
What evidence does the buyer/seller need to submit?:
- Buyer: Must email photos of damaged products showing the barcode and shipping label within 48 hours of delivery.
- Seller: Not applicable (consigned stock is pre-vetted at the warehouse).

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes
Any coverage cap on orders (e.g. max ₹X covered)?: Not applicable (Jaypore holds all merchant risk)
What happens to the provider if the buyer disputes unfairly?:
- The artisan supplier is completely shielded from end-customer disputes and chargebacks.
- However, if a batch fails Jaypore's strict warehouse quality checks, the vendor bears the return logistics cost and the stock is sent back without payment.

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

Glowroad collects full payment at checkout. The reseller markets the items on social media (WhatsApp/FB) but never touches the inventory or cash. Glowroad coordinates the shipping, collects the money, and pays the manufacturer/supplier.

RELEASE TRIGGERS
What triggers the escrow release?
- Expiration of the 7-day customer return window after delivery.
- Settlement payouts are processed weekly (7-10 days post-delivery) directly to the supplier's bank account.

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: 7 to 10 days post-delivery.
Nuances: Once delivery status updates via Glowroad's integrated logistics partner, the payout is queued automatically for the next weekly run.

DISPUTE HANDLING
Who decides disputes?: Glowroad customer care
What is the resolution timeline?: 3 to 5 business days
What evidence does the buyer/seller need to submit?:
- Buyer: Selection of return reason in app (no photos required for basic returns).
- Supplier (for wrong/damaged return claims): Compulsory unboxing video of the returned package showing the shipping label/invoice clearly, followed by the item's condition from all angles. No video = claim rejected.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes
Any coverage cap on orders (e.g. max ₹X covered)?: No stated cap
What happens to the provider if the buyer disputes unfairly?:
- If the return is categorized as "buyer's fault" (size fit issues, change of mind), the supplier is not debited.
- Glowroad has a strong RTO protection policy: if a customer cancels before delivery or rejects a COD package, the supplier pays zero logistics/RTO fees.

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

Grailed collects buyer payments at checkout and holds them. Funds are released to the seller's Stripe/PayPal account once delivery is confirmed. New sellers have a 3-day holding period post-delivery.

RELEASE TRIGGERS
What triggers the escrow release?
- Delivery confirmation from the carrier (payout is released within 3 days of confirmed delivery).
- If tracking is not uploaded, funds are released 21 days after transaction completion, provided no disputes are raised.

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: 3 days (for new/untrusted sellers) or immediately upon delivery confirmation (for trusted sellers).

DISPUTE HANDLING
Who decides disputes?: Grailed support team and PayPal (if PayPal was used)
What is the resolution timeline?: 5 to 10 business days
What evidence does the buyer/seller need to submit?:
- Seller: Active tracking link, package weight receipt, detailed photos of the item's tags, wash labels, zippers, and packaging.
- Buyer: Close-up photos of areas of damage, tag comparison for authenticity, or alignment measurements against a tape.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes (Grailed Seller Protection)
Any coverage cap on orders (e.g. max ₹X covered)?: No coverage cap on eligible items (covers the full sale value).
What happens to the provider if the buyer disputes unfairly?:
- The seller is protected if they shipped to the address on the invoice and uploaded tracking within 7 days.
- If a buyer files a fraudulent chargeback, Grailed covers the seller and handles the dispute with the card issuer.

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

StockX collects payment at checkout. The seller is required to ship the item to a StockX Authentication Center within 2 business days. The funds are held by StockX until the item is verified as authentic and in deadstock condition.

RELEASE TRIGGERS
What triggers the escrow release?
- Item passing StockX's physical inspection/authentication at their facility.
- Payout is initiated immediately after verification, bypassing customer delivery confirmation.

AUTO-RELEASE
Is there an auto-release? (Yes / No): No
If yes, how many days after delivery?: Not applicable (release is gated by physical verification, not delivery).

DISPUTE HANDLING
Who decides disputes?: StockX authentication specialists
What is the resolution timeline?: 1 to 3 business days for inspection. Customer disputes post-delivery are decided unilaterally by StockX.
What evidence does the buyer/seller need to submit?:
- Buyer: Must submit photos of the StockX green tag attached to the item, the StockX invoice, and detailed photos of the defect within 3 days of delivery.
- Seller: Not applicable (once the item passes physical inspection at the hub, the seller is paid and their liability ends).

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes
Any coverage cap on orders (e.g. max ₹X covered)?: No stated cap
What happens to the provider if the buyer disputes unfairly?:
- The seller is completely protected once the item passes verification. Any subsequent disputes, chargebacks, or courier damage are absorbed fully by StockX.

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

Vinted collects buyer payments at checkout and holds them. Funds are reflected as "pending" in the seller's Vinted Wallet. Once the transaction completes, the balance becomes available for withdrawal.

RELEASE TRIGGERS
What triggers the escrow release?
- The buyer clicking "Everything is OK" in the app after receiving the package.
- If the buyer does not report an issue within 2 days of delivery, the payout is triggered automatically.

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: 2 days (48 hours) after the package is marked as delivered by the carrier tracking system.

DISPUTE HANDLING
Who decides disputes?: Vinted Support
What is the resolution timeline?: 5 to 7 business days
What evidence does the buyer/seller need to submit?:
- Buyer: Detailed photos of the packaging, shipping label, and defects. Must report within 48 hours of delivery.
- Seller: Proof of posting (shipping receipt), photo of the item prior to packing, and measurements if sizing is disputed.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes
Any coverage cap on orders (e.g. max ₹X covered)?: Yes, compensation for lost/damaged packages is capped based on the shipping method selected (typically up to €500 for integrated shipping).
What happens to the provider if the buyer disputes unfairly?:
- If the seller can prove the item matched the description and was shipped correctly, Vinted will release the funds.
- However, if the buyer claims an item is counterfeit and Vinted agrees, Vinted is legally required to refund the buyer, and the seller does not get the item back.

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

Depop collections payment from the buyer at checkout. The funds are held in the seller's Depop balance. The payout is processed to the seller's bank account after a short clearing period.

RELEASE TRIGGERS
What triggers the escrow release?
- Standard release occurs 10 working days after the payment date.
- Accelerated release is triggered 2 days after the integrated shipping tracking status updates to "delivered."

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: 2 days (48 hours) post-delivery or 10 working days post-payment if tracking is not integrated.

DISPUTE HANDLING
Who decides disputes?: Depop Support
What is the resolution timeline?: 5 to 7 days
What evidence does the buyer/seller need to submit?:
- Buyer: Must open a case within 180 days of purchase. Photos of defects, measurements, and packaging are required.
- Seller: Proof of postage showing buyer's postcode, tracking information, and photos showing the item's condition prior to shipping.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes (Depop Seller Protection)
Any coverage cap on orders (e.g. max ₹X covered)?: No coverage cap for eligible sellers.
What happens to the provider if the buyer disputes unfairly?:
- Sellers are covered if they shipped via Depop's integrated label or shipped within 7 days using tracked mail to the address on the receipt.
- If a buyer files an unauthorized transaction chargeback, Depop handles it and covers the seller.

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

Okhai is a D2C retail brand that works with over 25,000 rural women artisans. It buys products directly from artisan self-help groups, conducts quality audits, and sells them. Artisans are paid directly for their labor and products upon delivery/procurement.

RELEASE TRIGGERS
What triggers the escrow release?
- Artisan payments are triggered by product completion and handoff to Okhai's field coordinators.
- Not linked to customer order or delivery triggers.

AUTO-RELEASE
Is there an auto-release? (Yes / No): No
If yes, how many days after delivery?: Not applicable.

DISPUTE HANDLING
Who decides disputes?: Okhai Customer Care
What is the resolution timeline?: 5 to 7 business days for returns/exchanges.
What evidence does the buyer/seller need to submit?:
- Buyer: Must return the product in unused condition with all tags and invoice within 30 days of receipt.
- Seller: Not applicable (handled by Okhai's field coordinators).

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Yes
Any coverage cap on orders (e.g. max ₹X covered)?: Not applicable (Okhai holds all inventory risk).
What happens to the provider if the buyer disputes unfairly?:
- Artisans are 100% shielded. Okhai manages all returns, customer chargebacks, and refund losses.

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

Meesho collects buyer payments at checkout (prepaid) or upon delivery (COD). Funds are held by Meesho. Payouts are made to suppliers (wholesalers/manufacturers) on a weekly settlement cycle.

RELEASE TRIGGERS
What triggers the escrow release?
- Expiration of the 7-day customer return window after delivery.
- Payout is released on the 15th day from order delivery, deducting returns and cancellations.

AUTO-RELEASE
Is there an auto-release? (Yes / No): Yes
If yes, how many days after delivery?: 15 days post-delivery.

DISPUTE HANDLING
Who decides disputes?: Meesho Support Panel
What is the resolution timeline?: 5 to 7 days
What evidence does the buyer/seller need to submit?:
- Buyer: Simple reason selection in app (no photos required for returns).
- Supplier (for wrong/damaged returns): Compulsory unboxing video showing the outer return label (AWB) and the actual item inside the bag.

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): Partial
Any coverage cap on orders (e.g. max ₹X covered)?: No stated cap
What happens to the provider if the buyer disputes unfairly?:
- Meesho has high buyer returns. If a buyer returns a worn/damaged item, the supplier is penalized unless they file a claim with an unboxing video.
- Meesho charges sellers return shipping fees for customer returns, which makes returns highly expensive for sellers.

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
