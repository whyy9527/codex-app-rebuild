import { pinyin } from "pinyin-pro";

export function studentNameInitials(name: string): string {
  return pinyin(name, {
    pattern: "first",
    toneType: "none",
    type: "array",
    mode: "surname",
  }).join("").toUpperCase();
}
