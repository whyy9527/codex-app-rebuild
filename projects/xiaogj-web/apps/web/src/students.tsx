import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { initClient } from "@ts-rest/core";
import { api } from "@xiaogj/contracts";
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Phone,
  HelpCircle,
  Bookmark,
  Menu,
} from "lucide-react";
import "./students.css";

const client = initClient(api, { baseUrl: "" });
const columns = [
  "姓名",
  "师生信账号",
  "学号",
  "身份证号",
  "手机号码",
  "英文名",
  "卡号",
  "公立学校",
  "学员状态",
  "操作",
];

export function StudentsPage() {
  const [input, setInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [jump, setJump] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const { data, error, isPending } = useQuery({
    queryKey: ["students", page, search],
    retry: false,
    queryFn: async () => {
      const result = await client.students({ query: { page, search } });
      if (result.status !== 200)
        throw new Error(
          result.status === 503 ? result.body.message : "学员数据读取失败",
        );
      return result.body;
    },
  });
  const pending = () => setMessage("此操作尚未完成复刻。");
  const submitQuery = () => {
    setPage(1);
    setSearch(input);
    setSelected([]);
  };
  const toggle = (id: string) =>
    setSelected((s) =>
      s.includes(id) ? s.filter((n) => n !== id) : [...s, id],
    );
  return (
    <div className="students-page">
      <div className="students-breadcrumb">
        当前位置： 前台业务 / 学员信息管理 / 学员信息管理
      </div>
      <div className="students-tabs">
        <button className="selected">学员信息管理</button>
        <button onClick={pending}>学员沟通管理</button>
      </div>
      <div className="students-content">
        <form
          className="students-query"
          onSubmit={(e) => {
            e.preventDefault();
            submitQuery();
          }}
        >
          <input
            aria-label="学员姓名及首字母/学号/电话"
            placeholder="学员姓名及首字母/学号/电话"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <HelpCircle className="students-query-help" size={16} aria-hidden />
          <a href="#student-query" className="students-query-submit" onClick={(e) => {
            e.preventDefault();
            submitQuery();
          }}>
            查询 <ChevronDown size={12} />
          </a>
          <a
            href="#student-reset"
            className="students-reset"
            onClick={(e) => {
              e.preventDefault();
              setInput("");
              setMessage("");
            }}
          >
            重置
          </a>
          <button type="button" onClick={pending}>
            导出 <HelpCircle size={14} />
          </button>
          <label>
            <input type="checkbox" defaultChecked onChange={pending} />
            正式学员
          </label>
          <label>
            <input type="checkbox" onChange={pending} />
            非正式学员 <HelpCircle size={14} />
          </label>
          <label>
            <input type="checkbox" defaultChecked onChange={pending} />
            包含跨校区学员 <HelpCircle size={14} />
          </label>
          <button
            type="button"
            className="students-bookmark"
            aria-label="收藏查询"
            onClick={pending}
          >
            <Bookmark size={18} />
          </button>
        </form>
        <div className="students-actions">
          {[
            "到校签到",
            "离校签退",
            "按课程一键转班",
            "合并学员",
            "安排试听",
            "批量操作",
          ].map((label, i) => (
            <button
              key={label}
              className={i === 0 ? "primary" : ""}
              onClick={pending}
            >
              {label}
              {i > 3 && <ChevronDown size={12} />}
            </button>
          ))}
          <button className="students-fields" onClick={pending}>
            自定义显示字段
          </button>
        </div>
        {message && (
          <div className="students-message" role="status">
            {message}
          </div>
        )}
        {error ? (
          <div role="alert" className="students-message">
            {error.message}
          </div>
        ) : isPending ? (
          <div role="status">加载中…</div>
        ) : (
          data && (
            <>
              <div className="students-table-scroll">
                <table className="students-table">
                  <colgroup>
                    {[30, 105, 105, 90, 170, 120, 120, 120, 150, 100, 80].map(
                      (width, i) => (
                        <col key={i} style={{ width }} />
                      ),
                    )}
                  </colgroup>
                  <thead>
                    <tr>
                      <th>
                        <input
                          aria-label="全选学员"
                          type="checkbox"
                          checked={
                            data.rows.length > 0 &&
                            selected.length === data.rows.length
                          }
                          onChange={(e) =>
                            setSelected(
                              e.target.checked
                                ? data.rows.map((r) => r.id)
                                : [],
                            )
                          }
                        />
                      </th>
                      {columns.map((label, i) => (
                        <th key={label}>
                          {i < 9 ? `${label} \ue60a` : label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.rows.map((row) => (
                      <tr key={row.id}>
                        <td>
                          <input
                            aria-label={`选择${row.name}`}
                            type="checkbox"
                            checked={selected.includes(row.id)}
                            onChange={() => toggle(row.id)}
                          />
                        </td>
                        <td>
                          {row.gender !== "unknown" && <span
                            className={`student-gender ${row.gender}`}
                            aria-label={row.gender === "male" ? "男" : "女"}
                          >
                            {row.gender === "male" ? "♂" : "♀"}
                          </span>}
                          <button className="student-name" onClick={pending}>
                            {row.name}
                          </button>
                        </td>
                        <td title={row.account}>{row.account}</td>
                        <td>{row.number}</td>
                        <td title={row.identity}>{row.identity}</td>
                        <td>
                          <span className="student-phone" title={row.phone}>
                            {row.phone}
                          </span>
                          <button
                            className="student-call"
                            aria-label="拨打电话"
                            onClick={pending}
                          >
                            <Phone size={13} />
                          </button>
                        </td>
                        <td>{row.englishName}</td>
                        <td>{row.card}</td>
                        <td title={row.school}>{row.school}</td>
                        <td>{row.status}</td>
                        <td>
                          <button
                            className="student-operation"
                            onClick={pending}
                          >
                            操作
                            <ChevronDown size={11} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {data.rows.length === 0 && <div className="students-empty">暂时还没有相关数据，试试别的查询条件吧。</div>}
              </div>
              {data.rows.length > 0 && <div className="students-pagination">
                <span>共 {data.total} 条</span>
                <span>每页 {data.pageSize} 条</span>
                <span>
                  第 {data.page} / {data.pages} 页
                </span>
                <button
                  aria-label="上一页"
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft size={15} />
                </button>
                <input
                  aria-label="按回车键跳转。"
                  placeholder="跳转页"
                  value={jump}
                  onChange={(e) => setJump(e.target.value)}
                  onKeyDown={(e) => {
                    if (
                      e.key === "Enter" &&
                      /^\d+$/.test(jump) &&
                      Number(jump) > 0 &&
                      Number(jump) <= data.pages
                    )
                      setPage(Number(jump));
                  }}
                />
                <button
                  aria-label="下一页"
                  disabled={page >= data.pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  <ChevronRight size={15} />
                </button>
              </div>}
            </>
          )
        )}
      </div>
      <button className="students-help" onClick={pending}>
        «<br />
        帮助中心
      </button>
    </div>
  );
}

export function StudentRailFooter({ onCollapse }: { onCollapse: () => void }) {
  return (
    <button className="student-rail-footer" onClick={onCollapse}>
      <Menu size={16} />
      收起
    </button>
  );
}
