import {api} from '../api/client'

export type LocalScope = 'camera' | 'adaptive' | 'photo'
type LocalPermit = {permit_id: string; expires_at: number; baseline_version: number}

export async function grantLocalPermit(sessionId: string, scope: LocalScope): Promise<LocalPermit> {
  const permit = await api<LocalPermit>('/vision/local/permits', {session_id: sessionId, scope})
  if (!permit?.permit_id || !Number.isFinite(permit.expires_at) || !Number.isInteger(permit.baseline_version)) {
    throw new Error('The local analysis permit response was incomplete.')
  }
  return permit
}

export function revokeLocalPermit(sessionId: string, permitId: string) {
  return api('/vision/local/' + encodeURIComponent(sessionId), {permit_id: permitId},
    'DELETE', undefined, true).then(() => {}).catch(() => {})
}

export function revokeLocalBaseline(sessionId: string, permitId: string) {
  return api<{baseline_version: number}>('/vision/local/' + encodeURIComponent(sessionId),
    {baseline: true, permit_id: permitId}, 'DELETE', undefined, true)
}
