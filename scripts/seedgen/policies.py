"""Original plain-language policy summaries for the six demo personas (no insurer or ISO wording)."""

from datetime import date

TERM = (date(2026, 3, 1), date(2027, 3, 1))


def cov(code, name, covers, not_covers, limit=None, ded=None, examples=(), limit_note=None, ded_note=None):
    return {"code": code, "name_plain": name, "limit_usd": limit, "limit_note": limit_note,
            "deductible_usd": ded, "deductible_note": ded_note, "what_it_covers_plain": covers,
            "what_it_does_not_plain": not_covers, "examples": list(examples)}


def endo(code, name, present, why):
    return {"code": code, "name_plain": name, "present": present, "why_it_matters_plain": why}


def excl(code, title, plain):
    return {"code": code, "title": title, "plain": plain}


FLOOD = excl("EX_FLOOD", "Flood and surface water",
             "Rising water from flash floods, washes, or overflowing streams is generally not part of "
             "this policy. Flood is usually a separate policy. Ask your agent about flood coverage, "
             "especially during monsoon season.")
GRADUAL = excl("EX_GRADUAL", "Slow, hidden leaks",
               "Damage from a leak that goes on for weeks or months, or from repeated seepage, is "
               "typically treated differently from a sudden pipe burst. Catching drips early matters.")
WEAR = excl("EX_WEAR", "Wear, age, and upkeep",
            "The cost to repair or replace the worn-out part itself (an old water heater, a cracked "
            "hose) is usually not covered, though resulting damage to other property may be considered.")
BACKUP_EX = excl("EX_BACKUP", "Sewer and drain backup",
                 "Water that backs up through sewers or drains, or comes up from a sump, is usually "
                 "covered only if you have a specific water-backup add-on.")
EARTH = excl("EX_EARTHQUAKE", "Earth movement", "Earthquake and ground movement are generally excluded.")
NEGLECT = excl("EX_NEGLECT", "Neglect",
               "Failing to take reasonable steps to protect the property after a loss starts, such as "
               "leaving a known leak running, can reduce what is paid.")


def policies():
    out = []

    # P1 Maya — Homeowners (personal-lines preview)
    out.append({
        "id": "pol-p1", "account_id": "acct-p1", "lob": "homeowners", "preview_flag": True,
        "product_label": "Homeowners (HO-3 style) — Personal-lines preview (AZ demo data)",
        "coverages": [
            cov("HO_DWELLING", "Your home (structure)",
                "The house itself, including attached garage, walls, roof, built-in appliances and "
                "fixtures, when damaged by a covered event such as fire, wind, hail, or a sudden "
                "pipe or appliance leak.",
                "Wear and tear, gradual leaks, flood, earthquake, and the cost to fix the failed part.",
                385000, 2500, ["A monsoon wind event lifts roof tiles", "A supply line bursts and soaks drywall"]),
            cov("HO_OTHER_STRUCT", "Other structures",
                "Detached items such as a block wall, shed, or detached garage.",
                "Structures used mainly for business.", 38500, 2500, ["A wall fence is knocked down by a microburst"]),
            cov("HO_CONTENTS", "Your belongings",
                "Furniture, clothing, electronics and other personal items, at home or while traveling.",
                "Flood damage, and high-value items beyond sub-limits (jewelry, collectibles).",
                192500, 2500, ["Furniture ruined by a sudden water-heater leak"]),
            cov("HO_LOSS_OF_USE", "Extra living costs",
                "Reasonable added costs to live elsewhere while a covered loss makes the home unlivable.",
                "Costs unrelated to a covered loss.", 77000, None, ["Hotel stay while floors are dried and replaced"]),
            cov("HO_WATER_SUDDEN", "Sudden water leaks (inside the home)",
                "Damage from water that escapes suddenly and accidentally from plumbing, an appliance, "
                "or an AC system — for example, a hose that bursts or a condensate line that overflows once.",
                "Leaks that happen slowly over time, seepage, flood, and sewer backup.",
                None, 2500, ["A washing-machine hose lets go while you're at work"],
                limit_note="Part of home and belongings limits"),
            cov("HO_LIABILITY", "Personal liability",
                "If someone is injured or their property is damaged and you are legally responsible, "
                "this helps with legal defense and settlements, up to the limit.",
                "Intentional acts, your own injuries, and business activities.", 300000, None,
                ["A guest slips on a wet floor at your house"]),
            cov("HO_MEDPAY", "Guest medical payments",
                "Small medical bills for guests hurt at your home, regardless of fault.",
                "Injuries to you or people who live with you.", 5000, None, []),
        ],
        "endorsements": [
            endo("END_WATER_BACKUP", "Water backup (sewer and drain)", False,
                 "Without it, a backed-up drain or sewer line is typically not covered. Ask your agent about adding it."),
            endo("END_EQUIP_BREAKDOWN", "Home systems / equipment breakdown", False,
                 "Helps with mechanical failure of AC units, pool equipment and appliances. Ask your agent about it."),
            endo("END_REPLACEMENT_COST", "Replacement cost on belongings", True,
                 "Pays to replace items with new ones rather than their depreciated value."),
        ],
        "exclusions_plain": [FLOOD, GRADUAL, WEAR, BACKUP_EX, EARTH],
        "deductibles": {"all_peril": 2500, "water": "same as all-peril", "wind_hail": "same as all-peril"},
    })

    # P2 Luis — Dwelling Fire (rental)
    out.append({
        "id": "pol-p2", "account_id": "acct-p2", "lob": "dwelling_fire", "preview_flag": True,
        "product_label": "Dwelling Fire (rental) — Personal-lines preview (AZ demo data)",
        "coverages": [
            cov("DF_DWELLING", "Rental house (structure)",
                "The rental house when damaged by a listed event such as fire, wind, hail, or a sudden "
                "leak from plumbing or equipment.", "Tenant belongings, gradual leaks, flood, wear and tear.",
                240000, 2500, ["A water heater tank splits and floods the kitchen"]),
            cov("DF_OTHER_STRUCT", "Other structures", "Detached garage, shed or fence on the lot.",
                "Anything rented out separately for business.", 24000, 2500, []),
            cov("DF_RENTAL_INCOME", "Lost rent",
                "Rent you lose while a covered loss makes the home unrentable, for a limited period.",
                "Rent lost for reasons not tied to a covered loss, such as a tenant simply leaving.",
                48000, None, ["Home is vacant for repairs after a covered leak"]),
            cov("DF_OWNER_CONTENTS", "Your items kept at the rental",
                "Appliances or furnishings that belong to you (not the tenant).",
                "Tenant belongings — tenants need their own renters insurance.", 15000, 2500, []),
            cov("DF_WATER_SUDDEN", "Sudden water leaks",
                "Damage from water that escapes suddenly from plumbing, appliances, or AC equipment.",
                "Slow or hidden leaks that continue over time, flood, drain backup, and damage that "
                "happens while the home sits vacant beyond the vacancy limit noted below.",
                None, 2500, ["A supply line fails between tenants"], limit_note="Part of dwelling limit"),
            cov("DF_LIABILITY", "Landlord liability",
                "If someone is hurt at the property and you're legally responsible, helps with defense "
                "and settlements up to the limit.", "Intentional acts and business activities beyond renting.",
                300000, None, ["A visitor is injured on a loose stair tread"]),
        ],
        "endorsements": [
            endo("END_VACANCY_PERMIT", "Extended vacancy permission", False,
                 "In this demo policy, certain water losses may be limited if the home is empty longer than 60 days. "
                 "Ask your agent about extending that between tenants."),
            endo("END_WATER_BACKUP", "Water backup (sewer and drain)", False,
                 "Without it, backed-up drains are typically not covered."),
            endo("END_ORDINANCE", "Ordinance or law", True,
                 "Helps pay extra costs when current building codes require upgrades during a covered repair."),
        ],
        "exclusions_plain": [FLOOD, GRADUAL, WEAR, BACKUP_EX, NEGLECT,
                             excl("EX_VACANCY", "Long vacancy",
                                  "If the home stays vacant for more than 60 days in a row, some water and freeze "
                                  "losses may be limited. Plan shutoff and checks between tenants.")],
        "deductibles": {"all_peril": 2500, "water": "same as all-peril"},
    })

    # P3 Saguaro Grill — BOP restaurant
    out.append({
        "id": "pol-p3", "account_id": "acct-p3", "lob": "bop",
        "product_label": "Businessowners Policy — Restaurant",
        "coverages": [
            cov("BOP_BUILDING", "Your building",
                "The restaurant building, built-in kitchen equipment and fixtures when damaged by a "
                "covered event such as fire, wind, hail or a sudden leak.",
                "Flood, wear and tear, gradual leaks, and earthquake.", 850000, 2500,
                ["Roof drain blocks and rain enters the dining room ceiling"]),
            cov("BOP_BPP", "Business belongings",
                "Kitchen equipment, furniture, inventory and supplies.", "Flood, and employee personal items.",
                310000, 2500, ["Ice machine line leaks into the dry-storage room"]),
            cov("BOP_BI", "Lost business income",
                "Net income and ongoing expenses while a covered loss forces a temporary closure.",
                "Slowdowns not caused by a covered loss; closures ordered for reasons not in the policy.",
                None, None, ["Dining room closed 3 weeks after a covered water loss"],
                limit_note="Up to 12 months of actual loss, after a short waiting period",
                ded_note="72-hour waiting period"),
            cov("BOP_SPOILAGE", "Food spoilage",
                "Spoiled food when refrigeration fails from a covered cause, including power failure "
                "on your premises.", "Spoilage from turning equipment off or poor maintenance.", 25000, 1000,
                ["Walk-in cooler compressor fails over a weekend"]),
            cov("BOP_WATER_SUDDEN", "Sudden water leaks",
                "Damage from water escaping suddenly from plumbing, kitchen equipment, or AC equipment.",
                "Long-term seepage, flood, and sewer backup unless added.", None, 2500,
                ["Dishwasher supply line bursts"], limit_note="Part of building and belongings limits"),
            cov("BOP_GL", "General liability",
                "If a customer is hurt or their property damaged and you're legally responsible, helps "
                "with defense and settlements.", "Intentional acts; liquor liability unless separately added.",
                1000000, None, ["A guest slips on a wet floor after a roof leak"],
                limit_note="$1,000,000 per occurrence / $2,000,000 total per year"),
            cov("BOP_MEDPAY", "Guest medical payments", "Small medical bills for injured guests regardless of fault.",
                "Injuries to employees (workers' compensation applies).", 10000, None, []),
        ],
        "endorsements": [
            endo("END_EQUIP_BREAKDOWN", "Equipment breakdown", True,
                 "Helps with sudden mechanical or electrical failure of kitchen and HVAC equipment."),
            endo("END_WATER_BACKUP", "Water backup", True,
                 "Helps with sewer or drain backup into the restaurant, up to a sub-limit of $25,000."),
            endo("END_UTILITY_SERVICES", "Off-premises power interruption", False,
                 "Without it, spoilage from a utility outage away from your building may not be covered."),
        ],
        "exclusions_plain": [FLOOD, GRADUAL, WEAR, NEGLECT, EARTH],
        "deductibles": {"all_peril": 2500, "spoilage": 1000, "water_backup": 5000},
    })

    # P4 Ponderosa Outfitters — BOP retail, freeze
    out.append({
        "id": "pol-p4", "account_id": "acct-p4", "lob": "bop",
        "product_label": "Businessowners Policy — Retail",
        "coverages": [
            cov("BOP_BUILDING", "Your building",
                "The store building and permanent fixtures when damaged by a covered event, including "
                "heavy snow weight and sudden pipe or sprinkler leaks.",
                "Flood, wear and tear, gradual leaks, and damage when heat was not kept on (see freeze note).",
                1400000, 5000, ["Roof damaged by heavy snow load", "Sprinkler line cracks in a hard freeze"]),
            cov("BOP_BPP", "Business belongings",
                "Inventory, shelving, registers and supplies.", "Flood and shoplifting or employee theft.",
                650000, 5000, ["Winter gear stock soaked by a burst pipe"]),
            cov("BOP_BI", "Lost business income",
                "Net income and ongoing expenses during a temporary closure from a covered loss.",
                "Seasonal slowdowns or closures not tied to a covered loss.", None, None,
                ["Store closed 5 weeks during holiday season after a covered freeze loss"],
                limit_note="Up to 12 months of actual loss, after a waiting period", ded_note="72-hour waiting period"),
            cov("BOP_FREEZE_CONDITION", "Freezing pipes and sprinklers",
                "Damage from pipes or sprinkler lines that freeze and burst, when you took reasonable "
                "care to keep the building heated or to drain and shut off the water.",
                "Freeze damage when heat was off and the water system was not drained or shut off.",
                None, 5000, ["Heat kept at 40°F or above over the holiday closure"],
                limit_note="Part of building and belongings limits"),
            cov("BOP_GL", "General liability",
                "If a customer is hurt or their property damaged and you're legally responsible, helps with "
                "defense and settlements.", "Intentional acts and professional advice claims.", 1000000, None,
                ["A customer slips on an icy entry"], limit_note="$1,000,000 per occurrence / $2,000,000 total per year"),
            cov("BOP_MEDPAY", "Guest medical payments", "Small medical bills for hurt customers regardless of fault.",
                "Injuries to employees.", 10000, None, []),
        ],
        "endorsements": [
            endo("END_EQUIP_BREAKDOWN", "Equipment breakdown", True,
                 "Helps with sudden failure of boilers, furnaces and electrical equipment."),
            endo("END_WATER_BACKUP", "Water backup", False,
                 "Without it, drain and sewer backup is typically not covered. Ask your agent."),
            endo("END_HEAT_MAINTAIN", "Heat-maintenance condition (policy condition)", True,
                 "Your policy expects heat to be kept on, or the water system drained, during closures. "
                 "Keeping the thermostat at 40°F or above is the simple way to meet this."),
        ],
        "exclusions_plain": [FLOOD, GRADUAL, WEAR, NEGLECT,
                             excl("EX_FREEZE_HEAT_OFF", "Freeze with no heat",
                                  "If the heat is off and the system isn't drained, freeze damage may not be paid.")],
        "deductibles": {"all_peril": 5000, "water": "same as all-peril"},
    })

    # P5 Mesa Palms — Commercial Real Estate (habitational)
    out.append({
        "id": "pol-p5", "account_id": "acct-p5", "lob": "commercial_real_estate",
        "product_label": "Commercial Property & Liability — Apartment Community (48 units)",
        "coverages": [
            cov("CRE_BUILDINGS", "Apartment buildings",
                "All residential buildings, common areas, and permanent equipment when damaged by a "
                "covered event such as fire, wind, hail or sudden water escape.",
                "Flood, wear and tear, gradual leaks, and tenants' belongings.", 9600000, 10000,
                ["A leak in Unit 3B damages the ceiling of 2B", "Hail damages roofing"]),
            cov("CRE_OWNER_PROPERTY", "Owner-provided property",
                "Appliances, furniture, maintenance equipment and supplies you own.", "Residents' belongings.",
                250000, 10000, []),
            cov("CRE_RENTAL_INCOME", "Lost rental income",
                "Rent you lose while units are unlivable from a covered loss.", "Vacancies unrelated to a loss.",
                1200000, None, ["Four units offline for repairs after water damage"],
                limit_note="Up to 12 months of actual loss"),
            cov("CRE_WATER_ESCAPE", "Water escaping from plumbing, appliances and HVAC",
                "Sudden escape of water from pipes, water heaters, appliances, or AC equipment, including "
                "damage to units below.", "Slow leaks over time, flood, and drain backup beyond the sub-limit. "
                "Repair of the failed fixture itself.", None, 25000,
                ["Washer hose in 3B fails and water reaches 2B"],
                limit_note="Part of buildings limit", ded_note="Higher deductible applies to water losses"),
            cov("CRE_GL", "Premises liability",
                "If a resident or visitor is hurt, or their property damaged, and you're legally responsible, "
                "helps with defense and settlements.", "Intentional acts; residents' own belongings.",
                1000000, None, ["A resident's belongings damaged and the owner is found responsible"],
                limit_note="$1,000,000 per occurrence / $2,000,000 total per year"),
            cov("CRE_LAW", "Building-code upgrade costs",
                "Extra cost to meet current building codes when repairing a covered loss.",
                "Upgrades not required by code.", 480000, None, []),
        ],
        "endorsements": [
            endo("END_WATER_BACKUP", "Water backup", True,
                 "Helps with sewer and drain backup, up to a sub-limit of $100,000."),
            endo("END_EQUIP_BREAKDOWN", "Equipment breakdown", False,
                 "Without it, sudden failure of boilers, pumps and elevators may not be covered. Ask your agent."),
            endo("END_SENSOR_PROGRAM", "Water-sensor program participation", False,
                 "Optional program. Using sensors can help find leaks sooner; it does not change what is covered."),
        ],
        "exclusions_plain": [FLOOD, GRADUAL, WEAR, BACKUP_EX, NEGLECT,
                             excl("EX_TENANT_PROP", "Residents' belongings",
                                  "Residents need their own renters insurance for their items.")],
        "deductibles": {"all_peril": 10000, "water": 25000, "water_backup": 10000},
    })

    # P6 Desert Bloom Produce — AgriBusiness
    out.append({
        "id": "pol-p6", "account_id": "acct-p6", "lob": "agribusiness",
        "product_label": "Agribusiness Property — Cooler & Packing Facility",
        "coverages": [
            cov("AG_BUILDINGS", "Cooler and packing buildings",
                "The cooling building, packing shed and permanent fixtures when damaged by a covered event.",
                "Flood, wear and tear, and gradual leaks.", 2200000, 10000,
                ["Monsoon wind damages the packing-shed roof"]),
            cov("AG_EQUIPMENT", "Machinery and equipment",
                "Packing lines, forklifts, washers and cooling equipment.", "Wear and tear; vehicles on roads.",
                1350000, 10000, ["Wash-down water reaches electrical panels in a sudden event"]),
            cov("AG_STOCK", "Harvested produce in storage",
                "Packed or stored harvested produce while in your buildings.",
                "Unharvested crops in the field (those are insured separately).", 600000, 10000,
                ["Lettuce stored in the cooler"]),
            cov("AG_SPOILAGE", "Spoilage from cooling failure",
                "Produce that spoils when the refrigeration system fails suddenly from a covered cause, "
                "including electrical failure on your premises.",
                "Spoilage from equipment you knew was failing and did not service, or from turning off power.",
                250000, 10000, ["Compressor trips during a heat wave and the room warms"],
                limit_note="Sub-limit", ded_note="Spoilage deductible"),
            cov("AG_UTILITY", "Off-premises power interruption",
                "Spoilage and income loss when a power outage away from your facility, such as a utility "
                "line failure, causes cooling to stop.", "Outages shorter than the waiting period.", 150000, None,
                ["Utility outage during a monsoon storm"], limit_note="24-hour waiting period"),
            cov("AG_BI", "Lost business income",
                "Net income and ongoing expenses while a covered loss halts packing and cooling.",
                "Market price drops or crop shortfalls.", None, None, ["Packing line down for 2 weeks"],
                limit_note="Up to 12 months of actual loss"),
            cov("AG_GL", "General and product liability",
                "If your produce or premises cause injury or damage and you're legally responsible, helps with "
                "defense and settlements.", "Recall costs unless separately added.", 2000000, None, []),
        ],
        "endorsements": [
            endo("END_EQUIP_BREAKDOWN", "Refrigeration / equipment breakdown", True,
                 "Helps with sudden mechanical or electrical failure of cooling equipment."),
            endo("END_UTILITY_SERVICES", "Off-premises power interruption", True,
                 "Applies after a 24-hour waiting period — important for monsoon outages."),
            endo("END_RECALL", "Product recall expense", False,
                 "Without it, costs of a recall are typically not covered. Ask your agent."),
        ],
        "exclusions_plain": [FLOOD, WEAR, NEGLECT, EARTH,
                             excl("EX_FIELD_CROPS", "Crops in the field",
                                  "Unharvested crops are not part of this policy.")],
        "deductibles": {"all_peril": 10000, "spoilage": 10000},
    })

    for p in out:
        p["term_start"], p["term_end"] = TERM
        p["status"] = "active"
    return out
