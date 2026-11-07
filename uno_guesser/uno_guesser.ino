// 20 Questions on an Arduino Uno: think of a thing (or an idea, like "nothing") and it guesses it.
// It gets 30 turns in total (MAX_TURNS in guesser_core.h): every question and every guess uses one.
//
// Wiring:
//   LCD (I2C backpack): GND->GND, VCC->5V, SDA->A4, SCL->A5
//   Answer buttons, each between a pin and GND (a bare jumper wire touched to GND works too):
//     D2 = Yes      D3 = Probably      D4 = Sometimes / not sure
//     D5 = Probably not      D6 = No
//   When it guesses a word, Yes or Probably means "right"; any other button means "wrong".
//   Pressed a wrong answer? HOLD D4 (the middle button) for one second to go back one step.
//   A normal "sometimes" answer doesn't use up a turn (up to 3 per game).
//
// Library needed: "LiquidCrystal I2C" by Frank de Brabander.
// Change LCD_ADDRESS to 0x3F if the screen stays blank.

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include "guesser_core.h"

#define LCD_ADDRESS 0x27

LiquidCrystal_I2C lcd(LCD_ADDRESS, 16, 2);
Game game;
uint16_t hist[MAX_TURNS + MAX_SKIPS + 2];                 // what has happened this game, for "back"
uint8_t histN;

const uint8_t BUTTON_PIN[5] = {2, 3, 4, 5, 6};          // yes, probably, sometimes, probably not, no
const uint8_t BUTTON_LEVEL[5] = {4, 3, 2, 1, 0};        // the answer level each button gives
const uint8_t STAR[8] = {0b00100, 0b10101, 0b01110, 0b11111, 0b01110, 0b10101, 0b00100, 0};

// ------------------------------------------------------------------ buttons
#define BACK 5                                            // returned for a 1-second hold of the middle button
#define HOLD_MS 1000

uint8_t waitForButton() {
  while (true) {
    for (uint8_t b = 0; b < 5; b++) {
      if (digitalRead(BUTTON_PIN[b]) == LOW) {
        delay(30);                                        // debounce
        if (digitalRead(BUTTON_PIN[b]) == LOW) {
          unsigned long t = millis();
          bool held = false;
          while (digitalRead(BUTTON_PIN[b]) == LOW) {     // wait for release
            if (b == 2 && !held && millis() - t >= HOLD_MS) { held = true; digitalWrite(LED_BUILTIN, HIGH); }
          }
          digitalWrite(LED_BUILTIN, LOW);
          delay(30);
          return held ? BACK : b;
        }
      }
    }
  }
}

// ------------------------------------------------------------------ screen
void printRow(uint8_t row, const char *text) {
  lcd.setCursor(0, row);
  uint8_t i = 0;
  for (; i < 16 && text[i]; i++) lcd.write(text[i]);
  for (; i < 16; i++) lcd.write(' ');
}

// Text on the left of the top row and on the whole bottom row; "7/20" in the top-right corner.
// The text is broken at a space (the build script checks that every question fits).
void showPrompt(uint8_t turn, const char *text) {
  char row0[11], row1[17];
  uint8_t len = strlen(text), cut = len;
  if (len > 10) {
    cut = 10;
    for (uint8_t i = 10; i > 0; i--) if (text[i] == ' ') { cut = i; break; }
  }
  uint8_t k = 0;
  for (uint8_t i = 0; i < cut; i++) row0[k++] = text[i];
  row0[k] = 0;
  const char *rest = text + cut;
  while (*rest == ' ') rest++;
  k = 0;
  while (*rest && k < 16) row1[k++] = *rest++;
  row1[k] = 0;

  lcd.clear();
  lcd.setCursor(0, 0); lcd.print(row0);
  uint8_t digits = turn >= 10 ? 5 : 4;                   // "7/30" or "13/30"
  lcd.setCursor(16 - digits, 0);
  if (turn >= 10) lcd.write('0' + turn / 10);             // (no lcd.print(number): it needs a 33-byte buffer)
  lcd.write('0' + turn % 10);
  lcd.write('/');
  lcd.write('0' + MAX_TURNS / 10);
  lcd.write('0' + MAX_TURNS % 10);
  lcd.setCursor(0, 1); lcd.print(row1);
}

void blinkBacklight(uint8_t times, uint16_t ms) {
  for (uint8_t i = 0; i < times; i++) {
    lcd.noBacklight(); delay(ms);
    lcd.backlight();   delay(ms);
  }
}

void showTwoRows(const char *top, const char *bottom) {
  lcd.clear();
  printRow(0, top);
  printRow(1, bottom);
}

// Win: flashing backlight, stars sweeping along the bottom row, then the word.
void winScreen(const char *word) {
  showTwoRows("     I WIN!", "");
  blinkBacklight(3, 150);
  for (uint8_t i = 0; i < 16; i++) { lcd.setCursor(i, 1); lcd.write((uint8_t)0); delay(60); }
  for (uint8_t i = 0; i < 16; i++) { lcd.setCursor(i, 1); lcd.write(' ');        delay(40); }
  showTwoRows("I WIN! It was:", word);
  waitForButton();
}

// Lose: "You got me!" slides in from the right, then two slow blinks.
void loseScreen() {
  const char *msg = "You got me!";
  uint8_t len = strlen(msg);
  lcd.clear();
  for (int8_t x = 15; x >= (16 - len) / 2; x--) {
    lcd.setCursor(0, 0);
    for (uint8_t i = 0; i < 16; i++) {
      int8_t k = i - x;
      lcd.write(k >= 0 && k < len ? msg[k] : ' ');
    }
    delay(70);
  }
  blinkBacklight(2, 400);
  showTwoRows("  You got me!", " Play again?");
  waitForButton();
}

// Wrong guess: a quick flash so each miss is visible.
void wrongGuessScreen() {
  showTwoRows("  Hmm... no.", "  Let me think");
  delay(900);
}

// ------------------------------------------------------------------ game
void goBack() {                                           // forget the last answer (or wrong guess)
  if (histN > 0) histN--;
  gameReplay(game, hist, histN);
  showTwoRows("  Going back...", "");
  delay(500);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  for (uint8_t b = 0; b < 5; b++) pinMode(BUTTON_PIN[b], INPUT_PULLUP);
  lcd.init();
  lcd.backlight();
  lcd.createChar(0, (uint8_t *)STAR);
}

void loop() {
  char text[28];

  showTwoRows("Think of a word,", "press any button");
  waitForButton();
  gameStart(game, (uint8_t)(micros() >> 4) ^ (uint8_t)analogRead(A0));   // varies the questions between games
  histN = 0;
  static bool tipShown = false;
  if (!tipShown) {
    tipShown = true;
    showTwoRows("Wrong button?", "Hold middle=back");
    delay(2000);
  }

  while (true) {
    lcd.setCursor(0, 0); lcd.print(F("Thinking...    "));   // the next step takes about 0.3 s
    uint16_t out;
    uint8_t turn = gameTurn(game);
    Action a = gameNext(game, &out);

    if (a == ASK) {
      questionText(out, text, sizeof text);
      showPrompt(turn, text);
      uint8_t b = waitForButton();
      if (b == BACK) { goBack(); continue; }
      gameAnswer(game, out, BUTTON_LEVEL[b]);
      hist[histN++] = ((uint16_t)BUTTON_LEVEL[b] << 8) | out;

    } else if (a == GUESS) {
      char name[20];
      wordName(out, name, sizeof name);
      strcpy(text, "Is it ");
      strcat(text, name);
      strcat(text, "?");
      showPrompt(turn, text);
      uint8_t b = waitForButton();
      if (b == BACK) { goBack(); continue; }
      if (b <= 1) {                                       // yes / probably
        winScreen(name);
        break;
      }
      gameWrongGuess(game, out);
      hist[histN++] = 0x8000 | out;
      if (gameTurn(game) <= MAX_TURNS) wrongGuessScreen();

    } else {
      loseScreen();
      break;
    }
  }
}
