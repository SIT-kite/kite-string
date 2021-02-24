# Lib: libreoffice
# Description: transform word into pdf
# Installation: go to  https://www.cnblogs.com/ruozhu/p/11190195.html
# you must make sure line 96 is same to your libreoffice's version

import os
import os.path

# Lib: pymupdf
# Description: pdf to png
# Installation: pip install pymupdf
import fitz
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBoxHorizontal, LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed
# Lib: pdfminer3k
# Description: pdf content extract
# Installation: pip install pdfminer3k
from pdfminer.pdfparser import PDFParser, PDFDocument


class DocExtract:
    def __init__(self, doc_path=""):
        # protected
        self._doc_path = doc_path
        # set doc path

    def load_path(self, doc_path):
        self._doc_path = doc_path


class PdfExtract(DocExtract):
    def __init__(self, pdf_path=""):
        super().__init__(pdf_path)

    def convert2png(self, png_path=""):
        pdfDoc = fitz.open(self._doc_path)
        file_name = os.path.split(self._doc_path)[1]
        file_name = file_name.split('.')[0]
        if png_path == "":
            png_path = './' + file_name
        else:
            png_path = png_path + '/' + file_name

        if not os.path.exists(png_path):
            os.makedirs(png_path)
        for pg in range(pdfDoc.pageCount):
            page = pdfDoc[pg]
            rotate = int(0)
            # 每个尺寸的缩放系数为1.3，这将为我们生成分辨率提高2.6的图像。
            # 此处若是不做设置，默认图片大小为：792X612, dpi=72
            zoom_x = 1.33333333  # (1.33333333-->1056x816)   (2-->1584x1224)
            zoom_y = 1.33333333
            mat = fitz.Matrix(zoom_x, zoom_y).preRotate(rotate)
            pix = page.getPixmap(matrix=mat, alpha=False)
            # extract file name          
            pix.writePNG(png_path + '/' + file_name + '_%s.png' % pg)
        print("Successfully save png to folder " + png_path)

    def show_path(self):
        return self._doc_path

    def pdf_extract(self):
        return self._prase()

    def _prase(self):
        fp = open(self._doc_path, 'rb')
        parser = PDFParser(fp)
        doc = PDFDocument()
        parser.set_document(doc)
        doc.set_parser(parser)
        doc.initialize()
        if not doc.is_extractable:
            raise PDFTextExtractionNotAllowed
        else:
            rsrcmgr = PDFResourceManager()
            laparams = LAParams()
            device = PDFPageAggregator(rsrcmgr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            # all content
            content = []
            for page in doc.get_pages():
                interpreter.process_page(page)
                layout = device.get_result()
                # content in one page
                content_single_page = ""
                for x in layout:
                    if (isinstance(x, LTTextBoxHorizontal)):
                        content_single_page += x.get_text().strip()
                content.append(content_single_page)
        return content


class WordExtract(DocExtract):
    _is2pdf = False
    _pdfExtract = PdfExtract()
    _pdf_out_path = os.getcwd() + '/tmp_pdf'

    def __init__(self, word_path=""):
        super().__init__(word_path)

    def show_path(self):
        return self._doc_path

    def _word2pdf_linux(self):
        cmd = 'libreoffice7.1 --headless --convert-to pdf ' + self._doc_path + ' --outdir ' + self._pdf_out_path
        print(cmd)
        res = os.system(cmd)
        if res is not 0:
            print("convert " + self._doc_path + "to pdf failed")
        else:
            self._is2pdf = True

    def word_extract(self):
        return self._prase()

    def convert2png(self, png_path=""):
        if not self._is2pdf:
            self._word2pdf_linux()
        file_name = os.path.split(self._doc_path)[1].split('.')[0]
        self._pdfExtract.load_path(self._pdf_out_path + '/' + file_name + '.pdf')
        self._pdfExtract.convert2png(png_path)

    def _prase(self):
        if not self._is2pdf:
            self._word2pdf_linux()
        file_name = os.path.split(self._doc_path)[1].split('.')[0]
        self._pdfExtract.load_path(self._pdf_out_path + '/' + file_name + '.pdf')
        return self._pdfExtract.pdf_extract()


wordExtract = WordExtract("./上海应用技术大学关于开展2019年学习标兵、学习型寝室的评选通知.doc")
wordExtract.convert2png()
print(wordExtract.word_extract())

pdfExtract = PdfExtract()
pdfExtract.load_path('./上海应用技术大学疫情防控指南.pdf')
pdfExtract.convert2png('../CNN')
print(pdfExtract.pdf_extract())
