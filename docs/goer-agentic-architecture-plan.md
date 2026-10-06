# Goer Agentic Architecture Plan

## Goal

Build Goer as LocalGo's conversational ordering interface. A customer should be able to discover products, configure them, manage a cart, confirm checkout, pay, and track an order through the chatbot.

The language model interprets requests and chooses tools. Backend code remains responsible for catalog data, prices, cart state, validation, payment state, and order state.

## Current Progress

The first discovery workflow is working with Groq:

1. The user sends a message to Goer.
2. Groq chooses a local tool.
3. The backend executes that tool against `menu.json`.
4. Tool results are sent back to Groq.
5. Goer presents a natural-language answer.

Implemented tools:

- `search_menu(product_name, merchant_id=None)` searches product names, optionally within one merchant.
- `get_menu(merchant_id)` retrieves a merchant's products.

The terminal prototype also keeps conversational history, so follow-ups such as “Which one is cheapest?” and “Do they have falafel?” can use earlier merchant and product context.

## Phase 1: Fix Context Management

The current conversation saves every raw tool result. A complete merchant menu can contain dozens of product dictionaries, so repeated requests eventually exceed Groq's token-per-minute limit.

### Required changes

- Return compact product records from discovery tools.
- Add a `limit` parameter to tools that may return many products.
- Add optional category filtering to merchant browsing.
- Keep user messages and final assistant answers in conversation history.
- Remove or summarize completed raw tool requests and tool results.
- Keep enough recent conversational context for references such as “they,” “that one,” and “the cheapest one.”
- Set a bounded number of model/tool iterations for each user message.
- Keep a request timeout and handle provider errors without terminating the whole chatbot.

### Target browsing contract

`get_menu` should eventually accept:

- `merchant_id`: required merchant identifier.
- `category`: optional category filter.
- `limit`: maximum number of returned products.

For a request such as “Show me Château Kabab desserts,” the backend should return only a small set of Château Kabab dessert products instead of the entire catalog.

## Phase 2: Complete Menu Discovery

Add narrowly scoped tools for reliable product retrieval.

### `list_categories`

Input:

- `merchant_id`

Output:

- The categories offered by that merchant.

Use this when the user wants to browse but has not chosen a type of food.

### Improved `get_menu`

Input:

- `merchant_id`
- Optional `category`
- Bounded `limit`

Output:

- Compact product summaries containing stable IDs, names, categories, prices, and short descriptions.

### Improved `search_menu`

Input:

- Search phrase or product name
- Optional `merchant_id`
- Bounded `limit`

Output:

- Relevant compact product summaries.

Improve matching only when tests show it is needed. Possible later improvements include descriptions, aliases, categories, typo handling, and ranked results.

### `get_product`

Input:

- Exact `product_id`

Output:

- One complete product record, including price and customization requirements.

This tool is required before cart actions. Product names may be similar, while product IDs are stable and unambiguous.

## Phase 3: Restore Product Customizations

The current exported JSON contains empty `option_groups` because the original menu-option mappings are missing.

Before Goer can create valid orders, restore and verify:

- Required sizes
- Protein choices
- Side selections
- Drink selections
- Add-ons
- Maximum and minimum selection counts
- Price changes for each choice
- Whether free-text notes are permitted

Goer must never guess required options. If required choices are missing, it should ask the customer before adding the item.

## Phase 4: Build Server-Owned Cart State

The cart must be authoritative backend state, not model memory. A model message can express intent, but only backend services may change the cart.

Each cart line should contain:

- A unique `cart_line_id`
- Merchant ID
- Product ID
- Quantity
- Selected option IDs
- Notes
- Server-calculated unit price
- Server-calculated line total

Use one merchant per cart for the first version. If a user requests a product from another merchant, ask whether to keep the existing cart or begin a separate order.

## Phase 5: Add Cart Tools

### `add_to_cart`

Input:

- Exact `product_id`
- Quantity
- Selected option IDs
- Optional notes

The backend validates that the product exists, belongs to the selected merchant, and has all required choices.

### `view_cart`

Returns current cart lines and backend-calculated totals.

### `change_quantity`

Input:

- Exact `cart_line_id`
- New quantity

Use the line ID so two differently configured versions of the same product remain distinguishable.

### `remove_from_cart`

Input:

- Exact `cart_line_id`

### `clear_cart`

Requires clear user intent before removing every line.

## Phase 6: Introduce Specialist Agents

Keep one user-facing Goer conversation. Internally, use bounded specialists with different instructions and tools.

### Coordinator

- Interprets the user's intent.
- Selects the appropriate specialist.
- Preserves a coherent user-facing conversation.
- Cannot bypass backend validation or claim an operation succeeded without a successful tool result.

### Discovery specialist

- Uses menu search, category, and product-detail tools.
- Recommends only products returned by tools.
- Never invents products, availability, prices, or dietary facts.

### Cart specialist

- Uses cart tools.
- Resolves quantities, product IDs, option IDs, and cart-line references.
- Cannot determine prices itself.

### Checkout specialist

- Collects missing delivery information.
- Requests a server-calculated quote.
- Presents the final confirmation.
- Cannot charge or place an order without explicit customer confirmation.

### Order-support specialist

- Retrieves active and past orders.
- Explains fulfillment and delivery status.
- Prepares supported cancellation actions.

Specialists should initially be logical prompt/tool configurations inside FastAPI, not separate deployed services.

## Phase 7: Build Checkout

### Address selection

- Retrieve the customer's saved addresses.
- Allow an address to be selected or added through chat UI.
- Geocode and validate the delivery zone on the backend.

### Server quote

Create an immutable quote containing:

- Product and customization snapshots
- Quantities
- Subtotal
- Taxes
- Delivery fee
- Tip
- Total
- Currency
- Expiration time
- Cart revision

All prices and totals must be calculated by backend code using authoritative catalog data.

### Explicit confirmation

Display the complete quote in chat. The customer must explicitly confirm that exact quote before payment and order creation.

### Payment

- Create or reuse one Stripe payment attempt per checkout attempt.
- Use stable idempotency keys to prevent duplicate charges.
- Use native payment UI for card details and bank authentication.
- Verify successful payment on the backend through signed provider events and reconciliation.
- Never treat a client-only success response as final payment authority.

### Canonical order creation

Use one order ID across payment, order history, merchant fulfillment, driver dispatch, chat, and tracking.

## Phase 8: Merchant Fulfillment and Driver Dispatch

Represent restaurant receipt explicitly. Driver acceptance is not proof that the merchant received or accepted the food order.

Define how each merchant receives and acknowledges an order:

- Merchant dashboard
- Operations workflow
- Merchant API
- Another explicit fulfillment integration

Keep payment, merchant fulfillment, and delivery as separate state dimensions.

## Phase 9: Order Tracking and Support

Add tools such as:

- `get_active_orders`
- `get_order_status`
- `get_order_history`
- `get_order_details`
- `get_cancellation_options`
- `stage_cancellation`

Order status should distinguish:

- Payment processing
- Awaiting merchant acknowledgment
- Merchant accepted or rejected
- Finding a driver
- Driver assigned
- Picked up
- Delivered
- Cancellation or refund state

## Phase 10: Connect Goer to the Mobile App

Replace the terminal `input()` loop with authenticated FastAPI conversation endpoints.

The React Native chat should render structured cards for:

- Merchant selection
- Product results
- Categories
- Product options
- Cart summaries
- Address selection and entry
- Quotes
- Payment launch
- Order confirmation
- Tracking status

Native payment or authentication screens may open over the conversation and return to it. Customers should not type sensitive payment data into chat messages.

## Phase 11: Persistence and Recovery

Persist:

- Conversations
- User and assistant messages
- Agent runs
- Tool calls and results
- Selected merchant
- Carts and cart revisions
- Quotes
- Checkout attempts
- Orders and order events

If a network request fails after a mutation, recover the recorded result instead of running the mutation again.

## Phase 12: Evaluation and Rollout

Test behavior using representative scenarios, including:

- Similar product names
- Typos
- Merchant omitted
- Merchant changed mid-conversation
- Required customizations
- Two versions of the same product
- Unknown or unavailable products
- Empty search results
- Stale prices
- Duplicate tool calls
- Duplicate confirmation taps
- Lost network responses
- Payment succeeds while the client response is lost
- Merchant rejection
- Driver-notification failure
- Unauthorized order IDs
- Prompt injection inside catalog descriptions

Measure:

- Task-completion rate
- Incorrect tool selection
- Product-resolution accuracy
- Checkout failures
- Duplicate prevention
- Response latency
- Tokens and model cost per completed order
- Cart abandonment

Roll out behind a feature flag and begin with a limited test cohort.

## Immediate Implementation Order

1. Fix context management and trim raw tool history.
2. Add category and limit support to menu browsing.
3. Add `list_categories`.
4. Add `get_product` using exact product IDs.
5. Restore and verify customization data.
6. Build backend-owned cart state.
7. Add and validate cart tools.
8. Introduce discovery and cart specialists behind one Goer coordinator.
9. Build server quotes, confirmation, and payments.
10. Add merchant fulfillment, driver dispatch, and order tracking.
11. Connect structured Goer events to the React Native chat UI.
12. Add persistence, recovery, evaluations, monitoring, and staged rollout.

The next implementation task is context compaction plus bounded category browsing. Do not begin cart mutations until product details and required customization options are reliable.
