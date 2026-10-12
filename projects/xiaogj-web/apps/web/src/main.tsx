import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import {
  createRootRoute,
  createRoute,
  createRouter,
  Link,
  Outlet,
  RouterProvider,
  useNavigate,
} from "@tanstack/react-router";
import { initClient } from "@ts-rest/core";
import { api, type HomeSnapshot } from "@xiaogj/contracts";
import {
  ChevronDown,
  ChevronRight,
  GripVertical,
  X,
  Plus,
  Check,
  ArrowDown,
} from "lucide-react";
import { navigation } from "./navigation";
import { useHomeState, defaultCards } from "./home-state";
import "./style.css";
import { StudentsPage, StudentRailFooter } from "./students";
const client = initClient(api, { baseUrl: "" });
function useHome() {
  return useQuery({
    queryKey: ["home"],
    queryFn: async () => {
      const r = await client.home();
      if (r.status !== 200)
        throw new Error(r.status === 503 ? r.body.message : "首页数据读取失败");
      return r.body;
    },
  });
}
function Icon({ name, className = "" }: { name: string; className?: string }) {
  return (
    <svg className={`icon ${className}`} aria-hidden="true">
      <use href={`/home-symbols.svg#w2-${name}`} />
    </svg>
  );
}
function BusinessLink({
  label,
  children,
  className = "",
  asButton = false,
}: {
  label: string;
  children?: React.ReactNode;
  className?: string;
  asButton?: boolean;
}) {
  const navigate = useNavigate();
  if (asButton)
    return (
      <button
        className={className}
        onClick={() =>
          navigate({ to: "/workspace/$page", params: { page: label } })
        }
      >
        {children ?? label}
      </button>
    );
  return (
    <Link className={className} to="/workspace/$page" params={{ page: label }}>
      {children ?? label}
    </Link>
  );
}
function AppShell() {
  const { data } = useHome();
  const [menu, setMenu] = useState<number | null>(null);
  const header = useRef<HTMLElement>(null);
  useEffect(() => {
    const click = (e: MouseEvent) => {
      if (!header.current?.contains(e.target as Node)) setMenu(null);
    };
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenu(null);
    };
    document.addEventListener("click", click);
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("click", click);
      document.removeEventListener("keydown", key);
    };
  }, []);
  return (
    <>
      <header className="site-header" ref={header}>
        <Link to="/" className="logo" aria-label="校管家首页">
          <img src="/logo.png" alt="校管家" />
        </Link>
        <nav className="main-navigation" aria-label="主导航">
          <ul>
            {navigation.map((n, i) => (
              <li key={n.title}>
                <button
                  className={`nav-button ${menu === i ? "selected" : ""}`}
                  aria-expanded={menu === i}
                  onClick={() => setMenu(menu === i ? null : i)}
                >
                  <i aria-hidden="true">{n.glyph}</i>
                  <span>{n.title}</span>
                </button>
                {menu === i && (
                  <div className="navigation-menu">
                    {n.items.map((item) => (
                      <div key={item} onClick={() => setMenu(null)}>
                        <BusinessLink label={item} />
                      </div>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </nav>
        <div className="header-tools">
          <button className="campus">
            {data?.profile.campus}
            <ChevronDown size={16} />
          </button>
          <button className="support" aria-label="客服">
            <img src="/support.png" alt="" />
          </button>
          <button className="account" aria-label="个人账户">
            <img className="avatar" src="/avatar.png" alt="" />
            <img className="enterprise" src="/enterprise.png" alt="企业版" />
          </button>
        </div>
      </header>
      <Outlet />
    </>
  );
}
const cardMeta: Record<
  string,
  { title: string; icon: string; color: string; subtitle?: string }
> = {
  todo: {
    title: "今日待办",
    icon: "jieridaiban",
    color: "#ff8935",
    subtitle: "优先处理重要事项",
  },
  quick: { title: "快捷操作", icon: "kuaijiecaozuo", color: "#7a5cff" },
  overview: { title: "数据概览", icon: "shujugailan", color: "#2465ff" },
  releases: { title: "升级足迹", icon: "shengjizuji", color: "#2465ff" },
  students: { title: "学员动态", icon: "xueyuandongtai", color: "#12cac1" },
  people: { title: "人数概况", icon: "renshugaikuang", color: "#ff872c" },
  classes: {
    title: "满班率",
    icon: "manbanshuai",
    color: "#7a5cff",
    subtitle: "截至当前",
  },
  notices: { title: "公告", icon: "gonggao", color: "#ff872c" },
  recent: { title: "最近30天开班", icon: "banjiguanli", color: "#2465ff" },
  guide: { title: "新手指南", icon: "kuaijiecaozuo", color: "#7a5cff" },
};
function Tabs({
  labels,
  value,
  onChange,
}: {
  labels: string[];
  value: number;
  onChange: (i: number) => void;
}) {
  return (
    <div className="tabs">
      {labels.map((s, i) => (
        <button
          key={s}
          className={i === value ? "active" : ""}
          aria-pressed={i === value}
          onClick={() => onChange(i)}
        >
          {s}
        </button>
      ))}
    </div>
  );
}
function Modal({
  title,
  children,
  footer,
  onClose,
  wide = false,
}: {
  wide?: boolean;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      aria-label={title}
      ref={ref}
      className={`modal ${wide ? "modal-wide" : ""}`}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <header>
        <h2>{title}</h2>
        <button aria-label="关闭" onClick={onClose}>
          <X size={20} />
        </button>
      </header>
      <div className="modal-body">{children}</div>
      {footer && <footer>{footer}</footer>}
    </dialog>
  );
}
function Home() {
  const home = useHome();
  const state = useHomeState();
  const layout = state.draft ?? state.layout;
  const [expanded, setExpanded] = useState(false);
  const [period, setPeriod] = useState(0);
  const [studentPeriod, setStudentPeriod] = useState(0);
  const [chart, setChart] = useState(0);
  const [background, setBackground] = useState("lotus");
  const [backgroundMenu, setBackgroundMenu] = useState(false);
  const [modal, setModal] = useState<string | null>(null);
  const [todoDraft, setTodoDraft] = useState<number[]>([]);
  const [todoOrder, setTodoOrder] = useState<number[]>([]);
  const dragging = useRef<string | null>(null);
  const draggedTodo = useRef<number | null>(null);
  if (home.isPending)
    return (
      <main className="loading" role="status">
        加载中…
      </main>
    );
  if (home.isError)
    return (
      <main className="loading" role="alert">
        {home.error.message}
        <button onClick={() => home.refetch()}>重试</button>
      </main>
    );
  const data = home.data;
  const configure = (id: string) => {
    if (id === "todo" || id === "overview") {
      const selected = id === "todo" ? layout.todos : layout.metrics;
      const entries = id === "todo" ? data.todos : data.metrics;
      setTodoDraft([...selected]);
      setTodoOrder([
        ...selected,
        ...entries.map((_, i) => i).filter((i) => !selected.includes(i)),
      ]);
    }
    setModal(id);
  };
  const renderCard = (id: string) => {
    const meta = cardMeta[id];
    if (!meta) return null;
    const extra =
      id === "overview" ? (
        <Tabs
          labels={["今日", "本周", "本月"]}
          value={period}
          onChange={setPeriod}
        />
      ) : id === "students" ? (
        <Tabs
          labels={["今日", "本周", "本月"]}
          value={studentPeriod}
          onChange={setStudentPeriod}
        />
      ) : id === "releases" ? (
        <BusinessLink label="升级足迹" className="text-link">
          查看全部
          <ChevronRight size={16} />
        </BusinessLink>
      ) : id === "classes" ? (
        <BusinessLink label="班级报表" className="text-link">
          查看报表
          <ChevronRight size={16} />
        </BusinessLink>
      ) : null;
    return (
      <article
        className={`panel panel-${id}`}
        data-panel-title={meta.title}
        key={id}
        draggable={!!state.draft}
        onDragStart={(e) => {
          dragging.current = id;
          e.dataTransfer.effectAllowed = "move";
        }}
        onDragOver={(e) => {
          if (dragging.current) e.preventDefault();
        }}
        onDrop={(e) => {
          e.preventDefault();
          if (dragging.current) state.move(dragging.current, id);
          dragging.current = null;
        }}
      >
        {state.draft && (
          <div className="card-editor">
            <span>
              <GripVertical size={14} />
              拖动排序
            </span>
            <div>
              {["todo", "quick", "overview"].includes(id) && (
                <button onClick={() => configure(id)}>配置</button>
              )}
              <button onClick={() => state.hide(id)}>隐藏</button>
            </div>
          </div>
        )}
        <header>
          <div className="heading">
            <span
              className="panel-icon"
              style={{ color: meta.color, backgroundColor: `${meta.color}29` }}
            >
              <Icon name={meta.icon} />
            </span>
            <b>{meta.title}</b>
            {meta.subtitle && <small>{meta.subtitle}</small>}
          </div>
          {extra}
        </header>
        <div className="panel-body">
          {id === "todo" && (
            <>
              <div className={`todos ${expanded ? "" : "collapsed"}`}>
                {layout.todos.map((i) => {
                  const todo = data.todos[i];
                  if (!todo) return null;
                  return (
                    <BusinessLink
                      asButton
                      key={i}
                      label={todo.label}
                      className="todo"
                    >
                      <Icon name={todo.icon} />
                      <span>
                        <small>{todo.label}</small>
                        <b>{todo.value}</b>
                      </span>
                      <ChevronRight className="todo-arrow" size={16} />
                    </BusinessLink>
                  );
                })}
              </div>
              {layout.todos.length > 3 && (
                <button
                  className="expand-todos"
                  aria-expanded={expanded}
                  onClick={() => setExpanded(!expanded)}
                >
                  {expanded ? "收起待办" : "展开更多待办"}
                  <ChevronDown
                    className={expanded ? "rotated" : ""}
                    size={16}
                  />
                </button>
              )}
            </>
          )}
          {id === "quick" && (
            <div className="quick-actions">
              {layout.quick
                .map(
                  (label) => data.quickCatalog.find((q) => q.label === label)!,
                )
                .map((q) => (
                  <BusinessLink
                    asButton
                    key={q.label}
                    label={q.label}
                    className="quick-action"
                  >
                    <span
                      className="quick-icon"
                      style={{ background: q.color }}
                    >
                      <Icon name={q.icon} />
                    </span>
                    <span>{q.label}</span>
                  </BusinessLink>
                ))}
            </div>
          )}
          {id === "overview" && (
            <>
              <div
                className="metrics"
                style={{
                  gridTemplateColumns: `repeat(${layout.metrics.length},minmax(0,1fr))`,
                }}
              >
                {layout.metrics
                  .map((i) => ({
                    ...data.metrics[i]!,
                    comparisonData: data.metricPeriods[period]![i]!,
                  }))
                  .map((m) => (
                    <BusinessLink label={m.label} key={m.label}>
                      <small>{m.label}</small>
                      <b>{m.value}</b>
                      <em className={m.comparisonData.tone}>
                        <span>{m.comparisonData.comparison}</span>
                        {m.comparisonData.direction && <ArrowDown size={14} />}
                        <span>{m.comparisonData.change}</span>
                      </em>
                    </BusinessLink>
                  ))}
              </div>
              <div className="trend-heading">
                <b>近7日数据</b>
                <Tabs
                  labels={["实收趋势", "排课点名", "出勤率"]}
                  value={chart}
                  onChange={setChart}
                />
              </div>
              <TrendChart mode={chart} data={data.trend} />
            </>
          )}
          {id === "releases" && (
            <ul className="releases">
              {data.releases.map((r) => (
                <li key={r.title}>
                  <BusinessLink label={r.title}>
                    <span className="release-title" title={r.title}>
                      {r.title}
                    </span>
                    {r.isNew && <Icon name="new1" className="release-new" />}
                  </BusinessLink>
                  <small>{r.date}</small>
                </li>
              ))}
            </ul>
          )}
          {id === "students" &&
            data.studentGroups.map((g, i) => (
              <div
                className={`student-group ${i === 0 ? "intention" : "formal"}`}
                key={g.label}
              >
                <b>
                  <Icon name={i === 0 ? "user-heart-fill" : "user-3-fill"} />
                  {g.label}
                </b>
                <div>
                  {g.counts.map((c, j) => (
                    <BusinessLink
                      asButton
                      key={c.label}
                      label={`${g.label}${c.label}`}
                    >
                      <strong>
                        {data.studentPeriods[studentPeriod]?.[i * 3 + j]}
                      </strong>
                      <small>{c.label}</small>
                    </BusinessLink>
                  ))}
                </div>
              </div>
            ))}
          {(id === "people" || id === "classes") && (
            <Donut
              data={data.donuts[id === "people" ? 0 : 1]!}
              classRate={id === "classes"}
            />
          )}
          {id === "notices" && (
            <ul className="notices">
              {data.notices.map((n, i) => (
                <li key={i}>
                  <em className={n.category === "外部" ? "outer" : ""}>
                    {n.category}
                  </em>
                  <BusinessLink label={n.title}>
                    <span title={n.title}>{n.title}</span>
                  </BusinessLink>
                  <small>{n.date}</small>
                </li>
              ))}
            </ul>
          )}
          {["recent", "guide"].includes(id) && (
            <p>尚待完成此卡片的内容与交互复刻。</p>
          )}
        </div>
      </article>
    );
  };
  const left = layout.cards.filter((id) =>
    ["todo", "quick", "overview", "recent", "guide"].includes(id),
  );
  const right = layout.cards.filter(
    (id) => !["todo", "quick", "overview", "recent", "guide"].includes(id),
  );
  return (
    <main className={`home-page theme-${background}`}>
      <header className="hero">
        <div>
          <b>{data.profile.greeting}</b>
          <small>{data.profile.date}</small>
        </div>
        <div className="hero-actions">
          <div className="background-control">
            <button
              className="standard-button"
              aria-expanded={backgroundMenu}
              onClick={() => setBackgroundMenu(!backgroundMenu)}
            >
              <Icon name="a-Plattetiaosepan" />
              换背景
            </button>
            {backgroundMenu && (
              <div className="background-menu">
                <b>更换首页背景</b>
                <small>点击后立即生效</small>
                <div>
                  {[
                    ["classic", "经典浅灰", "简洁耐看"],
                    ["sky", "晴空蓝", "清爽明亮"],
                    ["apricot", "暖杏橙", "温暖柔和"],
                    ["forest", "森氧绿", "清新自然"],
                    ["lotus", "荷塘清韵", "国风山水"],
                    ["mountain", "远山晨雾", "宁静雅致"],
                  ].map(([id, title, subtitle]) => (
                    <button
                      key={id}
                      className={`background-option theme-${id}`}
                      onClick={() => {
                        setBackground(id!);
                        setBackgroundMenu(false);
                      }}
                    >
                      <b>{title}</b>
                      <small>{subtitle}</small>
                      {background === id && <Check size={16} />}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
          <button className="standard-button" onClick={state.begin}>
            <Icon name="a-Setting-oneshezhi" />
            自定义首页
          </button>
        </div>
      </header>
      <div className="home-layout">
        <section className="left-column">{left.map(renderCard)}</section>
        <aside className="right-column">{right.map(renderCard)}</aside>
      </div>
      {state.draft && (
        <div className="edit-footer">
          <span>{10 - layout.cards.length} 个卡片可添加</span>
          <button className="standard-button" onClick={() => setModal("add")}>
            <Plus size={16} />
            添加卡片
          </button>
          <button className="standard-button" onClick={state.reset}>
            恢复默认
          </button>
          <div className="spacer" />
          <button className="standard-button" onClick={state.cancel}>
            取消
          </button>
          <button className="primary-button" onClick={state.save}>
            保存
          </button>
        </div>
      )}
      {(modal === "todo" || modal === "overview") && (
        <Modal
          title={modal === "todo" ? "配置今日待办" : "配置数据概览"}
          onClose={() => setModal(null)}
          footer={
            <>
              <span>已选择 {todoDraft.length} 项</span>
              <div className="spacer" />
              <button
                className="standard-button"
                onClick={() => setModal(null)}
              >
                取消
              </button>
              <button
                className="primary-button"
                onClick={() => {
                  (modal === "todo" ? state.setTodos : state.setMetrics)(
                    todoOrder.filter((i) => todoDraft.includes(i)),
                  );
                  setModal(null);
                }}
              >
                确定
              </button>
            </>
          }
        >
          <p>
            {modal === "todo"
              ? "至少选择 1 个待办项，拖动左侧手柄调整排序，勾选后显示在首页。"
              : "至少保留 1 个指标，拖动左侧手柄调整排序；无权限指标不可选择。"}
          </p>
          <div className="todo-options">
            {todoOrder.map((i) => (
              <label
                key={i}
                draggable
                onDragStart={(e) => {
                  e.stopPropagation();
                  draggedTodo.current = i;
                }}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (draggedTodo.current === null) return;
                  const list = todoOrder.filter(
                    (x) => x !== draggedTodo.current,
                  );
                  list.splice(
                    Math.max(0, list.indexOf(i)),
                    0,
                    draggedTodo.current,
                  );
                  setTodoOrder(list);
                  draggedTodo.current = null;
                }}
              >
                <GripVertical size={16} />
                <input
                  type="checkbox"
                  checked={todoDraft.includes(i)}
                  disabled={todoDraft.length === 1 && todoDraft.includes(i)}
                  onChange={(e) =>
                    setTodoDraft(
                      e.target.checked
                        ? [...todoDraft, i]
                        : todoDraft.filter((x) => x !== i),
                    )
                  }
                />
                {(modal === "todo" ? data.todos : data.metrics)[i]?.label}
              </label>
            ))}
          </div>
        </Modal>
      )}
      {modal === "quick" && (
        <QuickPicker
          data={data}
          selected={layout.quick}
          onClose={() => setModal(null)}
          onSave={(quick) => {
            state.setQuick(quick);
            setModal(null);
          }}
        />
      )}
      {modal === "add" && (
        <Modal
          title="添加卡片"
          onClose={() => setModal(null)}
          footer={
            <>
              <small>卡片尺寸及所在区域由系统自动安排</small>
              <div className="spacer" />
              <button
                className="standard-button"
                onClick={() => setModal(null)}
              >
                关闭
              </button>
            </>
          }
        >
          <p>仅展示当前未添加且有权限使用的系统卡片</p>
          {[...defaultCards, "recent", "guide"]
            .filter((id) => !layout.cards.includes(id))
            .map((id) => (
              <div className="add-card" key={id}>
                <div>
                  <b>{cardMeta[id]?.title}</b>
                  <small>
                    {id === "recent"
                      ? "展示最近30天新开班级"
                      : id === "guide"
                        ? "展示初始化设置和核心业务流程"
                        : ""}
                  </small>
                </div>
                <button
                  className="standard-button"
                  onClick={() => state.add(id)}
                >
                  添加
                </button>
              </div>
            ))}
        </Modal>
      )}
    </main>
  );
}
function QuickPicker({
  data,
  selected,
  onClose,
  onSave,
}: {
  data: HomeSnapshot;
  selected: string[];
  onClose: () => void;
  onSave: (selection: string[]) => void;
}) {
  const [selection, setSelection] = useState([...selected]);
  const [search, setSearch] = useState("");
  const tile = (label: string, removable: boolean) => {
    const item = data.quickCatalog.find((q) => q.label === label);
    if (!item) return null;
    const content = (
      <>
        <span className="quick-icon" style={{ background: item.color }}>
          {item.icon === "tianjia" ? label[0] : <Icon name={item.icon} />}
        </span>
        <span>{label}</span>
      </>
    );
    return (
      <div
        className={`shortcut-option ${removable ? "selected-shortcut" : ""}`}
        key={label}
      >
        {removable ? (
          <div className="shortcut-display">{content}</div>
        ) : (
          <button
            disabled={selection.includes(label)}
            onClick={() => setSelection([...selection, label])}
          >
            {content}
          </button>
        )}
        {removable ? (
          <button
            className="remove-shortcut"
            aria-label={`移除${label}`}
            onClick={() => setSelection(selection.filter((x) => x !== label))}
          >
            −
          </button>
        ) : (
          <span className="add-shortcut" aria-hidden="true">
            +
          </span>
        )}
      </div>
    );
  };
  return (
    <Modal
      wide
      title="配置快捷操作"
      onClose={onClose}
      footer={
        <>
          <small>菜单范围与当前登录人顶部菜单一致</small>
          <div className="spacer" />
          <button className="standard-button" onClick={onClose}>
            取消
          </button>
          <button className="primary-button" onClick={() => onSave(selection)}>
            确定
          </button>
        </>
      }
    >
      <p>配置首页常用功能，首页每行最多展示 7 项。</p>
      <h4>
        已选功能 <small>按选择顺序展示</small>
      </h4>
      <div className="shortcut-grid selected-shortcuts">
        {selection.map((s) => tile(s, true))}
      </div>
      <div className="shortcut-search">
        <h4>全部功能</h4>
        <input
          aria-label="搜索功能名称"
          placeholder="搜索功能名称"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      {navigation.map((group) => {
        const items = group.items.filter((label) => label.includes(search));
        return items.length ? (
          <section key={group.title}>
            <h4>{group.title}</h4>
            <div className="shortcut-grid">
              {items.map((label) => tile(label, false))}
            </div>
          </section>
        ) : null;
      })}
    </Modal>
  );
}
function TrendChart({
  mode,
  data,
}: {
  mode: number;
  data: HomeSnapshot["trend"];
}) {
  const [hover, setHover] = useState<number | null>(null);
  const names = [
    ["实收", "实退"],
    ["应点名排课", "已点名排课"],
    ["应出勤学员", "实际出勤学员"],
  ][mode]!;
  const numbers = data.summaries[mode]!;
  const values = [data.income, data.schedule, data.attendance][mode]!;
  const dates = data.dates;
  return (
    <section className="chart-panel">
      <div className="chart-heading">
        <div>
          <b>
            <span>{numbers[0]}</span> / <em>{numbers[1]}</em>
          </b>
          <small>
            {["近7日实收/实退", "近7日排课/点名", "近7日应出勤/实际出勤"][mode]}
          </small>
        </div>
        <div className="chart-legend">
          {names.map((s, i) => (
            <span key={s}>
              <i className={`series-${i}`} />
              {s}
            </span>
          ))}
        </div>
      </div>
      <div className="trend-chart" onMouseLeave={() => setHover(null)}>
        <svg
          viewBox="0 0 886 260"
          role="img"
          aria-label={`${names.join("/")}近7日趋势`}
        >
          {Array.from({ length: mode === 1 ? 5 : 6 }, (_, i) => (
            <g key={i}>
              <text
                x="36"
                y={17 + i * (mode === 1 ? 52.5 : 42)}
                textAnchor="end"
              >
                {mode === 2
                  ? `${100 - i * 20}%`
                  : mode === 1
                    ? `${2 - i * 0.5}`
                    : (1 - i * 0.2).toFixed(1).replace(".0", "")}
              </text>
              <line
                x1="48"
                x2="838"
                y1={12 + i * (mode === 1 ? 52.5 : 42)}
                y2={12 + i * (mode === 1 ? 52.5 : 42)}
              />
            </g>
          ))}
          {dates.map((d, i) => (
            <text
              key={d}
              x={mode === 1 ? 48 + ((i + 0.5) * 790) / 7 : 48 + (i * 790) / 6}
              y="250"
              textAnchor="middle"
            >
              {d}
            </text>
          ))}
          {mode === 1 &&
            data.schedule.map((series, i) =>
              series.map((value, n) => (
                <rect
                  key={`${i}-${n}`}
                  x={48 + ((n + 0.5) * 790) / 7 - 20 + i * 22}
                  y={222 - value * 105}
                  width="18"
                  height={value * 105}
                  className={`series-${i}`}
                />
              )),
            )}
          {mode !== 1 && (
            <>
              {[0, 1].map((i) => (
                <g key={i}>
                  <path
                    className={`chart-area series-${i}`}
                    d={
                      mode === 0
                        ? "M48 222H838V222Z"
                        : "M48 222H706.3C772 222 772 12 838 12V222Z"
                    }
                  />
                  <path
                    className={`chart-line series-${i}`}
                    d={
                      mode === 0
                        ? "M48 222H838"
                        : "M48 222H706.3C772 222 772 12 838 12"
                    }
                  />
                  {dates.map((_, n) => (
                    <circle
                      key={n}
                      cx={48 + (n * 790) / 6}
                      cy={mode === 2 && n === 6 ? 12 : 222}
                      r="3"
                      className={`chart-point series-${i}`}
                    />
                  ))}
                </g>
              ))}
            </>
          )}
          {dates.map((d, i) => (
            <rect
              key={d}
              x={(i * 886) / 7}
              y="0"
              width={886 / 7}
              height="260"
              fill="transparent"
              onMouseEnter={() => setHover(i)}
            />
          ))}
        </svg>
        {hover !== null && (
          <div
            className="chart-tooltip"
            style={{ left: `${Math.min(72, hover * 12)}%` }}
          >
            <b>{dates[hover]}</b>
            {names.map((n, i) => (
              <div key={n}>
                <i className={`series-${i}`} />
                {n}：{values[i]?.[hover]}
                {mode === 2 ? " 人次" : ""}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
function Donut({
  data,
  classRate,
}: {
  data: HomeSnapshot["donuts"][number];
  classRate: boolean;
}) {
  let offset = 0;
  return (
    <div className="donut-card">
      <div>
        <small>{data.label}</small>
        <b>{data.total}</b>
        <div className="donut-legend">
          {data.items.map((i) => (
            <BusinessLink label={i.label} key={i.label}>
              <i style={{ background: i.color }} />
              <em>{i.label}</em>
              <strong>{i.value}</strong>
            </BusinessLink>
          ))}
        </div>
      </div>
      <svg
        viewBox="0 0 148 148"
        className="donut-chart"
        role="img"
        aria-label={`${data.label}${data.total}`}
      >
        {data.items.map((i) => {
          const portion = (i.value / data.total) * 100;
          const start = offset;
          offset += portion;
          return (
            <circle
              key={i.label}
              cx="74"
              cy="74"
              r="53.3"
              fill="none"
              stroke={i.color}
              strokeWidth="15"
              pathLength="100"
              strokeDasharray={`${portion} ${100 - portion}`}
              strokeDashoffset={-start}
              transform="rotate(-90 74 74)"
            />
          );
        })}
        {classRate && (
          <>
            <text
              x="74"
              y="73"
              textAnchor="middle"
              className="donut-percentage"
            >
              {((data.items[0]!.value / data.total) * 100).toFixed(1)}%
            </text>
            <text x="74" y="94" textAnchor="middle" className="donut-caption">
              {data.items[0]!.label}
            </text>
          </>
        )}
      </svg>
    </div>
  );
}
function BusinessPage() {
  const [collapsed, setCollapsed] = useState(false);
  const { page } = businessRoute.useParams();
  const section = navigation.find((n) => n.items.includes(page));
  return (
    <main
      className={`business-shell ${page === "学员信息管理" ? "student-business" : ""} ${collapsed ? "rail-collapsed" : ""}`}
    >
      <aside>
        {page !== "学员信息管理" && <b>{section?.title}</b>}
        {section?.items.map((n) => (
          <BusinessLink
            label={n}
            key={n}
            className={n === page ? "active" : ""}
          />
        ))}
        {page === "学员信息管理" && (
          <StudentRailFooter onCollapse={() => setCollapsed((c) => !c)} />
        )}
      </aside>
      <section>
        {page === "学员信息管理" ? (
          <StudentsPage />
        ) : (
          <>
            <p>
              当前位置：{section?.title} &gt; {page}
            </p>
            <h1>{page}</h1>
            <p role="status">此业务页面尚未完成复刻。</p>
          </>
        )}
      </section>
    </main>
  );
}
const rootRoute = createRootRoute({ component: AppShell });
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: Home,
});
const businessRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/workspace/$page",
  component: BusinessPage,
});
const router = createRouter({
  routeTree: rootRoute.addChildren([indexRoute, businessRoute]),
});
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={new QueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
);
