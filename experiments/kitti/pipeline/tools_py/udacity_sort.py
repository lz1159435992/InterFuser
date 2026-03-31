import os
import re
import glob
import ast

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(TOOLS_DIR, 'output')

# ✅【配置区 —— 全部以变量形式定义】
INPUT_DIR = OUTPUT_DIR                     # 输入文件所在目录（可改为 "./raw" 等）
INPUT_PATTERN = "udacity_[1-6]_output.txt"  # 输入文件匹配模式
OUTPUT_DIR = OUTPUT_DIR                   # 输出目录（可改为 "./sorted"）

# ————————————————————————————————
# 以下为逻辑代码（一般无需改动）
# ————————————————————————————————

def parse_line(line):
    """Parse line like: (2513, {'psnr': ..., 'ssim': ..., 'lpips': ...})"""
    line = line.strip()
    if not line.startswith('('):
        return None, None
    try:
        m = re.match(r'^(\(.*\))', line)
        if m:
            tup_str = m.group(1)
            idx, metrics = ast.literal_eval(tup_str)
            return int(idx), metrics
    except Exception as e:
        # print(f"[Warn] Parse error: {line[:40]}... | {e}")
        pass
    return None, None

def sort_and_write(input_path, output_dir=OUTPUT_DIR):
    stem = os.path.splitext(os.path.basename(input_path))[0]
    entries = []
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            idx, met = parse_line(line)
            if idx is not None and met:
                entries.append((idx, met))

    if not entries:
        print(f"[Skip] No valid data in {input_path}")
        return

    # Sort orders:
    psnr_desc = sorted(entries, key=lambda x: x[1]['psnr'], reverse=True)
    ssim_desc = sorted(entries, key=lambda x: x[1]['ssim'], reverse=True)
    lpips_asc = sorted(entries, key=lambda x: x[1]['lpips'])  # lower better

    os.makedirs(output_dir, exist_ok=True)

    def write_file(data, suffix):
        out_path = os.path.join(output_dir, f"{stem}_sort_{suffix}.txt")
        with open(out_path, 'w', encoding='utf-8') as fw:
            for idx, met in data:
                fw.write(f"({idx}, {met})\n")
        print(f"[OK] {out_path}")

    write_file(psnr_desc, 'psnr')
    write_file(ssim_desc, 'ssim')
    write_file(lpips_asc, 'lpips')

def main():
    search_path = os.path.join(INPUT_DIR, INPUT_PATTERN)
    files = glob.glob(search_path)

    if not files:
        # Try looser match in case pattern is too strict
        all_files = os.listdir(INPUT_DIR)
        files = [os.path.join(INPUT_DIR, f) for f in all_files
                 if re.match(r'udacity_\d+_output\.txt', f)]

    if not files:
        print(f"[ERROR] No files found with pattern: {search_path}")
        return

    print(f"📁 Input dir: {INPUT_DIR}")
    print(f"📤 Output dir: {OUTPUT_DIR}")
    print(f"🔍 Found {len(files)} files: {sorted([os.path.basename(f) for f in files])}")

    for fp in sorted(files):
        print(f"\n➡️ Processing: {os.path.basename(fp)}")
        try:
            sort_and_write(fp, OUTPUT_DIR)
        except Exception as e:
            print(f"[ERROR] Failed on {fp}: {e}")

if __name__ == "__main__":
    main()