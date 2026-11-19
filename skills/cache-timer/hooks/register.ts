import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Label } from '../types'

const MINUTE = 60_000

const shownLabel = atom({ plugin: 'cache-timer', key: 'label' } as const, null as Label)

// The label's unit coarsens as the time left grows, so the hint line changes rarely until the end is near.
const stepFor = (left: number) => (left > 5 * MINUTE ? 5 * MINUTE : left > MINUTE ? MINUTE : 1000)

const label = (left: number) => {
  if (left <= 0) return 'Cache expired'
  const step = stepFor(left)
  const shown = Math.ceil(left / step) * step
  return step === 1000 ? `Cache ${shown / 1000}s` : `Cache ${shown / MINUTE}m`
}

const show = async ($: EngineInterface, expiresAt: number, isCurrent: () => boolean): Promise<void> => {
  const left = expiresAt - (await $.clock.now())
  if (!isCurrent()) return
  await update($, shownLabel, () => (isCurrent() ? label(left) : null))
  if (left <= 0) return
  const step = stepFor(left)
  $.clock.after(left % step || step, () => void show($, expiresAt, isCurrent))
}

export const register: Register = (on, options) => {
  const lifetime = options.ttl === '5m' ? 5 * MINUTE : 60 * MINUTE
  let expiresAt: number | undefined
  let mainTurnStarts = 0

  on('turn.start', async ($, e, next) => {
    if (e.agentId !== undefined) return next(e)
    mainTurnStarts++
    await update($, shownLabel, () => null)
    return next(e)
  })

  on('ui.render', { component: 'PromptHint' }, async ($, e, next) => {
    const tail = await read($, shownLabel)
    return tail === null ? next(e) : next({ ...e, props: { ...e.props, tail } })
  })

  // The provider measures a cache entry's lifetime from the start of the request that wrote or read it.
  on('turn.step', async function* ($, e, next) {
    if (e.agentId !== undefined) return yield* next(e)
    const sentAt = await $.clock.now()
    const response = yield* next(e)
    if (response.usage !== null) expiresAt = sentAt + lifetime
    return response
  })

  on('turn.complete', async ($, e, next) => {
    const startsSeen = mainTurnStarts
    const answer = await next(e)
    if (e.agentId !== undefined || expiresAt === undefined) return answer
    await show($, expiresAt, () => mainTurnStarts === startsSeen)
    return answer
  })
}
