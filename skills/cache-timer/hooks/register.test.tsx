import { test, expect, mock } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'
import type { On } from 'claude-code'

const usage = { model: 'm', input_tokens: 1, output_tokens: 1, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 }
const answered = { reason: 'answer', answer: 'done', durationMs: 1, isAborted: false, turnId: 't1', usage } as const
const aborted = { reason: 'aborted', answer: '', durationMs: 1, isAborted: true } as const

const HINT = { plugin: 'cache-timer', surface: 'terminal', component: 'PromptHint', props: { isDraft: false, isWorking: false, hint: '? for shortcuts' } } as const

const session = async ($: Engine, on: On) => {
  const clock = mock.clock(on)
  const shown: (string | undefined)[] = []
  const response: { takesMs: number, usage: typeof usage | null } = { takesMs: 0, usage }
  on('ui.render', ($, e) => {
    if (e.component === 'PromptHint') shown.push(e.props.tail)
    const { Text } = $.ui.resolve(e)
    return <Text>hint</Text>
  })
  on('turn.start', ($, e) => ({ turnId: e.turnId }))
  on('turn.step', async function* ($, e) {
    if (response.takesMs > 0) await clock.sleep(response.takesMs)
    return { turnId: e.turnId, index: e.index, answer: 'done', toolUses: [], stopReason: 'end_turn', usage: response.usage }
  })
  const turnEnd = { takesMs: 0 }
  on('turn.complete', async () => {
    if (turnEnd.takesMs > 0) await clock.sleep(turnEnd.takesMs)
    return { text: 'done' }
  })
  await $.ui.mount(HINT)
  shown.length = 0
  // The kit queues a redraw on the mocked clock.
  const drawn = async () => { await clock.advance(0); return shown }
  return { clock, drawn, response, turnEnd }
}

const request = async ($: Engine, fields: { index?: number, agentId?: string } = {}) => {
  for await (const _ of $.turn.step({ turnId: 't1', index: 0, model: 'm', messageCount: 1, ...fields })) {}
}

const answerTurn = async ($: Engine) => {
  await request($)
  await $.turn.complete(answered)
}

test('shows the whole lifetime when a turn ends', async ($, on) => {
  const { drawn } = await session($, on)

  await answerTurn($)

  expect(await drawn()).toEqual(['Cache 60m'])
})

test("counts the lifetime from the start of the turn's last request", async ($, on) => {
  const { clock, drawn, response } = await session($, on)
  await request($)
  await clock.advance(60_000)

  response.takesMs = 90_000
  const answering = request($, { index: 1 })
  await clock.advance(90_000)
  await answering
  await $.turn.complete(answered)
  await clock.advance(3.5 * 60_000 - 1)
  expect(await drawn()).toEqual(['Cache 60m'])
  await clock.advance(1)

  expect(await drawn()).toEqual(['Cache 60m', 'Cache 55m'])
})

test('starts from five minutes when the ttl option says 5m', { options: { ttl: '5m' } }, async ($, on) => {
  const { drawn } = await session($, on)

  await answerTurn($)

  expect(await drawn()).toEqual(['Cache 5m'])
})

test('counts down in steps of five minutes while more than five remain', async ($, on) => {
  const { clock, drawn } = await session($, on)
  await answerTurn($)

  await clock.advance(5 * 60_000 - 1)
  expect(await drawn()).toEqual(['Cache 60m'])
  await clock.advance(1)
  expect(await drawn()).toEqual(['Cache 60m', 'Cache 55m'])
  await clock.advance(50 * 60_000)

  expect(await drawn()).toEqual([
    'Cache 60m', 'Cache 55m', 'Cache 50m', 'Cache 45m', 'Cache 40m', 'Cache 35m',
    'Cache 30m', 'Cache 25m', 'Cache 20m', 'Cache 15m', 'Cache 10m', 'Cache 5m',
  ])
})

test('counts down by the minute from five minutes, by the second from one, and then says the cache expired', async ($, on) => {
  const { clock, drawn } = await session($, on)
  await answerTurn($)
  await clock.advance(55 * 60_000)
  ;(await drawn()).length = 0

  await clock.advance(4 * 60_000)
  expect(await drawn()).toEqual(['Cache 4m', 'Cache 3m', 'Cache 2m', 'Cache 60s'])
  await clock.advance(59_000)
  expect((await drawn()).slice(-2)).toEqual(['Cache 2s', 'Cache 1s'])
  await clock.advance(1000)
  expect((await drawn()).at(-1)).toBe('Cache expired')
  const settled = (await drawn()).length
  await clock.advance(10 * 60_000)

  expect(await drawn()).toHaveLength(settled)
})

test('rounds up to the next five minutes when a countdown resumes between two five-minute marks', async ($, on) => {
  const { clock, drawn } = await session($, on)
  await answerTurn($)
  await clock.advance(54 * 60_000)
  await $.turn.start({ text: 'next', turnId: 't2' })
  await clock.advance(30_000)
  ;(await drawn()).length = 0

  await $.turn.complete({ ...aborted, turnId: 't2' })
  expect(await drawn()).toEqual(['Cache 10m'])
  await clock.advance(30_000)

  expect(await drawn()).toEqual(['Cache 10m', 'Cache 5m'])
})

test('clears the label when the next turn starts and draws nothing while that turn runs', async ($, on) => {
  const { clock, drawn } = await session($, on)
  await answerTurn($)
  await drawn()

  await $.turn.start({ text: 'next', turnId: 't2' })
  await clock.advance(60 * 60_000)

  expect(await drawn()).toEqual(['Cache 60m', undefined])
})

test("draws nothing when the next turn starts while the last turn's end is still being handled", async ($, on) => {
  const { clock, drawn, turnEnd } = await session($, on)
  turnEnd.takesMs = 1000
  await request($)
  const ending = $.turn.complete(answered)

  await $.turn.start({ text: 'next', turnId: 't2' })
  await clock.advance(1000)
  await ending
  await clock.advance(60 * 60_000)

  expect(await drawn()).toEqual([undefined])
})

test("keeps the main conversation's countdown when a subagent's turn ends", async ($, on) => {
  const { clock, drawn } = await session($, on)
  await answerTurn($)
  await clock.advance(10 * 60_000)

  await $.turn.complete({ ...answered, turnId: 't2', agentId: 'a1' })
  await clock.advance(5 * 60_000)

  expect(await drawn()).toEqual(['Cache 60m', 'Cache 55m', 'Cache 50m', 'Cache 45m'])
})

test("keeps the main conversation's countdown when a subagent's turn starts", async ($, on) => {
  const { clock, drawn } = await session($, on)
  await answerTurn($)

  await $.turn.start({ text: 'look this up', turnId: 't2', agentId: 'a1' })
  await clock.advance(5 * 60_000)

  expect(await drawn()).toEqual(['Cache 60m', 'Cache 55m'])
})

test("keeps the main conversation's expiry when a subagent sends a request", async ($, on) => {
  const { clock, drawn } = await session($, on)
  await answerTurn($)
  await clock.advance(10 * 60_000)
  await $.turn.start({ text: 'next', turnId: 't2' })
  ;(await drawn()).length = 0

  await request($, { agentId: 'a1' })
  await $.turn.complete({ ...aborted, turnId: 't2' })

  expect(await drawn()).toEqual(['Cache 50m'])
})

test("resumes the earlier countdown when a turn's request comes back without usage", async ($, on) => {
  const { clock, drawn, response } = await session($, on)
  await answerTurn($)
  await clock.advance(10 * 60_000)
  await $.turn.start({ text: 'next', turnId: 't2' })
  await clock.advance(2 * 60_000)
  ;(await drawn()).length = 0

  response.usage = null
  await request($)
  await $.turn.complete({ ...aborted, turnId: 't2' })
  await clock.advance(3 * 60_000)

  expect(await drawn()).toEqual(['Cache 50m', 'Cache 45m'])
})

test("shows nothing when the session's first turn ends before any request", async ($, on) => {
  const { clock, drawn } = await session($, on)

  await $.turn.complete({ ...aborted, turnId: 't1' })
  await clock.advance(60_000)

  expect(await drawn()).toEqual([])
})
