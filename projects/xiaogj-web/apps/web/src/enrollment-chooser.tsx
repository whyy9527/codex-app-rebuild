import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { initClient } from "@ts-rest/core";
import { api } from "@xiaogj/contracts";
import "./enrollment-chooser.css";

const client = initClient(api, { baseUrl: "" });
export function EnrollmentChooser({ kind, onClose, onUnsupported }: {
  kind: "courses" | "items"; onClose: () => void; onUnsupported: () => void;
}) {
  const [selected, setSelected] = useState<Record<string, string[]>>({});
  const keyFor = (row: string[]) => JSON.stringify(row);
  const toggle = (row: string[]) => setSelected(current => {
    const next = { ...current }, key = keyFor(row);
    if (key in next) delete next[key]; else next[key] = row;
    return next;
  });
  const [draft, setDraft] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [jump, setJump] = useState("");
  const applySearch = () => { setSearch(draft); setPage(1); };
  const reset = () => { setDraft(""); setSearch(""); setPage(1); setJump(""); };
  const { data, error } = useQuery({ queryKey: ["enrollment-choices", kind, search, page, pageSize], queryFn: async () => {
    const result = await client.enrollmentChoices({ params: { kind }, query: { search, page, pageSize } });
    if (result.status !== 200) throw new Error(result.status === 503 ? result.body.message : "目录读取失败");
    return result.body;
  } });
  useEffect(() => {
    const key = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    document.addEventListener("keydown", key);
    return () => document.removeEventListener("keydown", key);
  }, [onClose]);
  return <div className="enrollment-chooser-backdrop"><section className={`enrollment-chooser enrollment-chooser-${kind}`} role="dialog" aria-modal="true" aria-label={kind === "courses" ? "选择课程" : "选择物品"}>
    <header><h2>{kind === "courses" ? "选择课程" : "选择物品"}</h2><button aria-label="关闭选择层" onClick={onClose}>×</button></header>
    {error ? <p role="alert">{error.message}</p> : !data ? <p role="status">加载中…</p> : <div className="enrollment-chooser-body">
      <div className="enrollment-chooser-catalog">
        <div className="enrollment-chooser-search"><input value={draft} onChange={event => setDraft(event.target.value)} onKeyDown={event => { if (event.key === "Enter") applySearch(); }} placeholder={kind === "courses" ? "请输入课程名称" : "物品名称/编码"} aria-label={kind === "courses" ? "请输入课程名称" : "物品名称/编码"} /><button className="primary" onClick={applySearch}>查询 <span>⌄</span></button><button onClick={reset}>重置</button>{kind === "items" && <label><input type="checkbox" checked={false} onChange={onUnsupported} />仅显示在当前校区登记过的物品</label>}</div>
        <table><colgroup>{(kind === "courses" ? [40, 200, 250, 100, 100] : [40, 240, 150, 100, 100, 60]).map((width, index) => <col key={index} style={{ width }} />)}</colgroup><thead><tr><th><input type="checkbox" checked={data.rows.length > 0 && data.rows.every(row => keyFor(row) in selected)} onChange={() => setSelected(current => {
          const next = { ...current }, all = data.rows.every(row => keyFor(row) in current);
          for (const row of data.rows) { if (all) delete next[keyFor(row)]; else next[keyFor(row)] = row; }
          return next;
        })} /></th>{data.headers.map((header, index) => <th key={index}>{header}{kind === "items" && <span className="chooser-sort" aria-hidden="true" />}</th>)}</tr></thead><tbody>{!data.rows.length && <tr className="chooser-empty"><td colSpan={data.headers.length + 1}>{kind === "courses" ? "未查找到相关数据" : "未找到相关记录。"}</td></tr>}{data.rows.map((row, index) => <tr key={keyFor(row)} className={keyFor(row) in selected ? "chooser-selected" : undefined}><td><input type="checkbox" checked={keyFor(row) in selected} onChange={() => toggle(row)} /></td>{row.map((cell, column) => <td key={column}>{cell}{column === 0 && data.presentation?.nameBadges[index] && <span className="chooser-name-badge" aria-hidden="true">{data.presentation.nameBadges[index]}</span>}</td>)}</tr>)}</tbody></table>
        <div className="enrollment-chooser-pagination">共{data.total}条　每页 <select aria-label="每页条数" value={data.pageSize} onChange={event => { setPageSize(Number(event.target.value)); setPage(1); }}>{[10, 15, 20, 30, 40, 50, 100, 150, 200].map(size => <option key={size} value={size}>{size}</option>)}</select> 条　第{data.page}/{data.totalPages}页 <button disabled={data.page <= 1} onClick={() => setPage(data.page - 1)}>‹</button><input placeholder="跳转页" aria-label="跳转页" value={jump} onChange={event => setJump(event.target.value)} onKeyDown={event => { if (event.key === "Enter" && /^\d+$/.test(jump) && Number(jump) >= 1 && Number(jump) <= data.totalPages) setPage(Number(jump)); }} /><button disabled={data.page >= data.totalPages} onClick={() => setPage(data.page + 1)}>›</button></div>
      </div>
      <aside><div>已选择： {Object.keys(selected).length} <button onClick={() => setSelected({})}>清空</button></div>{Object.entries(selected).map(([key, row]) => <article className="chooser-selection" key={key}><span>{row[0]}</span><button aria-label={`移除 ${row[0]}`} onClick={() => toggle(row)}>×</button></article>)}</aside>
    </div>}
    <footer><button onClick={onClose}>取消</button><button className="primary" onClick={onUnsupported}>确定</button></footer>
  </section></div>;
}
