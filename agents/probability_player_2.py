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

    def __fill_round_attr(self, round_state):

        my_stack  = round_state["seats"][0]["stack"]
        op_stack  = round_state["seats"][1]["stack"]

        if round_state["seats"][0]["uuid"] != self.uuid:
            my_stack, op_stack = op_stack, my_stack

        self.stack = my_stack

        # check we are SB or BB
        if round_state["seats"][round_state["dealer_btn"]]["uuid"] == self.uuid:
            self.paid = 2 * round_state["small_blind_amount"]
            self.pos = "BB"
        else:
            self.paid = round_state["small_blind_amount"]
            self.pos = "SB"

        # op may have raised
        if self.pos == "BB":
            op_stack += (round_state["pot"]["main"]["amount"] - 3 * round_state["small_blind_amount"])

        self.lead = my_stack - op_stack
        
        # calculate margin
        remaining_rounds = 20 - round_state["round_count"] + 1
        loses_per_round  = round_state["small_blind_amount"] * 2 * 2
        self.margin = remaining_rounds * loses_per_round

        return

    def __convert_card_format(self, card):
        return f"{card[1]}{card[0].lower()}"

    def __calculate_probability(self, hole_card, comm_card):
        board = [self.__convert_card_format(card) for card in comm_card]
        holes = [self.__convert_card_format(card) for card in hole_card]
        holes.extend(["?", "?"])
        # Arguments: board, Exact, N(Monte-Carl), file_input, holes, Verbose
        pTie, pWin, pLose = Probability.calculate(board, True, 1, None, holes, False)
        return pWin

    def declare_action(self, valid_actions, hole_card, round_state):

        # Per-Round Attr
        # * self.uuid
        # * self.pos
        # * self.paid
        # * self.stack
        # * self.margin
        # * self.lead
        if round_state["street"] == "preflop":
            self.__fill_round_attr(round_state)


        #print(f"{bcolors.OKGREEN}Pos   : {self.pos}{bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}Paid  : {self.paid}{bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}Stack : {self.stack}{bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}Margin: {self.margin}{bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}Lead  : {self.lead}{bcolors.ENDC}")

        # Actions
        fold_action = valid_actions[0]
        call_action = valid_actions[1]
        raise_action = valid_actions[2]

        print(f"{bcolors.OKGREEN}{fold_action}{bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}{call_action}{bcolors.ENDC}")
        print(f"{bcolors.OKGREEN}{raise_action}{bcolors.ENDC}")

        # Action Decision
        if round_state["street"] == "preflop":

            # if winning, we fold till the end
            if self.lead - self.margin > 0:
                print(f"{bcolors.OKGREEN}Decide to Fold: winning{bcolors.ENDC}")
                action = fold_action["action"]
                amount = fold_action["amount"]
            # else, we play properly
            else:
                if call_action["amount"] <= self.margin // 2:
                    print(f"{bcolors.OKGREEN}Decide to Call: default call{bcolors.ENDC}")
                    action = call_action["action"]
                    amount = call_action["amount"]
                else:
                    print(f"{bcolors.OKGREEN}Decide to Fold: stack too high{bcolors.ENDC}")
                    action = fold_action["action"]
                    amount = fold_action["amount"]
        else:

            pWin = self.__calculate_probability(hole_card, round_state["community_card"])

            print(f"{bcolors.OKGREEN}pWin  : {pWin}{bcolors.ENDC}")

            # Strategies
            winning_prob_strat, winning_bet = [0.9, 0.5], [4, 6]
            losing_prob_strat,  losing_bet  = [0.7, 0.3], [3, 6]

            if self.lead > 0:
                strat = winning_prob_strat
                bet   = winning_bet
            else:
                strat = losing_prob_strat
                bet   = losing_bet

            # decide action based on probability
            decided = False
            for i in [0, 1]:
                if pWin >= strat[i]:
                    # bet margin//bet[0]
                    target_stack = self.margin // bet[i]
                    if target_stack > self.stack:
                        target_stack = self.stack

                    if raise_action["amount"]["min"] <= target_stack:
                        print(f"{bcolors.OKGREEN}Decide to Raise: high pWin{bcolors.ENDC}")
                        action = raise_action["action"]
                        amount = target_stack
                        decided = True
                        break
                    if call_action["amount"] <= target_stack:
                        print(f"{bcolors.OKGREEN}Decide to Call: medium pWin{bcolors.ENDC}")
                        action = call_action["action"]
                        amount = call_action["amount"]
                        decided = True
                        break

            if not decided:
                # if fold loses 
                if pWin >= 0.6 and self.paid >= self.margin * 2 / 3:
                    print(f"{bcolors.OKGREEN}Decide to Call: steel head{bcolors.ENDC}")
                    action = call_action["action"]
                    amount = call_action["amount"]
                else:
                    print(f"{bcolors.OKGREEN}Decide to Fold: against odds{bcolors.ENDC}")
                    action = fold_action["action"]
                    amount = fold_action["amount"]

        if amount >= 0:
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
