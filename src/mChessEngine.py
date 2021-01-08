# Mick, Denmark, 2021-01-06

from stockfish import Stockfish

VERSION = "1.0.0"

if __name__ == '__main__':

    print(f"mChessEngine {VERSION} based on StockFish")

    stockfish = Stockfish("stockfish_20090216_x64.exe",
                          parameters={
                           "Write Debug Log": "true",
                           "Contempt": 0,
                           "Min Split Depth": 0,
                           "Threads": 2,
                           "Ponder": "false",
                           "Hash": 16,
                           "MultiPV": 1,
                           "Skill Level": 20,
                           "Move Overhead": 30,
                           "Minimum Thinking Time": 20,
                           "Slow Mover": 80,
                           "UCI_Chess960": "false",
                            }
                          )

    print(stockfish.get_parameters())

    moves = []

    while True:
        # Print out board
        stockfish.set_position(moves)
        print("  a   b   c   d   e   f   g   h")
        print(stockfish.get_board_visual())


        # Wait for user input
        move = input('Make a move: ')
        if stockfish.is_move_correct(move):
            print("Move is correct!")
            moves.append(move)
            stockfish.set_position(moves)
            print(stockfish.get_board_visual())
        elif move == 'q':
            print("Quitting program")
            break
        else:
            print("Move is not valid")

        # Wait for computer input
        computer_move = stockfish.get_best_move_time(1000)
        #print(f"Computer move: {computer_move}")
        moves.append(computer_move)

