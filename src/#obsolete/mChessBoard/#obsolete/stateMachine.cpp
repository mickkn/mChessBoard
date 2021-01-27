#include "stateMachine.hpp"
#include "mChessBoard.hpp"

void fsmInit(Fsm* fsm) {

    // Set the initial flag.
    fsm->initial = true;

    // Set the state.
    fsm->currentState = fsm->nextState = STATE_INIT;

}

void fsmHandleEvent(Fsm* fsm, FsmEvent evt) {

    // Set the firstEntry flag.
    bool firstEntry = fsm->initial || (fsm->nextState != fsm->currentState);

    // Update the current state.
    fsm->currentState = fsm->nextState;

    // Switch through states and events.
    // States are only allowed to react on events of type
    // `FsmEvent`, and all output/actions should be performed
    // through the `fsm->actions` interface.

    // Main state machine.
    switch(fsm->currentState) {

        case STATE_INIT:

            fsm->actions->initBoard(fsm);

            break;

        default:

            // Unknown state
            break;

    }

    fsm->initial = false;
}