
import re
from pathlib import Path
from typing import List, Dict
from pypdf import PdfReader

COURSE_HEADER_RE = re.compile(
    r"(?m)^\s*(?P<code>\d{5}-\d{4})\s+"
    r"(?P<name>.+?)\s+"
    r"(?P<t>\d)\s*-\s*(?P<p>\d{1,2})\s*-\s*(?P<c>\d)\s*$"
)

def read_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    return "\n".join(parts)

def fix_thai_pdf_noise(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\x00", " ").replace("\uf0a1", " ").replace("\uf0b7", " ")
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")

    replacements = {
        "สํ": "สำ", "คํา": "คำ", "กํ": "กำ", "ดํา": "ดำ", "นํา": "นำ", "ลํ": "ลำ", "ทํา": "ทำ",
        "เปuน": "เป็น", "เปfน": "เป็น", "เปwน": "เป็น", "เปTน": "เป็น", "เป น": "เป็น", "เป=ด": "เปิด",
        "ฝYมือ": "ฝีมือ", "ฝÇมือ": "ฝีมือ", "ฝ?มือ": "ฝีมือ", "ฝXก": "ฝึก", "ฝmก": "ฝึก",
        "ปlญหา": "ปัญหา", "ปWญหา": "ปัญหา", "ปQญหา": "ปัญหา", "ปEญหา": "ปัญหา",
        "ป'องกัน": "ป้องกัน", "ปVองกัน": "ป้องกัน", "ป'อน": "ป้อน", "เป'า": "เป้า",
        "ไฟฟ'า": "ไฟฟ้า", "ไฟฟ&า": "ไฟฟ้า", "ไฟฟVา": "ไฟฟ้า", "ไฟฟHา": "ไฟฟ้า", "ไฟฟ]า": "ไฟฟ้า",
        "กลุ!ม": "กลุ่ม", "กลุ#ม": "กลุ่ม", "กลุ&ม": "กลุ่ม", 'กลุ"ม': "กลุ่ม", "กลุ'ม": "กลุ่ม",
        "ฮาร(ดแวร(": "ฮาร์ดแวร์", "ฮาร)ดแวร)": "ฮาร์ดแวร์",
        "ช&าง": "ช่าง", "ช'าง": "ช่าง", "ช#าง": "ช่าง",
        "หน0าว#าง": "หน้าว่าง", "หน0าว!าง": "หน้าว่าง", "หน0าว0าง": "หน้าว่าง", "หน/าว'าง": "หน้าว่าง",
        "อ/างอิงมาตรฐาน": "อ้างอิงมาตรฐาน",
        "ผลลัพธ)การเรียนรู/ระดับรายวิชา": "ผลลัพธ์การเรียนรู้ระดับรายวิชา",
        "ผลลัพธ*การเรียนรู0ระดับรายวิชา": "ผลลัพธ์การเรียนรู้ระดับรายวิชา",
        "จุดประสงค)รายวิชา": "จุดประสงค์รายวิชา",
        "จุดประสงค*รายวิชา": "จุดประสงค์รายวิชา",
        "สมรรถนะรายวิชา": "สมรรถนะรายวิชา",
        "คําอธิบายรายวิชา": "คำอธิบายรายวิชา",
        "คําอธิบาย": "คำอธิบาย",
        "ผลลัพธ*": "ผลลัพธ์", "ผลลัพธ)": "ผลลัพธ์", "ประสงค*": "ประสงค์", "ประสงค)": "ประสงค์",
        "ประยุกต*": "ประยุกต์", "ประยุกต)": "ประยุกต์",
        "ศาสตร*": "ศาสตร์", "ศาสตร)": "ศาสตร์",
        "อุปกรณ*": "อุปกรณ์", "อุปกรณ)": "อุปกรณ์",
        "สัญลักษณ*": "สัญลักษณ์", "สัญลักษณ)": "สัญลักษณ์",
        "อินเทอร*เน็ต": "อินเทอร์เน็ต", "อินเทอร)เน็ต": "อินเทอร์เน็ต",
        "คอมพิวเตอร*": "คอมพิวเตอร์", "คอมพิวเตอร)": "คอมพิวเตอร์",
        "มอเตอร*": "มอเตอร์", "มอเตอร)": "มอเตอร์",
        "ไมโครคอนโทรลเลอร*": "ไมโครคอนโทรลเลอร์", "ไมโครคอนโทรลเลอร)": "ไมโครคอนโทรลเลอร์",
        "อิเล็กทรอนิกส*": "อิเล็กทรอนิกส์", "อิเล็กทรอนิกส)": "อิเล็กทรอนิกส์", "อิเล็กทรอนิกส(": "อิเล็กทรอนิกส์",
        "พัลส*": "พัลส์", "พัลส)": "พัลส์",
        "เซนเซอร*": "เซนเซอร์", "เซนเซอร)": "เซนเซอร์",
        "ทรานสดิวเซอร*": "ทรานสดิวเซอร์", "ทรานสดิวเซอร)": "ทรานสดิวเซอร์",
        "รู1": "รู้", "รู0": "รู้", "รู@": "รู้",
        "ผู1": "ผู้", "ผูP": "ผู้", "ผู@": "ผู้",
        "ให1": "ให้", "ให0": "ให้", "ให@": "ให้",
        "ใช1": "ใช้", "ใช@": "ใช้",
        "ได1": "ได้", "ได@": "ได้",
        "เข1า": "เข้า", "เข@า": "เข้า",
        "ต1อง": "ต้อง", "ต@อง": "ต้อง",
        "สร1าง": "สร้าง", "สร@าง": "สร้าง",
        "ข1อ": "ข้อ", "ข@อ": "ข้อ",
        "ด1วย": "ด้วย", "ด@วย": "ด้วย",
        "ด1าน": "ด้าน", "ด0าน": "ด้าน", "ด@าน": "ด้าน",
        "ต1น": "ต้น", "ต0น": "ต้น", "ต@น": "ต้น",
        "แก1": "แก้", "แก0": "แก้", "แก@": "แก้",
        "ค1น": "ค้น",
        "คู#มือ": "คู่มือ", "คู'มือ": "คู่มือ",
        "ต#อ": "ต่อ", "ต'อ": "ต่อ",
        "ต#าง": "ต่าง", "ต'าง": "ต่าง",
        "ส#วน": "ส่วน", "ส'วน": "ส่วน",
        "ร#วม": "ร่วม", "ร'วม": "ร่วม",
        "อย#าง": "อย่าง", "อย'าง": "อย่าง",
        "แหล#ง": "แหล่ง", "แหล'ง": "แหล่ง",
        "เครือข'าย": "เครือข่าย",
        "ต'อพ'วง": "ต่อพ่วง",
        "หุ'นยนต์": "หุ่นยนต์", "หุ'นยนต)": "หุ่นยนต์",
        "เว็บไซต)": "เว็บไซต์",
        "ข@อมูล": "ข้อมูล", "ข1อมูล": "ข้อมูล",
        "ฟlงก)ชัน": "ฟังก์ชัน", "ฟlงก)ชั่น": "ฟังก์ชัน",
        "กราฟsก": "กราฟิก", "ปsด": "ปิด", "ปlด": "ปิด",
        "กำาหนด": "กำหนด", "สำาหรับ": "สำหรับ",
        "สถาปlตยกรรม": "สถาปัตยกรรม",
        "ปlญญา": "ปัญญา",
        # เพิ่มจากชุดไฟล์สำนักมาตรฯ หลายสาขา
        "ให&": "ให้", "ใช&": "ใช้", "ได&": "ได้", "เข&า": "เข้า", "ต&อง": "ต้อง", "สร&าง": "สร้าง", "ด&วย": "ด้วย", "ผู&": "ผู้", "รู&": "รู้",
        "ใหC": "ให้", "ใชC": "ใช้", "ไดC": "ได้", "เขCา": "เข้า", "ตCอง": "ต้อง", "สรCาง": "สร้าง", "ดCวย": "ด้วย", "ผูC": "ผู้", "รูC": "รู้",
        "ใหL": "ให้", "ใชL": "ใช้", "ไดL": "ได้", "เขLา": "เข้า", "ตLอง": "ต้อง", "สรLาง": "สร้าง", "ดLวย": "ด้วย", "ผูL": "ผู้", "รูL": "รู้",
        "ใหO": "ให้", "ใชO": "ใช้", "ไดO": "ได้", "เขOา": "เข้า", "ตOอง": "ต้อง", "สรOาง": "สร้าง", "ดOวย": "ด้วย", "ผูO": "ผู้", "รูO": "รู้",
        "ใหF": "ให้", "ใชF": "ใช้", "ไดF": "ได้", "เขFา": "เข้า", "ตFอง": "ต้อง", "สรFาง": "สร้าง", "ดFวย": "ด้วย", "ผูF": "ผู้", "รูF": "รู้",
        "อCางอิงมาตรฐาน": "อ้างอิงมาตรฐาน", "อFางอิงมาตรฐาน": "อ้างอิงมาตรฐาน", "อLางอิงมาตรฐาน": "อ้างอิงมาตรฐาน",
        "ผลลัพธ+การเรียนรูFระดับรายวิชา": "ผลลัพธ์การเรียนรู้ระดับรายวิชา",
        "ผลลัพธ&การเรียนรูCระดับรายวิชา": "ผลลัพธ์การเรียนรู้ระดับรายวิชา",
        "ผลลัพธ%การเรียนรูCระดับรายวิชา": "ผลลัพธ์การเรียนรู้ระดับรายวิชา",
        "จุดประสงค+รายวิชา": "จุดประสงค์รายวิชา", "จุดประสงค&รายวิชา": "จุดประสงค์รายวิชา", "จุดประสงค%รายวิชา": "จุดประสงค์รายวิชา",
        "อุปกรณ&": "อุปกรณ์", "เครื่องมือวัด": "เครื่องมือวัด", "คอมพิวเตอร&": "คอมพิวเตอร์", "อินเทอร&เน็ต": "อินเทอร์เน็ต",
        "เมคคาทรอนิกส&": "เมคคาทรอนิกส์", "หุ$นยนต&": "หุ่นยนต์", "คอนโทรลเลอร&": "คอนโทรลเลอร์",
        "ทรานซิสเตอร&": "ทรานซิสเตอร์", "เพาเวอร&": "เพาเวอร์", "เซนเซอร&": "เซนเซอร์", "มัลติมิเตอร&": "มัลติมิเตอร์",
        "ก)อน": "ก่อน", "ต)อ": "ต่อ", "ต)าง": "ต่าง", "ส)วน": "ส่วน", "ร)วม": "ร่วม", "อย)าง": "อย่าง", "ง)าย": "ง่าย", "อ)าน": "อ่าน", "ค)า": "ค่า", "จ)าย": "จ่าย", "ซ)อม": "ซ่อม", "หน)วย": "หน่วย", "เครือข)าย": "เครือข่าย",
        "ก$อน": "ก่อน", "ต$อ": "ต่อ", "ต$าง": "ต่าง", "ส$วน": "ส่วน", "ร$วม": "ร่วม", "อย$าง": "อย่าง", "ง$าย": "ง่าย", "อ$าน": "อ่าน", "ค$า": "ค่า", "จ$าย": "จ่าย", "ซ$อม": "ซ่อม", "หน$วย": "หน่วย", "หุ$นยนต์": "หุ่นยนต์",
        "ไฟฟTา": "ไฟฟ้า", "ไฟฟWา": "ไฟฟ้า", "ไฟฟGา": "ไฟฟ้า", "ไฟฟXา": "ไฟฟ้า",
        "ปGองกัน": "ป้องกัน", "ปbญญา": "ปัญญา", "ปbญหา": "ปัญหา", "ปrญหา": "ปัญหา", "ปCญหา": "ปัญหา",

        "ผลลัพธ.การเรียนรู ระดับรายวิชา": "ผลลัพธ์การเรียนรู้ระดับรายวิชา",
        "จุดประสงค.รายวิชา": "จุดประสงค์รายวิชา",
        "อ างอิงมาตรฐาน": "อ้างอิงมาตรฐาน", "อ	างอิงมาตรฐาน": "อ้างอิงมาตรฐาน",
        "กล อง": "กล้อง", "กล	อง": "กล้อง", "ป2ด": "ปิด", "เป:น": "เป็น", "ป/ญหา": "ปัญหา", "แก.ปัญหา": "แก้ปัญหา", "แก.ป้ญหา": "แก้ปัญหา",
        "ไฟฟ%า": "ไฟฟ้า", "เมคคาทรอนิกส%": "เมคคาทรอนิกส์", "หุ#นยนต%": "หุ่นยนต์", "หุ#นยนต์": "หุ่นยนต์",
        "อ-างอิงมาตรฐาน": "อ้างอิงมาตรฐาน", "ผลลัพธการเรียนรู้ระดับรายวิชา": "ผลลัพธ์การเรียนรู้ระดับรายวิชา", "ผลลัพธการเรียนรู-ระดับรายวิชา": "ผลลัพธ์การเรียนรู้ระดับรายวิชา",
        "จุดประสงครายวิชา": "จุดประสงค์รายวิชา", "จุดประสงครายวิชา": "จุดประสงค์รายวิชา",
        "คอมพิวเตอร": "คอมพิวเตอร์", "คอมพิวเตอร": "คอมพิวเตอร์", "อิเล็กทรอนิกส": "อิเล็กทรอนิกส์", "อิเล็กทรอนิกส": "อิเล็กทรอนิกส์",
        "ให8": "ให้", "ใช8": "ใช้", "ได8": "ได้", "เข8า": "เข้า", "ต8อง": "ต้อง", "สร8าง": "สร้าง", "ด8วย": "ด้วย", "ผู8": "ผู้", "รู8": "รู้", "ต8น": "ต้น", "ข8อ": "ข้อ", "แก8": "แก้",
        "เรียนรู-": "เรียนรู้", "ความรู-": "ความรู้", "ผู-": "ผู้", "ให-": "ให้", "ใช-": "ใช้", "ได-": "ได้", "เข-า": "เข้า", "ต-อง": "ต้อง", "สร-าง": "สร้าง", "ด-วย": "ด้วย", "ข-อ": "ข้อ", "ด-าน": "ด้าน",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)

    # แก้สัญลักษณ์ที่มักถูกดึงแทนวรรณยุกต์/ทัณฑฆาต
    for ch in ["P", "1", "0", "8", "C", "O", "L", "F", "T", "G", "W", "V", "H", "]", "/"]:
        text = re.sub(rf"(?<=[ก-ฮ]){re.escape(ch)}", "้", text)
    for ch in ["#", "'", '"', "$"]:
        text = re.sub(rf"(?<=[ก-ฮ]){re.escape(ch)}", "่", text)
    for ch in ["*", "+", "%", "&", "(", ")"]:
        text = re.sub(rf"(?<=[ก-ฮ]){re.escape(ch)}", "์", text)

    text = re.sub(r"(?<=[ก-ฮ])[\x10-\x1f]", "์", text)

    regex_fixes = [
        (r"การ\s+เรียน\s*รู้", "การเรียนรู้"),
        (r"ผลลัพธ์\s*การเรียนรู้\s*ระดับรายวิชา", "ผลลัพธ์การเรียนรู้ระดับรายวิชา"),
        (r"จุดประสงค์\s*รายวิชา", "จุดประสงค์รายวิชา"),
        (r"สมรรถนะ\s*รายวิชา", "สมรรถนะรายวิชา"),
        (r"คำ\s*อธิบาย\s*รายวิชา", "คำอธิบายรายวิชา"),
        (r"อ้าง\s*อิง\s*มาตรฐาน", "อ้างอิงมาตรฐาน"),
        (r"คอม\s*พิวเตอร์", "คอมพิวเตอร์"),
        (r"คอมพ\s*ิวเตอร์", "คอมพิวเตอร์"),
        (r"อิเล็ก\s*ทรอนิกส์", "อิเล็กทรอนิกส์"),
        (r"เครือ\s*ข่าย", "เครือข่าย"),
        (r"เมค\s*คาทรอนิกส์", "เมคคาทรอนิกส์"),
        (r"หุ่น\s*ยนต์", "หุ่นยนต์"),
        (r"ไฟ\s*ฟ้า", "ไฟฟ้า"),
        (r"([ก-๙])\s+ๆ", r"\1 ๆ"),
    ]
    for pat, rep in regex_fixes:
        text = re.sub(pat, rep, text)

    lines = []
    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)

def clean_field(text: str) -> str:
    text = fix_thai_pdf_noise(text or "")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"^\d+\s*$", "", text, flags=re.M)
    return text.strip()

def normalize_text(text: str) -> str:
    return clean_field(text)

def detect_curriculum_meta(text: str) -> Dict[str, str]:
    lines = text.splitlines()
    cover = "\n".join(lines[:20])
    if "สารบัญ" in cover:
        cover = cover.split("สารบัญ")[0]
    head = "\n".join(lines[:260])
    base = cover + "\n" + head

    if "ประกาศนียบัตรวิชาชีพชั้นสูง" in cover or re.search(r"\bปวส\b|\(ปวส", cover):
        level = "ปวส."
    else:
        level = "ปวช."

    curriculum = "หลักสูตรประกาศนียบัตรวิชาชีพชั้นสูง (ปวส.) พุทธศักราช 2567" if level == "ปวส." else "หลักสูตรประกาศนียบัตรวิชาชีพ (ปวช.) พุทธศักราช 2567"

    program_type = ""
    occupational_group = ""
    major = ""

    m = re.search(r"ประเภทวิชา\s*([^\n]+)", base)
    if m:
        program_type = clean_field(m.group(1))
    m = re.search(r"กลุ่มอาชีพ\s*([^\n]+)", base)
    if m:
        occupational_group = clean_field(m.group(1))
    m = re.search(r"สาขาวิชา\s*([^\n]+)", base)
    if m:
        major = clean_field(m.group(1))

    if "สาขาวิชา" in occupational_group:
        parts = occupational_group.split("สาขาวิชา", 1)
        occupational_group = clean_field(parts[0])
        if not major:
            major = clean_field(parts[1])
    if "สาขาวิชา" in program_type:
        program_type = clean_field(program_type.split("สาขาวิชา", 1)[0])

    return {
        "level": level,
        "curriculum": curriculum,
        "program_type": program_type,
        "occupational_group": occupational_group,
        "major": major,
    }

def compact(s: str) -> str:
    s = clean_field(s)
    return re.sub(r"\n{2,}", "\n", s).strip()

def find_course_starts(text: str) -> List[re.Match]:
    return list(COURSE_HEADER_RE.finditer(text))

def section_between(block: str, start_markers: List[str], end_markers: List[str]) -> str:
    start_pos = None
    start_len = 0
    for marker in start_markers:
        pos = block.find(marker)
        if pos != -1 and (start_pos is None or pos < start_pos):
            start_pos = pos
            start_len = len(marker)
    if start_pos is None:
        return ""
    content_start = start_pos + start_len
    end_pos = len(block)
    for marker in end_markers:
        pos = block.find(marker, content_start)
        if pos != -1 and pos < end_pos:
            end_pos = pos
    return compact(block[content_start:end_pos])

def split_numbered_items(text: str) -> List[str]:
    text = compact(text)
    if not text:
        return []
    parts = re.split(r"(?:^|\n)\s*\d+[\.\)]\s*", text)
    items = [compact(p) for p in parts if compact(p)]
    items = [re.sub(r"^เพื่อให้\s*", "", i).strip() for i in items]
    bad_starts = ("เพื่อให้", "สมรรถนะรายวิชา", "คำอธิบายรายวิชา")
    return [i for i in items if len(i) > 2 and not i.startswith(bad_starts)][:20]

def make_units_from_description(description: str, course_name: str, theory: int, practice: int) -> List[dict]:
    desc = clean_field(description)
    desc = desc.replace("ศึกษาและปฏิบัติเกี่ยวกับ", "").replace("ศึกษาและปฏิบัติงานเกี่ยวกับ", "").replace("ศึกษาเกี่ยวกับ", "")
    raw_topics = re.split(r"[،,]| และ | การ", desc)
    topics = []
    for t in raw_topics:
        t = clean_field(t.strip(" .\n"))
        if len(t) >= 8 and t not in topics:
            topics.append(t)

    if len(topics) < 6:
        topics = [
            f"หลักการพื้นฐานของ{course_name}",
            f"เครื่องมือและอุปกรณ์ที่ใช้ใน{course_name}",
            f"การปฏิบัติงานพื้นฐานใน{course_name}",
            f"การวิเคราะห์และแก้ไขปัญหาใน{course_name}",
            f"การทดสอบและประเมินผลงาน{course_name}",
            f"โครงงานหรือภาระงานใน{course_name}",
        ]
    topics = topics[:10]
    while len(topics) < 10:
        topics.append(f"การประยุกต์ใช้{course_name}ในงานอาชีพ {len(topics)+1}")

    total_t = max(theory * 18, 1)
    total_p = max(practice * 18, 1)
    base_t = total_t // 10
    base_p = total_p // 10
    rem_t = total_t - base_t * 10
    rem_p = total_p - base_p * 10

    units = []
    for i, title in enumerate(topics, 1):
        th = base_t + (1 if i <= rem_t else 0)
        pr = base_p + (1 if i <= rem_p else 0)
        units.append({
            "no": i,
            "title": title,
            "theory": th,
            "practice": pr,
            "k": "K2,K3" if i < 7 else ("K3,K5" if i < 9 else "K3,K6"),
            "s": "S4" if i < 10 else "S5",
            "a": "A5",
            "ap": "Ap3",
            "bloom": ["-","20","20","-","-","-"] if i <= 4 else (["-","-","20","20","-","-"] if i <= 8 else ["-","-","20","-","-","20"])
        })
    return units

def detect_quality(course: Dict) -> Dict:
    missing = []
    if not course.get("description"):
        missing.append("คำอธิบายรายวิชา")
    if not course.get("objectives"):
        missing.append("จุดประสงค์รายวิชา")
    if not course.get("competencies"):
        missing.append("สมรรถนะรายวิชา")
    if not course.get("learning_outcome"):
        missing.append("ผลลัพธ์รายวิชา")

    suspicious_terms = ["ชั่", "ชื่", "สิ่", "ยี", "ประเ", "ค วา", "", "�", "กลุ!", "0าง"]
    blob = " ".join([
        course.get("name",""),
        course.get("description",""),
        " ".join(course.get("objectives",[])),
        " ".join(course.get("competencies",[])),
    ])
    suspicious = [t for t in suspicious_terms if t in blob]

    course["quality_missing"] = ", ".join(missing)
    course["quality_suspicious"] = ", ".join(suspicious)
    course["is_verified"] = not missing and not suspicious
    return course

def course_score(course: Dict) -> int:
    score = 0
    score += 10 if course.get("description") else 0
    score += 4 if course.get("objectives") else 0
    score += 4 if course.get("competencies") else 0
    score += 3 if course.get("learning_outcome") else 0
    score += 1 if course.get("standard_ref") else 0
    return score

def parse_block_to_course(block: str, match: re.Match, meta: Dict[str, str], filename: str) -> Dict:
    code = match.group("code")
    name = clean_field(match.group("name"))
    theory = int(match.group("t"))
    practice = int(match.group("p"))
    credits = int(match.group("c"))

    standard_ref = section_between(
        block,
        ["อ้างอิงมาตรฐาน"],
        ["ผลลัพธ์การเรียนรู้ระดับรายวิชา", "จุดประสงค์รายวิชา", "สมรรถนะรายวิชา", "คำอธิบายรายวิชา"],
    )
    learning_outcome = section_between(
        block,
        ["ผลลัพธ์การเรียนรู้ระดับรายวิชา"],
        ["จุดประสงค์รายวิชา", "สมรรถนะรายวิชา", "คำอธิบายรายวิชา"],
    )
    objectives_text = section_between(
        block,
        ["จุดประสงค์รายวิชา เพื่อให้", "จุดประสงค์รายวิชา"],
        ["สมรรถนะรายวิชา", "คำอธิบายรายวิชา"],
    )
    competencies_text = section_between(
        block,
        ["สมรรถนะรายวิชา"],
        ["คำอธิบายรายวิชา"],
    )
    description = section_between(block, ["คำอธิบายรายวิชา"], [])

    objectives = split_numbered_items(objectives_text)
    competencies = split_numbered_items(competencies_text)

    if not learning_outcome and competencies:
        learning_outcome = competencies[-1]

    row = {
        "code": code,
        "name": name,
        "level": meta["level"],
        "curriculum": meta["curriculum"],
        "program_type": meta["program_type"],
        "occupational_group": meta["occupational_group"],
        "major": meta["major"],
        "theory_hours": theory,
        "practice_hours": practice,
        "credits": credits,
        "standard_ref": standard_ref,
        "learning_outcome": learning_outcome,
        "objectives": objectives,
        "competencies": competencies,
        "description": description,
        "occupational_standard": standard_ref,
        "assessment": f"ให้ผู้เรียนจัดทำชิ้นงาน/ภาระงานที่สอดคล้องกับรายวิชา {name} พร้อมนำเสนอและรับการประเมินตามสมรรถนะรายวิชา",
        "source_note": f"นำเข้าอัตโนมัติจากไฟล์ PDF: {filename} | ดึงข้อมูลแบบรวมรายชื่อวิชา + รายละเอียดเต็ม และผ่านระบบแก้คำเพี้ยน PDF",
    }
    row["units"] = make_units_from_description(description, name, theory, practice)
    return detect_quality(row)

def merge_course(old: Dict, new: Dict) -> Dict:
    if course_score(new) > course_score(old):
        merged = old.copy()
        merged.update(new)
        for key in ["name", "level", "curriculum", "program_type", "occupational_group", "major"]:
            if not merged.get(key):
                merged[key] = old.get(key, "")
        return detect_quality(merged)
    merged = old.copy()
    for key, val in new.items():
        if key not in merged or not merged.get(key):
            merged[key] = val
    return detect_quality(merged)

def parse_courses_from_pdf(path: Path) -> Dict:
    raw = read_pdf_text(path)
    text = normalize_text(raw)
    meta = detect_curriculum_meta(text)

    starts = find_course_starts(text)
    courses_by_code: Dict[str, Dict] = {}

    for idx, match in enumerate(starts):
        start = match.start()
        end = starts[idx + 1].start() if idx + 1 < len(starts) else len(text)
        block = text[start:end]
        row = parse_block_to_course(block, match, meta, path.name)
        code = row["code"]
        if code not in courses_by_code:
            courses_by_code[code] = row
        else:
            courses_by_code[code] = merge_course(courses_by_code[code], row)

    all_courses = list(courses_by_code.values())
    all_courses.sort(key=lambda x: x["code"])

    # ฐานข้อมูลจริงควรนำเข้าเฉพาะรายวิชาที่มีรายละเอียดครบ
    # เพื่อไม่ให้มีแค่รหัส/ชื่อ/ท-ป-น แต่ขาดผลลัพธ์ จุดประสงค์ สมรรถนะ หรือคำอธิบาย
    complete_courses = [
        c for c in all_courses
        if c.get("learning_outcome") and c.get("objectives") and c.get("competencies") and c.get("description")
    ]

    return {
        "meta": meta,
        "courses": complete_courses,
        "all_courses_count": len(all_courses),
        "skipped_incomplete_count": len(all_courses) - len(complete_courses),
        "text_preview": text[:3000],
        "course_count": len(complete_courses),
    }
