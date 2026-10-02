# EAT_HACK Project Idea — Need-State Assortment Optimiser

## Working idea

A retailer chooses a product category (e.g. protein bars), shelf size, and optionally a retail context.
The tool recommends a **diverse assortment of products that covers distinct consumer need states**, rather than simply selecting the most popular products.

Core question:

> Which combination of products gives a retailer the best coverage of different consumer needs, while avoiding redundant products that appeal to the same people for the same reasons?

## Track fit

**Track 2 — Retail Futures**

Relevant challenge themes:
- Finding products people want that nobody is making yet.
- Understanding which products should be stocked or promoted in different retail contexts.
- Using trends, behaviour and external signals to generate, test or validate future products.
- Helping a retailer or brand decide what to do next, and why.

## User

Primary user:
- Retail buyer
- Category manager
- Challenger brand / product team

Example user question:

> “I have five shelf slots for protein bars. Which five products should I stock so that I cover the widest range of consumer needs?”

## Core workflow

1. User selects a category such as **protein bars**
2. Product dataset identifies the current market/product space
3. Behavioural evidence identifies recurring **need states**
4. Product attributes are mapped to those need states
5. Trend signals add momentum / emerging-interest information
6. Optimisation chooses a small assortment that:
   - maximises need-state coverage
   - rewards trend relevance
   - rewards strong product evidence
   - penalises redundancy
7. Tool explains **why each product has a place in the assortment**

## Behavioural layer

### Prefer need states over demographic stereotypes

Instead of defining personas manually as:
- “gym bros”
- “Pilates girls”
- “vegans”

derive behavioural clusters such as:

- **Performance optimisation**
  - high protein
  - low sugar
  - high protein-per-calorie
  - macro tracking

- **Convenience / meal replacement**
  - filling
  - portable
  - breakfast substitute
  - “no time”

- **Plant-based / dietary**
  - vegan
  - dairy-free
  - short ingredient list

- **Indulgence / treat**
  - chocolate
  - texture
  - flavour
  - dessert-like

- **Wellness / light snack**
  - lower calorie
  - low sugar
  - “clean” ingredients

- **Value**
  - price
  - price-per-gram protein
  - multipack value

### Persona layer for demo

The UI can convert clusters into human-readable personas, e.g.:

**“Macro Max”**
- optimises protein-per-calorie
- prioritises low sugar
- less sensitive to indulgent branding

**“On-the-Go Olivia”**
- prioritises convenience and satiety
- willing to accept more calories for meal replacement
- values portability

These persona names are **presentation labels generated from behavioural clusters**, not the source of the clusters.

## Possible modelling approach

### Step 1 — derive need states
Possible approaches:
- sentence embeddings of reviews/comments
- topic modelling
- clustering
- keyword / attribute extraction
- LLM-assisted labelling of clusters after the clusters are created

### Step 2 — map products to need states
Each product gets a score for each need state using:
- nutrition
- ingredients
- claims/labels
- price
- review-derived features
- product descriptions

### Step 3 — assortment optimisation

Conceptual objective:

**Assortment utility = need-state coverage + trend relevance + product quality - redundancy**

Potential simple implementation:
- greedy optimisation
- maximum coverage problem
- diversity-aware ranking
- cosine-similarity penalty between selected products

## Data catalogue

### 1. Open Food Facts
**Purpose:** product landscape / attributes

Potential fields:
- product name
- brand
- category
- ingredients
- nutrition
- labels
- allergens
- vegan / vegetarian indicators
- packaging
- Nutri-Score

Use for:
- defining product features
- comparing products
- measuring assortment redundancy
- mapping products to need states

Hackathon approach:
- query only one category / subset
- do not download the full database

### 2. Consumer reviews
Potential sources:
- Amazon Grocery review datasets
- Kaggle review datasets with clear provenance
- other public product-review datasets

Potential fields:
- product ID
- rating
- review text
- timestamp
- helpfulness
- product metadata

Use for:
- extracting pain points
- identifying product attributes consumers care about
- deriving behavioural / preference clusters

Hackathon approach:
- load a filtered category or sample only
- use perhaps hundreds or a few thousand reviews, not millions

### 3. Reddit / public discussion data
**Purpose:** rich explanations of consumer motivations

Potential signals:
- “too sweet”
- “good macros”
- “keeps me full”
- “expensive”
- “vegan”
- “easy breakfast”
- “texture is awful”

Use for:
- discovering need-state vocabulary
- qualitative validation of clusters
- generating hypotheses

Important:
- do not rely on uncontrolled scraping
- follow Reddit API / platform terms
- treat Reddit users as a non-representative, self-selecting sample
- better as a supplementary behavioural signal than the sole data source

### 4. Google Trends
**Purpose:** cultural / demand momentum

Google Trends shows **aggregated search interest over time and geography**.

Possible concepts:
- high protein
- protein snacks
- vegan protein
- low sugar
- meal replacement
- gut health
- pistachio
- matcha

Use for:
- adding a trend-growth / momentum score
- identifying rising consumer needs or flavours

Important:
- Trends measures search interest, not purchases
- use it as a supporting signal, not ground truth

### 5. dunnhumby / basket datasets
**Purpose:** observed retail purchasing behaviour

Potential fields:
- household/customer ID
- transaction
- product
- basket
- time
- promotion
- repeat purchase

Use for:
- product co-purchase patterns
- repeat purchase
- behavioural segmentation
- validating whether stated/review preferences align with purchases

Hackathon approach:
- use a small filtered subset if feasible
- likely optional for MVP

### 6. Kaggle
**Purpose:** dataset discovery

Treat Kaggle as a **hosting/discovery platform**, not as proof that a dataset is high quality.

Check:
- original source
- real vs synthetic
- licence
- data dictionary
- date
- unit of observation
- category coverage

Potentially useful for:
- review data
- retail basket data
- consumer survey data
- product metadata

## MVP data strategy

Minimum viable version:

**Open Food Facts**
+
**consumer review dataset**
+
**Google Trends**

This gives:

**what exists**
+
**why consumers care**
+
**what is gaining momentum**

Optional fourth source:

**basket / transaction data**
to add observed purchase behaviour.

## Managing huge datasets

Do **not** download everything.

Use:
- API filters
- category filtering
- parquet column selection
- SQL / DuckDB
- sampling
- date filtering
- only required columns

Example:
- “protein bars” only
- UK products only if possible
- 500–5,000 relevant reviews
- selected Google Trends terms

The demo needs a convincing working slice, not the entire global market.

## Demo concept

Input:
- Category: Protein bars
- Shelf slots: 5
- Optional context: London convenience store

Output:
1. Performance bar
2. Vegan / plant-based bar
3. Indulgent protein treat
4. Meal-replacement bar
5. Value bar

For each selected product:
- matched need states
- relevant consumer quotes / review themes
- product attributes
- trend signal

Comparison:
- naive assortment: lower need-state coverage
- optimised assortment: higher need-state coverage

## Key caveats

- review and Reddit users are not representative of the full population
- search interest is not purchase intent
- product availability / price may be incomplete
- true retailer transaction data would improve validation
- need-state clusters should be validated against real purchase outcomes before production deployment
- recommendations should support, not replace, buyer judgement

## Immediate next steps

- [ ] Find a small, accessible protein-bar product dataset / Open Food Facts query
- [ ] Find a usable review dataset with clear provenance
- [ ] Test Google Trends access
- [ ] Decide whether Reddit is necessary for MVP
- [ ] Define 4–6 preliminary need states
- [ ] Prototype product-to-need-state scoring
- [ ] Prototype diversity / coverage optimisation
- [ ] Sketch Streamlit demo
