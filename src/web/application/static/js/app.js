function onDrop(source, target, piece, orientation) {

    // see if the move is legal
    let pn = piece.includes('b')
        ? piece.toUpperCase().substring(1, 2)
        : piece.substring(1, 2);
    pn = piece.includes('P') ? '' : pn;
    let move = piece.includes('P')
        ? source + target
        : pn + source.substring(0, 1) + target;
    move =
        piece.includes('P') && target.includes('8')
        ? target.substring(0, 1) + '8Q'
        : move; // pawn promotion

    $.get('/app_move', {move: move}, function(data) {
        console.log(data);
        //document.querySelector('tbody#pgn-moves');
        //document.querySelector('#pgn').innerText = data.pgn;
        let moves = data.moves;
        if (data.game_over !== 'true') {
            let tbody = document.getElementById('pgn-moves');
            tbody.innerHTML = '';
            let i = 0;
            let m_len = moves.length;
            let row_number = 1;
            while (i < m_len) {
                let tr = document.createElement('tr');
                let th = document.createElement('th');
                th.setAttribute('scope', row_number.toString());
                th.innerText = row_number.toString();
                tr.appendChild(th);
                let td = document.createElement('td');
                td.innerText = moves[i].toString();
                tr.appendChild(td);
                if (m_len % 2 !== 1) {
                    td = document.createElement('td');
                    td.innerText = moves[i + 1].toString();
                    tr.appendChild(td);
                }
                i += 2;
                row_number++;
                tbody.appendChild(tr);
            }
            board.position(data.fen);
            $(".card-body#game-moves").scrollTop($(".card-body#game-moves")[0].scrollHeight);
        } else {
            document.querySelectorAll(".game-over")[1].innerText = "Game lost";
        }
    });
}

// to fix player with white/black peaces from messing around with other player's pieces.
// can be bypassed tho., that's why it's also validated in back-end too.
function onDragStart(source, piece, position, orientation) {
    if (
        (orientation === 'white' && piece.search(/^w/) === -1) ||
        (orientation === 'black' && piece.search(/^b/) === -1)
    ) {
        return false;
    }
}

$('#reset').click(function() {
    $.get('/reset', function(data) {
        board.position(data.fen);
        document.querySelector('#pgn').innerText = data.pgn;
    });
});

$('#undo').click(function() {
    if (!$(this).hasClass('text-muted')) {
        $.get('/undo', function(data) {
            board.position(data.fen);
            document.querySelector('#pgn').innerText = data.pgn;
        });
    } else {
    //
    }
});

$('#redo').click(function() {
    if (!$(this).hasClass('text-muted')) {
        $.get('/redo', function(data) {
            board.position(data.fen);
            document.querySelector('#pgn').innerText = data.pgn;
        });
    } else {
    //
    }
});

let cfg = {
    position: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR',
    showNotation: true,
    draggable: true,
    onDragStart: onDragStart,
    onDrop: onDrop
};
let board = ChessBoard('board', cfg);
$(window).resize(board.resize)

let socket = io();

socket.on('connect', function() {
    socket.emit('my_event', {data: 'Server is connected!'});
});

socket.on('move', function(msg) {

    console.log(msg.data)

    cfg = {
        position: msg.data.toString(),
    };
    board = ChessBoard('board', cfg);

});

socket.on('my_response', function(msg, cb) {
    console.log('Received #' + msg.count + ': ' + msg.data)
    $('#log').append('<br>' + $('<div/>').text('Received #' + msg.count + ': ' + msg.data).html());
    if (cb)
        cb();
});