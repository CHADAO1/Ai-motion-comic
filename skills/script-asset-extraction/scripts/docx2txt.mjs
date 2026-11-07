#!/usr/bin/env node
/**
 * docx2txt.mjs — 从 .docx (Office Open XML zip) 提取正文纯文本
 * 用法:   node docx2txt.mjs <input.docx> [output.txt]
 * 行为:   解析 ZIP 中央目录 -> 找到 word/document.xml -> inflateRaw 解压
 *         <w:p> 段落转换行, <w:tab/> 转 \t, <w:br/> 转换行, 剥离其余标签, 解码实体
 * 输出:   UTF-8 文本; stdout 打印字符数/行数作为 S0 通过证据
 * 映射:   SKILL.md S0; 无第三方依赖
 */
import { readFileSync, writeFileSync } from "node:fs";
import { inflateRawSync } from "node:zlib";
import { dirname, join } from "node:path";

const u16 = (b, o) => b.readUInt16LE(o);
const u32 = (b, o) => b.readUInt32LE(o);

/** 在 zip Buffer 中定位中央目录里的指定条目并解压返回 Buffer */
function extractEntry(buf, wanted) {
  let eocd = -1;
  const floor = Math.max(0, buf.length - 22 - 65535);
  for (let i = buf.length - 22; i >= floor; i--) {
    if (u32(buf, i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error("不是有效的 zip/docx（未找到 EOCD）");
  const count = u16(buf, eocd + 10);
  let off = u32(buf, eocd + 16);
  for (let k = 0; k < count; k++) {
    if (u32(buf, off) !== 0x02014b50) throw new Error("中央目录损坏 @ " + off);
    const method = u16(buf, off + 10);
    const csize = u32(buf, off + 20);
    const nlen = u16(buf, off + 28), elen = u16(buf, off + 30), clen = u16(buf, off + 32);
    const lho = u32(buf, off + 42);
    const name = buf.slice(off + 46, off + 46 + nlen).toString("utf8");
    if (name === wanted) {
      const lnlen = u16(buf, lho + 26), lelen = u16(buf, lho + 28);
      const start = lho + 30 + lnlen + lelen;
      const comp = buf.slice(start, start + csize);
      return method === 0 ? comp : inflateRawSync(comp);
    }
    off += 46 + nlen + elen + clen;
  }
  throw new Error("zip 内找不到 " + wanted);
}

function xmlToText(xml) {
  let t = xml
    .replace(/<\/w:p>/g, "\n")
    .replace(/<w:tab\b[^>]*\/?>/g, "\t")
    .replace(/<w:br\b[^>]*\/?>/g, "\n")
    .replace(/<[^>]+>/g, "");
  return t
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"').replace(/&apos;/g, "'")
    .replace(/&#x([0-9a-fA-F]+);/g, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(parseInt(d, 10)))
    .replace(/&amp;/g, "&");
}

const [, , inFile, outArg] = process.argv;
if (!inFile) { console.error("用法: node docx2txt.mjs <input.docx> [output.txt]"); process.exit(2); }
const outFile = outArg ?? join(dirname(inFile), "00_剧本全文.txt");

const zip = readFileSync(inFile);
const xml = extractEntry(zip, "word/document.xml").toString("utf8");
const text = xmlToText(xml).replace(/\n{3,}/g, "\n\n").trim() + "\n";
writeFileSync(outFile, text, "utf8");
const lines = text.split("\n").length;
console.log(`OK ${outFile}`);
console.log(`chars=${text.length} lines=${lines}`);
if (text.length === 0) process.exit(1);
