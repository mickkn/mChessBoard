import argparse
from stockfish import Stockfish     # https://pypi.org/project/stockfish/
from pcf8575 import PCF8575         # https://pypi.org/project/pcf8575/

APPTITLE = "mChessBoard"
AUTHOR = "by Mick Kirkegaard"
VERSION = "v1.0.0"
DATE = "Jan 01 2021 19:01"

"""! @brief     Board defines """
MCB_I2C_PORT_NUM = 1
MCB_I2C_ROW_AB_ADDRESS = 0x20
MCB_I2C_ROW_CD_ADDRESS = 0x21
MCB_I2C_ROW_EF_ADDRESS = 0x22
MCB_I2C_ROW_GH_ADDRESS = 0x23

"""! @brief     Board fields """
pcf_row_ab = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_AB_ADDRESS)
pcf_row_cd = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_CD_ADDRESS)
pcf_row_ef = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_EF_ADDRESS)
pcf_row_gh = PCF8575(MCB_I2C_PORT_NUM, MCB_I2C_ROW_GH_ADDRESS)

"""! @brief     Other defines """

Class Board()

def read_board():

    a = [i for i in pcf_row_ab.port][0:7]
    b = [i for i in pcf_row_ab.port][8:15]
    #c = [i for i in pcf_row_cd.port][0:7]
    #d = [i for i in pcf_row_cd.port][8:15]
    #e = [i for i in pcf_row_ef.port][0:7]
    #f = [i for i in pcf_row_ef.port][8:15]
    #g = [i for i in pcf_row_gh.port][0:7]
    #h = [i for i in pcf_row_gh.port][8:15]
    
    board = [a, b]

    return board

def menu():

    print("Menu")



def parser():

    """! @brief     Parser function to get all the arguments """

    # Description string
    description = "Description: " + APPTITLE + " " + VERSION + " " + DATE + " " + AUTHOR
    
    # Construct the argument parse and return the arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=description)
    
    parser.add_argument("-i", "--input", type=str, default="/home/pi/mChessBoard/src/stockfish-rpiz",
                        help="path to stockfish executable")
    parser.add_argument('--version', action='version', version=APPTITLE + " " + VERSION + " " + DATE + " " + AUTHOR)
    
    print('\n' + str(parser.parse_args()) + '\n')

    return parser.parse_args()


if __name__ == '__main__':

    """! @brief Main function """

    board = read_board()
    print(board)
    exit(0)

    # Get the arguments
    args = parser()

    #print(pcf_row_ab.port)
    #print(pcf_row_cd.port)
    #print(pcf_row_ef.port)
    #print(pcf_row_gh.port)

    try:
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
    except:
        print("Failed to init stockfish")

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

