import { api } from './client'
import type { MakeupPlan, Reply, Session } from '../types'

export function expectedPlan(plan?: MakeupPlan | null) {
  if (!plan) return {}
  return {
    expected_plan_id: plan.id,
    expected_revision: plan.revision,
    expected_step_id: plan.steps[plan.active_index]?.id,
  }
}

/** Look up the original event after an interrupted reply. This never resubmits it. */
export async function readCommittedCommand(sessionId: string, eventId: string, signal?: AbortSignal) {
  try {
    return await api<{event: {event_id: string; status: 'committed'}; session: Session}>(
      '/makeup/events/' + encodeURIComponent(sessionId) + '/' + encodeURIComponent(eventId),
      undefined,
      'GET',
      signal,
    )
  } catch (error) {
    if ((error as {status?: number}).status === 404) return null
    throw error
  }
}

export function replyFromSnapshot(session: Session, message: string): Reply {
  return {session, message, step: session.current_step ?? null}
}

const pendingKey = 'trace.pending-coaching-command'

export interface PendingCommand {
  sessionId: string
  eventId: string
}

export function readPendingCommand(): PendingCommand | null {
  try {
    const pending = JSON.parse(sessionStorage.getItem(pendingKey) ?? 'null')
    return typeof pending?.sessionId === 'string' && typeof pending?.eventId === 'string' ? pending : null
  } catch {
    return null
  }
}

export function rememberPendingCommand(command: PendingCommand) {
  sessionStorage.setItem(pendingKey, JSON.stringify(command))
}

export function forgetPendingCommand(eventId: string) {
  if (readPendingCommand()?.eventId === eventId) sessionStorage.removeItem(pendingKey)
}
