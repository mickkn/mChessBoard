/*
 *	Project mChessBoard
 * 
 *  Based on Arduino Leonardo, actually running on some 
 *  random TEENSY2.0 like board flashed with Arduino Bootload
 * 
 *  Developed in VSCODE, because Arduino IDE sucks
 * 
 */

#include "Keyboard.h"
//#include "mChessBoard.hpp"
#include "PCF8575.h"    // Library from Arduino library manager
#include "ButtonDebounce.h"
#include "settings.hpp"

/**
 *  @brief  Chess field sensor rows
 */
PCF8575 RowAB(0x20);
PCF8575 RowCD(0x21);
PCF8575 RowEF(0x22);
PCF8575 RowGH(0x23);

/**
 *  @brief  Chess led rows
 */
PCF8575 Leds(0x24);

/**
 * @brief Declaration of the states in FSM.
 */
enum FsmState {

    STATE_INIT,
    STATE_IDLE,
	STATE_ERROR,
    STATE_DEBUG,
    STATE_HUMAN_MOVE,
    STATE_AI_MOVE
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
    FsmControlFlags flags;
};

// Init. fsm
Fsm fsm;

/**
 *  @brief  Setup function
 */
void setup() {

	// Set the initial flag.
    fsm.initial = true;

    // Set the state.
    fsm.currentState = fsm.nextState = STATE_INIT;

	// Open the serial port for communication the the chess board.
	Serial.begin(115200);
	while(!Serial);

	// Initialize control over the keyboard.
	Keyboard.begin();

}

/**
 *  @brief  Main loop
 */
void loop() {

	// Set the firstEntry flag.
    bool firstEntry = fsm.initial || (fsm.nextState != fsm.currentState);

	// Update the current state.
    fsm.currentState = fsm.nextState;

	switch (fsm.currentState) {

		case STATE_INIT:

			Serial.println("-----( STATE : INIT )-----");

			if(firstEntry) {
				
				// Init. message.
				Serial.println("-----( Initializing mChessBoard v1.0.0 ... )-----");

				// Initialize the IO expander communication for sensors in ROW A and B.
				if(!RowAB.begin()) {
					Serial.println("ERROR: Could not initialize Row AB ...");
					// Just return on error
					if(!DEBUG) {
						fsm.nextState = STATE_ERROR;
						break;
					}
				}
			
				// Initialize the IO expander communication for sensors in ROW C and D.
				if(!RowCD.begin()) {
					Serial.println("ERROR: Could not initialize Row CD ...");
				}
			
				// Initialize the IO expander communication for sensors in ROW E and F.
				if(!RowEF.begin()) {
					Serial.println("ERROR: Could not initialize Row EF ...");
				}
			
				// Initialize the IO expander communication for sensors in ROW G and H.
				if(!RowGH.begin()) {
					Serial.println("ERROR: Could not initialize Row GH ...");
				}

				// Initialize the IO expander communication for LEDs.
				if(!Leds.begin()) {
					Serial.println("ERROR: Could not initialize Leds ...");
				}
			}

			// Changed state
			fsm.nextState = STATE_IDLE;

			break;
		
		case STATE_IDLE:

			if(firstEntry) {
				Serial.println("-----( STATE : IDLE )-----");
			}

			break;

		case STATE_ERROR:

			if(firstEntry) {
				Serial.println("-----( STATE : ERROR )-----");
			}

			break;

		default:
			break;
	}

	// Not initial anymore
	fsm.initial = false;
}
