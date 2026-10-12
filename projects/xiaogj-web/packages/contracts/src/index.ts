import { initContract } from '@ts-rest/core';
import { z } from 'zod';
const c = initContract();
export const api = c.router({
  health: { method: 'GET', path: '/api/health', responses: { 200: z.object({ status: z.literal('ok') }) } },
});
