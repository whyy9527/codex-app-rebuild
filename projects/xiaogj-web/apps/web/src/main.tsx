import React from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { createRootRoute, createRoute, createRouter, RouterProvider } from '@tanstack/react-router';
import { initClient } from '@ts-rest/core';
import { api } from '@xiaogj/contracts';
import './style.css';
const client = initClient(api, { baseUrl: '' });
function DevelopmentEntry() {
  const health = useQuery({ queryKey: ['health'], queryFn: async () => { const r = await client.health(); if (r.status !== 200) throw new Error('API unavailable'); return r.body; } });
  return <main><h1>校管家复刻开发入口</h1><p>正在采集原版页面与交互。本页用于验证前后端连接，尚未作为复刻页面交付。</p><p role="status">API：{health.isPending ? '连接中' : health.isError ? '未连接' : health.data.status}</p></main>;
}
const rootRoute = createRootRoute();
const indexRoute = createRoute({ getParentRoute: () => rootRoute, path: '/', component: DevelopmentEntry });
const router = createRouter({ routeTree: rootRoute.addChildren([indexRoute]) });
declare module '@tanstack/react-router' { interface Register { router: typeof router } }
createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={new QueryClient()}><RouterProvider router={router}/></QueryClientProvider></React.StrictMode>);
