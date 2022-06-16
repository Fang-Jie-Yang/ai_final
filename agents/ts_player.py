from game.players import BasePokerPlayer
from numpy import argmax

import copy

class bcolors:
    HEADER    = '\033[95m'
    OKBLUE    = '\033[94m'
    OKCYAN    = '\033[96m'
    OKGREEN   = '\033[92m'
    WARNING   = '\033[93m'
    FAIL      = '\033[91m'
    ENDC      = '\033[0m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'

# pFold, pCall, pRaise for different hand strength
opponent_model = [
                    [0.9, 0.05, 0.025, 0.025], # very weak hand 
                    [0.7, 0.15, 0.075, 0.075], # weak hand 
                    [0.5, 0.25, 0.125, 0.125], # medium hand 
                    [0.3, 0.35, 0.150, 0.200], # strong hand 
                    [0.1, 0.45, 0.150, 0.250]  # very strong hand 
                 ]
preflop_HS = [
                [.85, .68, .67, .66, .66, .64, .63, .63, .62, .62, .61, .60, .59], 
                [.66, .83, .64, .64, .63, .61, .60, .59, .58, .58, .57, .56, .55],
                [.65, .62, .80, .61, .61, .59, .58, .56, .55, .55 ,.54, .53, .50],
                [.65, .62, .59, .78, .59, .57, .56, .54, .53, .52 ,.51, .50, .50],
                [.64, .61, .59, .57, .75, .56, .54, .53, .51, .49, .49, .48, .47],
                [.62, .59, .57, .55, .53, .72, .53, .51, .50, .48, .46, .46, .45],
                [.61, .58, .55, .53, .52, .50, .69, .50, .49, .47, .45, .43, .43],
                [.60, .57, .54, .52, .50, .48, .47, .67, .48, .46, .45, .43, .41],
                [.59, .56, .53, .50, .48, .47, .46, .45, .64, .46, .44, .42, .40],
                [.60, .55, .52, .49, .47, .45, .44, .43, .43, .61, .44, .43, .41],
                [.59, .54, .51, .48, .46, .43, .42, .41, .41, .41, .58, .42, .40],
                [.58, .54, .50, .66, .45, .43, .40, .39, .39, .39, .38, .55, .39],
                [.57, .53, .49, .47, .44, .42, .40, .37, .37, .37, .36, .35, .51]
             ]
# for the above table
order = {'A': 0, '2': 12, '3': 11, '4': 10, '5': 9, '6': 8, '7': 7, '8': 6, '9': 5, 'T': 4, 'J': 3, 'Q': 2, 'K': 1}

class 

class TSPlayer(BasePokerPlayer):


    def declare_action(self, valid_actions, hole_card, round_state):

        for op_HS in range(5):

        return action, amount  # action returned here is sent to the poker engine


    # player state
    # [
    #     Player(We)
    #     { 
    #         "pos": "first" or "second" -> init at round(street)
    #         "amount": -> init at street, update with action
    #         "stack": -> init at street, update with action
    #         "add_amount": -1 or real value -> init at street, update with action
    #         "HS": -> init at round, update with street
    #     }
    #     ,
    #     Oppoenent
    #     {
    #         "pos": "first" or "second" -> init at round(street)
    #         "amount": -> init at street, update with action
    #         "stack": -> init at street, update with action
    #         "add_amount": -1 or real value -> init at street, update with action
    #         "HS": -> init with assumption, update with action
    #     }
    # ]
    # game:
    #   SB_amount, BB_amount, init_stack, max_round

    def receive_game_start_message(self, game_info):
        self.init_stack = game_info["rule"]["initial_stack"]
        self.max_round = game_info["rule"]["max_round"]
        self.SB_amount = game_info["rule"]["small_blind_amount"]
        self.BB_amount = game_info["rule"]["small_blind_amount"] * 2
        self.player_states = [{"pos": -1, "amount": -1, "stack": -1, "add_amount": -1, "HS": -1},
                              {"pos": -1, "amount": -1, "stack": -1, "add_amount": -1, "HS": -1}]
        return 
 
    # round:
    #   lead, remaining rounds, hole

    def receive_round_start_message(self, round_count, hole_card, seats):
        if seats[0]["uuid"] == self.uuid:
            my_stack = seats[0]["stack"]
            op_stack = seats[1]["stack"]
        else:
            op_stack = seats[0]["stack"] 
            my_stack = seats[1]["stack"]
        self.lead = my_stack - op_stack - self.SB_amount
        self.remaining_round = self.max_round - round_count + 1
        self.hole = hole_card
        # look up table
        suit0, suit1 = self.hole[0][0], self.hole[1][0]
        num0 , num1  = self.hole[0][1], self.hole[1][1]
        i = min(order[num0], order[num1])
        j = max(order[num0], order[num1])
        if suit0 == suit1:
            pWin = preflop_HS[i][j]
        else:
            pWin = preflop_HS[j][i]

        if pWin <= 0.2:
            self.player_states[0]["HS"] = 0
        elif pWin <= 0.4:
            self.player_states[0]["HS"] = 1
        elif pWin <= 0.6:
            self.player_states[0]["HS"] = 2
        elif pWin <= 0.8:
            self.player_states[0]["HS"] = 3
        else:
            self.player_states[0]["HS"] = 4
        return

    def __convert_card_format(self, card):
        return f"{card[1]}{card[0].lower()}"

    # street:
    #   street, community card

    def receive_street_start_message(self, street, round_state):

        if self.uuid == round_state["seats"][0]["uuid"]:
            seat_no = 0
        else:
            seat_no = 1
        if seat_no == round_state["dealer_btn"]:
            self.pos = "second"
        else:
            self.pos = "first"
        self.player_states[0]["stack"] = seats[seat_no]["stack"]
        self.player_states[1]["stack"] = seats[not seat_no]["stack"]

        self.street = street
        self.community_card = round_state["community_card"]
        if self.community_card:
            # calc probability
            board = [self.__convert_card_format(card) for card in self.community_card]
            holes = [self.__convert_card_format(card) for card in self.hole]
            holes.extend(["?", "?"])
            # Arguments: board, Exact, N(Monte-Carl), file_input, holes, Verbose
            pTie, pWin, pLose = Probability.calculate(board, True, 1, None, holes, False)
            if pWin <= 0.2:
                self.player_states[0]["HS"] = 0
            elif pWin <= 0.4:
                self.player_states[0]["HS"] = 1
            elif pWin <= 0.6:
                self.player_states[0]["HS"] = 2
            elif pWin <= 0.8:
                self.player_states[0]["HS"] = 3
            else:
                self.player_states[0]["HS"] = 4

        self.player_states[0]["amount"] = 0
        self.player_states[1]["amount"] = 0
        self.player_states[0]["add_amount"] = -1
        self.player_states[1]["add_amount"] = -1
        return

    # action:
    #   my_amount, op_amount, my_add_amount, op_add_amount, op HS distribution

    def receive_game_update_message(self, action, round_state):

        last_action = round_state["action_histories"][self.street][-1]

        if last_action["uuid"] == self.uuid:
            player = 0
        else:
            player = 1
        if last_action["action"] == "FOLD":
            return
        self.player_states[player]["amount"] = last_action["amount"]
        self.player_states[player]["stack"] -= last_action["paid"]
        if "add_amount" in last_action:
            self.player_states[player]["add_amount"] = last_action["add_amount"]
        return

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

    # return best_ev, best_action
    def __tree_search(self, node, player_states):

        my_state = player_states[node]
        op_state = player_states[not node]

        # *FOLD*
        fold_ev = - my_state["amount"]
        # *CALL*
        call_ev = 0
        if my_state["pos"] == "second" or op_state["add_amount"] != -1: # The Street Ends
            if my_state["HS"] > op_state["HS"]
                call_ev += op_state["amount"]
            if me_state["HS"] < op_state["HS"]
                call_ev -= my_state["amount"]
        else: # The Street Continues
            if op_state["amount"] <= my_state["stack"]:
                # *CALL*: Street Continues
                new_player_states = copy.deepcopy(player_states)
                new_player_states[node]["amount"] = new_player_states[not node]["amount"]
                call_ev, __ = self.__tree_search(not node, new_player_states)
            else: 
                # *ALL-IN*: straight to the showdown
                if my_state["HS"] > op_state["HS"]:
                    call_ev += my_state["stack"]
                if my_state["HS"] < op_state["HS"]:
                    call_ev -= my_state["stack"]
        # *RAISE*
        small_raise_ev = 0
        big_raise_ev = 0
        if op_state["add_amount"] == -1:
            min_amount = my_state["amount"] + self.BB_amount
        else:
            min_amount = op_state["amount"] + op_state["add_amount"]
        # IF CAN RAISE
        if min_amount <= my_state["stack"]:

            small_raise = min_amount + (my_state["stack"] - min_amount) // 4
            new_player_states = copy.deepcopy(player_states)
            new_player_states[node]["add_amount"] = small_raise - op_state["amount"]
            new_player_states[node]["amount"] = small_raise
            small_raise_ev, __ = self.__tree_search(not node, new_player_states)

            big_raise = min_amount + 3 * (my_state["stack"] - min_amount) // 4
            new_player_states = copy.deepcopy(player_states)
            new_player_states[node]["add_amount"] = big_raise - op_state["amount"]
            new_player_states[node]["amount"] = big_raise
            big_raise_ev, __ = self.__tree_search(not node, new_player_states)

        if node == 0:
            best_ev = max([fold_ev, call_ev, small_raise_ev, big_raise_ev])
            best_action = argmax([fold_ev, call_ev, small_raise_ev, big_raise_ev])
        else:
            best_ev = 0
            best_ev -= fold_ev * opponent_model[my_state["HS"]][0]
            best_ev -= call_ev * opponent_model[my_state["HS"]][1]
            best_ev -= small_raise_ev * opponent_model[my_state["HS"]][2]
            best_ev -= big_raise_ev * opponent_model[my_state["HS"]][3]
            best_action = None
        return best_ev, best_action


def setup_ai():
    return TSPlayer()
