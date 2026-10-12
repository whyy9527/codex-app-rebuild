import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { initClient } from "@ts-rest/core";
import { api } from "@xiaogj/contracts";
import { create } from "zustand";
import { ChevronDown, ChevronLeft, ChevronUp, Phone, Settings } from "lucide-react";
import "./student-detail.css";

const client = initClient(api, { baseUrl: "" });
const useDetailState = create<{
  expanded: Record<string, boolean>;
  setExpanded: (id: string, value: boolean) => void;
}>((set) => ({ expanded: {}, setExpanded: (id, value) => set((s) => ({ expanded: { ...s.expanded, [id]: value } })) }));

export function StudentDetailPage({ id, onReturn }: { id: string; onReturn: () => void }) {
  const expanded = useDetailState((s) => s.expanded[id] ?? false);
  const setExpanded = useDetailState((s) => s.setExpanded);
  const [tab, setTab] = useState(0);
  const [classFilter, setClassFilter] = useState(0);
  const [message, setMessage] = useState("");
  const { data, error, isPending } = useQuery({
    queryKey: ["student-detail", id], retry: false,
    queryFn: async () => {
      const result = await client.studentDetail({ params: { id } });
      if (result.status !== 200) throw new Error(result.status === 503 ? result.body.message : "学员详情暂时无法读取");
      return result.body;
    },
  });
  const unavailable = () => setMessage("暂时无法完成此操作");
  return <div className="students-page student-detail-page">
    <div className="students-breadcrumb">当前位置： 前台业务 / 学员信息管理 / 学员信息管理</div>
    <div className="student-detail-back"><a role="link" tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter") onReturn(); }} onClick={onReturn}><ChevronLeft size={16} />返回</a></div>
    {isPending ? <div className="student-detail-loading" role="status">加载中…</div> : error ? <div className="student-detail-error" role="alert">{error.message}</div> : data && <>
      <div className="student-detail-card">
        <div className="student-detail-photo">{data.photoSrc && <img src={data.photoSrc} alt="" />}</div>
        <div className="student-detail-information">
          <div className="student-detail-heading">
            <h1>{data.name}</h1><span>{data.status}</span>{data.gender !== "unknown" && <span>{data.gender === "male" ? "男" : "女"}</span>}
            <div className="student-detail-actions">{["收费", "退费", "结转", "修改", "操作"].map((name, i) => <button key={name} className={i === 0 ? "primary" : ""} onClick={unavailable}>{name}{i === 4 && <ChevronDown size={12} />}</button>)}</div>
          </div>
          <div className="student-detail-tags"><span>标签：</span><button onClick={unavailable}>{data.tag}</button><a href="#student-label" onClick={(e) => { e.preventDefault(); unavailable(); }}>添加标签</a>
            <a role="link" tabIndex={0} className="student-detail-expand" onKeyDown={(e) => { if (e.key === "Enter") setExpanded(id, !expanded); }} onClick={() => setExpanded(id, !expanded)}>{expanded ? "收起" : "展开"}{expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</a>
          </div>
          <div className="student-detail-grid student-detail-summary">{data.summary.map((field) => <div key={field.label}><span>{field.label}</span><b className={field.emphasis ? "emphasis" : ""}>{field.value}</b>{field.label === "手机号码：" && <button aria-label="拨打电话" onClick={unavailable}><Phone size={14} /></button>}</div>)}</div>
          {expanded && <div className="student-detail-sections">{data.sections.map((section) => <section key={section.title}><h2>{section.title}</h2><div className="student-detail-grid">{section.fields.map((field) => <div key={field.label}><span>{field.label}</span><b>{field.value}</b></div>)}</div></section>)}</div>}
        </div>
      </div>
      <div className="student-detail-business">
        <div className="student-detail-tabs"><ul>{data.tabs.map((name, i) => <li className={tab === i ? "active" : ""} tabIndex={0} key={name} onClick={() => setTab(i)} onKeyDown={(e) => { if (e.key === "Enter") setTab(i); }}>{name}</li>)}</ul><button className="student-detail-settings" aria-label="设置详情页签" onClick={unavailable}><Settings size={16} /></button></div>
        {tab === 0 ? <div className="student-detail-classes">
          <div className="student-detail-class-filters">{["只显示当前就读班级", "显示所有班级", "排队班级"].map((name, i) => <div key={name}><input type="radio" aria-label={name} name="student-detail-class-filter" checked={classFilter === i} onChange={() => setClassFilter(i)} /><span onClick={() => setClassFilter(i)}>{name}</span></div>)}</div>
          {classFilter === 0 ? <div className="student-detail-table-scroll"><table><thead><tr>{data.classes.headers.map((name) => <th key={name}>{name}{["进/出班日期", "开班日期"].includes(name) && " \ue60a"}</th>)}</tr></thead><tbody>{data.classes.rows.length ? data.classes.rows.map((row, i) => <tr key={i}>{row.map((value, j) => <td key={j}>{value}</td>)}</tr>) : <tr><td colSpan={data.classes.headers.length} className="student-detail-empty">暂时还没有相关数据，试试别的查询条件吧。</td></tr>}</tbody></table></div> : <div className="student-detail-error" role="status">该信息暂时无法读取</div>}
        </div> : <div className="student-detail-error" role="status">该信息暂时无法读取</div>}
      </div>
    </>}
    {message && <div className="students-message" role="status">{message}</div>}
    <button className="students-help" onClick={unavailable}>帮助中心<br />«</button>
  </div>;
}
