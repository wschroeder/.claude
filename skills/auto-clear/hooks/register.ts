import type { Register } from 'claude-code'

// Claude Code names a project's scratchpad folder after its cwd, every character
// outside [A-Za-z0-9] replaced by '-'.
const pendingHandoff = (uid: string, cwd: string, sessionId: string) =>
  `/private/tmp/claude-${uid}/${cwd.replace(/[^A-Za-z0-9]/g, '-')}/${sessionId}/scratchpad/pending-handoff.md`

export const register: Register = on => {
  let uid: string | undefined

  on('turn.complete', async ($, e, next) => {
    const answer = await next(e)
    if (e.reason !== 'answer' || e.agentId !== undefined) return answer

    uid ??= (await $.process.run(['id', '-u'])).stdout.trim()
    const pending = pendingHandoff(uid, await $.session.cwd(), await $.session.id())
    if (!(await $.fs.exists(pending))) return answer

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
