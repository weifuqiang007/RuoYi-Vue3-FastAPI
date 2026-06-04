"""
PDF分割工具脚本

将一个PDF文件按页数平均分割成指定份数，方便后续逐份转换为Markdown文件。

使用方式:
    # 命令行
    python -m module_rag.utils.pdf_splitter <pdf文件路径> [--parts 10] [--output_dir ./output]

    # 代码调用
    from module_rag.utils.pdf_splitter import split_pdf
    split_pdf("input.pdf", parts=10, output_dir="./split_output")

依赖: PyMuPDF (fitz)
"""

import argparse
import os
import sys
from pathlib import Path

import fitz  # PyMuPDF


def split_pdf(pdf_path: str, parts: int = 10, output_dir: str | None = None) -> list[str]:
    """
    将PDF文件按页数平均分割成指定份数。

    Args:
        pdf_path: 源PDF文件路径
        parts: 分割份数，默认10
        output_dir: 输出目录，默认为源文件同目录下的 {文件名}_split 子文件夹

    Returns:
        分割后的PDF文件路径列表

    Raises:
        FileNotFoundError: 源PDF文件不存在
        ValueError: parts 小于1或大于总页数
    """
    pdf_path = os.path.abspath(pdf_path)
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    # 打开源PDF
    src_doc = fitz.open(pdf_path)
    total_pages = len(src_doc)

    if total_pages == 0:
        src_doc.close()
        raise ValueError("PDF文件没有页面")

    if parts < 1:
        src_doc.close()
        raise ValueError(f"分割份数必须大于0，当前值: {parts}")

    if parts > total_pages:
        print(f"警告: 分割份数({parts})大于总页数({total_pages})，将调整为{total_pages}份")
        parts = total_pages

    # 计算输出目录
    if output_dir is None:
        base_name = Path(pdf_path).stem
        parent_dir = os.path.dirname(pdf_path)
        output_dir = os.path.join(parent_dir, f"{base_name}_split")

    os.makedirs(output_dir, exist_ok=True)

    # 计算每份的页数范围
    base_pages = total_pages // parts
    remainder = total_pages % parts  # 前remainder份各多1页

    base_name = Path(pdf_path).stem
    output_files = []

    print(f"源文件: {pdf_path}")
    print(f"总页数: {total_pages}，分割为 {parts} 份")
    print("-" * 50)

    current_page = 0
    for i in range(parts):
        # 前remainder份各多1页，保证页数均匀分布
        page_count = base_pages + (1 if i < remainder else 0)
        start_page = current_page
        end_page = current_page + page_count - 1

        # 创建新PDF并复制对应页面
        new_doc = fitz.open()
        new_doc.insert_pdf(src_doc, from_page=start_page, to_page=end_page)

        # 保存文件
        part_num = str(i + 1).zfill(len(str(parts)))
        output_filename = f"{base_name}_part{part_num}.pdf"
        output_path = os.path.join(output_dir, output_filename)
        new_doc.save(output_path)
        new_doc.close()

        output_files.append(output_path)
        print(f"  Part {part_num}: 第 {start_page + 1}-{end_page + 1} 页 ({page_count}页) -> {output_filename}")

        current_page += page_count

    src_doc.close()

    print("-" * 50)
    print(f"分割完成! {len(output_files)} 个文件已保存到: {os.path.abspath(output_dir)}")

    return output_files


def main():
    parser = argparse.ArgumentParser(
        description="PDF分割工具 - 将PDF文件按页数平均分割成多份"
    )
    parser.add_argument("pdf_path", help="源PDF文件路径")
    parser.add_argument("--parts", "-n", type=int, default=10, help="分割份数 (默认: 10)")
    parser.add_argument("--output_dir", "-o", type=str, default=None, help="输出目录 (默认: 源文件同目录下创建子文件夹)")

    args = parser.parse_args()

    try:
        split_pdf(args.pdf_path, parts=args.parts, output_dir=args.output_dir)
    except (FileNotFoundError, ValueError) as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
