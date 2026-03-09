import assert from 'node:assert/strict';

const INVALID_CUT_POINT_EMPTY_PREPARATION = 'invalid_cut_point_empty_preparation';

function synthesizePreparation({
  boundaryStart,
  firstKeptEntryIndex,
  turnStartIndex,
  isSplitTurn,
  sourceMessages,
}) {
  const pathEntries = sourceMessages.map((role, i) => ({ id: `e${i}`, type: 'message', message: { role } }));
  const historyEnd = isSplitTurn ? turnStartIndex : firstKeptEntryIndex;
  const usageMessages = pathEntries.map((e) => e.message).filter(Boolean);
  const messagesToSummarize = [];
  for (let i = boundaryStart; i < historyEnd; i++) {
    const msg = pathEntries[i]?.message;
    if (msg) messagesToSummarize.push(msg);
  }
  const turnPrefixMessages = [];
  if (isSplitTurn) {
    for (let i = turnStartIndex; i < firstKeptEntryIndex; i++) {
      const msg = pathEntries[i]?.message;
      if (msg) turnPrefixMessages.push(msg);
    }
  }
  const hasRealHistoryCandidates = usageMessages.some((msg) => ['user','assistant','toolResult'].includes(msg.role));
  if (messagesToSummarize.length === 0 && turnPrefixMessages.length === 0 && hasRealHistoryCandidates) {
    const err = new Error(INVALID_CUT_POINT_EMPTY_PREPARATION);
    err.name = 'InvalidCutPointEmptyPreparationError';
    throw err;
  }
  return { messagesToSummarize, turnPrefixMessages };
}

function run(name, fn) {
  try { fn(); console.log(`PASS ${name}`); }
  catch (err) { console.error(`FAIL ${name}`); throw err; }
}

run('A live-like regression', () => {
  assert.throws(() => synthesizePreparation({
    boundaryStart: 2,
    firstKeptEntryIndex: 2,
    turnStartIndex: 2,
    isSplitTurn: false,
    sourceMessages: ['user','assistant','user','assistant'],
  }), /invalid_cut_point_empty_preparation/);
});

run('B valid non-split path', () => {
  const prep = synthesizePreparation({
    boundaryStart: 1,
    firstKeptEntryIndex: 3,
    turnStartIndex: 3,
    isSplitTurn: false,
    sourceMessages: ['user','assistant','user','assistant'],
  });
  assert.equal(prep.messagesToSummarize.length, 2);
  assert.equal(prep.turnPrefixMessages.length, 0);
});

run('C valid split-turn path', () => {
  const prep = synthesizePreparation({
    boundaryStart: 1,
    firstKeptEntryIndex: 4,
    turnStartIndex: 3,
    isSplitTurn: true,
    sourceMessages: ['user','assistant','user','assistant','toolResult'],
  });
  assert.equal(prep.messagesToSummarize.length, 2);
  assert.equal(prep.turnPrefixMessages.length, 1);
});

run('D truly empty history', () => {
  const prep = synthesizePreparation({
    boundaryStart: 0,
    firstKeptEntryIndex: 0,
    turnStartIndex: 0,
    isSplitTurn: false,
    sourceMessages: [],
  });
  assert.equal(prep.messagesToSummarize.length, 0);
  assert.equal(prep.turnPrefixMessages.length, 0);
});
