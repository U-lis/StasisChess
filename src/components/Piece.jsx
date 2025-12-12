import React from 'react';

const pieceUnicode = {
  w: { king: '♔', queen: '♕', rook: '♖', bishop: '♗', knight: '♘', pawn: '♙' },
  b: { king: '♚', queen: '♛', rook: '♜', bishop: '♝', knight: '♞', pawn: '♟︎' }
};

const pieceStyle = (isStunned) => ({
  fontSize: '36px',
  cursor: 'pointer',
  opacity: isStunned ? 0.5 : 1,
  textShadow: isStunned ? '0 0 5px red' : 'none',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center'
});

const stackStyle = {
  fontSize: '10px',
  lineHeight: '1',
  marginTop: '-5px'
};

export default function Piece({ type, color, stun, moveStack, onSelect }) {
  const isStunned = stun > 0;
  return (
    <div style={pieceStyle(isStunned)} onClick={onSelect}>
      <div>{pieceUnicode[color][type]}</div>
      {(stun > 0 || moveStack > 0) && (
        <div style={stackStyle}>{`${stun}:${moveStack}`}</div>
      )}
    </div>
  );
}
