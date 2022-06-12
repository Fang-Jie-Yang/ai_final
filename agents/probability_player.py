from game.players import BasePokerPlayer

import sys
sys.path.append("agents/holdem_calc")

import copy

import parallel_holdem_calc as Probability

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ProbabilityPlayer(BasePokerPlayer):

    def __convert_card_format(self, card):
        return f"{card[1]}{card[0].lower()}"

    def declare_action(self, valid_actions, hole_card, round_state):

        fold_action = valid_actions[0]
        call_action = valid_actions[1]
        raise_action = valid_actions[2]

        pot_money = round_state["pot"]["main"]["amount"]
        print(f"{bcolors.OKGREEN}|Prob Player|: pot money is {pot_money}{bcolors.ENDC}")

        stack0 = round_state["seats"][0]["stack"]
        stack1 = round_state["seats"][1]["stack"]
        if round_state["seats"][0]["uuid"] == self.uuid:
            my_stack = stack0
            op_stack = stack1
        else:
            my_stack = stack1
            op_stack = stack0
        
        if round_state["street"] == "preflop":

            self.paid = 0

            # check we are SB or BB
            if round_state["seats"][round_state["dealer_btn"]]["uuid"] == self.uuid:
                self.paid = 2 * round_state["small_blind_amount"]
                self.pos = "BB"
            else:
                self.paid = round_state["small_blind_amount"]
                self.pos = "SB"

            # op may have raised
            if self.pos == "BB":
                op_stack += (pot_money - 3 * round_state["small_blind_amount"])
            lead = my_stack - op_stack

            remaining_rounds = 20 - round_state["round_count"] + 1
            loses = round_state["small_blind_amount"] * 2 * 2
            self.margin = remaining_rounds * loses
            # if winning, we fold till the end
            if lead - self.margin > 0:
                action = fold_action["action"]
                amount = fold_action["amount"]
                print(f"{bcolors.OKGREEN}|Prob Player|: fold reason -> winning!{bcolors.ENDC}")
            # else, we play properly
            else:
                # TODO: try to eval hand strength 
                action = call_action["action"]
                amount = call_action["amount"]
        else:
            # calculate probabilities
            board = [self.__convert_card_format(card) for card in round_state["community_card"]]
            holes = [self.__convert_card_format(card) for card in hole_card]
            holes.extend(["?", "?"])
            # Arguments: board, Exact, N(Monte-Carl), file_input, holes, Verbose
            pTie, pWin, pLose = Probability.calculate(board, True, 1, None, holes, False)
            pGood = pTie + pWin
            print(f"{bcolors.OKGREEN}|Prob Player|: {pGood}:{pLose}{bcolors.ENDC}")

            # decide action based on probability
            if round_state["street"] == "flop":
                if pWin >= 0.5:
                    action = raise_action["action"]
                    amount = my_stack // 10
                    print(f"{bcolors.OKGREEN}|Prob Player|: Raise at flop{bcolors.ENDC}")
                elif pWin >= 0.25 and call_action["amount"] < self.margin / 3:
                    action = call_action["action"]
                    amount = call_action["amount"]
                    print(f"{bcolors.OKGREEN}|Prob Player|: Call at flop{bcolors.ENDC}")
                else:
                    action = fold_action["action"]
                    amount = fold_action["amount"]
                    print(f"{bcolors.OKGREEN}|Prob Player|: fold reason -> bad flop{bcolors.ENDC}")
                    
            if round_state["street"] == "turn" or round_state["street"] == "river":
                if pWin >= 0.85:
                    action = raise_action["action"]
                    amount = raise_action["amount"]["max"] // 10
                    print(f"{bcolors.OKGREEN}|Prob Player|: Raise at turn/river{bcolors.ENDC}")
                elif (pot_money + call_action["amount"]) / (self.paid + call_action["amount"]) > pWin:
                    if call_action["amount"] < self.margin / 3:
                        action = call_action["action"]
                        amount = call_action["amount"]
                        print(f"{bcolors.OKGREEN}|Prob Player|: Call at turn/river{bcolors.ENDC}")
                    else:
                        action = fold_action["action"]
                        amount = fold_action["amount"]
                        print(f"{bcolors.OKGREEN}|Prob Player|: fold reason -> stack too high{bcolors.ENDC}")
                else:
                    action = fold_action["action"]
                    amount = fold_action["amount"]
                    print(f"{bcolors.OKGREEN}|Prob Player|: fold reason -> bad ture/river{bcolors.ENDC}")

        self.paid += amount
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
