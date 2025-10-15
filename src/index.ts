import 'dotenv/config';
import { Bot, Context } from 'grammy';
import { getUserState, setNetwork, upsertWallet } from './userState.js';
import { createWallet, encryptPrivateKey, getBalance, sendTransaction } from './evm.js';
import { NETWORKS } from './wallet.js';
import type { SupportedNetwork } from './wallet.js';
import { createOffer, listOffers } from './p2p.js';

const token = process.env.BOT_TOKEN;
if (!token) {
  console.error('BOT_TOKEN is missing');
  process.exit(1);
}

const bot = new Bot<Context>(token);

bot.command('start', async (ctx) => {
  const userId = ctx.from?.id;
  if (!userId) return;
  const state = await getUserState(userId);
  await ctx.reply(
    [
      'Добро пожаловать в Web3 кошелёк + P2P бот! 🔐',
      `Текущая сеть: ${state.network}`,
      'Используйте /help чтобы увидеть команды.',
    ].join('\n')
  );
});
bot.command('help', (ctx) =>
  ctx.reply(
    [
      'Команды:',
      '/start — приветствие и текущая сеть',
      '/network <sepolia|mainnet> — переключить сеть',
      '/address — показать ваш адрес (создаст кошелёк при необходимости)',
      '/balance — баланс текущей сети',
      '/send <to> <amount> — отправить ETH',
      '/offer <amount> <currency> — создать P2P оффер (заглушка)',
      '/offers — список офферов (заглушка)',
    ].join('\n')
  )
);

bot.command('network', async (ctx) => {
  const userId = ctx.from?.id;
  if (!userId) return;
  const arg = ctx.match?.toString().trim().toLowerCase() as SupportedNetwork | '';
  if (arg !== 'sepolia' && arg !== 'mainnet') {
    await ctx.reply('Укажите сеть: /network sepolia | mainnet');
    return;
  }
  const updated = await setNetwork(userId, arg);
  await ctx.reply(`Сеть переключена на: ${updated.network}`);
});

bot.command('address', async (ctx) => {
  const userId = ctx.from?.id;
  if (!userId) return;
  const state = await getUserState(userId);
  if (!state.wallet) {
    const w = createWallet();
    await upsertWallet(userId, {
      userId,
      network: state.network,
      encryptedPrivateKey: encryptPrivateKey(w.privateKey),
      address: w.address,
    });
    await ctx.reply(`Создан новый адрес: ${w.address}`);
    return;
  }
  await ctx.reply(`Ваш адрес: ${state.wallet.address}`);
});

bot.command('balance', async (ctx) => {
  const userId = ctx.from?.id;
  if (!userId) return;
  const state = await getUserState(userId);
  if (!state.wallet) {
    await ctx.reply('Кошелёк ещё не создан. Введите /address чтобы создать.');
    return;
  }
  const bal = await getBalance(state.wallet.address, state.network);
  await ctx.reply(`Баланс (${state.network}): ${bal} ETH`);
});

bot.command('send', async (ctx) => {
  const userId = ctx.from?.id;
  if (!userId) return;
  const state = await getUserState(userId);
  if (!state.wallet) {
    await ctx.reply('Кошелёк ещё не создан. Введите /address чтобы создать.');
    return;
  }
  const [to, amount] = ctx.match?.toString().split(/\s+/).filter(Boolean) ?? [];
  if (!to || !amount) {
    await ctx.reply('Использование: /send <to> <amount>');
    return;
  }
  try {
    const hash = await sendTransaction(state.wallet.encryptedPrivateKey, to, amount, state.network);
    await ctx.reply(`Транзакция отправлена: ${hash}`);
  } catch (e: any) {
    await ctx.reply(`Ошибка отправки: ${e?.message || e}`);
  }
});

// P2P заглушки
bot.command('offer', async (ctx) => {
  const userId = ctx.from?.id;
  if (!userId) return;
  const [amount, currencyRaw] = ctx.match?.toString().split(/\s+/).filter(Boolean) ?? [];
  const currency = (currencyRaw || '').toUpperCase();
  if (!amount || !currency) {
    await ctx.reply('Использование: /offer <amount> <currency>. Пример: /offer 0.1 ETH');
    return;
  }
  const state = await getUserState(userId);
  const id = `${Date.now()}_${userId}`;
  await createOffer({ id, userId, amount, currency, network: state.network, createdAt: Date.now() });
  await ctx.reply(`Оффер создан: ${amount} ${currency} в сети ${state.network}. ID: ${id}`);
});

bot.command('offers', async (ctx) => {
  const offers = await listOffers();
  if (!offers.length) {
    await ctx.reply('Пока нет офферов. Создайте с помощью /offer');
    return;
  }
  const top = offers.slice(0, 10);
  const lines = top.map((o) => `#${o.id} • ${o.amount} ${o.currency} • ${o.network} • by ${o.userId}`);
  await ctx.reply(['Последние офферы:', ...lines].join('\n'));
});

bot.hears(/.*/, (ctx) => ctx.reply('Бот активен. Используйте /help.'));

bot.catch((err) => {
  console.error('Bot error', err);
});

bot.start();
console.log('Bot started');
