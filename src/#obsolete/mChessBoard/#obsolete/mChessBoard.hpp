/*
 *    File:   mChessBoard.h
 *
 *    Handle chess board movement.
 * 
 */

#ifndef MCHESSBOARD_H
#define MCHESSBOARD_H

#include "stdint.h"

struct ChessBoardData {

    uint8_t prevBoardStatus[8];

    uint8_t currentBoardStatus[8];
};

class ChessBoard {

    private:

        static ChessBoardData data;

        static bool getBoardStatus(void);

        static bool setPrevBoardStatus(void);

        static bool setCurrentBoardStatus(void);

    public:

        static void init(void);

        /**
         *  @brief	Get the field name of the lifted token.
         *
         *  @return String  Field that the token is lifted from, e.g. "e2", "h5", etc.
         */
        static String getLiftedField(const uint8_t fields[8]);

        /**
         * @brief	Get the field name of the placed token.
         *  
         * @return	String  Field that the token is placed on, e.g. "e2", "h5", etc.
         */
        static String getPlacedField(const uint8_t fields[8]);

};

#endif /* MCHESSBOARD_H */