import pgvector
import fitz
import docx
import chardet
# print('所有依赖安装成功')

from module_rag.service.parser.pdf_parser import PdfParser

pdf_file_path = r"G:\zhangyichi\ruoyi-fastapi-backend\utils\ragmodels\files\社工22级教材《社会工作行动研究》.pdf"

pdf = PdfParser()
res = pdf.parse(pdf_file_path)
print(res)

# 写入文本文件
out_path = r"G:\zhangyichi\ruoyi-fastapi-backend\tests\pdf解析结果.txt"
with open(out_path, "w", encoding="utf-8") as f:
    # res一般是列表[{page,content},...]格式，循环写入
    if isinstance(res, list):
        for idx, item in enumerate(res, 1):
            # f.write(f"=====第{item.get('page',idx)}页,页面属性为：{item.get(type)}=====\n")
            f.write(item.get("text", "") + "\n\n")
    else:
        f.write(str(res))

print(f"文本已输出至：{out_path}")