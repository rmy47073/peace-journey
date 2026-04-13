/** 不把接口里的特定英文错误句直接展示在页面上（例如画面旁的状态条） */
export function uiErrorMessage(raw) {
  if (raw == null || raw === '') return ''
  const s = String(raw)
  if (/service not found/i.test(s)) return ''
  return s
}
