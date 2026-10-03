Pop-up Pick for RGC · EAT_HACK

# How PopUpPick works

Events, products and people are all scored on the same 10 WatchHumans archetypes. The model matches each event's expected crowd to RGC's client products, picks 2 to 5 to bring, and puts a pound value on the pop-up. One command runs everything and opens the website.

**Run**`python app.py`

1 · Data flow

## From raw inputs to the website

Real data Synthetic stand-in for RGC data Team assumption, editable Script or model step

Two keyword-scoring scripts put products and real events on the same 10 archetypes. The model combines them with the synthetic pop-up history (to learn how a match turns into sign-ups and reviews) and RGC's pricing (to turn reviews into pounds). It writes `outputs/`, which the website reads without recalculating anything.

2 · Inside the model

## How archetype scores become a lineup

Worked example: **Aladdin Pantomime at the Grand Leicester**, 143 people, so 4 products. Every archetype in the crowd is credited with its favourite product in the lineup, so the best set covers the whole crowd rather than repeating one profile.

**Lineup match** = Σ over the 10 archetypes of crowd share × the best score any lineup product has for that archetype. Product scores come from label claims, segments and category, rescaled so each product's top archetype is 1, then nudged by WatchHumans ratings from each archetype. A product's score for a group feeds the forecasts: a higher match means more people stop, sign up and review.

3 · With real data

## Every pop-up teaches the next one

Today the history is synthetic, so the numbers show what is at stake, not a measured result. With a QR code in the WatchHumans sign-up flow and reviews tagged to each pop-up, the same pipeline learns from RGC's real results with no code changes.

Current results · synthetic

## What it adds up to

**Monthly impact**£751 a month (£511 from better lineups, £240 of marketing time), about £9,010 a year

**Held-out pop-ups**+18.6% reviews and +£255 net per pop-up (95% CI £121 to £419)

**December plan**2 candlelight concerts, £850 net against £325 for the usual lineup at the biggest events

**Learning**Ratings cut the error in product archetype profiles by 21% against keywords alone

Brands and products are RGC's real clients; events are real PredictHQ listings. WatchHumans users, reviews and pop-up outcomes are synthetic and never a client's real results. Pound values use RGC's £599 per 15 reviews plus assumptions in `data/assumptions/value_assumptions.csv`.