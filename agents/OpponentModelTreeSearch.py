from game.players import BasePokerPlayer

import sys
sys.path.append("/tmp2/b08902059/python-packages")
sys.path.append("agents/holdem_calc")

import numpy as np

import math

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

# pFold, pCall, pRaise for different hand strength
opponent_model = [
                    [0.9, 0.05, 0.05], # HS 0
                    [0.9, 0.05, 0.05], # HS 1
                    [0.7, 0.15, 0.15], # HS 2
                    [0.7, 0.15, 0.15], # HS 3
                    [0.5, 0.25, 0.25], # HS 4
                    [0.5, 0.25, 0.25], # HS 5
                    [0.1, 0.70, 0.20], # HS 6
                    [0.1, 0.70, 0.20], # HS 7
                    [0.0, 0.80, 0.20], # HS 8
                    [0.0, 0.80, 0.20]  # HS 9
                 ]

class OPMPlayer(BasePokerPlayer):

    def declare_action(self, valid_actions, hole_card, round_state):

        '''
        call_action_info = valid_actions[1]

        action, amount = call_action_info["action"], call_action_info["amount"]

        return action, amount  # action returned here is sent to the poker engine
        '''

        fold_action_info = valid_actions[0]
        call_action_info = valid_actions[1]
        raise_action_info = valid_actions[2]
        
        #print(f'{bcolors.OKCYAN}My HS: {self.player_states[0]["HS"]}{bcolors.ENDC}')

        if self.street == "preflop":
            # already won
            if self.lead - (self.remaining_round * self.BB_amount * 2) > 0:
                action = fold_action_info["action"]
                amount = fold_action_info["amount"]
            # bad hole
            elif self.player_states[0]["HS"] < 2:
                action = fold_action_info["action"]
                amount = fold_action_info["amount"]
            # op big raise, medium/weak hole
            elif call_action_info["amount"] > self.BB_amount * 15 and self.player_states[0]["HS"] < 8:
                action = fold_action_info["action"]
                amount = fold_action_info["amount"]
            # op samll raise, weak hole
            elif call_action_info["amount"] > self.BB_amount * 5 and self.player_states[0]["HS"] < 4:
                action = fold_action_info["action"]
                amount = fold_action_info["amount"]
            else:
                action = call_action_info["action"]
                amount = call_action_info["amount"]
            return action, amount
        
        rmin = raise_action_info["amount"]["min"]
        rmax = raise_action_info["amount"]["max"]
        if rmin != -1:
            raise_num = math.floor((rmax - rmin) / (10 * self.BB_amount))
        else:
            raise_num = 0
        
        # fold, call, raise0, raise1, ..., raiseN
        avg_evs = np.zeros(2 + raise_num)

        temp_display = ["{0:0.2f}".format(i) for i in self.op_HS_assumption]
        #print(f"{bcolors.OKBLUE}Assumption on op HS:\n{temp_display}{bcolors.ENDC}")

        for op_HS in range(10):
            #print(f"{bcolors.OKBLUE}{op_HS}{bcolors.ENDC}")
            if self.op_HS_assumption[op_HS] == 0:
                continue
            self.player_states[1]["HS"] = op_HS
            HS_ev = self.__tree_search(0, self.player_states)
            avg_evs = avg_evs + HS_ev * self.op_HS_assumption[op_HS]

        
        #print(f"{bcolors.OKBLUE}Fold : {avg_evs[0]}{bcolors.ENDC}")
        #print(f"{bcolors.OKBLUE}Call : {avg_evs[1]}{bcolors.ENDC}")
        if raise_num > 0:
            temp_display = ["{0:0.2f}".format(i) for i in avg_evs[2:]]
            #print(f"{bcolors.OKBLUE}Raise: {temp_display}{bcolors.ENDC}")

        choice = np.argmax(avg_evs)
        if choice == 0:
            action = fold_action_info["action"]
            amount = fold_action_info["amount"]
        elif choice == 1:
            action = call_action_info["action"]
            amount = call_action_info["amount"]
        elif rmin == -1:
            action = call_action_info["action"]
            amount = call_action_info["amount"]
        else:
            action = raise_action_info["action"]
            offset = choice - 2
            amount = rmin + offset * ((10 * self.BB_amount))
        #print(f"{bcolors.OKGREEN}{action}, {amount}{bcolors.ENDC}")

        return action, int(amount)  # action returned here is sent to the poker engine

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
    #
    # ** OPM **
    #   op_num_action                    => init at game, update with action
    #   op_aggression_cnt                => init at game, update with action
    #   op_aggression_feq                => init at game, update with action
    #   op_streets_cnt                   => init at game, update with round
    #   op_avg_street_played(per round)  => init at game, update with round (preflop->1, flop->2, ...)
    #
    #   op_HS_assumption      = [n0, n1, ..., n9] => init at round, update with action
    #

    #
    # Game Info:
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
        self.op_num_action = 0
        self.op_aggression_cnt = 0
        self.op_aggression_feq = -1
        self.op_streets_cnt = 0
        self.op_avg_street_played = -1
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

        self.player_states[0]["HS"] = math.floor(pWin * 10 - 0.001)
        if self.player_states[0]["HS"] < 0:
            self.player_states[0]["HS"] = 0

        # ** OPM **
        # assume uniform distribution first
        self.op_HS_assumption = [0.1 for _ in range(10)]

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
            self.player_states[0]["HS"] = math.floor(pWin * 10 - 0.001)
            if self.player_states[0]["HS"] < 0:
                self.player_states[0]["HS"] = 0

        self.player_states[0]["amount"] = 0
        self.player_states[1]["amount"] = 0
        self.player_states[0]["add_amount"] = -1
        self.player_states[1]["add_amount"] = -1

        # ** OPM **
        # if op doesn't fold at preflop, we assume his holes are not bad
        if self.street == "flop":
            self.op_HS_assumption = [0.0, 0.0, 0.05, 0.05, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15]

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

        # ** OPM **
        if player == 1:
            self.op_num_action += 1
            if last_action["action"] == "RAISE":
                self.op_aggression_cnt += 1
            self.op_aggression_feq = self.op_aggression_cnt / self.op_num_action

            # update op_HS_assumption
            if round_state["round_count"] > 7:
                self.__update_assumption(last_action)

        #print(f"{bcolors.OKGREEN}{self.op_HS_assumption}{bcolors.ENDC}")
        return

    def receive_round_result_message(self, winners, hand_info, round_state):
        # ** OPM **
        last_action = round_state["action_histories"][self.street][-1]
        if last_action["uuid"] == self.uuid and last_action["action"] == "FOLD":
            self.op_streets_cnt += 3
        else:
            self.op_streets_cnt += len(round_state["action_histories"])
        self.op_avg_street_played = self.op_streets_cnt / round_state["round_count"]
        return

    # ** OPM **
    def __update_assumption(self, last_action):
        # classify op type
        # 0: aggresive
        # 1: passive, optimistic
        # 2: passive, pessimistic
        if self.op_aggression_feq >= 0.125:
            op_type = 0
        elif self.op_avg_street_played >= 1.5:
            op_type = 1
        else:
            op_type = 2
        #print(f"{bcolors.OKGREEN}** OPM **{bcolors.ENDC}")
        #print(f"{bcolors.OKGREEN}Aggression Fequency  : {self.op_aggression_feq}{bcolors.ENDC}")
        #print(f"{bcolors.OKGREEN}Average Street Played: {self.op_avg_street_played}{bcolors.ENDC}")
        #print(f"{bcolors.OKGREEN}Assumed Oppenent Type: {op_type}{bcolors.ENDC}")
        #print(f"{bcolors.OKGREEN}*********{bcolors.ENDC}")

        # update ratio
        raise_update_rule = \
        [ [0.5, 0.5, 1   , 1   , 1   , 1   , 1   , 1   , 1   , 1   ],
          [0.5, 0.5, 0.5 , 0.5 , 1.25, 1.25, 1.50, 1.50, 1.50, 1.50],
          [0.5, 0.5, 0.5 , 0.5 , 1.25, 1.25, 1.50, 1.50, 2.00, 2.00] ]
        call_update_rule = \
        [ [0.5, 0.5, 1   , 1   , 1   , 1   , 1   , 1   , 1   , 1   ],
          [0.5, 0.5, 1   , 1   , 1.25, 1.25, 1.25, 1.25, 1.25, 1.25],
          [0.5, 0.5, 0.5 , 0.5 , 1.25, 1.25, 1.50, 1.50, 1.50, 1.50] ]

        if last_action["action"] == "CALL":
            new_assumption = np.array([a*b for a,b in zip(self.op_HS_assumption, call_update_rule[op_type])])
            new_assumption = new_assumption / sum(new_assumption)
            self.op_HS_assumption = new_assumption
        if last_action["action"] == "RAISE":
            new_assumption = np.array([a*b for a,b in zip(self.op_HS_assumption, raise_update_rule[op_type])])
            new_assumption = new_assumption / sum(new_assumption)
            self.op_HS_assumption = new_assumption

    # return [fold_ev, call_ev, raise_ev0, raise_ev1, ..., raise_evN]
    def __tree_search(self, node, player_states):

        my_state = player_states[node]
        op_state = player_states[not node]

        # *FOLD*
        #print(f"{bcolors.OKBLUE}FOLD{bcolors.ENDC}")
        fold_ev = - my_state["in_pot"]
        if node == 1:
            fold_ev *= -1

        # *CALL*
        #print(f"{bcolors.OKBLUE}CALL{bcolors.ENDC}")
        call_ev = 0
        if my_state["pos"] == "second" or op_state["add_amount"] != -1: # The Street Ends
            #print(f"{bcolors.OKBLUE}CALL-STOP-1{bcolors.ENDC}")

            if my_state["HS"] > op_state["HS"]:
                call_ev += op_state["in_pot"]
            if my_state["HS"] < op_state["HS"]:
                call_ev -= op_state["in_pot"]
            if node == 1:
                call_ev *= -1

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
                    op_action_prob = copy.deepcopy(opponent_model[op_state["HS"]])
                    total_raise_prob = op_action_prob.pop()
                    child_raise_num = len(evs) - 2

                    if child_raise_num > 0:
                        raise_probs = []
                        tmp = 0.5
                        for i in range(child_raise_num):
                            raise_probs.append(tmp)
                            tmp *= tmp
                        raise_probs = np.array(raise_probs)
                        raise_probs = raise_probs / sum(raise_probs)
                    for i in range(child_raise_num):
                        op_action_prob.append(raise_probs[i] * total_raise_prob)
                    call_evs = sum([a * b for a, b in zip(evs, op_action_prob)])
                else:
                    call_evs = max(evs)
            else: 
                # *ALL-IN*: straight to the showdown
                #print(f"{bcolors.OKBLUE}CALL-STOP-2{bcolors.ENDC}")
                if my_state["HS"] > op_state["HS"]:
                    call_ev += (my_state["in_pot"] + my_state["stack"])
                if my_state["HS"] < op_state["HS"]:
                    call_ev -= (my_state["in_pot"] + my_state["stack"])
                if node == 1:
                    call_ev *= -1

        # *RAISE*
        #print(f"{bcolors.OKBLUE}*RAISE*{bcolors.ENDC}")
        if op_state["add_amount"] == -1:
            min_amount = my_state["amount"] + self.BB_amount
        else:
            min_amount = op_state["amount"] + op_state["add_amount"]
        # IF CAN RAISE
        raise_evs = []
        if min_amount <= my_state["stack"]:

            max_amount = my_state["stack"]

            raise_num = math.floor((max_amount - min_amount) / (10 * self.BB_amount))
            
            for i in range(raise_num):

                raise_amount = min_amount + i * (10 * self.BB_amount)
                new_player_states = copy.deepcopy(player_states)
                paid = raise_amount - new_player_states[node]["amount"]
                new_player_states[node]["add_amount"] = raise_amount - op_state["amount"]
                new_player_states[node]["amount"] = raise_amount
                new_player_states[node]["in_pot"] += paid
                new_player_states[node]["stack"] -= paid
                #print(f"{bcolors.OKBLUE}RAISE ITER: {i} BEFORE RECUR{bcolors.ENDC}")
                evs = self.__tree_search(not node, new_player_states)
                #print(f"{bcolors.OKBLUE}RAISE ITER: {i} AFTER RECUR{bcolors.ENDC}")

                if node == 0:
                    op_action_prob = copy.deepcopy(opponent_model[op_state["HS"]])
                    #print(f"{bcolors.OKBLUE}1, {op_action_prob}{bcolors.ENDC}")
                    total_raise_prob = op_action_prob.pop()
                    #print(f"{bcolors.OKBLUE}2, {total_raise_prob}{bcolors.ENDC}")
                    child_raise_num = len(evs) - 2
                    #print(f"{bcolors.OKBLUE}3, {child_raise_num}{bcolors.ENDC}")
                    if child_raise_num > 0:
                        raise_probs = []
                        tmp = 0.5
                        for i in range(child_raise_num):
                            raise_probs.append(tmp)
                            tmp *= tmp
                        raise_probs = np.array(raise_probs)
                        raise_probs = raise_probs / sum(raise_probs)
                        #print(f"{bcolors.OKBLUE}3.5, {raise_probs}{bcolors.ENDC}")
                    for i in range(child_raise_num):
                        op_action_prob.append(raise_probs[i] * total_raise_prob)
                    #print(f"{bcolors.OKBLUE}4, {op_action_prob}{bcolors.ENDC}")
                    #print(f"{bcolors.OKBLUE}5, {len(evs)}{bcolors.ENDC}")
                    raise_evs.append(sum([a * b for a, b in zip(evs, op_action_prob)]))
                else:
                    raise_evs.append(max(evs))

        ret_evs = [fold_ev, call_ev]
        ret_evs.extend(raise_evs)
        return np.array(ret_evs)


def setup_ai():
    return OPMPlayer()
