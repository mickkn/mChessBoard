import argparse
from stockfish import Stockfish

APPTITLE = "mChessBoard"
AUTHOR = "by Mick Kirkegaard"
VERSION = "v1.0.0"
DATE = "Jan 01 2021 19:01"

def parser():

    """! @brief     Parser function to get all the arguments """

    # Description string
    description = "Description: " + APPTITLE + " " + VERSION + " " + DATE + " " + AUTHOR
    
    # Construct the argument parse and return the arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=description)
    parser.add_argument("-i", "--input", type=str, default="stockfish_20090216_x64.exe",
                        help="path to stockfish executable")
    parser.add_argument('--version', action='version', version=APPTITLE + " " + VERSION + " " + DATE + " " + AUTHOR)
    print('\n' + str(parser.parse_args()) + '\n')

    return parser.parse_args()


if __name__ == '__main__':

    """! @brief Main function """

    # Get the arguments
    args = parser()

    stockfish = Stockfish(args.input,
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

