#!/usr/bin/env python3
"""
Moventure adventure generator (v1).

Builds a branching gamebook from a theme pack and a classic beat structure,
then writes it as a Moventure story JSON plus a Mermaid map of the graph.

The graph underneath every generated book:

    start ─┬─ take starter item ──┐
           └─ ignore it ──────────┴─> hub ─┬─> side location 1 (key)      ─┐
                                           ├─> side location 2 (ally/lore) ─┼─> back to hub
                                           ├─> side location 3 (trap)      ─┘
                                           ├─> the gate (needs key) ─> passage ─> confrontation
                                           └─> leave (neutral ending)              │
                                                                  ┌────────────────┘
                                                                  ├─ item + ally  -> best ending
                                                                  ├─ lore, no ally-> twist ending
                                                                  ├─ item only    -> good ending
                                                                  ├─ bare hands   -> bad ending
                                                                  └─ flee         -> neutral ending

    (lore is earned by surviving the trap location, which needs the item)

Which side location hides the key, how many side locations exist, and the
flavour text are randomised per seed, so the same theme yields different books.

Usage:
    python moventure_gen.py --list
    python moventure_gen.py --theme starship --seed 7 -o stories/derelict.json
    python moventure_gen.py --theme random --mermaid
    python moventure_gen.py --theme forest --tier 3 --seed 5 -o stories/forest_t3.json
"""

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_story import to_mermaid  # noqa: E402

# ---------------------------------------------------------------------------
# Theme packs. Add a new dict here to get a new world. Every string can use the
# slots {place} {item} {key} {ally} {threat} {gate} {prize}.
# ---------------------------------------------------------------------------
THEMES = {
    "starship": {
        "category": "Sci-Fi",
        "title": ["Silence on the {ship}", "The Drift of the {ship}", "{ship}: No Reply"],
        "ship": ["Kestrel", "Halcyon", "Ninth Meridian", "Vesper Ann"],
        "place": "the derelict",
        "item": "cutting torch",
        "key": "engineering keycard",
        "ally": "the ship's last surviving medic",
        "threat": "the thing that used to be the captain",
        "gate": "the sealed bridge hatch",
        "prize": "the distress beacon",
        "arrive": [
            "Your boarding tube kisses the hull with a soft clang. No lights on the other side. No answer on any channel for six days.\nInside the airlock, a {item} is clamped to the wall where someone dropped it in a hurry.",
            "The {ship} tumbles slowly against the stars, one running light still blinking. You cycle the lock. Frost on every surface.\nSomeone left a {item} on the floor, pointing inward like an arrow.",
        ],
        "take": "You unclip the {item}. The battery is low but not dead. Better than nothing.",
        "hub": "The central corridor runs the length of the ship. Emergency strips glow the color of old blood. Doors lead off in every direction. Ahead, {gate} is shut tight, a red panel beside it.",
        "sides": [
            {"id": "medbay", "title": "MEDBAY", "text": "Cots overturned. A single monitor still traces a heartbeat, steady and slow. Behind a curtain, someone whispers: don't let it hear you.",
             "search": "You pull the curtain aside.", "ally_text": "{ally} looks up at you, alive, barely. I know what it is, they say. And I know how it dies. Take me with you.",
             "key_text": "Among the spilled supplies is a lanyard with an {key} still clipped to it.",
             "trap_text": "The heartbeat on the monitor is not a patient's. It is a proximity alarm.", "trap_die": "Something in the ceiling drops before you can turn around.", "trap_live": "You swing the {item} up and the thing in the ceiling shrinks from the flame. You back out fast."},
            {"id": "cargo", "title": "CARGO BAY", "text": "Crates the size of houses, half of them open. Scratches on the inside of the lids. One crate hums.",
             "search": "You climb onto the humming crate and look in.",
             "ally_text": "Curled inside is {ally}, hiding, awake. They put a finger to their lips, then nod toward the bridge. Together, they mouth.",
             "key_text": "The crate holds a dead crewman and, in his fist, an {key}. You take it. You do not look at his face.",
             "trap_text": "The hum stops the moment you touch the lid.", "trap_die": "The lid slams down with you half inside it.", "trap_live": "You jam the {item} in the closing gap and roll clear as the lid slams."},
            {"id": "engineering", "title": "ENGINEERING", "text": "The reactor is idling. Someone kept it alive on purpose. Tools laid out neatly on a bench, and a note: IF YOU READ THIS, IT IS ON THE BRIDGE.",
             "search": "You go through the bench.",
             "ally_text": "A locker opens and {ally} steps out with a wrench raised, then lowers it. Finally, they say. Finally someone.",
             "key_text": "Taped under the bench: an {key}, and a second note. DON'T.",
             "trap_text": "The reactor note has a second line you did not read: the floor is live.", "trap_die": "You step onto the grating. You do not step off it.", "trap_live": "You test the grating with the {item} first. Sparks. You find another way around."},
            {"id": "quarters", "title": "CREW QUARTERS", "text": "Bunks, photos, a child's drawing of the ship taped to a wall. Every door is open except one.",
             "search": "You try the closed door.",
             "ally_text": "It opens from inside. {ally}, gaunt and holding a flare gun, says: you are either rescue or dinner. Prove it.",
             "key_text": "Inside, on a made bed, someone has left an {key} squared neatly on the pillow, like a gift.",
             "trap_text": "The door was closed for a reason.", "trap_die": "It was not closed to keep something out.", "trap_live": "You light the {item} before opening it. Whatever is inside does not like light. You close the door again."},
        ],
        "locked": "The panel by {gate} blinks red. NO CARD. Somewhere on this ship there is a way in.",
        "leave": "You back into the tube and seal it. The {ship} keeps drifting. Six weeks later the beacon starts up on its own, and you spend the rest of your life not answering it.",
        "gate_open": "The card turns the panel green. {gate} groans open on a room lit only by the stars.",
        "confront": "{threat} is waiting in the captain's chair. It turns. It still has the captain's voice.\nBehind it, {prize} blinks, unlit, one switch away.",
        "end_best": "{ally} shouts the word and you strike with the {item} where they told you. It comes apart like wet paper. You throw the switch and {prize} screams into the dark, and this time, someone answers.",
        "end_good": "You swing the {item} with everything you have. It is enough, barely. You hit the switch with a broken hand. {prize} lights. Rescue comes, and you never tell them what you saw.",
        "end_lore": "You say the name from the note. It stops. For one second it is the captain again, and it reaches past you and throws the switch itself. Then it is gone, and so is the light in its eyes.",
        "end_bad": "You have nothing but your hands. It has the whole ship.",
        "end_flee": "You run. You make the tube. Behind you the {ship} tumbles on, dark, and {prize} never lights. You tell the inquiry there was nothing to find.",
    },
    "tomb": {
        "category": "Adventure",
        "title": ["The Tomb of {name}", "{name} Sleeps", "Beneath the Dunes of {name}"],
        "name": ["Ashkar", "Sel-Amun", "the Ninth Pharaoh", "the Salt Queen"],
        "place": "the tomb",
        "item": "oil lamp",
        "key": "scarab seal",
        "ally": "the old guide, Nefret",
        "threat": "the guardian that was buried standing up",
        "gate": "the sealed inner door",
        "prize": "the sun disc",
        "arrive": [
            "The sandstorm dies at dusk and there it is: a black doorway in the dune where yesterday there was only sand.\nYour porters have fled. One of them dropped an {item}.",
            "Three days of digging and the shovel rings on stone. The lintel bears a warning you cannot read. The porters can, and they leave.\nAn {item} sits on the sand where the last one stood.",
        ],
        "take": "You fill the {item} from your own flask of oil and light it. The doorway swallows the glow.",
        "hub": "A long hall, painted floor to ceiling with a procession that walks the same way you do. Side passages open left and right. At the far end, {gate} is carved with an empty circle the size of your palm.",
        "sides": [
            {"id": "offering", "title": "OFFERING ROOM", "text": "Jars, bowls, bread gone to stone. Someone has been here recently. The dust has footprints.",
             "search": "You follow the footprints.",
             "ally_text": "They end at {ally}, sitting against a jar with a broken ankle. You came, she says. Then you can carry me. I know the words.",
             "key_text": "The footprints end at a jar that has been opened. Inside, wrapped in linen, a {key}.",
             "trap_text": "The footprints end at a flagstone that is slightly higher than the rest.", "trap_die": "It is exactly the right size to be a lid.", "trap_live": "You hold the {item} low and see the seam. You step around it."},
            {"id": "well", "title": "THE WELL", "text": "A shaft drops into the earth. A rope ladder hangs into it, fraying. Cool air rises, smelling of water.",
             "search": "You climb down.",
             "ally_text": "At the bottom, {ally} sits by a spring, waiting. I told them not to go further, she says. You will go anyway. Take me, I can read the door.",
             "key_text": "At the bottom, in the shallow spring, something glints: a {key}, dropped by someone in a hurry to climb.",
             "trap_text": "The ladder holds. The floor at the bottom does not.", "trap_die": "The water is much deeper than it looks.", "trap_live": "You lower the {item} first and see the false floor. You climb back up."},
            {"id": "gallery", "title": "THE GALLERY", "text": "Statues line both walls, each one a little larger than the last. The last one is missing.",
             "search": "You look at the empty plinth.",
             "ally_text": "Behind the plinth, {ally} whispers: it walks at night. I have the words to make it stop. Get me out of here.",
             "key_text": "On the empty plinth, a {key} rests where the statue's foot would be. The others seem to be watching you take it.",
             "trap_text": "The last statue is not missing.", "trap_die": "It was behind you.", "trap_live": "The {item} throws its shadow on the wall a heartbeat before it moves. You run."},
        ],
        "locked": "The empty circle on {gate} wants something you do not have. The painted procession seems to be laughing.",
        "leave": "You climb back out into the dark and the sand has already started to fill the doorway. By morning there is only dune. You tell no one, and no one asks.",
        "gate_open": "The {key} fits the circle. The stone drinks it in and {gate} swings inward without a sound.",
        "confront": "The burial chamber is lit by its own gold. {prize} rests on the sarcophagus. Between you and it, {threat} steps down from its alcove, sand pouring from its joints.",
        "end_best": "{ally} speaks the words and the guardian falters. You raise the {item} and it sees its own shadow for the first time in three thousand years, and kneels. {prize} is warm in your hands as you carry her out.",
        "end_good": "You hold the {item} high and the guardian flinches from the light long enough for you to reach {prize}. The chamber shakes. You do not stop running until you see stars.",
        "end_lore": "You say the name you learned. The guardian stops. It looks at you a long time, then returns to its alcove. You leave {prize} where it is. Some things are not for taking.",
        "end_bad": "You have no light and no words. The guardian has all night.",
        "end_flee": "You run back through the procession and out into the cold. The dune closes behind you. You have sand in your teeth for a year and you never go back.",
    },
    "forest": {
        "category": "Fantasy",
        "title": ["What the {wood} Keeps", "Under the {wood}", "The {wood} Does Not Forget"],
        "wood": ["Blackpine", "Hollowmere", "Old Ashwood", "Whisperfen"],
        "place": "the forest",
        "item": "iron knife",
        "key": "carved token",
        "ally": "the charcoal burner's daughter",
        "threat": "the Antlered One",
        "gate": "the ring of white stones",
        "prize": "your brother",
        "arrive": [
            "The village stops at the treeline and so does the road. Your brother went in three nights ago after the goats. The goats came back.\nOn the last fencepost someone has left an {item}.",
            "Every child in the village knows: do not go past the white stones. Your brother was never good at rules.\nAn {item} is stuck in the gatepost, and it was not there yesterday.",
        ],
        "take": "You work the {item} free. Cold iron. The old women say it matters.",
        "hub": "A clearing where three paths meet under a sky you can barely see. Deeper in, {gate} glows faintly between the trunks, and you know without knowing that you cannot cross it uninvited.",
        "sides": [
            {"id": "hut", "title": "THE HUT", "text": "A charcoal burner's hut, door open, fire out. Two bowls on the table. One is still warm.",
             "search": "You touch the warm bowl.",
             "ally_text": "A voice from the loft: {ally}, hiding. They took my father too, she says. I know the way through the stones. Take me.",
             "key_text": "Under the warm bowl is a {key}, carved with a stag. Whoever left it wanted it found.",
             "trap_text": "The bowl is warm because something is still sitting at the table.", "trap_die": "You do not see it until it stands up.", "trap_live": "You see the {item} reflected in its eyes before you see it. You leave, walking backwards."},
            {"id": "pool", "title": "THE POOL", "text": "Black water, perfectly still, ringed with mushrooms. Your reflection is a second late.",
             "search": "You kneel at the edge.",
             "ally_text": "Your reflection is not yours. It is {ally}, on the other side, mouthing: pull me through. You do.",
             "key_text": "In the shallows, a {key} rests on the silt, and your reflection is holding one too.",
             "trap_text": "Your reflection reaches up first.", "trap_die": "It is stronger than you.", "trap_live": "You cut the water with the {item} and your reflection lets go, screaming without sound."},
            {"id": "hanging", "title": "THE HANGING TREE", "text": "An oak so old it has grown around its own branches. Ribbons tied to every one, some new, some rotten. One has your brother's colors.",
             "search": "You reach for his ribbon.",
             "ally_text": "{ally} drops from the branches beside you. Don't touch it, she says. It counts them. I know another way.",
             "key_text": "Tied inside the ribbon is a {key}. He left it for you. He knew you would come.",
             "trap_text": "The ribbon is a lure.", "trap_die": "The branches close like a fist.", "trap_live": "You cut the ribbon with the {item} instead of untying it. The tree shudders and lets you go."},
        ],
        "locked": "You step toward {gate} and the forest simply turns you around. You are facing the clearing again. You need to be invited.",
        "leave": "You walk back to the treeline and the village lights. Your mother does not ask. Every autumn after that, the goats come back on their own, and you count them twice.",
        "gate_open": "You hold up the {key} and {gate} lets you pass. On the other side the trees are taller and the moon is wrong.",
        "confront": "A hall of living trunks. {threat} sits on a throne of roots, and at its feet, asleep or worse, is {prize}.",
        "end_best": "{ally} names it, and a named thing can be bargained with. You lay the {item} at its feet, iron for a life, and it accepts. You carry your brother home and he wakes at the treeline.",
        "end_good": "You put the {item} to the root-throne and the whole hall recoils. You grab your brother and run while it screams. He does not speak for a month, but he speaks.",
        "end_lore": "You say the true name you learned. The Antlered One inclines its head. Your brother stays, it says, but you may visit. You do, every year. He is happy. That is the worst part.",
        "end_bad": "You have nothing of iron and nothing of its name. It has your brother, and now it has you.",
        "end_flee": "You run and the forest lets you. You never go past the stones again. Some nights you hear two voices calling from the trees now, not one.",
    },
}

# Generic connective tissue shared by all themes.
GENERIC = {
    "ignore_item": [
        "You leave it. You are not here to pick up junk.",
        "You have enough to carry. You leave it where it lies.",
    ],
    "back_hub": "You make your way back to the crossroads.",
    "passage": [
        "A narrow way, then a wider one. Your footsteps come back to you a beat late. Then a door, and beyond it, light.",
        "The way beyond slopes down and grows warm. You count your breaths to keep from counting anything else.",
    ],
}


def fill(s, ctx):
    return s.format(**ctx)


def generate(theme_name, seed=None, num_sides=None, tier=1):
    """tier 1: choices only. tier 2: + dice rolls at the trap and the confrontation.
    tier 3: + stats (luck, grit): the ally boosts luck, misses cost grit, grit 0 = death."""
    rng = random.Random(seed)
    t = THEMES[theme_name]

    # Resolve theme wildcards into a context dict for string slots.
    ctx = {k: v for k, v in t.items() if isinstance(v, str)}
    for k, v in t.items():
        if isinstance(v, list) and v and isinstance(v[0], str) and k != "arrive" and k != "title":
            ctx[k] = rng.choice(v)
    title = fill(rng.choice(t["title"]), ctx)

    sides = list(t["sides"])
    rng.shuffle(sides)
    n = num_sides or rng.choice([2, 3])
    sides = sides[:max(2, min(n, len(sides)))]
    roles = ["key", "ally", "trap"][:len(sides)]
    if len(sides) == 2:
        roles = ["key", rng.choice(["ally", "trap"])]
    rng.shuffle(roles)

    nodes = {}

    def add(nid, title_, text, **kw):
        node = {"title": title_.upper()[:15], "text": fill(text, ctx)}
        node.update(kw)
        nodes[nid] = node

    # --- Act 1: arrival -------------------------------------------------------
    add("start", "Arrival", rng.choice(t["arrive"]), choices=[
        {"label": f"Take the {ctx['item']}"[:19], "to": "take_item", "set": ["has_item"]},
        {"label": "Leave it", "to": "ignore_item"},
    ])
    add("take_item", "Arrival", t["take"], goto="hub")
    add("ignore_item", "Arrival", rng.choice(GENERIC["ignore_item"]), goto="hub")

    # --- Act 2: the hub and its spokes ----------------------------------------
    hub_choices = []
    for side, role in zip(sides, roles):
        sid = side["id"]
        hub_choices.append({"label": f"Go to {side['title'].title()}"[:19], "to": sid, "require": [f"!done_{sid}"]})
        if role == "key":
            add(sid, side["title"], side["text"], choices=[
                {"label": "Search", "to": f"{sid}_found", "set": ["has_key", f"done_{sid}"]},
                {"label": "Go back", "to": "hub"},
            ])
            add(f"{sid}_found", side["title"], side["search"] + "\n" + side["key_text"] + "\n" + GENERIC["back_hub"], goto="hub")
        elif role == "ally":
            add(sid, side["title"], side["text"], choices=[
                {"label": "Investigate", "to": f"{sid}_found", "set": ["has_ally", f"done_{sid}"]},
                {"label": "Go back", "to": "hub"},
            ])
            ally_node = {"goto": "hub"}
            if tier == 3:
                ally_node["mod"] = {"luck": 2}
            add(f"{sid}_found", side["title"], side["search"] + "\n" + side["ally_text"] + ("\nYou feel luckier already." if tier == 3 else "") + "\n" + GENERIC["back_hub"], **ally_node)
        else:  # trap: with the item you are safe; without it (tier 2+) you roll for it
            if tier == 1:
                trap_choices = [
                    {"label": "Look closer", "to": f"{sid}_live", "require": ["has_item"], "set": ["has_lore", f"done_{sid}"]},
                    {"label": "Look closer", "to": f"{sid}_die", "require": ["!has_item"]},
                ]
            else:
                roll = {"dice": "1d6", "dc": 5, "pass": f"{sid}_live", "fail": f"{sid}_die"}
                if tier == 3:
                    roll["stat"] = "luck"
                trap_choices = [
                    {"label": "Look closer", "to": f"{sid}_live", "require": ["has_item"], "set": ["has_lore", f"done_{sid}"]},
                    {"label": "Risk it", "require": ["!has_item"], "set": ["has_lore", f"done_{sid}"], "roll": roll},
                ]
            add(sid, side["title"], side["text"], choices=trap_choices + [{"label": "Go back", "to": "hub"}])
            add(f"{sid}_live", side["title"], side["search"] + "\n" + side["trap_text"] + " " + side["trap_live"] + "\nScratched on the wall on your way out is a single word. A name. You remember it.\n" + GENERIC["back_hub"], goto="hub")
            add(f"{sid}_die", side["title"], side["search"] + "\n" + side["trap_text"] + " " + side["trap_die"], ending="bad")

    hub_choices += [
        {"label": "Open the way", "to": "gate_open", "require": ["has_key"]},
        {"label": "Try the way", "to": "gate_locked", "require": ["!has_key"]},
        {"label": "Turn back", "to": "end_leave"},
    ]
    add("hub", "Crossroads", t["hub"], choices=hub_choices)
    add("gate_locked", "Crossroads", t["locked"], goto="hub")
    add("end_leave", "Home", t["leave"], ending="neutral")

    # --- Act 3: passage and confrontation ------------------------------------
    add("gate_open", "The Way", t["gate_open"], goto="passage")
    add("passage", "The Way", rng.choice(GENERIC["passage"]), goto="confront")
    if tier == 1:
        add("confront", "The End", t["confront"], choices=[
            {"label": "Fight together", "to": "end_best", "require": ["has_item", "has_ally"]},
            {"label": "Speak the name", "to": "end_lore", "require": ["has_lore", "!has_ally"]},
            {"label": f"Use the {ctx['item']}"[:19], "to": "end_good", "require": ["has_item", "!has_ally", "!has_lore"]},
            {"label": "Face it", "to": "end_bad", "require": ["!has_item"]},
            {"label": "Run", "to": "end_flee"},
        ])
    else:
        # Tier 2/3: the fight is a dice loop. Ally lowers the difficulty, misses hurt (tier 3: cost grit).
        strike = lambda dc: {"dice": "1d6", "dc": dc, "pass": "end_good", "fail": "miss", **({"stat": "luck"} if tier == 3 else {})}
        add("confront", "The End", t["confront"], choices=[
            {"label": "Strike together", "require": ["has_item", "has_ally"], "roll": {**strike(3), "pass": "end_best"}},
            {"label": f"Use the {ctx['item']}"[:19], "require": ["has_item", "!has_ally"], "roll": strike(5)},
            {"label": "Speak the name", "to": "end_lore", "require": ["has_lore", "!has_ally"]},
            {"label": "Bare hands", "require": ["!has_item"], "roll": {**strike(6), "pass": "end_good"}},
            {"label": "Run", "to": "end_flee"},
        ])
        miss = {"text": "You miss, or it does not care. Something hits you hard enough to make the room ring."}
        if tier == 3:
            miss["mod"] = {"grit": -1}
            miss["choices"] = [
                {"label": "Get up", "to": "confront", "require": ["grit>0"]},
                {"label": "Stay down", "to": "end_bad", "require": ["grit<=0"]},
            ]
        else:
            miss["roll"] = {"dice": "1d6", "dc": 3, "pass": "confront", "fail": "end_bad"}
            miss["text"] += "\nYou are still breathing. Barely."
        add("miss", "The End", miss.pop("text"), **miss)
    add("end_best", "The End", t["end_best"], ending="good")
    add("end_good", "The End", t["end_good"], ending="good")
    add("end_lore", "The End", t["end_lore"], ending="neutral")
    add("end_bad", "The End", t["end_bad"], ending="bad")
    add("end_flee", "The End", t["end_flee"], ending="neutral")

    # --- prune: drop choices that need a flag nothing ever sets, then drop
    #     nodes nothing points to anymore (e.g. end_lore when there is no trap)
    settable = set()
    for n in nodes.values():
        settable |= set(n.get("set", []))
        for c in n.get("choices", []):
            settable |= set(c.get("set", []))
    for n in nodes.values():
        n["choices"] = [c for c in n.get("choices", [])
                        if all(r.startswith("!") or r in settable or not r.isidentifier() for r in c.get("require", []))] if "choices" in n else None
        if n["choices"] is None:
            del n["choices"]
    reachable, stack = set(), ["start"]
    while stack:
        nid = stack.pop()
        if nid in reachable:
            continue
        reachable.add(nid)
        n = nodes[nid]
        for c in n.get("choices", []):
            stack += [c["roll"]["pass"], c["roll"]["fail"]] if c.get("roll") else [c["to"]]
        if n.get("goto"):
            stack.append(n["goto"])
        if n.get("roll"):
            stack += [n["roll"]["pass"], n["roll"]["fail"]]
    for nid in list(nodes):
        if nid not in reachable:
            del nodes[nid]

    flags = sorted(settable)
    return {
        "meta": {
            "title": title,
            "author": "Moventure generator",
            "version": 1,
            "start": "start",
            "tier": tier,
            "category": t.get("category", "Adventure"),
            "blurb": f"Theme: {theme_name}, seed: {seed}. " + {1: "Choices only.", 2: "Choices and dice.", 3: "Choices, dice and stats."}[tier],
            **({"stats": {"luck": 1, "grit": 3}} if tier == 3 else {}),
            "generator": {"theme": theme_name, "seed": seed, "tier": tier, "sides": [s["id"] for s in sides], "roles": roles},
        },
        "flags": flags,
        "nodes": nodes,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", default="random", help="theme name or 'random'")
    ap.add_argument("--seed", type=int, default=None, help="random seed (default: random)")
    ap.add_argument("--sides", type=int, default=None, help="number of side locations (2-3)")
    ap.add_argument("--tier", type=int, default=1, choices=[1, 2, 3], help="1 = choices, 2 = + dice, 3 = + stats")
    ap.add_argument("--list", action="store_true", help="list themes and exit")
    ap.add_argument("--mermaid", action="store_true", help="also print a Mermaid map of the graph")
    ap.add_argument("-o", "--out", help="output JSON path (default: stdout)")
    args = ap.parse_args()

    if args.list:
        for k, v in THEMES.items():
            print(f"{k:10s} {len(v['sides'])} side locations")
        sys.exit(0)

    seed = args.seed if args.seed is not None else random.randrange(1_000_000)
    theme = args.theme if args.theme != "random" else random.Random(seed).choice(list(THEMES))
    if theme not in THEMES:
        sys.exit(f"unknown theme '{theme}', try --list")

    book = generate(theme, seed, args.sides, args.tier)
    text = json.dumps(book, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}  ({book['meta']['title']}, theme={theme}, tier={args.tier}, seed={seed}, {len(book['nodes'])} nodes)")
    else:
        print(text)
    if args.mermaid:
        print(to_mermaid(book))
