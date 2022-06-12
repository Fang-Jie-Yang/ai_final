from game.players import BasePokerPlayer

import sys
sys.path.append("agents/holdem_calc")

import copy

import parallel_holdem_calc as Probability

class ProbabilityPlayer(BasePokerPlayer):

    def __convert_card_format(self, card):
        return f"{card[1]}{card[0].lower()}"

    def declare_action(self, valid_actions, hole_card, round_state):

        fold_action = valid_actions[0]
        call_action = valid_actions[1]
        raise_action = valid_actions[2]

        if round_state["street"] == "preflop":
            # simply call in preflop
            # TODO: try to eval head strength 
            action = call_action["action"]
            amount = call_action["amount"]
        else:
            # calculate probability of winning or tie
            board = [self.__convert_card_format(card) for card in round_state["community_card"]]
            holes = [self.__convert_card_format(card) for card in hole_card]
            holes.extend(["?", "?"])
            # Arguments: board, Exact, N(Monte-Carl), file_input, holes, Verbose
            probs = Probability.calculate(board, True, 1, None, holes, False)
            tie = probs[0]
            win = probs[1]
            # decide action based on probability
            good_prob = tie + win
            print("*Prob Player*:", good_prob)
            if good_prob < 0.2:
                action = fold_action["action"]
                amount = fold_action["amount"]
            elif good_prob >= 0.2 and good_prob < 0.8:
                action = call_action["action"]
                amount = call_action["amount"]
            elif good_prob >= 0.8:
                action = raise_action["action"]
                amount = raise_action["amount"]["max"] * good_prob // 2

        return action, amount  # action returned here is sent to the poker engine

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

def setup_ai():
    return ProbabilityPlayer()
