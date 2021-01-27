#ifndef STATEMACHINE_H
#define STATEMACHINE_H

/**
 * @brief   Function pointer for the actions.
 *
 * @param   fsm     Finite State Machine pointer.
 *
 * @return  true/false.
 */
typedef bool (*FsmActionFn)(struct Fsm*);

/**
 * @brief Declaration of the states in FSM.
 */
enum FsmState {

    STATE_INIT,
    STATE_IDLE,
    STATE_DEBUG,
    STATE_HUMAN_MOVE,
    STATE_AI_MOVE
};

/**
 * @brief   Declaration of Events / Inputs in FSM.
 */
enum FsmEvent {

    NO_EVENT,
    EVENT_PIECE_LIFTED,
    EVENT_PIECE_PLACED,
};

/**
 * @brief   Declaration of Actions / Outputs in the FSM.
 *
 * @note    Actions that can be called from within the state machine.
 *          No other "outside" functions should be called.
 */
struct FsmActions {

};

/**
 * @brief   Declaration of the Control flags.
 * @note    Used for example to disable/enable certain submodules at runtime.
 *          As creating more state is bad design, the use of state variables like
 *          these should be limited.
 */
struct FsmControlFlags {

};

/**
 * @brief   Declaration of the single encapsulation of the state machine.
 */
struct Fsm {

    bool initial;
    FsmState currentState;
    FsmState nextState;
    FsmActions* actions;
    FsmControlFlags flags;
};

/**
 * @brief   Function for initializing the state machine.
 *
 * @param   fsm      The state machine.
 */
void fsmInit(Fsm* fsm);

/**
 * @brief   Function for getting the next event for the state machine.
 *
 * @param   fsm        The state machine.
 *
 * @return  fsmEvent        The next event in the queue.
 */
FsmEvent fsmGetNextEvent(Fsm* fsm);

/**
 * @brief   Function for executing the next state.
 *
 * @param   fsm        The state machine.
 * @param   evt        The next event in the queue.
 */
void fsmHandleEvent(Fsm* fsm, FsmEvent evt);

#endif /* STATEMACHINE_H */