"""
v3 Uno table: hand-curated word list + objective questions only.

Reads words_full.json (1,870 words + 39 wildcards x 140 questions) and writes
uno_table.h, uno_table.json and uno_truth.txt.

Usage: python build_v3.py [K] [N]     K = words on the Uno (default 1300), N = questions (default 64)
"""
import json
import math
import sys
import numpy as np

K = int(sys.argv[1]) if len(sys.argv) > 1 else 10000   # default: every curated word
N = int(sys.argv[2]) if len(sys.argv) > 2 else 64

full = json.load(open("words_full.json"))
Q = full["questions"]
W = full["words"]
WILD_START = list(W).index("nothing")
WILD = set(list(W)[WILD_START:])

# ---------------------------------------------------------------- questions
# Left out: questions people answer differently for the same thing
# (opinion, shape, colour, "how common"), and abstract questions whose
# answer was only filled in for the wildcards.
SUBJECTIVE = """medical tool breakable danger protect school money kids weekly expensive
store city decor storage office livingroom smell loud shiny soft longthin flat coldplace""".split()
# Kept although a little fuzzy, because nothing else tells these apart:
#   colours and "round" (lion/zebra, football/basketball), "hot climate" (wolf/giraffe).
# Kept abstract questions (about time, already happened...) are only asked once the
# game already thinks it is an idea or feeling: the engine skips questions that
# almost every remaining candidate answers the same way.
pool = [q for q in Q if q not in SUBJECTIVE]

# ---------------------------------------------------------------- words
# Words people rarely pick in 20 Questions (obscure, too vague, or a part of something).
DROP = set(x.strip() for x in """
air pump, airboat, altar, amber, anklet, appetizer, apple tree, arch, arugula, awning, backdrop,
backgammon, backscratcher, baklava, balance beam, ballot box, banana peel, barnacle, barrette,
bassinet, bassoon, bathmat, batter, bedpan, bedpost, belt buckle, bin, birdbath, blind, blinder,
blower, blowgun, boa, board, bobsled, bok choy, bolo tie, bologna, bongo, bonnet, bowler hat,
brace, bracket, braid, brake, brass knuckles, breadbox, breadstick, breathalyzer, brooch, buffet,
buggy, bumper, bungee, burner, cake mix, calamari, calf, calzone, camcorder, camera lens, car door,
car seat, cardinal, carriage, casserole, cd player, cement mixer, centerpiece, centrifuge, chaps,
chariot, checkbook, chicken wire, chickpea, chime, chinaware, chip, chive, chute, cigarette butt,
cigarette holder, cilantro, clasp, cleat, cleaver, clipper, cloak, clove, coat rack, cockatoo,
coffee bean, coffee filter, coffee pot, coil, column, compost, container, cooker, cookie cutter,
cookie sheet, coop, copier, cord, cordon bleu, corkboard, corkscrew, cornhusk, cornmeal, cornucopia,
corsage, corset, cot, counter, coverall, crank, crate, crayfish, crouton, crumb, crucifix,
cufflink, cummerbund, curb, curling iron, dashboard, defibrillator, denture, detonator, dial, dip,
dirt bike, dish, dishrag, dishwashing liquid, diskette, dogfood, dolly, doorhandle, doorknocker,
doorstop, drain, duct, duffel bag, dumbwaiter, duster, earwig, eggbeater, eggshell, electric chair,
exerciser, exhaust pipe, eyedropper, eyepiece, fencepost, figurine, file, filter, fire pit,
firewood, fishnet stockings, flagpole, flan, flashbulb, flatiron, flipper, float, flypaper, foam,
fondue, food processor, footbath, footrest, fountain pen, fungus, fur coat, furnace, fuse, gallows,
game, garter, gasket, gauge, gauze, gel, goalpost, goblet, gondola, gong, gopher, gourd, gramophone,
granite, grapevine, grate, gravel, grille, grinder, grits, guardrail, gurney, gutter, gyro,
gyroscope, hairnet, hairpin, handbrake, handle, handlebar, handprint, hard disk, harness, hash,
hatbox, headdress, headlamp, headrest, headscarf, hearse, hedge, hinge, hobbyhorse, hoe, holster,
home plate, honeypot, hood, hot-water bottle, hotplate, hubcap, humvee, ice pack, ice-cream cone,
icemaker, icepick, incubator, inkwell, insole, jack, jewel, jug, juicer, jumpsuit, keyhole, kneepad,
knitting, knob, lamb chop, lamppost, lampshade, landmine, latch, lectern, leech, leek, leotard,
letter opener, lifesaver, lingerie, lip gloss, loincloth, loom, loveseat, lumber, macadamia, mallet,
mandolin, manhole, mantle, mast, mat, matchbox, meat grinder, metronome, mixer, moccasin, modem,
mold, mongoose, mosquito net, mouthpiece, muff, mulberry, mulch, mullet, mussel, napkin ring, navel,
nightshirt, noisemaker, noose, notepad, oilcan, okra, orange rind, ottoman, outfit, pallet,
pantsuit, pantyhose, patch, patty, pedometer, peg, penholder, penlight, pennant, pepper mill,
pesto, pet food, petal, petri dish, pheasant, photo booth, piecrust, pillbox, pincushion,
pine needle, pita, place mat, plaster cast, plastic film, playpen, pole, polisher, polo shirt,
polygraph, pom-pom, porthole, potholder, potpie, potpourri, powder, power line, prism, prune,
pulpit, pump, punch, quad, quiche, quill, racehorse, rack, rag, railing, rain gauge, ram, ramp,
ratchet, ready meal, red carpet, reel, retainer, rim, riser, roadsweeper, robe, roll, roller,
rollerblade, roof rack, root, rosary, rudder, rust, saffron, sandbag, sarcophagus, scaffold,
scaffolding, scallion, scallop, scanner, scoop, scraper, screen, scuba, seaplane, seismograph,
sequin, sewage, sewing kit, shaker, shawl, shears, sheath, shoe polish, shoehorn, shopping basket,
shuffleboard, shutter, sickle, sidecar, sifter, silicone, silverware, sim card, skewer, ski boots,
ski pole, slicer, sling, slot, snowplow, snowshoe, snowsuit, soda fountain, sofa bed,
soldering iron, sonogram, souffle, spareribs, spark plug, spool, spout, springboard, spur,
squeegee, stake, stalagmite, staple, station wagon, stem, stilt, stirrup, stockings,
straightjacket, strap, stretcher, stuffing, stump, sugar cube, sundial, sunroof, swab, sweeper,
swizzle stick, tab, tack, tackle, tag, taillight, tamale, tarp, teabag, tee, telegraph,
telephone pole, thimble, tile, tinsel, toga, tongs, tool, torso, tortellini, tostada, totem pole,
touchpad, towel rack, train car, train set, trap, trapdoor, trigger, trolley, trough, trowel,
tube top, tuning fork, turbine, turf, turnstile, turtleneck, undershirt, urn, valve, vent, vial,
videocassette, viewfinder, vise, visor, wafer, waffle iron, washboard, washcloth, water filter,
water heater, waterwheel, wax, wax paper, weather vane, wedge, wick, windowsill, windsock,
wine cooler, wire, wooden leg, workbench, wrap, wreck, yoke, block, cornbread, magnifier,
cellphone, hydrant, bicycle, grain, bean, seed, bun, gem, berry, vegetable, fruit, bug, plant,
dessert, snack, drink, meat, seafood, fast food, breakfast, clothes, jewelry, makeup, toy,
abacus, air mattress, airbag, amplifier, ashtray, badge, barbed wire, baton, beaker, bib, birdhouse,
bulletin board, bunkbed, buoy, chalice, chess piece, chinchilla, clothesline, cream cheese, creme brulee,
cuckoo clock, doily, doormat, dreidel, dustpan, earplug, eclair, egg roll, eggnog, flask, fruitcake,
gargoyle, gearshift, gumdrop, honeycomb, hovercraft, lanyard, marmalade, measuring cup, metal detector,
mousse, nightstand, odometer, paperweight, parfait, pendulum, periscope, pickax, poinsettia, pulley,
radiator, rickshaw, roulette wheel, sawhorse, sea urchin, shower cap, speedometer, splinter, staple gun,
star fruit, step stool, terrarium, thermostat, tiramisu, toaster oven, water cooler, wire cutters, yak,
yolk, whoopee cushion, revolving door, stained glass, 
""".replace("\n", " ").split(",")) - {""}
assert not (DROP - set(W)), DROP - set(W)

# Same thing under two names: keep one row under the clearer name.
RENAME = {"combination lock": "combo lock", "aircraft carrier": "carrier ship", "brussels sprouts": "sprouts",
          "bulletproof vest": "armor vest", "magnifying glass": "magnifier", "pencil sharpener": "sharpener",
          "windshield wiper": "wiper blade", "bike": "bicycle", "cash machine": "ATM", "computer screen": "monitor",
          "extinguisher": "extinguisher", "lightning bug": "firefly", "hotdog": "hot dog",
          "trashcan": "trash can", "videogame": "video game", "stair": "stairs",
          "iceskate": "ice skate", "ticktacktoe": "tic-tac-toe", "rollerskate": "roller skate",
          "dumpster": "dumpster", "remote control": "TV remote", "polaroid": "polaroid camera"}

# The Kaggle row for "mouse" mixed the animal and the computer part. Split it by hand.
HAND = {
    "mouse": "alive animal pocket hand moves legs fourlegs furfeather tail eyes pet wild inhome sound",
    "computer mouse": "manmade hand plastic buttons electric inhome movingparts",
}

rows = {}
for name, r in W.items():
    if name in DROP:
        continue
    rows[RENAME.get(name, name)] = {"v": dict(r["v"]), "plays": r["plays"], "wild": name in WILD}
for name, tags in HAND.items():
    tags = tags.split()
    assert all(t in Q for t in tags)
    rows[name] = {"v": {q: float(q in tags) for q in Q}, "plays": W["mouse"]["plays"], "wild": False}

# Final trim to fit the Uno's RAM: 66 words people are least likely to think of.
# (Word-frequency ties made the old automatic cut alphabetical, so this is chosen by hand.)
DROP2 = """armor vest, aluminum foil, anvil, applesauce, bagpipe, bazooka, bandanna, barcode, basketball hoop,
beanbag, candelabra, candlestick, canister, cannonball, carrier ship, catapult, chandelier, charcoal,
clothespin, cocoon, coleslaw, combo lock, crowbar, deodorant, doghouse, dollhouse, drumstick, duct tape,
dynamite, extinguisher, fingerprint, fire hydrant, firecracker, fishhook, flamethrower, flyswatter,
footprint, gavel, gingerbread man, gravestone, guillotine, gumball, harmonica, hatchet, headset, hookah,
hopscotch, hourglass, hula hoop, icicle, incense, inhaler, jackhammer, jalapeno, javelin, kaleidoscope,
kazoo, keg, kilt, kimono, ladle, laser pointer, machete, maggot, mannequin, megaphone""".replace("\n", " ").split(",")
for n in DROP2:
    n = n.strip()
    assert n in rows, n
    del rows[n]
names = list(rows)
pop = np.array([rows[w]["plays"] for w in names], float)
isw_all = np.array([rows[w]["wild"] for w in names])
wild_idx = [i for i in range(len(names)) if isw_all[i]]
rest = [i for i in np.argsort(-pop, kind="stable") if not isw_all[i]]
print(f"curated: {len(rest)} words + {len(wild_idx)} wildcards available; keeping {K}")
K = min(K, len(rest) + len(wild_idx))
pick = rest[: K - len(wild_idx)] + wild_idx
left_out = [names[i] for i in rest[K - len(wild_idx):]]
nm = [names[i] for i in pick]
isw = isw_all[pick]
qids = pool
B = np.array([[rows[w]["v"][q] >= .5 for q in qids] for w in nm], dtype=np.uint8)


def split_gain(grp, col):
    _, cnt = np.unique(grp * 2 + col, return_counts=True)
    return -(cnt.astype(float) ** 2).sum()


def refine(grp, col):
    _, g = np.unique(grp * 2 + col, return_inverse=True)
    return g.ravel()


grp_w = np.zeros(isw.sum(), int)
chosen = []
while len(chosen) < 24:
    g, q = max((split_gain(grp_w, B[isw][:, q]), q) for q in range(len(qids)) if q not in chosen)
    if g == split_gain(grp_w, np.zeros_like(grp_w)):
        break
    chosen.append(q)
    grp_w = refine(grp_w, B[isw][:, q])
print(f"{len(chosen)} questions reserved for wildcards; {len(set(grp_w))} groups among {isw.sum()} wildcards")
grp = np.zeros(len(nm), int)
for q in chosen:
    grp = refine(grp, B[:, q])
while len(chosen) < N:
    best = max((split_gain(grp, B[:, q]), q) for q in range(len(qids)) if q not in chosen)[1]
    chosen.append(best)
    grp = refine(grp, B[:, best])
sel = chosen
Bs = B[:, sel]
twins = len(nm) - len(set(map(bytes, Bs)))
print(f"Uno table: {len(nm)} words x {N} questions; words sharing an identical row: {twins}")

# Gentler popularity prior than v2 (was up to 40): word frequency in text is a weak guide.
pri = np.minimum(12, np.round(2 * (math.log(pop.max()) - np.log(pop[pick])))).astype(int)

rowbytes = []
for r in Bs:
    for byte in range(N // 8):
        rowbytes.append(sum(int(r[byte * 8 + b]) << b for b in range(8)))
# Short wording so every question fits the 2-row LCD without scrolling
# (row 1 has 10 characters because the turn counter sits in the top-right corner).
SHORT = {
 "mind": "Only in the mind?", "inhome": "Is one in most homes?", "experience": "Do you experience it?",
 "comm": "Used to communicate?", "everywhere": "Is it everywhere?", "natural": "A natural event?",
 "feeling": "Is it a feeling?", "absence": "Is it an absence?", "outdoors": "Used mostly outdoors?",
 "bedroom": "Found in a bedroom?", "logic": "Numbers or logic?", "online": "Is it mostly online?",
 "happened": "Already happened?", "pleasant": "A pleasant feeling?", "bigcar": "Bigger than a car?",
 "kitchen": "Found in a kitchen?", "hand": "Fits in one hand?", "disposable": "Thrown out after use?",
 "blackgray": "Often black or gray?", "hollow": "Can it hold things?", "bigperson": "Bigger than a person?",
 "buttons": "Has buttons or keys?", "tiny": "Smaller than a coin?", "sharp": "Has a sharp part?",
 "hot": "Usually hot or warm?", "fabric": "Fabric or leather?", "grows": "Grows from the ground?",
 "write": "Used to write or draw?", "movingparts": "Has moving parts?", "garage": "Kept in a garage?",
 "redpink": "Often red or pink?", "heavy": "Too heavy to carry?", "paper": "Paper or cardboard?",
 "eatwith": "Used to eat or drink?", "bathroom": "Found in a bathroom?", "humanbody": "A human body part?",
 "baked": "Baked or fried?", "sky": "Found in the sky?", "cook": "Used for cooking?",
 "holiday": "Used at holidays?", "hotplace": "From a hot climate?",
}
def wraps(s, w0=10, w1=16):
    words = s.split(" "); r0 = ""; i = 0
    while i < len(words) and len((r0 + " " + words[i]).strip()) <= w0:
        r0 = (r0 + " " + words[i]).strip(); i += 1
    return len(" ".join(words[i:])) <= w1
qtext = [SHORT.get(qids[q], Q[qids[q]]) for q in sel]
bad = [t for t in qtext if not wraps(t)]
assert not bad, bad
badw = [w for w in nm if not wraps("Is it " + w + "?") or len(w) > 16]
assert not badw, badw
with open("uno_table.h", "w") as f:
    f.write("// Generated by build_v3.py - do not edit by hand.\n#pragma once\n#include <stdint.h>\n")
    f.write("#ifndef PROGMEM\n#include <avr/pgmspace.h>\n#endif\n")
    f.write(f"#define N_WORDS {len(nm)}\n#define N_QUESTIONS {N}\n#define ROW_BYTES {N // 8}\n")
    f.write(f"const uint8_t PRIOR[N_WORDS] PROGMEM = {{{','.join(map(str, pri))}}};\n")
    f.write(f"const uint8_t ANSWERS[N_WORDS * ROW_BYTES] PROGMEM = {{{','.join(map(str, rowbytes))}}};\n")
    f.write('const char NAMES[] PROGMEM = "' + "\\0".join(nm) + '\\0";\n')
    f.write('const char QUESTIONS[] PROGMEM = "' + "\\0".join(qtext) + '\\0";\n')
LEVEL = {0.0: 0, 0.25: 1, 0.5: 2, 0.75: 3, 1.0: 4}
with open("uno_truth.txt", "w") as f:
    for w in nm:
        f.write("".join(str(LEVEL[round(rows[w]["v"][qids[q]] * 4) / 4]) for q in sel) + "\n")
json.dump({"words": nm, "questions": qtext, "qids": [qids[q] for q in sel], "prior": pri.tolist(),
           "bits": Bs.tolist(), "left_out": left_out}, open("uno_table.json", "w"))
print("left out by the size limit:", len(left_out), left_out[:40])
print("questions:", [qids[q] for q in sel])
