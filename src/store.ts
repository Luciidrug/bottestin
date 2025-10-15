import { readFile, writeFile, mkdir } from 'fs/promises';
import { dirname } from 'path';

export async function ensureDir(path: string): Promise<void> {
  try {
    await mkdir(path, { recursive: true });
  } catch {}
}

export async function readJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const raw = await readFile(path, 'utf8');
    return JSON.parse(raw) as T;
  } catch (e) {
    return fallback;
  }
}

export async function writeJson<T>(path: string, data: T): Promise<void> {
  await ensureDir(dirname(path));
  const raw = JSON.stringify(data, null, 2);
  await writeFile(path, raw, 'utf8');
}
