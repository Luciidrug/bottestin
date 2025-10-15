import { readJson, writeJson, ensureDir } from './store.js';

export interface Offer {
  id: string;
  userId: number;
  amount: string; // in ETH or token units (string to keep exact)
  currency: string; // e.g., ETH, USDT
  network: 'sepolia' | 'mainnet';
  createdAt: number;
}

const DB_PATH = 'data/offers.json';

export async function listOffers(): Promise<Offer[]> {
  return readJson<Offer[]>(DB_PATH, []);
}

export async function createOffer(offer: Offer): Promise<void> {
  const offers = await readJson<Offer[]>(DB_PATH, []);
  offers.unshift(offer);
  await writeJson(DB_PATH, offers);
}
