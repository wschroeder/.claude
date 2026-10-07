import { test, expect } from 'claude-code/testing'
import type { On } from 'claude-code'

const OWN = '/private/tmp/claude-777/-Users-x-my-repo/S1/scratchpad/pending-handoff.md'
const OTHER = '/private/tmp/claude-777/-Users-x-my-repo/S2/scratchpad/pending-handoff.md'

const turn = {
  reason: 'answer',
  answer: 'done',
  durationMs: 1,
  isAborted: false,
  turnId: 't1',
} as const

const session = (on: On, own: string | null = 'resume the work\n', cwd = '/Users/x/my.repo') => {
  const files = new Map([[OTHER, 'not mine']])
  if (own !== null) files.set(OWN, own)
  const commands: string[] = []
  const submitted: string[] = []
  let settle!: () => void
  const done = new Promise<void>(resolve => { settle = resolve })

  on('turn.complete', () => ({ text: 'done' }))
  on('process.run', ($, e) => ({
    value: e.argv.join(' ') === 'id -u'
      ? { exitCode: 0, stdout: '777\n', stderr: '', isStdoutTruncated: false, isStderrTruncated: false }
      : { exitCode: 1, stdout: '', stderr: 'unexpected', isStdoutTruncated: false, isStderrTruncated: false },
  }))
  on('session.id', () => ({ value: 'S1' }))
  on('session.cwd', () => ({ value: cwd }))
  on('fs.exists', ($, e) => ({ value: files.has(e.path) }))
  on('fs.list', ($, e) => {
    const names = new Set(
      [...files.keys()]
        .filter(path => path.startsWith(`${e.path}/`))
        .map(path => path.slice(e.path.length + 1).split('/')[0]!),
    )
    return { value: [...names].map(name => ({ name, kind: 'dir' as const, size: 0, mtimeMs: 0, isLink: false })) }
  })
  on('fs.read', ($, e) => {
    const text = files.get(e.path)
    if (text === undefined) throw new Error(`ENOENT: ${e.path}`)
    return { value: text }
  })
  on('fs.write', ($, e) => { files.set(e.path, e.text); return { value: undefined } })
  on('command.run', ($, e) => { commands.push(e.command); return {} })
  on('prompt.submit', ($, e) => { submitted.push(e.text); settle(); return { text: e.text } })

  return { files, commands, submitted, done }
}

test("submits the handoff from this session's own scratchpad after /clear", async ($, on) => {
  const { files, commands, submitted, done } = session(on)

  await $.turn.complete(turn)
  await done

  expect(commands).toEqual(['clear'])
  expect(submitted).toEqual(['resume the work'])
  expect(files.get(OWN)).toBe('')
  expect(files.get(OTHER)).toBe('not mine')
})

test('finds the handoff after the session moves into a worktree', async ($, on) => {
  const { files, commands, submitted, done } = session(on, 'resume the work\n', '/Users/x/my.repo/.claude/worktrees/W')

  await $.turn.complete(turn)
  await done

  expect(commands).toEqual(['clear'])
  expect(submitted).toEqual(['resume the work'])
  expect(files.get(OWN)).toBe('')
  expect(files.get(OTHER)).toBe('not mine')
})

test("leaves the handoff alone when a subagent's turn ends", async ($, on) => {
  const { files, commands, submitted } = session(on)

  await $.turn.complete({ ...turn, agentId: 'sub1' })

  expect(commands).toEqual([])
  expect(submitted).toEqual([])
  expect(files.get(OWN)).toBe('resume the work\n')
})

test('leaves the handoff alone when the turn was interrupted', async ($, on) => {
  const { files, commands, submitted } = session(on)

  await $.turn.complete({ ...turn, reason: 'aborted', isAborted: true })

  expect(commands).toEqual([])
  expect(submitted).toEqual([])
  expect(files.get(OWN)).toBe('resume the work\n')
})

test('does not clear when the handoff file was already emptied', async ($, on) => {
  const { commands, submitted } = session(on, '  \n')

  await $.turn.complete(turn)

  expect(commands).toEqual([])
  expect(submitted).toEqual([])
})

test('does not clear when no handoff file exists', async ($, on) => {
  const { commands, submitted } = session(on, null)

  expect(await $.turn.complete(turn)).toEqual({ text: 'done' })

  expect(commands).toEqual([])
  expect(submitted).toEqual([])
})
