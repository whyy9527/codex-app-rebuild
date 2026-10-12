import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { initClient } from "@ts-rest/core";
import { api } from "@xiaogj/contracts";
import "./enrollment-chooser.css";

const client = initClient(api, { baseUrl: "" });
export function EnrollmentChooser({ kind, onClose, onUnsupported }: {
  kind: "courses" | "items"; onClose: () => void; onUnsupported: () => void;
}) {
  const { data, error } = useQuery({ queryKey: ["enrollment-choices", kind], queryFn: async () => {
    const result = await client.enrollmentChoices({ params: { kind } });
    if (result.status !== 200) throw new Error(result.status === 503 ? result.body.message : "目录读取失败");
    return result.body;
  } });
  useEffect(() => {
    const key = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    document.addEventListener("keydown", key);
    return () => document.removeEventListener("keydown", key);
  }, [onClose]);
  return <div className="enrollment-chooser-backdrop"><section className="enrollment-chooser" role="dialog" aria-modal="true" aria-label={kind === "courses" ? "选择课程" : "选择物品"}>
    <header><h2>{kind === "courses" ? "选择课程" : "选择物品"}</h2><button aria-label="关闭选择层" onClick={onClose}>×</button></header>
    {error ? <p role="alert">{error.message}</p> : !data ? <p role="status">加载中…</p> : <div className="enrollment-chooser-body">
      <div className="enrollment-chooser-catalog">
        <div className="enrollment-chooser-search"><input autoFocus placeholder={kind === "courses" ? "请输入课程名称" : "物品名称/编码"} aria-label={kind === "courses" ? "请输入课程名称" : "物品名称/编码"} /><button className="primary" onClick={onUnsupported}>查询 <span>⌄</span></button><button onClick={onUnsupported}>重置</button>{kind === "items" && <label><input type="checkbox" checked={false} onChange={onUnsupported} />仅显示在当前校区登记过的物品</label>}</div>
        <table><thead><tr><th><input type="checkbox" checked={false} onChange={onUnsupported} /></th>{data.headers.map((header, index) => <th key={index}>{header}</th>)}</tr></thead><tbody>{data.rows.map((row, index) => <tr key={index}><td><input type="checkbox" checked={false} onChange={onUnsupported} /></td>{row.map((cell, column) => <td key={column}>{cell}</td>)}</tr>)}</tbody></table>
        <div className="enrollment-chooser-pagination">共 {data.total} 条　每页 <select aria-label="每页条数" value={data.pageSize} onChange={onUnsupported}><option>{data.pageSize}</option></select> 条　第 {data.page} / {data.totalPages} 页 <button disabled>‹</button><input placeholder="跳转页" aria-label="跳转页" onKeyDown={event => { if (event.key === "Enter") onUnsupported(); }} /><button onClick={onUnsupported}>›</button></div>
      </div>
      <aside><div>已选择： 0 <button onClick={onUnsupported}>清空</button></div></aside>
    </div>}
    <footer><button onClick={onClose}>取消</button><button className="primary" onClick={onUnsupported}>确定</button></footer>
  </section></div>;
}
