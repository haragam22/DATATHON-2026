"""BriefFacts narrative content + the gang/network planning device that
makes multi-case offender networks exist for Phase 9's graph layer to find.

Two things live here, deliberately paired:
1. Narrative text generation — CaseMaster.BriefFacts is the field a chatbot
   actually reasons over, so a flat one-line template is worthless content.
   Templates vary by offence type and are meaningfully longer/richer for
   "network" cases (gang-linked murder, dacoity, NDPS, kidnapping, arms).
2. Offender personas — a fixed pool of ~250 recurring synthetic identities
   (name, baseline age, gender, gang affiliation, role). Accused is a
   case-scoped row in the schema (no cross-case person ID exists, and
   CLAUDE.md forbids inventing a schema column for this) — so cross-case
   identity is represented the same way real KSP data resolves it without
   biometrics: matching Name + AgeYear + GenderID. case_children.py draws
   network-case accused from this pool so the same persona's name
   deliberately recurs across multiple CaseMasterIDs, giving the graph
   module (inv_arrestsurrenderaccused backbone) real repeat-offender edges
   to visualize instead of an all-strangers dataset.

All names/gangs are fully fictional constructions (adjective+noun gang
names, common Indian first names for personas) — never references a real
person, gang, or reported case, per CLAUDE.md's synthetic-only constraint.
"""

from __future__ import annotations

import random
from typing import Any

PERSONA_FIRST_NAMES = [
    "Arjun", "Deepa", "Suresh", "Lakshmi", "Manjunath", "Kavya", "Ravindra",
    "Anitha", "Prakash", "Sowmya", "Naveen", "Divya", "Ganesh", "Meera",
    "Vinod", "Pooja", "Santosh", "Rekha", "Basavaraj", "Chandru", "Iqbal",
    "Farhan", "Nagesh", "Shivu", "Muniraj", "Ravi", "Kumar", "Ashok",
    "Manoj", "Geetha", "Harish", "Vidya", "Srinivas", "Padma", "Raghu",
    "Shanthi", "Umesh", "Nandini", "Vijay", "Roopa", "Mahesh", "Latha",
    "Girish", "Sunita", "Dinesh", "Yamuna", "Rajesh", "Bhagya", "Sharath",
    "Manasa", "Prashanth", "Vani", "Anand", "Jyothi", "Srikanth", "Radha",
]

# Surnames, kept separate from PERSONA_FIRST_NAMES so one-off Accused names
# (first+middle-initial+last combo, tens of thousands of combinations)
# rarely collide by chance — otherwise coincidental first-name-only reuse
# would masquerade as the deliberate persona-pool recidivism signal the
# graph module should find. A real production run found this pool (28
# first x 40 last, no middle initial = ~1,100 combos) FAR too small: at
# ~4,700 non-persona Accused draws, 83% of distinct names recurred 3+
# times purely from birthday-paradox collision, not modeled recidivism.
# Fixed by widening both lists and adding a middle initial (28x40 ->
# ~56x50x26 ≈ 72,800 combos), which keeps coincidental repeats a small
# minority instead of dominating the distribution.
SURNAMES = [
    "Gowda", "Reddy", "Naik", "Shetty", "Hegde", "Rao", "Patil", "Kumar",
    "Nayak", "Devaraj", "Kulkarni", "Achar", "Bhat", "Poojary", "Setty",
    "Rai", "Hosmani", "Byrappa", "Chowdary", "Malagi", "Iyer", "Menon",
    "Pillai", "Shastri", "Urs", "Bailur", "Deshpande", "Jain", "Khan",
    "Pinto", "Fernandes", "Sequeira", "Bhandary", "Adiga", "Prabhu",
    "Salian", "Poojar", "Chavan", "Vastrad", "Kotian", "Acharya", "Baliga",
    "Kamath", "Shenoy", "Hebbar", "Nair", "Warrier", "Bhandari", "Suvarna",
    "Pai",
]

MIDDLE_INITIALS = [chr(c) for c in range(ord("A"), ord("Z") + 1)]


def random_full_name(rng: random.Random) -> str:
    """One-off name for non-network Accused/Victim/Complainant — deliberately
    NOT drawn from the persona pool, see SURNAMES docstring above."""
    return f"{rng.choice(PERSONA_FIRST_NAMES)} {rng.choice(MIDDLE_INITIALS)}. {rng.choice(SURNAMES)}"

GANG_ADJECTIVES = ["Silver", "Iron", "Shadow", "Crimson", "Northside",
                    "Riverside", "Highway", "Steel", "Midnight", "Cobra",
                    "Falcon", "Thunder", "Black Rock", "Diamond"]
GANG_NOUNS = ["Gang", "Crew", "Syndicate", "Network", "Squad", "Circle",
              "Outfit", "Ring"]

GANG_ROLES = ["Leader", "Lieutenant", "Member", "Associate"]
GANG_ROLE_WEIGHTS = [0.1, 0.2, 0.5, 0.2]

WEAPONS = ["country-made pistol", "knife", "iron rod", "sickle", "chopper",
           "wooden club", "machete"]
DRUGS = [("ganja", "kg", (2, 40)), ("brown sugar", "gm", (50, 900)),
         ("MDMA", "gm", (20, 300)), ("heroin", "gm", (30, 500)),
         ("hashish", "kg", (1, 15))]

# CrimeSubHead names (from lookups.CRIME_SUBHEADS) eligible for the
# gang/network treatment — organized, repeat-offender-shaped offences.
NETWORK_ELIGIBLE_SUBHEADS = {"Murder", "Dacoity", "Robbery", "NDPS",
                              "Kidnapping", "Arms Act"}

SIMPLE_TEMPLATES = [
    "Complainant reported {offence_lower} at {place_type} in {district} "
    "jurisdiction on the date of occurrence. {case_category} registered; "
    "investigation taken up by the local station and is ongoing.",
    "A case of {offence_lower} was registered following a complaint at "
    "{place_type} within {district} district. Preliminary inquiry "
    "conducted; case classified under {case_category}.",
    "Incident of {offence_lower} reported at {place_type}, {district}. "
    "Statements of complainant and available witnesses recorded; "
    "investigation in progress under {case_category} category.",
]

NETWORK_TEMPLATES = {
    "Murder": (
        "Victim was found at {place_type} in {district} district with "
        "injuries consistent with an assault by {weapon}. Investigation "
        "indicates the attack was carried out by {accused_count} "
        "individuals identified as associates of the {gang_name}, "
        "suspected to be linked to a prior rivalry over territory. "
        "Police intelligence flags possible connections to other pending "
        "cases involving the same group; further verification underway."
    ),
    "Dacoity": (
        "A group of {accused_count} armed persons, believed to be members "
        "of the {gang_name}, committed dacoity at {place_type} in "
        "{district} district using {weapon} to threaten occupants. "
        "Cash and valuables were reported stolen. The group's pattern of "
        "operation matches prior cases attributed to the same network; "
        "cross-case linkage is being examined."
    ),
    "Robbery": (
        "Robbery reported at {place_type} in {district} district, "
        "allegedly executed by {accused_count} persons associated with "
        "the {gang_name} and armed with {weapon}. Victim sustained minor "
        "injuries while resisting. Modus operandi is consistent with "
        "similar robberies previously linked to this group."
    ),
    "NDPS": (
        "Acting on specific intelligence, police intercepted "
        "{accused_count} persons linked to the {gang_name} at "
        "{place_type} in {district} district and seized approximately "
        "{quantity} {drug_unit} of {drug_name}. The network is suspected "
        "of running a wider distribution chain across the district; "
        "financial trail and associate identification are in progress."
    ),
    "Kidnapping": (
        "Victim was reported abducted from {place_type} in {district} "
        "district by {accused_count} individuals believed to be operating "
        "under the {gang_name}. Ransom demand is under verification. "
        "Investigators are cross-referencing accused identities against "
        "prior kidnapping and extortion cases linked to the same group."
    ),
    "Arms Act": (
        "A raid at {place_type} in {district} district, based on "
        "intelligence about the {gang_name}, led to recovery of illegal "
        "firearms including {weapon} from {accused_count} persons "
        "present. Investigation is examining the source of the weapons "
        "and links to other cases involving the same network."
    ),
}


_GANG_NAMES: list[str] | None = None
_PERSONA_POOL: list[dict[str, Any]] | None = None


def generate_gang_name(rng: random.Random) -> str:
    return f"{rng.choice(GANG_ADJECTIVES)} {rng.choice(GANG_NOUNS)}"


def get_gang_names(rng: random.Random, count: int = 16) -> list[str]:
    """Module-level singleton so case_master.py's narrative text and
    case_children.py's persona pool draw from the SAME fixed gang roster —
    otherwise a case naming "Cobra Squad" would have no persona actually
    tagged to that gang for generate_accused() to reuse."""
    global _GANG_NAMES
    if _GANG_NAMES is None:
        # sorted(), not list(set(...)) directly — Python's per-process hash
        # randomization makes raw set iteration order non-deterministic,
        # which silently broke reproducibility of network-case narratives
        # across process runs (same rng state, different gang_name string).
        _GANG_NAMES = sorted({generate_gang_name(rng) for _ in range(count * 2)})[:count]
    return _GANG_NAMES


def get_persona_pool(count: int, rng: random.Random) -> list[dict[str, Any]]:
    """A generation-time device, not a DB table — see module docstring.

    Gang assignment is ROUND-ROBIN, not `rng.choice(gangs)` — a real bug
    found via a live spot-check: pure random choice let some gangs draw as
    few as 2 personas out of 120 by chance, so cases whose BriefFacts
    narrative claimed "N individuals" (N up to 6, see
    plan_case_narrative's accused_count) sometimes got fewer actual
    Accused rows than the text claimed once generate_accused's
    `k=min(accused_count, len(pool))` truncated to the gang's real size —
    8/127 live network cases had this exact mismatch. Round-robin
    guarantees every gang gets floor(count/len(gangs)) or that +1 members
    (>=7 with count=120, gangs=16), always covering accused_count's max of
    6, while shuffling first keeps which persona lands in which gang
    random."""
    global _PERSONA_POOL
    if _PERSONA_POOL is not None:
        return _PERSONA_POOL
    gangs = get_gang_names(rng)
    indices = list(range(count))
    rng.shuffle(indices)
    gang_for_index = {idx: gangs[i % len(gangs)] for i, idx in enumerate(indices)}
    personas = []
    for i in range(count):
        personas.append({
            "PersonaID": i + 1,
            "Name": random_full_name(rng),
            "BaseAge": rng.randint(18, 55),
            "GenderID": rng.choice([1, 2]),
            "GangName": gang_for_index[i],
            "GangRole": rng.choices(GANG_ROLES, weights=GANG_ROLE_WEIGHTS, k=1)[0],
        })
    _PERSONA_POOL = personas
    return _PERSONA_POOL


def plan_case_narrative(subhead_name: str, network_rate: float, rng: random.Random) -> dict[str, Any]:
    """Decides, at CaseMaster generation time, whether this case is a
    gang/network case and what its narrative needs — consumed both by
    build_brief_facts() here and by case_children.generate_accused() so the
    BriefFacts text and the actual Accused/gang rows agree with each other.
    """
    is_network = subhead_name in NETWORK_ELIGIBLE_SUBHEADS and rng.random() < network_rate
    plan: dict[str, Any] = {"is_network": is_network, "accused_count": rng.randint(1, 4)}
    if not is_network:
        return plan

    plan["accused_count"] = rng.randint(3, 6)
    plan["gang_name"] = rng.choice(get_gang_names(rng))
    plan["weapon"] = rng.choice(WEAPONS)
    if subhead_name == "NDPS":
        drug_name, unit, qty_range = rng.choice(DRUGS)
        plan["drug_name"] = drug_name
        plan["drug_unit"] = unit
        plan["quantity"] = rng.randint(*qty_range)
    return plan


def build_brief_facts(
    subhead_name: str, place_type: str, district: str, case_category: str,
    plan: dict[str, Any], rng: random.Random,
) -> str:
    if plan["is_network"]:
        template = NETWORK_TEMPLATES.get(subhead_name)
        if template:
            return template.format(
                place_type=place_type, district=district,
                accused_count=plan["accused_count"], gang_name=plan["gang_name"],
                weapon=plan.get("weapon", "a weapon"),
                quantity=plan.get("quantity", ""), drug_unit=plan.get("drug_unit", ""),
                drug_name=plan.get("drug_name", "contraband"),
            )
    return rng.choice(SIMPLE_TEMPLATES).format(
        offence_lower=subhead_name.lower(), place_type=place_type,
        district=district, case_category=case_category,
    )


_PARAPHRASE_SYSTEM_PROMPT = (
    "Rewrite the following police case summary in different wording. "
    "Preserve every specific fact exactly: place, district, weapon, gang "
    "name, number of accused, drug name and quantity, and case category. "
    "Keep all numbers as digits, not spelled out (write '5', not 'Five'). "
    "Never substitute a legal offence term for a different one — if the "
    "text says 'dacoity', keep 'dacoity'; do not change it to 'robbery' or "
    "any other offence name, they are legally distinct. Do not add or "
    "remove any fact, name, or number. Return only the rewritten "
    "paragraph, no preamble."
)


def paraphrase_brief_facts(text: str, *, enable_thinking: bool = False) -> str:
    """QuickML paraphrase pass over template-generated BriefFacts text —
    varies phrasing only, never invents new facts (CLAUDE.md: synthetic
    content must stay fact-faithful to what generation actually decided).
    Falls back to the template text unchanged on any QuickML failure (rate
    limit, network, malformed response) — a paraphrase failure mid-run
    isn't fatal to a 2000-row generation pass, but it's logged explicitly,
    never silently swallowed (CLAUDE.md's no-silent-failure rule)."""
    from data_generation import quickml_client

    try:
        result = quickml_client.chat(
            [
                {"role": "system", "content": _PARAPHRASE_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            max_tokens=300, temperature=0.6, enable_thinking=enable_thinking,
        ).strip()
        return result or text
    except Exception as e:  # noqa: BLE001 - explicit logged fallback, not a swallow
        print(f"[narratives] QuickML paraphrase failed, keeping template text: {e}")
        return text
