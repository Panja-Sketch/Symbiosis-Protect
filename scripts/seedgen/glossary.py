"""Glossary and coverage notes — original plain-language text, used by the AI assistant and Coverage Lens."""

GLOSSARY = [
    ("Deductible", "The amount you pay yourself on a covered loss before the insurance pays the rest.", []),
    ("Limit", "The most the policy will pay for a given type of coverage.", []),
    ("Sub-limit", "A smaller cap inside a larger coverage, for one kind of loss (for example, water backup).", []),
    ("Endorsement", "An add-on that changes a policy by adding, removing or adjusting coverage.", []),
    ("Exclusion", "Something the policy generally does not cover.", []),
    ("Sudden and accidental", "Happening quickly and unexpectedly, like a hose bursting — as opposed to a slow drip over weeks.", ["HO_WATER_SUDDEN"]),
    ("Gradual leak", "Water that escapes slowly over a long period. These are usually treated differently from sudden leaks.", []),
    ("Water backup", "Water that comes up through a drain, sewer or sump instead of coming from a pipe. Usually needs its own add-on.", ["END_WATER_BACKUP"]),
    ("Flood", "Water from rising creeks, washes or surface runoff. Usually insured separately, not under property policies.", ["EX_FLOOD"]),
    ("Equipment breakdown", "Coverage for sudden mechanical or electrical failure of machinery such as AC or refrigeration.", ["END_EQUIP_BREAKDOWN"]),
    ("Replacement cost", "Paying to replace an item with a new one, rather than its used value.", ["END_REPLACEMENT_COST"]),
    ("Actual cash value", "What an item was worth at the time of loss after wear is taken into account.", []),
    ("Loss of use", "Extra living costs while a covered loss makes your home unlivable.", ["HO_LOSS_OF_USE"]),
    ("Business income", "Net income and ongoing expenses covered while a covered loss temporarily closes your business.", ["BOP_BI"]),
    ("Waiting period", "Time at the start of a closure or outage during which the policy does not yet pay.", []),
    ("Spoilage", "Perishable goods that go bad after cooling fails from a covered cause.", ["BOP_SPOILAGE", "AG_SPOILAGE"]),
    ("Off-premises power interruption", "A power outage caused away from your building, such as a utility line failure.", ["AG_UTILITY", "END_UTILITY_SERVICES"]),
    ("Liability", "Your legal responsibility when someone else is hurt or their property is damaged.", []),
    ("Medical payments", "Small medical bills for injured guests paid regardless of who is at fault.", ["HO_MEDPAY", "BOP_MEDPAY"]),
    ("Ordinance or law", "Extra repair cost to meet current building codes after a covered loss.", ["END_ORDINANCE", "CRE_LAW"]),
    ("Vacancy", "A building with no one living in or using it. Long vacancy can limit some coverage.", ["EX_VACANCY"]),
    ("Heat-maintenance condition", "A policy expectation to keep the building heated, or to drain the water system, to prevent freeze damage.", ["END_HEAT_MAINTAIN", "BOP_FREEZE_CONDITION"]),
    ("Wet sprinkler system", "A fire sprinkler system with water in the pipes all the time, which can freeze in unheated spaces.", []),
    ("Condensate line", "The small drain pipe that carries water produced by your air conditioner outdoors. Clogs can overflow indoors.", []),
    ("Supply line", "The flexible hose connecting a fixture or appliance to the building's water pipes.", []),
    ("Shutoff valve", "A valve that stops water flow to a fixture, a unit, or the whole building.", []),
    ("Monsoon season", "June 15 through September 30 in Arizona, when storms bring wind, hail, dust and flash floods.", []),
    ("Proof level", "How strongly a completed safety task is evidenced: a tap (E0), a photo (E1), a document (E2), a review (E3), or sensor data (E4).", []),
    ("Sensor-verified", "A fix confirmed by device readings returning to normal, not just by someone saying it was done.", []),
    ("Agent", "Your independent insurance agent, who confirms coverage decisions and can change your policy.", []),
]

COVERAGE_NOTES = [
    ("water_sudden_vs_gradual", "Sudden leak vs. slow leak",
     "Policies like this one generally respond to water that escapes suddenly and accidentally, such as a burst "
     "hose or a one-time AC drain overflow. They generally treat leaks that go on for a long time differently. "
     "That's why catching a small drip early, and clearing a clogged AC drain before it overflows, matters. "
     "Your agent confirms how any specific loss would be handled.",
     ["HO_WATER_SUDDEN", "DF_WATER_SUDDEN", "BOP_WATER_SUDDEN", "CRE_WATER_ESCAPE"]),
    ("flood_exclusion", "Flash flooding is usually not included",
     "Water rising from washes, streets or creeks during a monsoon storm is generally a flood loss, which property "
     "policies usually exclude. Flood is typically a separate policy with its own waiting period. "
     "Ask your agent whether flood coverage makes sense for your location.",
     ["EX_FLOOD"]),
    ("water_backup", "Drain and sewer backup",
     "Water that comes back up through drains is usually covered only with a water-backup add-on, often with a "
     "lower limit. Check whether your policy lists it under endorsements.",
     ["END_WATER_BACKUP", "EX_BACKUP"]),
    ("freeze_heat_condition", "Keep the heat on — or drain the system",
     "For freeze losses, the policy expects reasonable care: keep the building heated, or shut off and drain "
     "the water system. A thermostat at 40°F or above is the simple, common practice. Your agent can explain "
     "what applies to your policy.",
     ["BOP_FREEZE_CONDITION", "END_HEAT_MAINTAIN", "EX_FREEZE_HEAT_OFF"]),
    ("spoilage_cooling_failure", "Spoilage when cooling fails",
     "Spoilage coverage is for sudden failures from covered causes. Showing regular service records helps "
     "demonstrate reasonable care. Outages caused away from your site depend on the off-premises power add-on "
     "and its waiting period.",
     ["AG_SPOILAGE", "BOP_SPOILAGE", "AG_UTILITY", "END_UTILITY_SERVICES"]),
    ("vacancy_limit", "Empty properties are treated more carefully",
     "If a home or unit stays empty for a long time, some water and freeze losses may be limited. "
     "Between tenants: shut off the water, check for drips, and ask your agent about vacancy permission.",
     ["EX_VACANCY", "END_VACANCY_PERMIT"]),
    ("unit_below_damage", "A leak upstairs can damage the unit below",
     "Water from an upper unit can damage ceilings and belongings below. The building's coverage and the "
     "residents' own renters insurance each play a part. Fast detection and shutoff reduce the damage. "
     "Your agent confirms how a loss would be handled.",
     ["CRE_WATER_ESCAPE", "CRE_BUILDINGS", "CRE_GL"]),
    ("wear_and_age", "Old parts are your upkeep",
     "Policies usually do not pay to replace a worn-out water heater or hose themselves. They may respond to "
     "resulting sudden damage. Replacing aging parts on a schedule is the best protection.",
     ["EX_WEAR"]),
    ("slip_fall_liability", "Wet floors and liability",
     "If a guest slips on a wet floor after a leak or roof leak, liability coverage may help with defense and "
     "settlements. Putting out signs, drying the floor, and documenting what you did are good practice.",
     ["BOP_GL", "BOP_MEDPAY"]),
    ("roof_wind_hail", "Monsoon wind and hail",
     "Policies generally respond to wind and hail damage to roofs. Rain entering through an opening that the storm "
     "just created is treated differently from rain entering through an existing leak or clogged drain. "
     "Keeping roofs and drains maintained matters.",
     ["HO_DWELLING", "BOP_BUILDING", "CRE_BUILDINGS", "AG_BUILDINGS"]),
]
