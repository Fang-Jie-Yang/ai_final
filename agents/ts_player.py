from game.players import BasePokerPlayer

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
                    [0.9, 0.05, 0.05], # very weak hand 
                    [0.7, 0.15, 0.15], # weak hand 
                    [0.5, 0.25, 0.25], # medium hand 
                    [0.3, 0.35, 0.35], # strong hand 
                    [0.1, 0.45, 0.45]  # very strong hand 
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

class 

class TSPlayer(BasePokerPlayer):

    #player state
    #[
    #    Player(We)
    #    { 
    #        "pos": "first" or "second"
    #        "amount":
    #        "stack":
    #        "add_amount": -1 or real value
    #        "HS":
    #    }
    #    ,
    #    Oppoenent
    #    {
    #        "pos":
    #        "amount":
    #        "stack":
    #        "add_amount": -1 or real value
    #        "HS":
    #    }
    #]

    # return [fold_ev, call_ev, raise0_ev, raise1_ev, ... raiseN_ev]
    def __tree_search(self, node, player_states):

        my_state = player_states[node]
        op_state = player_states[not node]

        # *FOLD*
        fold_ev = - my_state["amount"]
        if node == 1:
            fold_ev *= -1
        # *CALL*
        call_ev = 0
        if my_state["pos"] == "second" or op_state["add_amount"] != -1: # The Street Ends
            if my_state["HS"] > op_state["HS"]
                call_ev += op_state["amount"]
            if me_state["HS"] < op_state["HS"]
                call_ev -= my_state["amount"]
            if node == 1:
                call_ev *= -1
        else: # The Street Continues
            if op_state["amount"] <= my_state["stack"]:
                # *CALL*: Street Continues
                new_player_states = copy.deepcopy(player_states)
                new_player_states[node]["amount"] = new_player_states[not node]["amount"]
                if node == 0:
                    call_ev = max(self.__tree_search(not node, new_player_states))
                else:
                    call_ev = min(self.__tree_search(not node, new_player_states))
            else: 
                # *ALL-IN*: straight to the showdown
                if my_state["HS"] > op_state["HS"]:
                    call_ev += my_state["stack"]
                if my_state["HS"] < op_state["HS"]:
                    call_ev -= my_state["stack"]
                if node == 1:
                    call_ev *= -1
        # *RAISE*
        raise_evs = []
        if op_state["add_amount"] == -1:
            min_amount = my_state["amount"] + self.BB_amount
        else:
            min_amount = op_state["amount"] + op_state["add_amount"]
        # IF CAN RAISE
        if min_amount <= my_state["stack"]:
            for bet in range(min_amount, my_state["stack"], 200):
                # UPDATE PLAYER STATES
                new_player_states = copy.deepcopy(player_states)
                new_player_states[node]["add_amount"] = bet - op_state["amount"]
                new_player_states[node]["amount"] = bet
                if node == 0:
                    raise_evs.append(max(self.__tree_search(not node, new_player_states)))
                else:
                    raise_evs.append(min(self.__tree_search(not node, new_player_states)))

        return [fold_ev, call_ev].extend(raise_evs)

    def declare_action(self, valid_actions, hole_card, round_state):

        #player state
        #[
        #    Player(We)
        #    { 
        #        "pos": "first" or "second"
        #        "amount":
        #        "stack":
        #        "add_amount": -1 or real value
        #        "HS":
        #    }
        #    ,
        #    Oppoenent
        #    {
        #        "pos":
        #        "amount":
        #        "stack":
        #        "add_amount": -1 or real value
        #        "HS":
        #    }
        #]
        for op_HS in range(5):


        return action, amount  # action returned here is sent to the poker engine

    # attr
    # game:
    #   BB_amount
    # round:
    #   lead, remaining rounds, hole, pos
    # street:
    #   street, community card, probability
    #   my_HS
    # action:
    #   paid, opp paid, opp prev action, opp hole distribution

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
    return TSPlayer()
