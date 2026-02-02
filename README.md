# upliance.ai


# AI Judge for Rock-Paper-Scissors Plus



---

## Overview

This solution implements an AI Judge that evaluates user moves in a Rock-Paper-Scissors Plus game using **prompt-driven decision making** rather than hardcoded logic. The focus is on prompt quality, clean architecture, and robust edge-case handling.

---

## Architecture

The solution follows a clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    GameEngine                           │
│                 (Orchestration Layer)                   │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│                    AIJudge                              │
│          (Prompt-Driven Decision Making)                │
│                                                         │
│  1. Intent Understanding ──────────────────┐            │
│     "What did the user mean?"              │            │
│                                            │            │
│  2. Validation ────────────────────────────┤            │
│     "Is it valid given rules and state?"   │            │
│                                            │            │
│  3. Game Logic ────────────────────────────┤            │
│     "Who won the round?"                   │            │
│                                            │            │
│  4. Response Generation ───────────────────┘            │
│     "What should the user see?"                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│                  GameState                              │
│            (Minimal State Tracking)                     │
│  - Round number                                         │
│  - Bomb usage                                           │
│  - Scores                                               │
└─────────────────────────────────────────────────────────┘
```

### Key Components

1. **AIJudge** - Prompt-driven decision maker
   - Receives user input + game context
   - Delegates to LLM with carefully crafted prompts
   - Returns structured judgments

2. **GameEngine** - Orchestration layer
   - Manages game flow
   - Updates state based on judgments
   - Formats user-facing responses

3. **GameState** - Minimal state storage
   - Tracks bomb usage (critical constraint)
   - Maintains scores and round count

---

## Prompt Design Rationale

### Why This Structure?

The prompt is designed with several key principles:

#### 1. **Clear Rule Definition**
```
The system prompt explicitly lists:
- All valid moves
- Win conditions
- Validity criteria
- Special constraints (bomb usage)
```

**Rationale**: LLMs excel when given explicit, unambiguous rules. By front-loading all game logic into the prompt, we avoid hardcoding and make the system easily modifiable.

#### 2. **Structured Output Requirements**
```json
{
  "move_validity": "VALID" | "INVALID" | "UNCLEAR",
  "user_move": "rock" | "paper" | "scissors" | "bomb" | null,
  "reasoning": "...",
  "round_winner": "user" | "bot" | "draw",
  "round_explanation": "...",
  "bomb_used_this_round": true | false
}
```

**Rationale**: Forcing JSON output makes parsing reliable and ensures the LLM addresses all necessary decision points. This separates thinking (LLM) from parsing (code).

#### 3. **Edge Case Guidance**
The prompt explicitly handles:
- Typos (lenient vs strict threshold)
- Conversational variations ("I choose rock")
- Ambiguous inputs ("rock or paper")
- Constraint violations (bomb already used)
- Empty/nonsensical inputs

**Rationale**: By providing examples of edge cases directly in the prompt, we guide the model's behavior without needing extensive if-else logic.

#### 4. **Three-Tier Validity System**
- **VALID**: Clear, rule-compliant move
- **INVALID**: Clear but rule-breaking (wrong move, bomb reuse)
- **UNCLEAR**: Ambiguous intent

**Rationale**: This tri-state system handles the inherent ambiguity in natural language while maintaining strict game rules. It's more nuanced than binary valid/invalid.

#### 5. **Context Injection**
Each judgment receives:
- Current round number
- Bomb usage state
- User input
- Bot's move

**Rationale**: The LLM needs full context to make informed decisions. This approach treats each round as a fresh evaluation with proper state context.

---


- 

---

## Testing Approach

### Manual Test Cases
The solution was designed considering these scenarios:

**Valid Inputs:**
- "rock" → VALID
- "SCISSORS!!!" → VALID
- "I choose paper" → VALID
- "bomb" (first use) → VALID

**Invalid Inputs:**
- "gun" → INVALID
- "bomb" (second use) → INVALID
- "hello" → INVALID
- "" → INVALID (code-level)

**Unclear Inputs:**
- "rock or paper" → UNCLEAR
- "r" → UNCLEAR
- "maybe scissors?" → UNCLEAR
- "rck" → UNCLEAR (depends on threshold)

---
## Dependencies

```bash
pip install google-generativeai
```

---

## Usage

1. Get a free Google Gemini API key from https://ai.google.dev/
2. Run: `python game.py`
3. Enter your API key when prompted
4. Play 5 rounds
5. See final results

---

## Files

- `prompts.py` - System and user prompt templates
- `game.py` - Game engine and AI Judge implementation
- `README.md` - This file

---



## Author Notes

This solution demonstrates that with careful prompt engineering, complex decision-making can be delegated to LLMs while maintaining:
- Correctness (rules are followed)
- Explainability (reasoning is provided)
- Robustness (edge cases are handled)
- Maintainability (logic is readable)

The focus was on creating a prompt that acts as a "rule book" the LLM can reliably consult, rather than trying to encode game logic in code.
