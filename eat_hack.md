# Pop-up Pick for RGC: Build Plan

Oct 3, 2026 · @Maks

## The tool

Pop-up Pick is a new planning module for RGC's RGC-first pop-ups. It tells RGC which events to pop up at, which 4 to 5 client brands to bring, and what to sample, and it gives every client brand an event profile showing where its products win.

**Why RGC needs it.** Every pop-up costs staff time and free product from clients, and pays back in [WatchHumans](https://watchhumans.com/) sign-ups, reviews and publicity. WatchHumans already partners with run clubs and other communities to put products in front of people in person. Today the choice of event and lineup is judgement; this tool makes it a forecast RGC can check afterwards.

**It works both ways.**

- **Events to brands:** pick an event, get the best lineup, the products and quantities to bring, the best time slot, and the reasons.
- **Brands to events:** pick a client brand, get its event profile (event types, moments and audiences where it wins, and where it doesn't) and its best upcoming events.

**The headline number** is qualified reviews per pop-up: WatchHumans reviews from people in each brand's target audience. One figure captures what RGC gains (sign-ups and data) and what the client gains (honest feedback from the right people).

**Built today** on synthetic WatchHumans data, real upcoming London events and public location data. RGC's real data replaces the synthetic tables without changing the model.

## Impact metric

The north-star metric is qualified reviews per pop-up (QRP): WatchHumans reviews completed at a pop-up, or within 7 days of it, by people in the reviewed brand's target segment.

```latex
\text{QRP}(e, L) = \sum_{b \in L} F_e \times s(e, L) \times r_{b,e} \times q_{b,e}
```

F is footfall past the stall at event e. s is the share who stop and sign up, which depends on the lineup L. r is the chance a sign-up reviews brand b. q is the share of those reviewers inside b's target segment.

| Metric | Who it serves | How RGC measures it for real |
| --- | --- | --- |
| Sign-ups per pop-up | RGC: traction | A QR code per pop-up in the WatchHumans sign-up flow |
| QRP | RGC and clients | Reviews tagged with the pop-up's code, joined to the reviewer's segment |
| Cost per qualified review | RGC: efficiency | Staff hours, stall fee, travel and units given, divided by QRP |
| Brand coverage | Clients | Share of brands that hit their monthly review target |

**The tool's impact** is its uplift over how RGC plans today:

```latex
\text{Uplift} = \frac{\text{QRP}_{\text{tool}}}{\text{QRP}_{\text{habit}}} - 1
```

The habit plan is the baseline: RGC's favourite brands at the biggest events. Today, measure uplift on 12 held-out synthetic pop-ups, with a bootstrap confidence interval. With real data, alternate tool-picked and manually picked pop-ups for a season and compare QRP and cost per qualified review.

On synthetic data, the uplift shows how much is at stake if the patterns hold; it is not a measured result. Say so on the slide.

## Data

Three sources: synthetic WatchHumans tables, real upcoming London events, and public Census 2021 location data. The synthetic tables mirror what the app already collects: interests, hobbies and goals, likes and dislikes, and rated video reviews.

| File | Rows | Source | Key fields |
| --- | --- | --- | --- |
| `brands.csv` | 20 client brands | Synthetic, fictional names | category, sub-category, flavour profile, format, needs chilling, dietary flags, need states served, target segments, units available |
| `users.csv` | 5,000 | Synthetic WatchHumans | age band, borough, segment (students, young professionals, fitness, families, foodies), traits, category affinities, dietary needs, sign-up source (pop-up code or organic) |
| `reviews.csv` | 20,000 | Synthetic WatchHumans | user, brand, pop-up code or none, rating 1 to 5, would buy, liked or disliked attribute, in target segment; pop-up reviews reconcile with `popup_brands.csv` |
| `popups.csv` | 60 past pop-ups | Synthetic | date, event type (one of seven), borough, footfall, 5-brand lineup, sign-ups, reviews, cost |
| `popup_brands.csv` | 300 | Synthetic | pop-up, brand, units given, reviews, qualified reviews, average rating |
| `events.csv` | 30 to 40 upcoming | Real London listings, collected by hand | type, start and end, venue, latitude and longitude, expected attendance, indoor or outdoor, audience tags, stall cost, link |
| `boroughs.csv` | 33 | Census 2021 (ONS TS007, via Nomis); WatchHumans users synthetic | population, share aged 18 to 34, inner or outer, WatchHumans users per 1,000 people |

**Event types.** Seven categories, used in `popups.csv` and `events.csv`: community, concerts, conferences, expos, festivals, performing arts, sports. The gatherings in the crowd table map onto them: run clubs, food markets, family days and workshops are community; gigs and club nights are concerts; hackathons are conferences; campus fairs are expos; races and match screenings are sports.

**How the generator works.**

- A hidden "truth" sets each rating and sign-up rate from need-state fit, audience match and brand quality, plus noise. The model never sees these parameters; it learns only from the noisy tables.
- Past lineups follow habit: RGC's five favourite brands appear in 70% of past pop-ups. That gives the tool something real to beat.
- Train on the first 48 past pop-ups and test on the last 12, split by date.
- Fictional brand names only, so synthetic ratings are never attached to a real client in a public video.

**Where the events come from.** The London hackathon aggregator, Let's Do This for runs and races, food markets, match screenings and campus fairs. Record facts and links only.

## What each crowd wants

Each event type has a moment and a set of need states. This table seeds the synthetic data and the fit score; real WatchHumans ratings refine it over time. These are starting assumptions; the evidence behind three rows is below the table.

## What each niche gathering might want

Small gatherings offer specific moments to explore: a coffee after a social run, an ingredient to take home after a cooking class, or a snack during a pottery break.

These are **starting hypotheses for synthetic data and the fit score**. WatchHumans feedback can help refine them; actual purchase behaviour is needed to validate demand. A good fit depends on timing, price, what the organiser already provides, and whether outside food is welcome.

| Gathering | The moment | Possible needs or motivations | Food and drink to test | Condiments or take-home products | Potentially weaker fit |
| --- | --- | --- | --- | --- | --- |
| **Weekend social run club** | Finished running; staying to chat | Refreshment, hunger, a social ritual | Water, iced coffee, pastries, small savoury snacks | Nut butter sample packs, breakfast granola | Large meals when people are leaving quickly |
| **Evening distance-running group** | Training ends close to dinner | Thirst, substantial food, convenience | Drinks, wraps, sandwiches, filling snack bars | Easy meal sauces for dinner at home | Tiny tasting portions when people want a meal |
| **Small overnight hackathon** | Coding through dinner or taking a late break | Convenience, hunger, minimal interruption | Wraps, onigiri, resealable snacks, coffee and caffeine-free drinks | Sauce sachets with meals | Food requiring assembly or leaving greasy hands |
| **Beginner cooking class** | Participants taste the dish they have just made | Recreate it at home, build confidence, discover ingredients | Samples of ingredients used in the lesson; a recipe-linked ingredient kit | The exact spice blend, chilli oil, paste or dressing used | Unrelated products with no connection to the recipe |
| **Pasta-making workshop** | Sitting down to eat the finished pasta | Complete the meal, share, recreate the experience | Focaccia, paired drinks, a take-home pasta kit | Pesto, tomato sauce, finishing olive oil | Snacks that compete with an included meal |
| **Dessert or baking class** | Decorating, tasting and packing creations | Customisation, gifting, trying techniques at home | Tea, coffee, small contrasting flavour samples | Fruit curds, compotes, chocolate sauces, decorating kits | More full-size desserts when participants already have plenty |
| **Wine-tasting evening** | Comparing wines between guided pours | Explore pairings, share small bites, remember favourites | Cheese, crackers, olives, bread, water | Chutneys, tapenade, products used in the tasting | Strong flavours that interfere with the planned tasting |
| **Morning yoga class** | Class ends; some participants linger before work | Refreshment, a light breakfast, convenience | Tea, coffee, fruit pots, small breakfast pots | Granola or fruit compote to take home | Full meals when the venue has no seating or time to linger |
| **Yoga festival or day retreat** | Break between sessions or a scheduled lunch | Eat comfortably, refresh, accommodate varied dietary preferences | Clearly labelled bowls, wraps, fruit, hot and cold drinks | Dressings or snack packs tied to food served that day | Large portions immediately before an active session |
| **Evening painting or drawing class** | Social break or end-of-class conversation | A small treat, refreshment, sharing | Drinks with lids, bite-size savouries, individually portioned treats | Packaged local preserves or giftable treats, if relevant to the event | Open dips and messy food beside artwork |
| **Weekend pottery workshop** | Hands washed; a scheduled break | Warm drink, small reward, conversation | Tea, coffee, biscuits, small cakes | Take-home tea, coffee or biscuit gift packs | Food served while participants are handling clay |
| **Fermentation or pickling workshop** | Tasting results and discussing home experiments | Learn, compare flavours, try making something | Guided samples, bread or crackers for tasting | Starter kits, pickling spice blends, jars of the products demonstrated | Generic snacks with no link to the workshop |
| **Match screening** | Two hours of shared viewing | Sharing, savoury, celebration | Crisps, popcorn, sharing snacks, soft drinks, low and no alcohol beer | Dips, hot sauce | Single-serve health products |
| **Gig, club night** | Late, dancing, hot room | Hydrate, energy, late savoury | Electrolytes, water, energy drinks | None | Breakfast items |
| **All-day outdoor festival** | Heat, walking, queues | Hydrate, cool down, portable | Cold drinks, ice lollies, portable snacks | Hot sauce near food stalls | Chilled items with no power |
| **Campus fair, freshers** | Students browsing stalls | Value, novelty, energy | Energy drinks, snacks, quick meals | Condiments for student cooking | Premium-priced items |

### How this informs the fit score

Score the **specific product in the specific moment**, using:

- **Occasion fit:** Is there an observed reason to eat, drink or take something home?
- **Practical fit:** Can people comfortably consume or carry it?
- **Offer fit:** Is the price, portion and format suitable?
- **Unmet need:** Is the organiser already providing an equivalent?
- **Evidence:** Is the match based on an assumption, participant feedback or actual purchases?

A cooking-class participant asking to buy the sauce they just used is stronger evidence than assuming every yoga attendee wants a particular snack.

**Evidence behind three rows.**

- **Runs:** sports-medicine guidance says the goal after exercise is to replace any fluid and electrolyte deficit; sweat rates run roughly 0.5 to 2.0 litres an hour.
- **Hackathons:** dehydration measurably dulls attention, and sugary carbohydrates are linked to more fatigue within an hour, which is why sugar-led products sit in the weak-fit column.
- **Match screenings:** on Euro 2024 England match days, beer purchases rose 13% and crisps and snacks 5%.

Sources are listed at the end of the doc.

## How it works

Six steps run in order: score every brand at every event, predict outcomes, pick the best lineup, choose the month's events, then write the profiles, quantities and timing. Every number traces back to its inputs.

1. **Fit score for every brand at every event.**

   ```latex
   \text{fit}_{b,e} = \cos(n_b, n_e) \times a_{b,e} \times c_{b,e} \times (1 + h_{b,k})
   ```

   n is the need-state vector of the brand and of the event type, from the crowd table. a is audience overlap: the event's expected age and interest mix against the brand's target segments. c is context: time of day, indoor or outdoor, and whether the product needs chilling. h is the brand's learned lift at event type k from WatchHumans ratings, shrunk towards zero when it has few reviews there.
2. **Expected outcomes.** A Poisson regression trained on the 48 training pop-ups predicts sign-ups from footfall, event type, dwell time and lineup appeal. Combined with fit, it gives expected reviews and QRP per brand.
3. **Lineup optimiser.** For each event, score every 5-brand combination of eligible brands: 20 brands give 15,504 combinations, scored in under a second. The score is total brand QRP, plus a bonus for covering a drink, a savoury, a sweet and a condiment, minus a penalty for two brands in the same sub-category. Hard constraints: at least one vegan and one gluten-free option, chilled capacity, units in stock.
4. **Month plan.** Rank events by best-lineup QRP per pound and fill RGC's capacity, for example 4 pop-ups, with no date clashes. Every client brand gets at least one slot a month. Boroughs where WatchHumans has few users get a bonus, because new sign-ups are worth more there.
5. **Brand event profiles.** For each brand: fit across the seven event types, its best moment and audience, what to sample, where to avoid, and its top five upcoming events with expected reviews. A language model writes the profile paragraph from these numbers; it never sets them.
6. **Quantities and timing.** Units to bring equal expected stops times one sample times a 1.2 buffer. The time slot is the event's peak-need moment from the crowd table.

**Stack.** Python, pandas, scikit-learn (PoissonRegressor) and Streamlit. A language model also tags each event description into one of the seven event types.

## Inputs and outputs

The app has three screens, one per question RGC asks. Each reads the same scored files, so the three of you can build in parallel from the first 15 minutes.

| Screen | RGC enters | RGC gets |
| --- | --- | --- |
| Event planner (events to brands) | An event, or a date range; units available; stall size | Ranked events with expected sign-ups, QRP and cost per qualified review; best lineup with products, units, time slot and three reasons; the habit lineup's QRP for comparison |
| Brand profiles (brands to events) | A client brand | Its event profile: fit across the seven event types, best moment, best audience, what to sample, where to avoid; its top five upcoming events with expected reviews |
| Month plan and impact | Month, pop-up capacity, client commitments | A calendar of pop-ups and lineups; total QRP versus the habit plan, with the uplift and its confidence interval |

**File contract.** Agree these at T+0:00. Write stub files with five fake rows at T+0:15 so the app starts immediately.

```
scores.csv     event_id, brand_id, fit, exp_signups, exp_reviews, exp_qrp, reason_1, reason_2, reason_3
lineups.json   event_id -> brands[5], units{brand: n}, slot, qrp, habit_qrp, cost
profiles.json  brand_id -> fit_by_type{7}, best_moment, best_audience, sample, avoid, top_events[5], text
impact.json    uplift, ci_low, ci_high, qrp_tool, qrp_habit, cost_per_qr_tool, cost_per_qr_habit
```

## Team split

Build for 2.5 hours, then spend 1.5 hours on the demo, all inside your 4 hours. If you start at 13:30, T+4:00 is the 17:30 deadline.

&#91;embedded content: team timeline · 3 people, 2 gates, submit at T+3:45\]

Bars run in parallel; diamonds are gates and fixed times.

| Person | Builds | Hands over |
| --- | --- | --- |
| Data lead | Generator, `events.csv`, `boroughs.csv`, the crowd table as code, profile text | Synthetic tables by T+1:00, events by T+1:30 |
| Model lead | Fit score, Poisson model, lineup optimiser, month plan, uplift test | `scores.csv` by T+1:15; lineups, profiles and impact by T+2:30 |
| App and demo lead | Streamlit: event planner, brand profiles, month plan and impact; then the video | Working app by T+2:30, video by T+3:30 |

**Rules.**

- Stub files go in at T+0:15, so nobody waits on anybody.
- Gate at T+1:15: one event becomes a lineup end to end on synthetic data. If not, drop the month plan and keep the two-way screens.
- Feature freeze at T+2:30; after that, fixes only.
- Cut order if late: borough bonus, then the Poisson model (use fit times footfall instead), then the map, then the month plan. Never cut the two-way screens or the uplift number.

## Demo

The demo runs the three screens in order and lands on one number: the uplift in qualified reviews per pop-up over the habit plan. Replace bracketed values with real output before recording.

**2-minute video**

| Time | Screen | Line |
| --- | --- | --- |
| 0:00 | Title over a photo of The Shelf | "RGC runs RGC-first pop-ups: four or five client brands, free product, and every pop-up should grow WatchHumans. Today the event and the lineup are judgement calls." |
| 0:15 | Brand profiles: a fictional hot-sauce brand | "This client wins at street food markets and match screenings, in the evening, with 25 to 34s. It loses at runs and family mornings." |
| 0:35 | Event planner: a real upcoming London hackathon | "Pick a real event. The planner brings \[five brands\], \[N\] units each, timed for the mid-afternoon slump. Here are the three reasons." |
| 1:00 | Same event: habit lineup against tool lineup | "RGC's usual five would earn \[X\] qualified reviews here. The planner's five earn \[Y\]." |
| 1:15 | Month plan and impact | "Across next month's four pop-ups: \[Z\]% more qualified reviews and \[W\]% lower cost per review, tested on 12 held-out pop-ups." |
| 1:35 | How it works | "Synthetic WatchHumans data, real London events. Plug in real data and a QR code per pop-up measures the result." |
| 1:50 | Close | "Every pop-up becomes an experiment that makes the next one better." |

**5-minute live final**

1. *0:00 Hook.* "This room is a pop-up audience, and The Shelf is today's lineup." Run the planner live on EAT\_HACK itself as a hackathon event.
2. *0:45 Live demo.* Brand profile, then event planner, then month plan.
3. *2:30 How it works.* The six steps on one slide. "The language model writes and tags; it never ranks."
4. *3:30 Impact and honesty.* Uplift with its confidence interval, and why synthetic data still proves the pipeline.
5. *4:15 Next.* Real WatchHumans data, a QR code per pop-up, a season of alternating tool-picked and manual pop-ups, and the run clubs and communities WatchHumans already partners with.

**Judge questions**

| Question | Answer |
| --- | --- |
| It's synthetic data, so what does it prove? | The pipeline and the metric are real. The generator hides its truth from the model, and real data swaps in without code changes. |
| Why not just pick the biggest events? | Footfall isn't fit. The habit plan against the tool plan shows the gap in qualified reviews. |
| How do you keep every client happy? | Each brand gets at least one slot a month, and its profile shows where it wins. |

## Sources

- [WatchHumans](https://watchhumans.com/): free products, honest video reviews, rewards, community partners such as run clubs
- [London hackathons aggregator](https://london-hackathons.vercel.app): upcoming London hackathons from Luma, Meetup, Devpost, MLH and Eventbrite
- [Let's Do This, London running events](https://www.letsdothis.com/gb/running-events/in-london): races and 50+ London parkrun locations
- [ACSM position stand, Exercise and Fluid Replacement (2007)](https://pubmed.ncbi.nlm.nih.gov/17277604/): replace fluid and electrolyte deficits after exercise
- [Baker, sweat testing (GSSI)](https://gssiweb.org/docs/default-source/sse-docs/baker_sse_161.pdf?sfvrsn=2): sweat rates of roughly 0.5 to 2.0 litres an hour
- [Wittbrodt and Millard-Stafford, 2018](https://library.fabresearch.org/viewItem.php?id=11865): dehydration impairs attention and executive function
- [Mantantzis et al., 2019](https://pubmed.ncbi.nlm.nih.gov/30951762/): sugary carbohydrates linked to more fatigue within an hour
- [Kantar, July 2024](https://www.kantar.com/uki/Inspiration/FMCG/2024-wp-falling-inflation-football-and-fake-tan): England match days lifted beer 13% and snacks 5%
