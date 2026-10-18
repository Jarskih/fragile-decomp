---
title: Trade
---

# Trade

*Status: the parties, schedule, price model, stock rules and virus mechanics are
read from the game's code and data (**[code]**). Legality of goods is only
stated in the game's text (**[text]**) and has no mechanical flag. Which alien
cultures the Trade menu lists as available, and a few visit lengths, are not
resolved (**?**).*

Trade lets you buy and sell luxury goods, medicines, anti-personnel viruses
(APVs), high-grade ores, missiles and information. Everything is paid for from
**Money** (see [Colony economy](colony-economy.md)).

## Who you trade with

Each trade party holds its own stock of each item. The market pool is the
unowned supply.

| party | who |
|---|---|
| pool | the market's unowned stock |
| 1 to 8 | player slots |
| 9 to 14 | the six alien cultures (they hold stock lines too) |
| 8 slots | **Trade Merchants** (delegates who deal in goods and medicines) |
| 8 slots | **Traders** (visit one of your colonies; deal in ores, missiles, APVs, information) |

### When delegates appear

Both mechanisms are unlocked by the player's own colony claims (Traders after
2 to 3 claims, Merchants after 3 to 4) and are off in the second game mode.

| | Trade Merchant | Trader |
|---|---|---|
| offered to each player every | 150 to 239 days | 150 to 199 days |
| stays | 150 to 199 days (warning 10 days before leaving) | a visit at a colony of your choice; 30 days to choose the colony |
| message | "Trade Merchant available" | "Trader requesting target"; chosen colony receives the goods and gives the stock |
| if none free | retry in 20 days | retry in 20 days |
| reachable | from the Trade menu without choosing a colony | goods are delivered to, and taken from, the visited colony's ore store and missile silos |

The player cannot be offered the same slot twice in a row. If you do not pick a
colony before the window ends the Trader leaves. The first offer comes about 256
days after unlock **(inferred)**.

## Items

101 items: 68 luxury goods, 5 medicines, 4 APVs, 10 ores, 13 missiles and
Information. Merchants and cultures trade the first 73; **Traders** trade only
APVs, the six higher ores (Quazinc to Nexos), ten missiles (Hellfire upward) and
Information.

### Luxury goods (reference price, global supply)

The reference price is the long-run average; this month's price is in the price
model below. The supply is the total in existence.

| id | item | ref. price | supply | id | item | ref. price | supply |
|---|---|---|---|---|---|---|---|
| 0 | Beers | 4000 | 200 | 34 | Astramarine | 16000 | 8 |
| 1 | Wines | 6000 | 200 | 35 | Peridot | 5000 | 15 |
| 2 | Altarian Panther Sweat | 70000 | 50 | 36 | Amethyst | 8000 | 12 |
| 3 | St.Etienne's Real Cream & Honey Liqueur | 50000 | 100 | 37 | Abstract Sculpture | 20000 | 40 |
| 4 | Muet & Champignon vintage champagne | 64000 | 100 | 38 | Domestic interior units | 10000 | 60 |
| 5 | Fizzimo Lumiere | 75000 | 30 | 39 | Decorative drinking horns | 10000 | 45 |
| 6 | Bristol glass | 6000 | 45 | 40 | Worked leather | 5000 | 65 |
| 7 | Crystal Cantata Inc. products | 24000 | 25 | 41 | Ornamental archaic weaponry | 20000 | 20 |
| 8 | Deep pile velvet | 20000 | 50 | 42 | Fizzimo Liqueurs | 1000 | 500 |
| 9 | Silk | 10000 | 100 | 43 | Rigellian ant eggs | 500 | 1000 |
| 10 | Watered silk | 12000 | 80 | 44 | Pearls dissolved in brandy | 1100 | 350 |
| 11 | Raw silk | 10000 | 80 | 45 | Goat's ear mushrooms | 600 | 250 |
| 12 | Satin taffeta | 15000 | 60 | 46 | Organic corn on the cob | 450 | 1000 |
| 13 | Egyptian sea-cotton | 1000 | 200 | 47 | Braccatian kulos cheese | 850 | 800 |
| 14 | Achaean angora | 20000 | 100 | 48 | Grains | 100 | 15000 |
| 15 | Tiara & Bracelet set | 115000 | 5 | 49 | Seaweed | 150 | 15000 |
| 16 | Choker | 123000 | 2 | 50 | Krill | 100 | 15000 |
| 17 | Solitaire emerald | 250000 | 6 | 51 | Water | 200 | 10000 |
| 18 | Brooch | 150000 | 8 | 52 | Ortok's Mansions | 100000 | 3 |
| 19 | Necklace | 65000 | 6 | 53 | Shades of Brutos | 850000 | 1 |
| 20 | Eternity ring | 125000 | 5 | 54 | Huskar Cigars | 4000 | 20 |
| 21 | Pectoral | 250000 | 2 | 55 | Maunik's Cube | 110000 | 5 |
| 22 | Collar | 75000 | 3 | 56 | Gong of Death Song | 1000000 | 1 |
| 23 | 3-strand bracelet | 55000 | 10 | 57 | Holostar globes | 85000 | 5 |
| 24 | Diamond | 35000 | 15 | 58 | Besthelda's Apothecary | 150000 | 3 |
| 25 | Emerald | 45000 | 5 | 59 | Photoplasmic Cocoon | 1250000 | 2 |
| 26 | Sapphire | 28000 | 12 | 60 | Steam Racers | 700000 | 5 |
| 27 | Ruby | 30000 | 6 | 61 | KKZ Quad | 550000 | 5 |
| 28 | Ultropaz | 17000 | 8 | 62 | Kraagil Oil | 500000 | 3 |
| 29 | Alexandrite | 17000 | 10 | 63 | Sacrificial Axe | 75000 | 1 |
| 30 | Metachrome | 18000 | 10 | 64 | Horn of Plenty | 70000 | 1 |
| 31 | Opal | 11000 | 10 | 65 | Dionne's Lightwork | 2500000 | 1 |
| 32 | Pearl | 13000 | 10 | 66 | Loving Cup | 30000 | 1 |
| 33 | Moonstone | 7000 | 17 | 67 | Law of the Cube | 1250000 | 1 |

### Medicines

| item | ref. price | supply |
|---|--:|--:|
| Biofort | 20,000 | 50 |
| Vir-Attack | 15,000 | 50 |
| Supa-Shellac | 13,000 | 50 |
| Swat | 18,000 | 50 |
| Star Balm | 13,000 | 50 |

### APVs

| item | ref. price | supply |
|---|--:|--:|
| Shell Shock | 56,000 | 30 |
| Phantom | 64,000 | 30 |
| Judgement Day | 85,000 | 25 |
| Silicon Death | 83,000 | 25 |

### Ores

| ore | ref. price | supply |
|---|--:|--:|
| Selenium | 50 | not traded |
| Asteros | 80 | not traded |
| Barium | 150 | not traded |
| Crystalite | 400 | not traded |
| Quazinc | 1,200 | 500 |
| Bytanium | 1,300 | 500 |
| Korellium | 2,300 | 500 |
| Dragonium | 3,500 | 500 |
| Traxium | 50,000 | 20 |
| Nexos | 150,000 | 20 |

### Missiles and Information

Missile prices are not fixed but recomputed every month as the missile's own
price plus the number of ore units it uses times that month's ore price (see
[Missiles](missiles.md) for the base price): Explosive 800 + 1 Selenium, Area
Explosive 6,400 + 2 Barium, Napalm 5,000 + 1 Quazinc, Hellfire 16,000 + 3
Quazinc, Scatter 15,000 + 3 Selenium, Vortex 8,000 + 3 Crystalite, Nuclear
50,000 + 5 Bytanium, Virus 30,000 + 1 Traxium, Anti-Virus 10,000 + 4 Barium,
Mega 100,000 + 1 Nexos, Stasis 40,000 + 2 Korellium. Bug Hunter and Meat-Eater
have reference prices of **55,000** and **95,000**. Explosive, Area Explosive and
Napalm are never offered by Traders.

**Information** (reference 15,000): a Trader sells up to three asteroid
locations; buying it marks those asteroids as known to you. Its monthly price is
one random value from 7,500 to 37,400 Cr; it cannot be sold back.

## Price model

Prices are **global**: every party quotes the same price for an item. They are
recomputed every **30 days** (and 12 times at new game to warm up the cycle).

```
for each item with a reference price R:
    w = 0.5 x ( sin(a)  + 0.33 x sin(b) + 0.20 x sin(c) )          # about -0.5 .. +0.5; halved again for ores
    price = R x (1 + w)
    price = price x (1 + a random 0 .. 9.4%)
```

The three phases advance each month by fixed amounts (one cycle takes about 60,
20 and 12 months respectively); each item starts at a random point on its own
cycles. The result swings between about **0.23 and 1.77 times** the reference
(ores: 0.62 to 1.38) plus the 0 to 9% noise. The past year's prices are kept for
the price graph. The ten ore prices are also the **Federation ore prices**
used when the Federal Transporter buys your ore.

| item class | you buy at | you sell at |
|---|---|---|
| luxuries, medicines | P | 0.85 P |
| APVs | P | 0.50 P |
| ores | max(P, 1.4 x (P + 0.2 x (P - R))) | P + 0.2 x (P - R) |
| missiles | 1.40 P | 1.03 P |
| Information | monthly price | cannot be sold |

(P = this month's price, R = reference price.) Your **average price paid** is
tracked per item; a sale removes the cost proportionally.

## Stock

- The pool starts with the global supply of each item. Each month the pool of
  medicines, APVs, ores and missiles is reset to the supply minus what the other
  parties hold; luxury goods are never restocked.
- **Merchants and cultures** hold 5 to 12 stock lines: 40% of new lines for a
  Merchant (20% for a culture) are a medicine, otherwise a random luxury good.
- **Traders** hold 4 to 8 lines: 50% one of the six higher ores, 40% one of the
  ten missiles, 10% an APV. Typical quantities: about 32 to 63 units of a
  500-supply ore, 2 to 3 units of Traxium, Nexos or an APV, 1 missile.
- A party above its minimum (Merchants 5, Traders 4) returns a random line to the
  pool each month, with some chance of a second return or of a new line.

## Gifts and hostility

A transfer at price zero is a **gift**. It lowers the receiving alien's
hostility toward the giver by `value / 1000` raw units (value in Cr), with the
current hostility never below its baseline. The value is multiplied by 25 or 10
for a culture's own sacred artefact or remedy: Braccatia receiving the **Gong of
Death Song** (25) or the **Horn of Plenty** (10); Artemia receiving the
**Sacrificial Axe**, **Supa-Shellac** or **Swat** (10). One raw unit is
1/32,767 of the range, so a 100,000 Cr gift is worth about 0.3%; only the Gong
(25 x 1,000,000 / 1,000 = about 76%) moves a culture.

A hidden **Braccatian grudge** exists: some trade action stamps a day and 90
days later Braccatia's current hostility toward you rises 12.5% and its
baseline 3%. Returning the Gong undoes it; any gift worth over 100,000 (after
the multiplier) clears the stamp. What arms the stamp is inferred (acquiring the
Gong, as the game text suggests) **(?)**. See
[Aliens and diplomacy](aliens-and-diplomacy.md) for the hostility model.

## Anti-personnel viruses (APVs)

The six viruses are colony events. Susceptibility is per race; the cure column
names the medicine that stops it. A virus cannot be doubled up on one asteroid,
and a natural disease blocks a second disease.

| virus | affects | cure | stage length (days) |
|---|---|---|--:|
| Shell Shock | Artemia | Swat | 30 |
| Phantom | Mikotaj | none | 30 |
| Judgement Day | Terran, Braccatia, Achaean | none | 20 |
| Silicon Death | Braccatia, Mauna, Achaean | Biofort | 30 |
| Bug Hunter | Artemia | Vir-Attack | 30 |
| Meat-Eater | Terran, Braccatia, Achaean | Vir-Attack | 20 |

(The Bug Hunter and Meat-Eater viruses are also missiles: the same effect is
launched by those two missiles, which the game calls illegal.)

Population effect (one step per day while the event is active):

| virus | acute phase | afterwards, every day until cured |
|---|---|---|
| Shell Shock | none; loses 2 to 6 per day | same, never ends (100%) |
| Phantom | 80% of the population over 8 to 10 days | loses 1 to 2 per day |
| Judgement Day | incubation 10 to 19 days, then one blow of 70 to 79%; 5% chance the event ends there | loses 1 to 5 per day (95%) |
| Silicon Death | loses 3 to 4 per day | same, never ends |
| Bug Hunter | 50% of the population over 3 to 6 days | loses 1 to 4 per day |
| Meat-Eater | loses 2 to 4 per day | same, never ends |

An event ends only when its handler ends it or the colony's medical officer
authorises the cure. **Phantom and Judgement Day have no cure**, so they end only
by extinction (Judgement Day has the 5% exit).

Risk to a human colony: only **Judgement Day** (no cure) and **Meat-Eater**
(cure Vir-Attack, 15,000 Cr reference). Delivery: the agent mission "APV
delivery" (see [Personnel](personnel.md)) releases a virus you own; "You do not
have any APVs to use" is the refusal. The sellers are the Traders (10% of their
lines are APVs). The six **natural diseases** (Astrophobia, Rigellian Flu, Deep
Space Debilitation, Korsakov's Syndrome, Belt Fever, Spacer's Salmonella) affect
Terrans only and come from the random colony-event system: durations of 21 to 28
days (Astrophobia), 28 to 41 days with 5 to 10 deaths per day up to 40% of the
population (Rigellian Flu), and 120 to 179 or 90 to 149 days of reduced
efficiency without deaths (Debilitation, Korsakov's); cures Star Balm,
Vir-Attack and Biofort. Whether aliens use APVs against the player is not
established **(?)**.

## The black market and legality **[text]**

The game's text flags some goods as illegal or banned: Fizzimo Lumiere (export
from Achaean space), Shades of Brutos, the Law of the Cube, all trade with the
Mauna, Huskar Cigars, Besthelda's Apothecary, the Photoplasmic Cocoon, Steam
Racers, the KKZ Quad, Kraagil Oil (black market only), and probably goat's-ear
mushrooms. Sacred artefacts (Gong, Horn of Plenty, Loving Cup, Law of the Cube)
should not be sold back to their owners. **None of this is a flag in the price or
stock tables**; the banned goods are simply the 500,000 to 2,500,000 Cr entries.
The only code consequence found is the Braccatian grudge above, and the text
mentions Mikotaj and Achaean accusations about trading with the Mauna whose
trigger was not located **(?)**. Purchases from Sci-Tek or black-market traders
come from Money.

## Open questions

- Which of the six cultures the Trade menu lists as available, and which of the
  eight delegate names are cultures versus black-market dealers.
- The Trader's visit length once a colony is chosen, and the exact first offer
  time.
- Whether aliens ever buy from or sell to the pool beyond the monthly refresh.

*Related: [Colony economy](colony-economy.md); [Game time](game-time.md);
[Personnel](personnel.md); [Aliens and diplomacy](aliens-and-diplomacy.md);
[Ores and mining](ore-and-mining.md); [Missiles](missiles.md).*
