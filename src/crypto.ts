import { randomBytes, createCipheriv, createDecipheriv, scryptSync } from 'crypto';

const IV_LENGTH = 12; // AES-GCM recommended iv length

export function getMasterKey(): Buffer {
  const secret = process.env.ENCRYPTION_KEY || '';
  if (!secret) throw new Error('ENCRYPTION_KEY is missing');
  // derive 32-byte key from passphrase
  return scryptSync(secret, 'tg-bot-salt', 32);
}

export function encryptUtf8(plaintext: string): string {
  const key = getMasterKey();
  const iv = randomBytes(IV_LENGTH);
  const cipher = createCipheriv('aes-256-gcm', key, iv);
  const ciphertext = Buffer.concat([cipher.update(Buffer.from(plaintext, 'utf8')), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([iv, tag, ciphertext]).toString('base64');
}

export function decryptUtf8(encoded: string): string {
  const key = getMasterKey();
  const data = Buffer.from(encoded, 'base64');
  const iv = data.subarray(0, IV_LENGTH);
  const tag = data.subarray(IV_LENGTH, IV_LENGTH + 16);
  const ciphertext = data.subarray(IV_LENGTH + 16);
  const decipher = createDecipheriv('aes-256-gcm', key, iv);
  decipher.setAuthTag(tag);
  const plaintext = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
  return plaintext.toString('utf8');
}
