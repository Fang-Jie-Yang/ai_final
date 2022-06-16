from game.players import BasePokerPlayer

import sys
sys.path.append("/tmp2/b08902059/python-packages")
sys.path.append("agents/holdem_calc")

import numpy as np

import random

import parallel_holdem_calc as Probability

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

class TSPlayer(BasePokerPlayer):

    def declare_action(self, valid_actions, hole_card, round_state):

        '''
        call_action_info = valid_actions[1]

        action, amount = call_action_info["action"], call_action_info["amount"]

        return action, amount  # action returned here is sent to the poker engine
        '''

        fold_action_info = valid_actions[0]
        call_action_info = valid_actions[1]
        raise_action_info = valid_actions[2]

        if self.street == "preflop":
            if self.player_states[0]["HS"] <= 1:
                action = fold_action_info["action"]
                amount = fold_action_info["amount"]
            else:
                action = call_action_info["action"]
                amount = call_action_info["amount"]
            return action, amount

        HS_range = [0, 1, 2, 3, 4]
        avg_evs = np.array([0, 0, 0, 0])

        for op_HS in range(5):
            if self.op_HS_assumption[op_HS] == 0:
                continue
            self.player_states[1]["HS"] = op_HS
            HS_ev = self.__tree_search(0, self.player_states)
            avg_evs = avg_evs + HS_ev * self.op_HS_assumption[op_HS]

        print(f"{bcolors.OKBLUE}{avg_evs}{bcolors.ENDC}")

        choice = np.argmax(avg_evs)
        if choice == 0:
            action = fold_action_info["action"]
            amount = fold_action_info["amount"]
        elif choice == 1:
            action = call_action_info["action"]
            amount = call_action_info["amount"]
        elif raise_action_info["amount"]["min"] == -1:
            action = call_action_info["action"]
            amount = call_action_info["amount"]
        elif choice == 2:
            action = raise_action_info["action"]
            amount = raise_action_info["amount"]["min"]
        elif choice == 3:
            action = raise_action_info["action"]
            amount = (raise_action_info["amount"]["min"] + raise_action_info["amount"]["max"]) // 3
        print(f"{bcolors.OKBLUE}{action}{bcolors.ENDC}")

        return action, amount  # action returned here is sent to the poker engine


    # player state
    # [
    #     Player(We)
    #     { 
    #         "pos": "first" or "second" -> init at round(preflop)
    #         "in_pot": init at round(preflop), update with action
    #         "amount": -> init at street, update with action
    #         "stack": -> init at street, update with action
    #         "add_amount": -1 or real value -> init at street, update with action
    #         "HS": -> init at round, update with street
    #     }
    #     ,
    #     Oppoenent
    #     {
    #         "pos": "first" or "second" -> init at round(street)
    #         "in_pot": init at round(preflop), update with action
    #         "amount": -> init at street, update with action
    #         "stack": -> init at street, update with action
    #         "add_amount": -1 or real value -> init at street, update with action
    #         "HS": -> init with assumption, update with action, street
    #     }
    # ]
    # op_HS_assumption = [a, b, c, d, e]
    # game:
    #   SB_amount, BB_amount, init_stack, max_round

    def receive_game_start_message(self, game_info):
        self.init_stack = game_info["rule"]["initial_stack"]
        self.max_round = game_info["rule"]["max_round"]
        self.SB_amount = game_info["rule"]["small_blind_amount"]
        self.BB_amount = game_info["rule"]["small_blind_amount"] * 2
        self.player_states = [{"pos": -1, "amount": -1, "in_pot": -1, "stack": -1, "add_amount": -1, "HS": -1},
                              {"pos": -1, "amount": -1, "in_pot": -1, "stack": -1, "add_amount": -1, "HS": -1}]
        #print(f"{bcolors.OKGREEN}(Game Start) Init player_states{bcolors.ENDC}")
        #print(f"{bcolors.OKGREEN}{self.player_states[0]}{bcolors.ENDC}")
        #print(f"{bcolors.OKGREEN}{self.player_states[1]}{bcolors.ENDC}")
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

        self.op_HS_assumption = [0.2, 0.2, 0.2, 0.2, 0.2]

        #print(f"{bcolors.OKGREEN}(Round Start) Update player_states{bcolors.ENDC}")
        #print(f"{bcolors.OKGREEN}{self.player_states[0]}{bcolors.ENDC}")
        #print(f"{bcolors.OKGREEN}{self.player_states[1]}{bcolors.ENDC}")
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
        if street == "preflop":
            if seat_no == round_state["dealer_btn"]:
                self.player_states[1]["pos"] = "first"
                self.player_states[1]["in_pot"] = self.SB_amount
                self.player_states[0]["pos"] = "second"
                self.player_states[0]["in_pot"] = self.BB_amount
            else:
                self.player_states[0]["pos"] = "first"
                self.player_states[0]["in_pot"] = self.SB_amount
                self.player_states[1]["pos"] = "second"
                self.player_states[1]["in_pot"] = self.BB_amount

        self.player_states[0]["stack"] = round_state["seats"][seat_no]["stack"]
        self.player_states[1]["stack"] = round_state["seats"][not seat_no]["stack"]

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

        # update op HS
        if self.street == "flop":
            self.op_HS_assumption = [0, 0.1, 0.3, 0.3, 0.3]

        #print(f"{bcolors.OKGREEN}(Street Start) Update player_states{bcolors.ENDC}")
        #print(f"{bcolors.OKGREEN}{self.player_states[0]}{bcolors.ENDC}")
        #print(f"{bcolors.OKGREEN}{self.player_states[1]}{bcolors.ENDC}")
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
        self.player_states[player]["in_pot"] += last_action["paid"]

        if "add_amount" in last_action:
            self.player_states[player]["add_amount"] = last_action["add_amount"]

        #print(f"{bcolors.OKGREEN}(Action) Update player_states{bcolors.ENDC}")
        #print(f"{bcolors.OKGREEN}{self.player_states[0]}{bcolors.ENDC}")
        #print(f"{bcolors.OKGREEN}{self.player_states[1]}{bcolors.ENDC}")

        # update op HS
        if player == 1:
            if last_action["amount"] / (self.player_states[player]["stack"] + 0.1) > 0.1:
                orign = np.array(self.op_HS_assumption)
                shift = np.array([0, -0.05, -0.05, 0.05, 0.05])
                self.op_HS_assumption = orign + shift

        #print(f"{bcolors.OKGREEN}{self.op_HS_assumption}{bcolors.ENDC}")
        return

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass

    # return [fold_ev, call_ev, small_raise_ev, big_raise_ev]
    def __tree_search(self, node, player_states):

        my_state = player_states[node]
        op_state = player_states[not node]

        # *FOLD*
        #print(f"{bcolors.OKBLUE}FOLD{bcolors.ENDC}")
        fold_ev = - my_state["in_pot"]

        # *CALL*
        #print(f"{bcolors.OKBLUE}CALL{bcolors.ENDC}")
        call_ev = 0
        if my_state["pos"] == "second" or op_state["add_amount"] != -1: # The Street Ends
            #print(f"{bcolors.OKBLUE}CALL-STOP-1{bcolors.ENDC}")

            if my_state["HS"] > op_state["HS"]:
                call_ev += op_state["in_pot"]
            if my_state["HS"] < op_state["HS"]:
                call_ev -= op_state["in_pot"]

        else: # The Street Continues
            if op_state["amount"] <= my_state["stack"]:
                # *CALL*: Street Continues
                #print(f"{bcolors.OKBLUE}CALL-RECURR{bcolors.ENDC}")
                new_player_states = copy.deepcopy(player_states)
                new_player_states[node]["amount"] = new_player_states[not node]["amount"]
                new_player_states[node]["stack"] -= (new_player_states[not node]["in_pot"] - new_player_states[node]["in_pot"])
                new_player_states[node]["in_pot"] = new_player_states[not node]["in_pot"]
                evs = self.__tree_search(not node, new_player_states)
                if node == 0:
                    call_evs = sum([a * b for a, b in zip(evs, opponent_model[op_state["HS"]])])
                else:
                    call_evs = max(evs)
            else: 
                # *ALL-IN*: straight to the showdown
                #print(f"{bcolors.OKBLUE}CALL-STOP-2{bcolors.ENDC}")
                if my_state["HS"] > op_state["HS"]:
                    call_ev += (my_state["in_pot"] + my_state["stack"])
                if my_state["HS"] < op_state["HS"]:
                    call_ev -= (my_state["in_pot"] + my_state["stack"])

        # *RAISE*
        #print(f"{bcolors.OKBLUE}RAISE{bcolors.ENDC}")
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
            paid = small_raise - new_player_states[node]["amount"]
            new_player_states[node]["add_amount"] = small_raise - op_state["amount"]
            new_player_states[node]["amount"] = small_raise
            new_player_states[node]["in_pot"] += paid
            new_player_states[node]["stack"] -= paid
            evs = self.__tree_search(not node, new_player_states)
            if node == 0:
                small_raise_ev = sum([a * b for a, b in zip(evs, opponent_model[op_state["HS"]])])
            else:
                small_raise_ev = max(evs)

            big_raise = min_amount + (my_state["stack"] - min_amount) // 2
            new_player_states = copy.deepcopy(player_states)
            paid = big_raise - new_player_states[node]["amount"]
            new_player_states[node]["add_amount"] = big_raise - op_state["amount"]
            new_player_states[node]["amount"] = big_raise
            new_player_states[node]["in_pot"] += paid
            new_player_states[node]["stack"] -= paid
            evs = self.__tree_search(not node, new_player_states)
            if node == 0:
                big_raise_ev = sum([a * b for a, b in zip(evs, opponent_model[op_state["HS"]])])
            else:
                big_raise_ev = max(evs)

        return np.array([fold_ev, call_ev, small_raise_ev, big_raise_ev])


def setup_ai():
    return TSPlayer()
