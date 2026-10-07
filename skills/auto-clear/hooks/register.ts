import type { EngineInterface, Register } from 'claude-code'

// A session's scratchpad folder can be named after a directory other than its current
// cwd, as after the session moves into a worktree. The session id is unique, so search
// every project folder for it.
const findPendingHandoff = async ($: EngineInterface, uid: string, sessionId: string) => {
  const tmp = `/private/tmp/claude-${uid}`
  const projects = await $.fs.list(tmp)
  for (const project of projects) {
    const path = `${tmp}/${project.name}/${sessionId}/scratchpad/pending-handoff.md`
    if (await $.fs.exists(path)) return path
  }
  return undefined
}

export const register: Register = on => {
  let uid: string | undefined

  on('turn.complete', async ($, e, next) => {
    const answer = await next(e)
    if (e.reason !== 'answer' || e.agentId !== undefined) return answer

    uid ??= (await $.process.run(['id', '-u'])).stdout.trim()
    const pending = await findPendingHandoff($, uid, await $.session.id())
    if (pending === undefined) return answer

    const handoff = (await $.fs.read(pending)).trim()
    if (handoff === '') return answer

    // Emptied before queuing so a second turn.complete cannot replay it.
    await $.fs.write(pending, '')
    $.ui.toast('auto-clear: queuing /clear and the handoff')
    // Not awaited: $.command.run rejects inside a hook the turn is waiting on.
    void $.command.run({ command: 'clear', args: '' })
      .then(() => $.prompt.submit({ text: handoff }))
      .catch(err => $.ui.toast(`auto-clear failed: ${String(err)}`))
    return answer
  })
}
