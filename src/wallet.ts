import { ethers } from 'ethers';

export type SupportedNetwork = 'sepolia' | 'mainnet';

export interface WalletRecord {
  userId: number;
  network: SupportedNetwork;
  encryptedPrivateKey: string; // base64
  address: string;
}

export interface NetworkConfig {
  name: SupportedNetwork;
  rpcUrl: string;
  chainId: number;
}

export const NETWORKS: Record<SupportedNetwork, NetworkConfig> = {
  mainnet: {
    name: 'mainnet',
    rpcUrl: process.env.RPC_URL_MAINNET || 'https://cloudflare-eth.com',
    chainId: 1,
  },
  sepolia: {
    name: 'sepolia',
    rpcUrl: process.env.RPC_URL_SEPOLIA || 'https://rpc.sepolia.org',
    chainId: 11155111,
  },
};

export function getProvider(network: SupportedNetwork): ethers.JsonRpcProvider {
  const cfg = NETWORKS[network];
  return new ethers.JsonRpcProvider(cfg.rpcUrl, cfg.chainId);
}

export function formatEth(amountWei: bigint): string {
  try {
    return ethers.formatEther(amountWei);
  } catch {
    return '0';
  }
}
