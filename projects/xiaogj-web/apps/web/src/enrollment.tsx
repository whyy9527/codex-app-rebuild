import { useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { initClient } from "@ts-rest/core";
import { api } from "@xiaogj/contracts";
import { CircleHelp, UsersRound, ChevronDown } from "lucide-react";
import "./enrollment.css";
import Decimal from "decimal.js";
import { EnrollmentChooser } from "./enrollment-chooser";

const client = initClient(api, { baseUrl: "" });
const headers = ["项目名称", "收费规格", "有效期至", "原单价", "数量", "单位", "已领取", "优惠方案", "优惠金额", "金额", "赠送数量", "收费类型", "操作"];

function Field({ label, required, children }: { label: string; required?: boolean; children: ReactNode }) {
  return <div className="enrollment-field"><span>{required && <em>*</em>}{label}：</span>{children}</div>;
}

export function EnrollmentPage() {
  const [charges, setCharges] = useState<{ kind: "courses" | "items"; row: string[]; nameBadge: string | null; quantity: string; discount: string; gift: string }[]>([]);
  const updateCharge = (index: number, field: "quantity" | "discount" | "gift", value: string) => setCharges(current => current.map((charge, i) => i === index ? { ...charge, [field]: value } : charge));
  const [notice, setNotice] = useState("");
  const [chooser, setChooser] = useState<"courses" | "items" | null>(null);
  const unavailable = () => setNotice("此操作尚未完成复刻");
  const { data, error } = useQuery({
    queryKey: ["enrollment-defaults"],
    queryFn: async () => {
      const r = await client.enrollment();
      if (r.status !== 200) throw new Error(r.status === 503 ? r.body.message : "报名数据读取失败");
      return r.body;
    },
  });
  return <div className="enrollment-page">
    <div className="enrollment-location">当前位置： 前台业务 / 新学员报名</div>
    {error ? <p role="alert">{error.message}</p> : !data ? <p role="status">加载中…</p> :
      <div className="enrollment-scroll"><div className="enrollment-content">
        <div className="enrollment-fields">
          <div className="enrollment-field-row">
            <Field label="姓名" required><div className="enrollment-name"><input aria-label="姓名" /><button aria-label="选择学员" onClick={unavailable}><UsersRound size={17} /></button></div></Field>
            <Field label="手机号" required><input aria-label="手机号" /></Field>
            <Field label="性别"><div className="enrollment-gender"><label><input type="radio" name="enrollment-gender" value="male" />男</label><label><input type="radio" name="enrollment-gender" value="female" />女</label></div></Field>
            <Field label="师生信账号" required><div className="enrollment-account"><input aria-label="师生信账号" /><span>{data.accountSuffix}</span></div></Field>
          </div>
          <div className="enrollment-field-row">
            <Field label="身份证号"><input aria-label="身份证号" /></Field>
            <Field label="招生人员"><button className="enrollment-text-link" onClick={unavailable}>选择</button></Field>
            <Field label="招生来源"><input aria-label="招生来源" readOnly onClick={unavailable} /></Field>
            <Field label="介绍人"><input aria-label="介绍人" readOnly onClick={unavailable} /></Field>
            <Field label="年级"><select aria-label="年级" defaultValue="">{data.gradeOptions.map((grade, index) => <option key={index} value={grade}>{grade}</option>)}</select></Field>
          </div>
          <div className="enrollment-field-row">
            <Field label="学员标签"><input aria-label="学员标签" placeholder="请选择" readOnly onClick={unavailable} /></Field>
            <Field label="学管师"><button className="enrollment-text-link" onClick={unavailable}>分配</button></Field>
          </div>
        </div>
        <div className="enrollment-toolbar">
          <label>交费日期：<input aria-label="交费日期" key={`payment-${data.observedAt}`} defaultValue={data.paymentDate} /></label>
          <label>业绩归属日：<input aria-label="业绩归属日" key={`attribution-${data.observedAt}`} defaultValue={data.attributionDate} /></label>
          <label>快捷查询：<input aria-label="快捷查询" placeholder="请输入课程、物品、班级" /></label>
          {["选课", "选班", "选物品", "选模板", "选套餐", "先学后付"].map((label, i) => <button key={label} className={`enrollment-select selection-${i}`} onClick={() => i === 0 ? setChooser("courses") : i === 2 ? setChooser("items") : unavailable()}>{label}</button>)}
        </div>
        <table className="enrollment-table"><colgroup>{[280, 90, 125, 95, 80, 80, 145, 90, 90, 110, 95, 110, 80].map((width, i) => <col key={i} style={{ width }} />)}</colgroup><thead><tr>{headers.map((header) => <th key={header}>{header === "已领取" ? <label><input type="checkbox" aria-label="已领取" onChange={unavailable} />已领取</label> : header === "有效期至" ? <><button onClick={unavailable}>有效期至 <ChevronDown size={13} /></button><CircleHelp size={12} /></> : <>{header}{header === "收费规格" && <CircleHelp size={12} />}</>}</th>)}</tr></thead>
          <tbody>{!charges.length ? <tr><td colSpan={headers.length}>请选择要收费的课程或物品</td></tr> : charges.map((charge, index) => {
            const course = charge.kind === "courses", stored = charge.nameBadge === "储", unit = charge.row[course ? 2 : 3];
            const price = new Decimal(charge.row[course ? 3 : 2].replace(/[^\d.-]/g, "") || "0");
            const numeric = (value: string) => /^\d+(?:\.\d*)?$/.test(value) ? new Decimal(value) : new Decimal(0);
            const amount = price.mul(numeric(charge.quantity)).minus(numeric(charge.discount));
            return <tr className={`enrollment-charge ${stored ? "charge-stored" : ""}`} key={index}>
              <td><div><span className={`charge-kind ${course ? "course" : "item"}`}>{course ? "课" : "物"}</span>{charge.row[0]}{charge.nameBadge && <span className="chooser-name-badge">{charge.nameBadge}</span>}</div>{course && <button className="charge-class" onClick={unavailable}><span className="charge-kind class">班</span>选班</button>}</td>
              <td></td><td>{course && <button onClick={unavailable}>不限 <ChevronDown size={13} /></button>}</td>
              <td>{price.toFixed(2)}</td><td>{stored ? "1" : <div className="charge-quantity"><button aria-label="减少数量" onClick={() => updateCharge(index, "quantity", Decimal.max(0, numeric(charge.quantity).minus(1)).toString())}>−</button><input aria-label="数量" value={charge.quantity} onChange={event => updateCharge(index, "quantity", event.target.value)} /><button aria-label="增加数量" onClick={() => updateCharge(index, "quantity", numeric(charge.quantity).plus(1).toString())}>+</button></div>}</td>
              <td>{unit}</td><td>{stored && <input type="checkbox" aria-label="已领取物品" onChange={unavailable} />}</td><td>{!stored && <button className="charge-discount" aria-label="优惠方案" onClick={unavailable}>⌄</button>}</td>
              <td>{!stored && <input aria-label="优惠金额" value={charge.discount} onChange={event => updateCharge(index, "discount", event.target.value)} />}</td>
              <td>{stored ? "" : amount.toFixed(2)}</td><td>{!stored && <input aria-label="赠送数量" placeholder={unit} value={charge.gift} onChange={event => updateCharge(index, "gift", event.target.value)} />}</td><td>新增</td>
              <td><button aria-label="移除收费项目" onClick={() => setCharges(current => current.filter((_, i) => i !== index))}>×</button></td>
            </tr>;
          })}</tbody>
        </table>
        <div className="enrollment-submit"><button onClick={unavailable}>报名</button></div>
      </div></div>}
    {chooser && <EnrollmentChooser kind={chooser} onClose={() => setChooser(null)} onUnsupported={unavailable} onConfirm={rows => {
      setCharges(current => [...current, ...rows.map(choice => ({ kind: chooser, row: choice.row, nameBadge: choice.nameBadge, quantity: "", discount: "0", gift: "" }))]); setChooser(null);
    }} />}
    {notice && <div role="status" className="enrollment-notice">{notice}<button aria-label="关闭提示" onClick={() => setNotice("")}>×</button></div>}
  </div>;
}
