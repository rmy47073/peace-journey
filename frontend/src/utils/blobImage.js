/**
 * 帧接口出错时常返回 JSON；用 blob 当 <img> 的 src 会误显示正文。
 * 只认 JPEG 文件头，不信任 Content-Type（避免 JSON 被标成 image/jpeg）。
 */
export async function isLikelyJpegBlob(blob) {
  if (!(blob instanceof Blob) || blob.size < 3) return false
  const head = new Uint8Array(await blob.slice(0, 3).arrayBuffer())
  return head[0] === 0xff && head[1] === 0xd8 && head[2] === 0xff
}
