import { readJson, writeJson } from './store.js';
import { encryptUtf8, decryptUtf8 } from './crypto.js';
import type { WalletRecord, SupportedNetwork } from './wallet.js';

export interface UserState {
  userId: number;
  network: SupportedNetwork;
  wallet?: WalletRecord;
}

const DB_PATH = 'data/users.json';

export async function getUserState(userId: number): Promise<UserState> {
  const db = await readJson<Record<string, UserState>>(DB_PATH, {});
  const key = String(userId);
  const stored = db[key];
  if (!stored) {
    const state: UserState = { userId, network: 'sepolia' };
    db[key] = state;
    await writeJson(DB_PATH, db);
    return state;
  }
  return stored;
}

export async function setNetwork(userId: number, network: SupportedNetwork): Promise<UserState> {
  const db = await readJson<Record<string, UserState>>(DB_PATH, {});
  const key = String(userId);
  const prev = db[key] || { userId, network };
  prev.network = network;
  db[key] = prev;
  await writeJson(DB_PATH, db);
  return prev;
}

export async function upsertWallet(userId: number, wallet: WalletRecord): Promise<void> {
  const db = await readJson<Record<string, UserState>>(DB_PATH, {});
  const key = String(userId);
  const prev = db[key] || { userId, network: 'sepolia' };
  prev.wallet = wallet;
  db[key] = prev;
  await writeJson(DB_PATH, db);
}
