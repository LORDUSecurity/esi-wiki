import raw from '../data/media.json';

/** Every asset here came from Wikimedia Commons; keep the credit line reachable. */
export const ASSETS = raw;

export function byTopic(topic) {
  return raw.filter((a) => a.topic === topic);
}

export function pick(topic, index = 0) {
  const list = byTopic(topic);
  return list[index % Math.max(list.length, 1)] || null;
}

export function credits() {
  const seen = new Map();
  for (const a of raw) {
    const key = `${a.artist}|${a.license}`;
    if (!seen.has(key)) seen.set(key, a);
  }
  return [...seen.values()];
}
