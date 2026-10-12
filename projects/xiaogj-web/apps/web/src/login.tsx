import { useEffect, useState } from "react";
import { initClient } from "@ts-rest/core";
import { api } from "@xiaogj/contracts";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import "./login.css";

const client = initClient(api, { baseUrl: "" });
const usernameHint = "请输入带有后缀的用户名，如：张三@xiaogj";
function shufflePhotos() {
  const ids = Array.from({ length: 98 }, (_, i) => i + 1);
  for (let i = ids.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [ids[i], ids[j]] = [ids[j]!, ids[i]!]; }
  return ids;
}
function LoginForm({ onLogin }: { onLogin: () => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [photos] = useState(() => [...shufflePhotos(), ...shufflePhotos()]);
  const [size, setSize] = useState(() => ({ width: window.innerWidth, height: window.innerHeight }));
  useEffect(() => { const resize = () => setSize({ width: window.innerWidth, height: window.innerHeight }); window.addEventListener("resize", resize); return () => window.removeEventListener("resize", resize); }, []);
  const width = Math.ceil((size.height / 2 + Math.sqrt(3) * size.width / 2) / 200) * 210;
  const height = Math.ceil((size.width / 2 + Math.sqrt(3) * size.height / 2) / 276) * 286;
  const submit = async () => {
    if (busy) return;
    if (!username || !password) { setMessage("请输入用户名和密码"); return; }
    setBusy(true); setMessage("");
    try {
      const actual = await client.login({ body: { username, password } });
      if (actual.status === 200) { setPassword(""); onLogin(); }
      else setMessage(actual.status === 401 ? actual.body.message : "登录暂时不可用");
    } catch { setMessage("登录暂时不可用"); }
    finally { setBusy(false); }
  };
  return <main className="login-page">
    <div className="login-background" aria-hidden="true"><div className="login-coverage" style={{ width, height, transform: `translate(${Math.trunc((size.width - width) / 2)}px, ${Math.trunc((size.height - height) / 2)}px) rotate(-30deg)` }}><div className="login-photo-list">{photos.map((id, i) => <div key={i} style={{ backgroundImage: `url(/login-photos/${id}.webp)` }} />)}</div></div></div>
    <div className="login-shade" />
    <div className="login-panel"><div className="login-banner" aria-hidden="true" /><section className="login-entry">
      <h1>欢迎登录</h1>
      <form onSubmit={e => { e.preventDefault(); void submit(); }}>
        <input autoFocus aria-label={usernameHint} placeholder={usernameHint} autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} />
        <input type="password" aria-label="请输入密码" placeholder="请输入密码" autoComplete="current-password" maxLength={50} value={password} onChange={e => setPassword(e.target.value)} />
        {message && <p role="alert">{message}</p>}
        <div className="login-forgot"><a href="/forgetPwd.aspx">忘记密码</a></div>
        <a href="#login" className="login-submit" aria-disabled={busy} onClick={e => { e.preventDefault(); void submit(); }}>{busy ? "登录中…" : "登录"}</a>
      </form>
      <p className="login-bookmark">按 <span>{/Mac/i.test(navigator.platform) ? "Command+D" : "Ctrl+D"}</span> 收藏本页，下次操作更方便</p>
    </section></div>
    <footer><span>客服热线：400-800-<u>5291</u><small>(我爱教育)</small> 或 400-101-6688</span><i /> <span>ISO27001:2022信息安全管理体系认证</span><i /><span>校管家提供技术支持</span><i /><a href="https://chromeliulanqi.com/" target="_blank" rel="noreferrer">下载谷歌浏览器</a></footer>
    <small className="login-photo-notice">*以上照片均获得使用许可</small>
  </main>;
}

export function AuthenticationGate({ children }: { children: React.ReactNode }) {
  const cache = useQueryClient();
  const navigate = useNavigate();
  const { data, isPending, error } = useQuery({ queryKey: ["auth-session"], retry: false, queryFn: async () => {
    const result = await client.session();
    if (result.status === 401) return null;
    if (result.status !== 200) throw new Error("登录状态暂时无法读取");
    return result.body;
  } });
  useEffect(() => {
    if (!isPending && !error && !data && window.location.pathname !== "/login.aspx") void navigate({ to: "/login.aspx", replace: true });
    if (data && window.location.pathname === "/login.aspx") void navigate({ to: "/", replace: true });
  }, [data, isPending, error, navigate]);
  if (isPending) return <div className="loading">加载中…</div>;
  if (error) return <div role="alert">{error.message}</div>;
  if (!data) return <LoginForm onLogin={() => { void cache.invalidateQueries({ queryKey: ["auth-session"] }); void navigate({ to: "/", replace: true }); }} />;
  return children;
}
