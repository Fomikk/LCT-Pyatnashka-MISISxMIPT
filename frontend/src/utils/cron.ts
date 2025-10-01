export function validateCron(cron: string): { valid: boolean; message?: string } {
  const parts = cron.trim().split(/\s+/);
  if (parts.length !== 5) return { valid: false, message: 'Ожидается 5 полей: min hour dom mon dow' };
  const [min, hour, dom, mon, dow] = parts;
  const token = "(?:\*|\d+|\*/\d+|\d+-\d+|(?:\d+,)+\d+)";
  const re = new RegExp(`^${token}$`);
  const ok = [min, hour, dom, mon, dow].every((p) => re.test(p));
  return ok ? { valid: true } : { valid: false, message: 'Недопустимые символы в одном из полей' };
}

export const cronExamples: Array<{ label: string; value: string }> = [
  { label: 'Каждый день в 12:00', value: '0 12 * * *' },
  { label: 'Каждый час', value: '0 * * * *' },
  { label: 'Каждые 15 минут', value: '*/15 * * * *' },
  { label: 'По будням в 09:30', value: '30 9 * * 1-5' },
];


