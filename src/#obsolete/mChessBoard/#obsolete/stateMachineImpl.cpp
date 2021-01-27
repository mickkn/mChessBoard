#include "stateMachineImpl.hpp"
#include "mChessBoard.hpp"

/**
 * @brief Declaration of all the action proto types used for the action handler.
 */

// mChessBoard actions.
static bool initBoard(Fsm* fsm);

/**
 * @brief   Set the action list.
 */
FsmActions fsmTargetActions = {

    // mChessBoard actions.
    .initBoard = initBoard
    
};

/**
 * @brief   Get the next event for the state machine.
 *
 * @note    This is the target specific implementation of this function,
 *          as it extracts the events directly from the hardware. A stub of
 *          this function should be implemented for testing.
 *
 * @param   fsm     The state machine.
 * @return  Return the next event in the queue.
 */
FsmEvent fsmGetNextEvent(Fsm* fsm) {

    // Finally return NO_EVENT.
    return NO_EVENT;

}

/**
 * @brief   Setting up the chess board.
 */
static bool initBoard(Fsm* fsm) {

    Chessboard::init();

}