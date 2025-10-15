import { ethers } from 'ethers';
import { encryptUtf8, decryptUtf8 } from './crypto.js';
import { getProvider, formatEth, NETWORKS } from './wallet.js';
import type { SupportedNetwork } from './wallet.js';

export interface WalletPlain {
  address: string;
  privateKey: string;
}

export function createWallet(): WalletPlain {
  const wallet = ethers.Wallet.createRandom();
  return { address: wallet.address, privateKey: wallet.privateKey };
}

export function encryptPrivateKey(privateKey: string): string {
  return encryptUtf8(privateKey);
}

export function decryptPrivateKey(enc: string): string {
  return decryptUtf8(enc);
}

export async function getBalance(address: string, network: SupportedNetwork): Promise<string> {
  const provider = getProvider(network);
  const balance = await provider.getBalance(address);
  return formatEth(balance);
}

export async function sendTransaction(
  encPrivateKey: string,
  to: string,
  amountEth: string,
  network: SupportedNetwork
): Promise<string> {
  const provider = getProvider(network);
  const pk = decryptPrivateKey(encPrivateKey);
  const signer = new ethers.Wallet(pk, provider);
  const tx = await signer.sendTransaction({ to, value: ethers.parseEther(amountEth) });
  const receipt = await tx.wait();
  return receipt?.hash || tx.hash;
}
