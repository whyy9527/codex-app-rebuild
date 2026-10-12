import type { ReactNode } from "react";
import type { StudentDetailSnapshot } from "@xiaogj/contracts";
import { ChevronLeft, ChevronRight, CircleHelp } from "lucide-react";
import "./student-business-tabs.css";

type Tabs = NonNullable<StudentDetailSnapshot["businessTabs"]>;
type Table = Tabs["tuition"]["table"];
function Action({ children, onClick }: { children: ReactNode; onClick: () => void }) {
  return <a role="link" tabIndex={0} onClick={onClick} onKeyDown={(e) => { if (e.key === "Enter") onClick(); }}>{children}</a>;
}
function Pager({ table, unavailable }: { table: Table; unavailable: () => void }) {
  const p = table.pagination;
  if (!p) return null;
  return <div className="student-tab-pager"><span>共 {p.total} 条 每页</span><span className="student-tab-size" onClick={unavailable}>{p.pageSize}</span><span>条 第 {p.page} / {p.pages} 页</span><button disabled={p.page === 1} onClick={unavailable} aria-label="上一页"><ChevronLeft size={16} /></button><input aria-label="按回车键跳转。" placeholder="跳转页" onKeyDown={(e) => { if (e.key === "Enter") unavailable(); }} /><button disabled={p.page === p.pages} onClick={unavailable} aria-label="下一页"><ChevronRight size={16} /></button></div>;
}
function DataTable({ table, type, unavailable }: { table: Table; type: string; unavailable: () => void }) {
  const columns = type === "consumption" ? 16 : table.headers[0]?.length ?? 1;
  return <><div className={`student-tab-table-scroll ${type}`}><table><thead>{table.headers.map((headers, row) => <tr key={row}>{headers.map((name, i) => <th key={i} rowSpan={type === "consumption" && row === 0 && i !== 11 ? 2 : undefined} colSpan={type === "consumption" && row === 0 && i === 11 ? 3 : undefined}>{name}{type === "tuition" && [3,5].includes(i) && <CircleHelp size={12} aria-hidden="true" />}</th>)}</tr>)}</thead><tbody>{table.rows.length ? table.rows.map((row, i) => <tr key={i}>{row.map((value, j) => <td key={j} className={type === "points" && j === 0 ? "points-value" : type === "tuition" && j === 3 ? "quantity-value" : ""}>{type === "tuition" && j === 6 ? <Action onClick={unavailable}>{value}</Action> : value}</td>)}</tr>) : <tr><td className="student-tab-empty" colSpan={columns}>{table.emptyText}</td></tr>}</tbody></table></div><Pager table={table} unavailable={unavailable} /></>;
}
function Check({ label, checked, unavailable }: { label: string; checked: boolean; unavailable: () => void }) {
  return <span className="student-tab-check"><input type="checkbox" aria-label={label} checked={checked} onChange={unavailable} /><span>{label}</span></span>;
}
export function StudentBusinessTab({ tab, data, unavailable }: { tab: string; data: Tabs; unavailable: () => void }) {
  if (tab === "学费") {
    const d = data.tuition;
    return <div className="student-tab-content"><div className="student-tab-query"><span>显示明细：</span><button className="student-tab-switch" role="switch" aria-label="显示明细" aria-checked={d.showDetails} onClick={unavailable} /><Check label="显示剩余数量为0的课程" checked={d.includeZero} unavailable={unavailable} /></div><DataTable table={d.table} type="tuition" unavailable={unavailable} /></div>;
  }
  if (tab === "课消明细") {
    const d = data.consumption;
    return <div className="student-tab-content"><div className="student-tab-query"><span>上课时间</span><select aria-label={d.preset} value={d.preset} onChange={unavailable}><option>{d.preset}</option></select><input value={d.startDate} placeholder="请选择" onChange={unavailable} /><span>到</span><input value={d.endDate} placeholder="请选择" onChange={unavailable} /><span>课消类型</span><select aria-label={d.type} value={d.type} onChange={unavailable}><option>{d.type}</option></select><span>课程：</span><input aria-label="选择课程" value={d.course} onChange={unavailable} /><Action onClick={unavailable}>选择</Action><Action onClick={unavailable}>查询</Action></div><DataTable table={d.table} type="consumption" unavailable={unavailable} /></div>;
  }
  const d = data.points;
  return <div className="student-tab-content"><div className="student-tab-query"><span className="student-tab-rule">{"积分规则 " + d.rule}</span><Action onClick={unavailable}>选择</Action><span>时间</span><select aria-label={d.timePreset} value={d.timePreset} onChange={unavailable}><option>{d.timePreset}</option></select><input aria-label="开始日期" value={d.startDate} onChange={unavailable} /><span>-</span><input aria-label="结束日期" value={d.endDate} onChange={unavailable} /><Action onClick={unavailable}>查询</Action><Check label="加分" checked={d.add} unavailable={unavailable} /><Check label="减分" checked={d.subtract} unavailable={unavailable} /><Check label="积分手动清零" checked={d.cleared} unavailable={unavailable} /></div><div className="student-tab-point-actions">{["+ 加分","- 减分","积分清零"].map(name => <Action key={name} onClick={unavailable}>{name}</Action>)}</div><DataTable table={d.table} type="points" unavailable={unavailable} /></div>;
}
