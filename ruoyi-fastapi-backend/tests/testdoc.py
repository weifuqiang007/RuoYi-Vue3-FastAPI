from module_rag.service.parser.docx_parser import DocxParser

doc_path =  r"G:\zhangyichi\ruoyi-fastapi-backend\utils\ragmodels\files\社会工作行动研究全部提问.docx"
doc = DocxParser()

res = doc.parse(doc_path)
print(res)