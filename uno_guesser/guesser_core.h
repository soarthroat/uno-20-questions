// 20 Questions engine for a small board. No Arduino-specific code in here,
// so the same file is tested on a PC and runs on the Uno.
//
// Every word has a "penalty" byte. Each answer adds a penalty to the words
// that disagree with it, and the word with the lowest penalty is the best guess.
#pragma once
#include <stdint.h>
#include <string.h>
#include "uno_table.h"

#ifndef pgm_read_byte               // building on a PC
#define pgm_read_byte(p) (*(const uint8_t *)(p))
#endif

#ifndef MARGIN
#define MARGIN       10     // guess early when the best word leads by this much
#endif
#ifndef MAX_TURNS
#define MAX_TURNS    30     // every question AND every guess uses one turn
#endif
#ifndef LAST_GUESSES
#define LAST_GUESSES  2     // the last turns are all guesses
#endif
#ifndef FORCED_AT
#define FORCED_AT    13     // a guess at this question count even without a clear leader
#endif
#ifndef MAX_SKIPS
#define MAX_SKIPS     3     // "sometimes" answers that don't use up a turn
#endif
#ifndef JITTER_DIV
#define JITTER_DIV   20     // pick randomly among questions within ~1/20 of the best split (0 = off)
#endif
#define DROPPED     255

enum Action : uint8_t { ASK, GUESS, GIVE_UP };

// answer levels: 0=no 1=probably not 2=sometimes 3=probably 4=yes
static const uint8_t COST_IF_YES[5] PROGMEM = {12, 5, 3, 1, 0};   // word's stored answer is yes
static const uint8_t COST_IF_NO[5]  PROGMEM = {0, 1, 3, 5, 12};   // word's stored answer is no
// how much a word counts when choosing a question, by how far behind the leader it is
static const uint8_t WEIGHT[25] PROGMEM = {255,199,155,120,94,73,57,44,35,27,21,16,13,10,8,6,5,4,3,2,2,1,1,1,1};

struct Game {
  uint8_t  pen[N_WORDS];
  uint8_t  asked[ROW_BYTES];
  uint8_t  n;            // questions asked so far
  uint8_t  lastGuessN;   // question count at the last guess
  uint8_t  guesses;
  uint8_t  seed;         // makes questions vary between games
  uint8_t  skips;        // free "sometimes" answers used
  uint32_t work;         // inner-loop count, only used for timing estimates
};

inline uint8_t answerBit(uint16_t w, uint8_t q) {
  return (pgm_read_byte(&ANSWERS[(uint32_t)w * ROW_BYTES + (q >> 3)]) >> (q & 7)) & 1;
}

inline void gameStart(Game &g, uint8_t seed = 0) {
  for (uint16_t i = 0; i < N_WORDS; i++) g.pen[i] = pgm_read_byte(&PRIOR[i]);
  memset(g.asked, 0, sizeof(g.asked));
  g.n = 0; g.lastGuessN = 255; g.guesses = 0; g.work = 0; g.seed = seed; g.skips = 0;
}

// Record the player's answer to question q (level 0..4).
inline void gameAnswer(Game &g, uint8_t q, uint8_t level) {
  g.asked[q >> 3] |= 1 << (q & 7);
  g.n++;
  if (level == 2 && g.skips < MAX_SKIPS) g.skips++;
  uint8_t cy = pgm_read_byte(&COST_IF_YES[level]);
  uint8_t cn = pgm_read_byte(&COST_IF_NO[level]);
  for (uint16_t i = 0; i < N_WORDS; i++) {
    if (g.pen[i] == DROPPED) continue;
    uint16_t p = g.pen[i] + (answerBit(i, q) ? cy : cn);
    g.pen[i] = p > 254 ? 254 : p;
  }
}

inline void gameWrongGuess(Game &g, uint16_t w) { g.pen[w] = DROPPED; }

// Decide what to do next. For ASK, *out is a question number; for GUESS, a word number.
inline Action gameNext(Game &g, uint16_t *out) {
  uint16_t best = 0;
  for (uint16_t i = 1; i < N_WORDS; i++) if (g.pen[i] < g.pen[best]) best = i;
  uint16_t second = (best == 0) ? 1 : 0;
  for (uint16_t i = 0; i < N_WORDS; i++) if (i != best && g.pen[i] < g.pen[second]) second = i;

  uint8_t turns = g.n + g.guesses - g.skips;
  if (turns >= MAX_TURNS || g.pen[best] == DROPPED) return GIVE_UP;
  bool endgame = turns >= MAX_TURNS - LAST_GUESSES;
  bool lead = g.n >= 4 && (uint16_t)g.pen[second] - g.pen[best] >= MARGIN;
  bool forced = g.n == FORCED_AT;
  if (endgame || ((lead || forced) && g.n != g.lastGuessN)) {
    g.lastGuessN = g.n; g.guesses++; *out = best; return GUESS;
  }

  {
    uint8_t base = g.pen[best];
    int16_t bestQ = -1;
    uint32_t bestScore = 0xFFFFFFFFUL;
    for (uint8_t q = 0; q < N_QUESTIONS; q++) {
      if (g.asked[q >> 3] & (1 << (q & 7))) continue;
      uint32_t sum = 0, yes = 0;
      for (uint16_t i = 0; i < N_WORDS; i++) {
        uint8_t p = g.pen[i];
        if (p == DROPPED) continue;
        uint8_t d = p - base;
        if (d > 24) continue;
        uint8_t w = pgm_read_byte(&WEIGHT[d]);
        sum += w;
        if (answerBit(i, q)) yes += w;
      }
      g.work += N_WORDS;
      if (yes * 200 < sum || (sum - yes) * 200 < sum) continue;      // nearly everyone agrees
      uint32_t score = (2 * yes > sum) ? 2 * yes - sum : sum - 2 * yes;
#if JITTER_DIV > 0
      uint16_t h = (g.seed * 251u) ^ (q * 2654u) ^ (g.n * 40503u);   // same state -> same choice, so "back" repeats the question
      h ^= h >> 7; h *= 0x9E37u; h ^= h >> 9;
      score += h % (sum / JITTER_DIV + 1);
#endif
      if (score < bestScore) { bestScore = score; bestQ = q; }
    }
    if (bestQ >= 0) { *out = bestQ; return ASK; }
  }

  g.lastGuessN = g.n; g.guesses++; *out = best; return GUESS;
}

// Copy the i-th string out of a PROGMEM blob of NUL-separated strings.
inline void blobString(const char *blob, uint16_t index, char *buf, uint8_t max) {
  const char *p = blob;
  while (index--) { while (pgm_read_byte(p++)) {} }
  uint8_t k = 0;
  char c;
  while (k < max - 1 && (c = (char)pgm_read_byte(p++))) buf[k++] = c;
  buf[k] = 0;
}
inline void wordName(uint16_t i, char *buf, uint8_t max)     { blobString(NAMES, i, buf, max); }
inline void questionText(uint8_t q, char *buf, uint8_t max)  { blobString(QUESTIONS, q, buf, max); }

// Turn number for the screen (1..MAX_TURNS) of the prompt about to be shown.
inline uint8_t gameTurn(const Game &g) { return g.n + g.guesses - g.skips + 1; }

// History entries: a question answer is (level << 8) | question; a wrong guess is 0x8000 | word.
// Going back = start again and replay everything except the last entry.
inline void gameReplay(Game &g, const uint16_t *hist, uint8_t count) {
  uint8_t seed = g.seed;
  gameStart(g, seed);
  for (uint8_t i = 0; i < count; i++) {
    uint16_t e = hist[i];
    if (e & 0x8000) { gameWrongGuess(g, e & 0x7FFF); g.guesses++; g.lastGuessN = g.n; }
    else gameAnswer(g, e & 0xFF, e >> 8);
  }
}
