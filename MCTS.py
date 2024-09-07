import math
import random
import time
import copy
import csv
from Azul import AzulState, AzulGame

class MCTSNode:
    def __init__(self, state, game, parent=None, move =None):
        self.state = state
        self.parent = parent
        self.parent_move = move
        self.children = []
        self.untried_actions = game.get_legal_moves(self.state)
        self.visits = 0
        self.wins = 0

    def is_fully_expanded(self):
        """
        Returns True if all possible actions have been explored
        """
        return len(self.untried_actions) == 0

    def best_child(self, exploration_weight=1.4):
        """
        Selects the best child based on UCB (Upper Confidence Bound)
        """
        if not self.children:
            raise Exception("No children nodes available to select the best child.")
        
        choices_weights = [
            (child.wins / child.visits) + exploration_weight * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]
    
    def update(self, result):
        """ 
        Updates the node with the result of a simulation 
        """
        self.visits += 1
        self.wins += result

    def print_children_info(self):
        print("Children of current node:")
        for child in self.children:
            print(f"Move: {child.parent_move}, Wins: {child.wins}, Visits: {child.visits}, Win Rate: {child.wins / child.visits if child.visits > 0 else 0}")

    def print_legal_actions(self):
        print(f"Legal actions: {self.untried_actions}")
   


class MCTS:
    def __init__(self, game, exploration_weight=2.5, max_simulation_depth=10, min_visits_per_node=15):
        self.game = game
        self.exploration_weight = exploration_weight    # Exploration parameter for UCB
        self.max_simulation_depth = max_simulation_depth
        self.min_visits_per_node = min_visits_per_node

    def search(self, initial_state, num_simulations=None, simulation_seconds=None):
        """
        Executes the MCTS search. Runs simulations for a given number of iterations or within a time limit.
        """
        root = MCTSNode(initial_state, self.game)
        start_time = time.time()

        if num_simulations is None :
            # Time-limited search
            assert(simulation_seconds is not None)
            end_time = time.time() + simulation_seconds
            while time.time() < end_time:
                if root.is_fully_expanded() and all(child.is_fully_expanded() for child in root.children):
                    break  
                node = self._select(root)
                result = self._simulate(node.state)
                self._backpropagate(node, result)
        else:
            # Search limited by number of simulations
            for i in range(num_simulations):
                node = self._select(root)
                result = self._simulate(node.state)
                self._backpropagate(node, result)

        best_child_node = root.best_child(0)
        best_move = best_child_node.parent_move
        search_time = time.time() - start_time

        return best_move, search_time
    

    def _select(self, node):
        """
        Selects the node to expand using the UCB policy
        """
        while not self.game.check_end_of_game(node.state):
            if node.is_fully_expanded():
                if not node.children:
                    return node  
                else:
                    # Select the best child if the node is fully expanded
                    if node.children and all(child.visits >= self.min_visits_per_node for child in node.children):
                        node = node.best_child(self.exploration_weight)
                    else:
                        node = self._select_child_with_less_visits(node)
            else:
                return self._expand(node)
        return node
    
    def _select_child_with_less_visits(self, node):
        """
        Select the best child without the minimun number of visits
        """
        for child in node.children:
            if child.visits < self.min_visits_per_node:
                return child

        return node.children[0]


    def _expand(self, node):
        """
        Expands the node by trying a new action
        """
        if not node.untried_actions:
            raise Exception("No untried actions available for expansion.")

        rand_idx = random.randrange(len(node.untried_actions))
        move = node.untried_actions.pop(rand_idx)
        new_state = self.apply_move(node.state, move)
        
        child_node = MCTSNode(new_state, self.game, parent=node, move=move)
        node.children.append(child_node)

        return child_node   
    
    
    def _simulate(self, state):
        """
        Simulates a game to its end or until the maximum depth is reached
        """
        depth = 0
        while not self.game.check_end_of_game(state) and depth < self.max_simulation_depth:
            if self.game.check_end_of_round(state):
                self.game.draw_tiles(state)
                state.move_tiles_to_wall()
            legal_moves = self.game.get_legal_moves(state)
            if not legal_moves:
                break  
            move = random.choice(legal_moves)
            state = self.apply_move(state, move)
            depth += 1     
        
        result = self.game.get_result(state)
        return result
    

    def apply_move(self, state, move):
        """
        Returns a copy of the new state after the move
        """
        if not isinstance(state, AzulState):
            raise ValueError("state debe ser una instancia de AzulState")
       
        factory_num, tile_color, row_num = move
        new_state = copy.deepcopy(state)

        new_state.move_tiles(factory_num, tile_color, row_num)
        return new_state
    

    def _backpropagate(self, node, result):
        """
        Propagates the result of the simulation upwards through the tree
        """
        while node:
            node.update(result)
            node = node.parent



# Example of MCTS vs Random player simulation
if __name__ == "__main__":
    azul_game = AzulGame()
    initial_state = azul_game.get_initial_state() 
    azul_game.draw_tiles(initial_state) 
    initial_state.display_state()

    mcts = MCTS(azul_game)
    current_state = initial_state
    total_games = 20

    for game_number in range(total_games):
        round_number = 0
        round_execution_times = []

        while not azul_game.check_end_of_game(current_state):
            if current_state.current_player == 0:
                print("MCTS's turn")
                best_move, search_time = mcts.search(current_state, num_simulations=5000)
                print(f"MCTS action: {best_move}")
                current_state.move_tiles(best_move[0], best_move[1], best_move[2])
                current_state.display_state()
            else:
                print("Random player's turn")
                random_move = azul_game.random_player(current_state)
                print(f"Random action: {random_move}")
                current_state.move_tiles(random_move[0], random_move[1], random_move[2])
                current_state.display_state()
            
            if azul_game.check_end_of_round(current_state):
                current_state.move_tiles_to_wall()
                azul_game.display_scores(current_state)
                current_state.display_state()

                azul_game.draw_tiles(current_state)


        print(f"Game Over: {game_number}")
        print("Final State:")
        current_state.display_state()
        input()

        azul_game.display_scores(current_state)
        for i, player in enumerate(current_state.players):
                print(f"Player {i+1} final score: {player['score']} points")

        # Reset for next game
        current_state = azul_game.get_initial_state() 
        azul_game.draw_tiles(current_state)
        


