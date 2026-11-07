# 20 Questions on an Arduino Uno

A 20-Questions-style guessing game that runs entirely on an Arduino Uno. Think of an object or an idea, answer with five buttons and displays on a 16x2 LCD. It knows 1,200 words, including abstract
ones like "nothing", "love" and "time".

<img width="120" height="160" alt="image" src="https://github.com/user-attachments/assets/8fa2487b-8ca1-422a-bc46-e75dcadbbf5b" />

## How it works (no computer-science background needed)

1. **Building the knowledge (only run once, on PC).** I started with the THINGS dataset, a large collection of everyday objects used by researchers to study how the human brain recognizes and understands things. Next, I used an AI model, Gemma 4 12B (ran on Kaggle's free GPUs), to score how well each of 1,870 words fits each of
   129 yes/no questions, such as "Does it use electricity?". This process took ~6 hours to complete, which is why I avoided running it on something like Claude. Since the dataset only covers physical objects, I also wrote answers for 39 common abstract ideas. A script then compressed it down by picking the "best" 1,200 words out of 1870 words and 64 questions out of 129 to fit the Uno's memory.
2. **Playing (on the Uno).** The game is *not* an AI. It keeps a score for every word. Each answer raises the
   score of words that fit and lowers the score of words that don't. It then asks the question that best splits
   the words still in the running, like a clever game of elimination.
3. **Guessing.** It guesses when one word clearly leads, drops each wrong guess and carries on. It gives up after
   30 turns (every question and guess uses one turn). Holding the middle button for one second undoes your last answer.

## Parts

| Part | Note |
|---|---|
| Arduino Uno | ATmega328P, 2 KB RAM, 32 KB flash |
| 16x2 LCD with I2C backpack | address 0x27 (try 0x3F if the screen stays blank) |
| 5 push buttons (or jumper wires touched to GND) | no resistors needed |

## Wiring

- LCD: GND to GND, VCC to 5V, SDA to A4, SCL to A5.
- Buttons: one side of each button to GND, the other to D2 (Yes), D3 (Probably), D4 (Sometimes / hold = back),
  D5 (Probably not) and D6 (No). The sketch uses the Uno's internal pull-up resistors.
- Diagrams: `docs/wiring_diagram.png` and `docs/breadboard_layout.png`.
  On a 4-legged push button, use two diagonally opposite legs.

## Run it

1. Install the Arduino IDE and, in Sketch --> Manage Library, **LiquidCrystal I2C** by Frank de Brabander. I recommend to search for the author's name instead, "Frank de Brabander."
2. Open `uno_guesser/uno_guesser.ino` (keep the three files in that folder together).
3. Select board **Arduino Uno**, pick your port, and Upload.

Expected size: about 28.3 KB flash (88%) and 1.7 KB RAM (85%) of the Uno's 32 KB / 2 KB. The IDE will show a
"low memory" warning; that is expected.

## Rebuild the word list (optional)

```
cd tools
pip install numpy
python build_v3.py          # reads words_full.json, writes uno_table.h
```

Copy the new `uno_table.h` (and, if you changed the engine settings, `guesser_core.h`) into `uno_guesser/`.
`words_full.json` holds the AI's scores for 1,870 words and 140 questions. `kaggle/` has the notebook that
produced the scores (needs a GPU), the word list and the question list. `uno_words.txt` lists the 1,200 words
the game knows.

Settings you may want to change in `guesser_core.h`: `MAX_TURNS` (30), `MAX_SKIPS` (3 free "sometimes"
answers) and `MARGIN` (how far ahead a word must be to be guessed early).

## Limitations

- Only 1,200 words, limited by the Uno's 2 KB RAM and 32 KB flash.
- The AI's scores contain mistakes, and the game trusts them. Wrong answers hurt it, and "undo" helps.
- In PC simulation it did well, but the simulated player answers from the same table the game uses, so real
  players will do worse. I have not measured real-player accuracy yet.
- The 12 newest abstract questions are only filled in for the 39 abstract words I wrote by hand.

## Credits

- THINGS concept database: Hebart et al. (2019), "THINGS: A database of 1,854 object concepts and more than
  26,000 naturalistic object images", PLoS ONE. Used for the word list; please follow its license and cite it.
- Gemma 4 12B (Google), run through Ollama, for scoring answers. Follow the Gemma license terms.
- `wordfreq` was used to estimate how common a word is.
- Code was written with help from Claude (Anthropic).

Code in this repository is released under the MIT License (see `LICENSE`); the data files keep their original licenses.
