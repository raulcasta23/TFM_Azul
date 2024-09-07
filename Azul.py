import random

class AzulState:
    def __init__(self, tiles, factories, player_boards, center, bag, discard, player, board_pattern):
        self.tiles = tiles  # Available tile colors
        self.factories = factories  # Factories where tiles are distributed
        self.players = player_boards  # Player boards
        self.center = center  # Tiles in the center
        self.bag = bag  # Remaining tiles in the bag
        self.discard = discard  # Discarded tiles
        self.current_player = player  
        self.board_pattern = board_pattern  # Color pattern on the wall
        self.chosen_tiles = []  
        self.empty_floor = []  # Empty floor for penalties
        

    def display_state(self):
        """
        Initializes the game state with the initial parameters.
        """

        print("\nFactories:")
        for i, factory in enumerate(self.factories):
            print(f"Factory {i+1}: {factory}")
        print(f"\nCenter: {self.center}")
        for i, player in enumerate(self.players):
            print(f"\nPlayer {i+1}'s board:")
            for row in player['board']:
                print(row)
            print(f"Pattern Lines: {player['pattern_lines']}")
            print(f"Floor: {player['floor']}")
            print(f"Score: {player['score']}")
        print("\n")


    def take_turn(self):
        """
        Handles the player's turn, allowing them to select tiles and a pattern line.
        """

        player = self.players[self.current_player]
        
        while True:
            try:
                source = input(f"Player {self.current_player + 1}, choose a source (factory 1-5 or 'center'): ").strip().lower()
                if source == 'center':
                    if not self.center or self.center == ['1']:
                        print("The center is empty. Please choose a non-empty factory.\n")
                        continue
                    factory_num = -1
                else:
                    factory_num = int(source) - 1
                    if factory_num < 0 or factory_num >= len(self.factories):
                        print("Invalid factory number. Please choose a factory between 1 and 5 or 'center'.\n")
                        continue
                    if not self.factories[factory_num]:
                        print("The selected factory is empty. Please choose a non-empty factory.\n")
                        continue
                break
            except ValueError:
                print("Please enter a valid number for the factory or 'center'.")
        
        while True:
            if factory_num == -1:
                print(f"\nAvailable tiles in center: {self.center}")
                tile_color = input(f"Player {self.current_player + 1}, choose a tile color from the center: ").strip().upper()

                if tile_color not in self.tiles:
                    print("Invalid tile color. Please choose from B, Y, R, K, W.")
                    continue
                if tile_color not in self.center:
                    print("No tiles of the chosen color in the selected source.\n")
                    continue
            else:
                print(f"\nAvailable tiles in factory {factory_num + 1}: {self.factories[factory_num]}")
                tile_color = input(f"Player {self.current_player + 1}, choose a tile color from the factory: ").strip().upper()

                if tile_color not in self.tiles:
                    print("Invalid tile color. Please choose from B, Y, R, K, W.")
                    continue              
                if tile_color not in self.factories[factory_num]:
                    print("No tiles of the chosen color in the selected source.\n")
                    continue
            break
        
        can_pl = False
        for i in range(5):
            if AzulGame.can_place_tiles(player, tile_color, i):
                can_pl = True
                
        if can_pl == False:
            row_num = -1
            print("Cannot place any tiles, moving all to the floor.\n")
        else:
            while True:
                try:
                    row_num = int(input(f"Player {self.current_player + 1}, choose a pattern line to place tiles (1-5): ")) - 1
                    if row_num < 0 or row_num >= len(player['pattern_lines']):
                        print("Invalid row number. Please choose a row between 1 and 5.\n")
                        continue
                    if player['pattern_lines'][row_num].count('') != row_num + 1 and player['pattern_lines'][row_num].count(tile_color) == 0:
                        print("The chosen row already has a different color or is full.\n")
                        continue
                    if tile_color in player['board'][row_num]:
                        print("The chosen color is already in the corresponding row on the board.\n")
                        continue
                    break
                except ValueError:
                    print("Please enter a valid number for the row.\n")

        return factory_num, tile_color, row_num


    def move_tiles(self, factory_num, tile_color, row_num):
        """
        Moves selected tiles from the factory or center to the pattern lines or floor if they can't be placed.
        """
        
        player = self.players[self.current_player]
        self.empty_floor = player['floor'].copy()

        if factory_num == -1:
            self.chosen_tiles = [tile for tile in self.center if tile == tile_color]
            remaining_tiles = [tile for tile in self.center if tile != tile_color]
            self.center = remaining_tiles  # Update the center without the chosen tiles
            if '1' in self.center:
                self.center.remove('1')
                player['floor'].append('1')  # The first player token is added to the floor line
        else:
            self.chosen_tiles = [tile for tile in self.factories[factory_num] if tile == tile_color]
            remaining_tiles = [tile for tile in self.factories[factory_num] if tile != tile_color]
            self.center.extend(remaining_tiles)

        if row_num == -1: # Can't place selected tiles in any row
            player['floor'].extend(self.chosen_tiles)
        else:
            empty_spaces = player['pattern_lines'][row_num].count('')
            if empty_spaces >= len(self.chosen_tiles):
                for _ in range(len(self.chosen_tiles)):
                    player['pattern_lines'][row_num][player['pattern_lines'][row_num].index('')] = tile_color
            else:
                for _ in range(empty_spaces):
                    player['pattern_lines'][row_num][player['pattern_lines'][row_num].index('')] = tile_color
                player['floor'].extend(self.chosen_tiles[empty_spaces:])
        
        if factory_num != -1:
            self.factories[factory_num] = []
        
        if self.current_player == 0:
            self.current_player = 1
        else:
            self.current_player = 0


    def move_tiles_to_wall(self):
        """
        Moves tiles from the pattern lines to the wall, calculates points, and updates the discarded tiles.
        """

        for player in self.players:
            for row_num, pattern_line in enumerate(player['pattern_lines']):
                if len(pattern_line) == row_num + 1 and all(tile != '' for tile in pattern_line):
                    tile_color = pattern_line[0]
                    if tile_color != '1':
                        # Find the correct column on the wall
                        col_num = self.board_pattern[row_num].index(tile_color)
                        player['board'][row_num][col_num] = tile_color
                        player['pattern_lines'][row_num] = [''] * (row_num + 1)
                        # Add remaining tiles to discard
                        self.discard.extend(pattern_line[1:])
                        # Calculate points for this tile placement
                        score = AzulGame.calculate_score(player, row_num, col_num)
                         # Update player's score
                        player['score'] += score
 
            # Calculate penalty points 
            AzulGame.penalties(player)
            AzulGame.bounties(player)
            # Empty the floor line
            self.discard.extend(player['floor'])
            player['floor'] = []



class AzulGame:

    def get_initial_state(self):
        """
        Returns the initial state of the game with factories, boards, and tile bag ready.
        """

        tiles = ['B', 'Y', 'R', 'K', 'W']  # Blue, Yellow, Red, Black, White
        num_players = 2
        initial_factories = [[], [], [], [], []]  # 5 factories for 2 players        
        initial_player_boards = [{'board': [['' for _ in range(5)] for _ in range(5)], 
                         'pattern_lines': [[''] * (i + 1) for i in range(5)], 
                         'floor': [], 
                         'score': 0} for _ in range(num_players)]
        initial_center = ['1']  # Center of the table starts with the first player token
        initial_bag = tiles * 20
        initial_discard = []
        initial_player = 0
        board_pattern = [
            ['B', 'Y', 'R', 'K', 'W'],  # First row pattern
            ['W', 'B', 'Y', 'R', 'K'],  # Second row pattern
            ['K', 'W', 'B', 'Y', 'R'],  # Third row pattern
            ['R', 'K', 'W', 'B', 'Y'],  # Fourth row pattern
            ['Y', 'R', 'K', 'W', 'B']   # Fifth row pattern
        ]

        return AzulState( tiles, initial_factories, initial_player_boards, initial_center, initial_bag, initial_discard, initial_player, board_pattern)


    @staticmethod
    def draw_tiles(state):
        """
        Draws tiles from the bag and distributes them to the factories at the start of the round.
        """

        random.shuffle(state.bag)

        for factory in state.factories:
            factory.clear()
            for _ in range(4):
                if state.bag:
                    factory.append(state.bag.pop())
                else:
                    # If the bag is empty, refill it with discard pile
                    state.discard = [x for x in state.discard if x != '1']
                    state.bag = state.discard
                    state.discard = []
                    random.shuffle(state.bag)
                    if state.bag:
                        factory.append(state.bag.pop())
        # Add the first player token to the center at the beginning of the round
        state.center = ['1'] 


    @staticmethod
    def get_result(state):
        """
        Returns the result of the game, providing the player's score.
        """

        return state.players[0]['score']

    
    @staticmethod
    def calculate_score(player, row_num=None, col_num=None):
        """
        Calculates the points earned by placing tiles on the wall.
        """

        score = 0
        if row_num is not None and col_num is not None:
            # Check horizontally
            horizontal_count = 1
            for i in range(col_num + 1, 5):
                if player['board'][row_num][i] != '':
                    horizontal_count += 1
                else:
                    break
            for i in range(col_num - 1, -1, -1):
                if player['board'][row_num][i] != '':
                    horizontal_count += 1
                else:
                    break
            if horizontal_count > 1:
                score += horizontal_count

            # Check vertically
            vertical_count = 1
            for i in range(row_num + 1, 5):
                if player['board'][i][col_num] != '':
                    vertical_count += 1
                else:
                    break
            for i in range(row_num - 1, -1, -1):
                if player['board'][i][col_num] != '':
                    vertical_count += 1
                else:
                    break
            if vertical_count > 1:
                score += vertical_count

            # If it's a single tile, it gets 1 point
            if horizontal_count == 1 and vertical_count == 1:
                score += 1

        return score


    @staticmethod
    def immediate_action_scoring(state, row_num, tile_color):
        """
        Calculates the immediate score when placing tiles in the pattern line, including future points.
        """

        points = 0
        
        if state.current_player == 0:
            player = state.players[1]
        else:
            player = state.players[0]
        
        if row_num != -1:
            # Points for getting closer to completing a pattern line
            total_tiles_in_row = row_num + 1
            filled_spaces = total_tiles_in_row - player['pattern_lines'][row_num].count('') # Empty spaces

            if filled_spaces <= 0:
                progress_bonus = 1.0
            else:
                progress_bonus = filled_spaces / total_tiles_in_row
            points += progress_bonus * 3
        
            # Points for future placement of tiles on the wall
            col_num = state.board_pattern[row_num].index(tile_color) # Find the correct column on the wall
            future_points = AzulGame.calculate_score(player, row_num, col_num)
            points += future_points 

            # Additional bonus for completing a row on the board
            if all(tile != '' for tile in player['board'][row_num]):
                points += 10

            # Additional bonus for completing a column on the board
            if all(player['board'][r][col_num] != '' for r in range(5)):
                points += 25 

            # Additional bonus for completing all tiles of one color on the board
            color_count = sum(row.count(tile_color) for row in player['board'])
            if color_count == 5:
                points += 30  

        # Penalty for tiles that fall to the floor
        if len(state.empty_floor) < len(player['floor']):
            fallen_tiles = len(player['floor']) - len(state.empty_floor)
            penalty = fallen_tiles * (-3)  
            points += penalty

        return points


    @staticmethod
    def penalties(player):
        """
        Applies penalties to players who have tiles on the floor.
        """

        floor_penalties = [0, -1, -2, -4, -6, -8, -11, -14]
        num_floor_tiles = len(player['floor'])
        penalty = floor_penalties[min(num_floor_tiles, len(floor_penalties) - 1)]
        player['score'] += penalty


    @staticmethod
    def bounties(player):
        """
        Grants additional points for completing rows, columns, or colors on the wall.
        """

        for row in player['board']:
            if all(tile != '' for tile in row):
                player['score'] += 2

        for col in range(5):
            if all(player['board'][row][col] != '' for row in range(5)):
                player['score'] += 7

        for color in ['B', 'Y', 'R', 'K', 'W']:
            if sum(row.count(color) for row in player['board']) == 5:
                player['score'] += 10


    def get_legal_moves(self, state):
        """
        Returns all possible legal moves from the current game state.
        """

        legal_actions = []
        player = state.players[state.current_player]

        # Loop through all factories
        for i, factory in enumerate(state.factories):
            for tile_color in set(factory):
                can_place = False
                for row_num in range(5):
                    
                    if self.can_place_tiles(player, tile_color, row_num):
                        if not any(tile != '' and tile != tile_color for tile in player['pattern_lines'][row_num]):
                            legal_actions.append((i, tile_color, row_num))
                            can_place = True
                if not can_place:
                    legal_actions.append((i, tile_color, -1)) 
        
        # Loop through the center of the table
        if state.center:
            for tile_color in set(state.center):
                if tile_color == '1':   # Ignore the '1' tile
                    continue
                can_place = False
                for row_num in range(5):
                    if self.can_place_tiles(player, tile_color, row_num):
                        if not any(tile != '' and tile != tile_color for tile in player['pattern_lines'][row_num]):
                            legal_actions.append((-1, tile_color, row_num))
                            can_place = True
                if not can_place:
                    legal_actions.append((-1, tile_color, -1)) 

        return legal_actions
    
    @staticmethod
    def can_place_tiles(player, tile_color, row_num):
        """
        Checks if tiles of a certain color can be placed in a pattern line.
        """

        pattern_line = player['pattern_lines'][row_num] 

        # Checks if the color is already in the corresponding row on the wall
        if tile_color in player['board'][row_num]:
            return False
        # Checks if the pattern line is full
        if '' not in pattern_line:
            return False
        # Checks if the pattern line contains only the same color or is empty
        if all(tile == '' or tile == tile_color for tile in pattern_line):
            return True
        return False


    @staticmethod
    def check_end_of_round(state):
        """
        Checks if the round has ended (all factories and the center are empty).
        """
        return all(not factory for factory in state.factories) and not state.center


    @staticmethod
    def check_end_of_game(state):
        """
        Checks if the game has ended (a player has completed a row on the wall).
        """

        if not isinstance(state, AzulState):
            raise ValueError("state must be an instance of AzulState")
        
        for player in state.players:
            for row in player['board']:
                if all(tile != '' for tile in row):
                    return True
        return False
    

    @staticmethod
    def display_scores(state):
        """
        Displays the scores of all players.
        """

        print("\nScores after this round:")
        for i, player in enumerate(state.players):
            print(f"Player {i+1}: {player['score']} points")


    def step(self, state, action):
        """
        Executes an action (placing tiles) and calculates the immediate reward for the DQN agent.
        """

        factory_num, tile_color, row_num = action
        state.move_tiles(factory_num, tile_color, row_num)
        reward = self.immediate_action_scoring(state, row_num, tile_color)

        return state, reward


    def random_player(self, state):
        """
        Chooses a random action from the possible legal moves.
        """

        legal_actions = self.get_legal_moves(state)
        return random.choice(legal_actions)


    def play_game(self, state):
        """
        Runs a full game, handling rounds and player turns (for human players).
        """

        round_number = 1

        while True:
            print(f"\n--- Round {round_number} ---")
            game.draw_tiles(state)

            while not self.check_end_of_round(state):
                for i in range(len(state.players)):
                    state.display_state()
                    self.get_legal_moves(state)
                    factory_num, tile_color, row_num = state.take_turn()
                    state.move_tiles(factory_num, tile_color, row_num)

                    if self.check_end_of_round(state):
                        break

            state.move_tiles_to_wall()
            self.display_scores(state)

            if self.check_end_of_game(state):
                break
            round_number += 1

        print("Game over! Calculate the final scores.")
        for i, player in enumerate(state.players):
            print(f"Player {i+1} final score: {player['score']} points")


if __name__ == "__main__":

    game = AzulGame()
    state = game.get_initial_state()
    game.play_game(state)