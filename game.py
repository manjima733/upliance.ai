"""
AI Judge for Rock-Paper-Scissors Plus
Clean architecture: Intent Understanding → Validation → Game Logic → Response
"""

import json
import random
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

# Using Google Gemini (free tier)
try:
    import google.generativeai as genai
except ImportError:
    print("Please install: pip install google-generativeai")
    exit(1)


class GameState:
    """Minimal state tracking"""
    def __init__(self):
        self.round_num = 0
        self.bomb_used = False
        self.user_score = 0
        self.bot_score = 0
        self.rounds_history = []
    
    def use_bomb(self):
        self.bomb_used = True
    
    def increment_round(self):
        self.round_num += 1
    
    def update_score(self, winner):
        if winner == "user":
            self.user_score += 1
        elif winner == "bot":
            self.bot_score += 1


class AIJudge:
    """
    AI Judge that evaluates moves using LLM prompting
    Architecture:
    1. Intent Understanding - What did user mean?
    2. Validation - Is it valid given rules and state?
    3. Game Logic - Who won?
    4. Response Generation - What to show user?
    """
    
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name='models/gemini-flash-latest',
            generation_config={
                'temperature': 0.1,  # Low temperature for consistent rule application
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 1024,
            }
        )
        self.system_prompt = SYSTEM_PROMPT
    
    def judge_move(self, user_input, bot_move, game_state):
        """
        Main judging function - delegates to LLM for decision making
        
        Args:
            user_input: Raw text from user
            bot_move: Bot's chosen move
            game_state: Current game state
            
        Returns:
            dict: Structured judgment with validity, winner, reasoning
        """
        # Create prompt with current context
        user_prompt = USER_PROMPT_TEMPLATE.format(
            round_num=game_state.round_num,
            bomb_used=game_state.bomb_used,
            user_input=user_input,
            bot_move=bot_move
        )
        
        # Send to LLM for judgment
        try:
            response = self.model.generate_content(
                f"{self.system_prompt}\n\n{user_prompt}"
            )
            
            # Parse JSON response
            result = self._parse_llm_response(response.text)
            
            # Validate and clean response
            return self._validate_judgment(result, game_state)
            
        except Exception as e:
            # Fallback for API errors
            return {
                "move_validity": "INVALID",
                "user_move": None,
                "reasoning": f"Error processing move: {str(e)}",
                "round_winner": "bot",
                "round_explanation": "Technical error - bot wins by default",
                "bomb_used_this_round": False
            }
    
    def _parse_llm_response(self, response_text):
        """Extract JSON from LLM response"""
        # Clean markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        return json.loads(text)
    
    def _validate_judgment(self, judgment, game_state):
        """
        Validate LLM judgment for correctness
        This is minimal code-based validation, main logic is in prompt
        """
        required_fields = [
            "move_validity", "user_move", "reasoning",
            "round_winner", "round_explanation", "bomb_used_this_round"
        ]
        
        for field in required_fields:
            if field not in judgment:
                judgment[field] = None
        
        # Ensure validity is one of expected values
        if judgment["move_validity"] not in ["VALID", "INVALID", "UNCLEAR"]:
            judgment["move_validity"] = "INVALID"
        
        # Ensure winner is valid
        if judgment["round_winner"] not in ["user", "bot", "draw"]:
            judgment["round_winner"] = "bot"  # Safe default
        
        return judgment


class GameEngine:
    """
    Orchestrates the game flow
    Separation: Engine handles flow, Judge handles decisions
    """
    
    def __init__(self, api_key):
        self.judge = AIJudge(api_key)
        self.state = GameState()
        self.valid_moves = ["rock", "paper", "scissors", "bomb"]
    
    def get_bot_move(self):
        """Bot randomly selects from basic moves (no bomb)"""
        return random.choice(["rock", "paper", "scissors"])
    
    def play_round(self, user_input):
        """
        Play a single round
        
        Returns:
            dict: Round results with feedback
        """
        self.state.increment_round()
        bot_move = self.get_bot_move()
        
        # Delegate to AI Judge for decision
        judgment = self.judge.judge_move(user_input, bot_move, self.state)
        
        # Update state based on judgment
        if judgment["bomb_used_this_round"]:
            self.state.use_bomb()
        
        self.state.update_score(judgment["round_winner"])
        
        # Store history
        self.state.rounds_history.append({
            "round": self.state.round_num,
            "user_input": user_input,
            "user_move": judgment["user_move"],
            "bot_move": bot_move,
            "validity": judgment["move_validity"],
            "winner": judgment["round_winner"],
            "reasoning": judgment["reasoning"]
        })
        
        # Format response for user
        return self._format_round_response(judgment, bot_move, user_input)
    
    def _format_round_response(self, judgment, bot_move, user_input):
        """
        Response Generation - Format clear feedback for user
        """
        response = {
            "round_number": self.state.round_num,
            "user_input": user_input,
            "user_move": judgment["user_move"],
            "bot_move": bot_move,
            "validity": judgment["move_validity"],
            "winner": judgment["round_winner"],
            "reasoning": judgment["reasoning"],
            "explanation": judgment["round_explanation"],
            "current_score": {
                "user": self.state.user_score,
                "bot": self.state.bot_score
            }
        }
        return response
    
    def get_final_result(self):
        """Determine final game outcome"""
        if self.state.user_score > self.state.bot_score:
            result = "User wins!"
        elif self.state.bot_score > self.state.user_score:
            result = "Bot wins!"
        else:
            result = "Draw!"
        
        return {
            "result": result,
            "final_score": {
                "user": self.state.user_score,
                "bot": self.state.bot_score
            },
            "rounds_played": self.state.round_num,
            "history": self.state.rounds_history
        }


def print_round_result(round_data):
    """Pretty print round results"""
    print(f"\n{'='*60}")
    print(f"ROUND {round_data['round_number']}")
    print(f"{'='*60}")
    print(f"Your input: '{round_data['user_input']}'")
    print(f"Move validity: {round_data['validity']}")
    
    if round_data['user_move']:
        print(f"Your move: {round_data['user_move']}")
    
    print(f"Bot's move: {round_data['bot_move']}")
    print(f"\nReasoning: {round_data['reasoning']}")
    print(f"Explanation: {round_data['explanation']}")
    print(f"\nRound winner: {round_data['winner'].upper()}")
    print(f"Score - You: {round_data['current_score']['user']} | Bot: {round_data['current_score']['bot']}")
    print(f"{'='*60}\n")


def main():
    """Main game loop"""
    print("="*60)
    print("ROCK-PAPER-SCISSORS PLUS - AI Judge Edition")
    print("="*60)
    print("\nRules:")
    print("- Valid moves: rock, paper, scissors, bomb")
    print("- bomb beats everything but can only be used ONCE")
    print("- Invalid/unclear moves waste your turn")
    print("- Best of 5 rounds")
    print("\n" + "="*60 + "\n")
    
    # Initialize (you need to set your API key)
    api_key = input("Enter your Google Gemini API key: ").strip()
    
    if not api_key:
        print("Error: API key required")
        return
    
    game = GameEngine(api_key)
    max_rounds = 5
    
    # Play rounds
    for i in range(max_rounds):
        user_input = input(f"\nRound {i+1} - Enter your move: ").strip()
        
        if not user_input:
            print("Empty input - skipping turn")
            continue
        
        round_result = game.play_round(user_input)
        print_round_result(round_result)
    
    # Final results
    final = game.get_final_result()
    print("\n" + "="*60)
    print("GAME OVER")
    print("="*60)
    print(f"\n{final['result']}")
    print(f"Final Score - You: {final['final_score']['user']} | Bot: {final['final_score']['bot']}")
    print(f"Rounds played: {final['rounds_played']}\n")
    print("="*60)


if __name__ == "__main__":
    main()
