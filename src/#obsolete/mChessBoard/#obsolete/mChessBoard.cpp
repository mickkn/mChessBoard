/*
 *    File:   mChessBoard.c
 *
 *    Handle chess board movement.
 * 
 */

#include "mChessBoard.hpp"
#include "settings.hpp"
#include "arduino.h"

ChessBoardData ChessBoard::data; 


bool ChessBoard::getBoardStatus(void) {


    return true;
}

bool ChessBoard::setPrevBoardStatus(void) {


    return true;
}

bool ChessBoard::setCurrentBoardStatus(void) {

    return true;
}

void ChessBoard::init() {

    // 
    ChessBoard::getBoardStatus();

 
}


String ChessBoard::getLiftedField(const uint8_t fields[8]) {
    
    return "0";
}

String ChessBoard::getPlacedField(const uint8_t fields[8]) {
    
    return "0";
}


