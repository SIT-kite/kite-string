# -*- coding: utf-8 -*-
# @Time    : 2021/2
# @Author  : wanfengcxz, sunnysab
# @File    : document-parser.py
# @Description : Use pdfminer: pdf -> text
#             Use libreoffice: doc, docx, .. -> pdf
#             Use
# @Note    : The module will convert all documents into pdf format, and then use pdfminer to get text and its page num.
#            Installation reference: https://www.cnblogs.com/ruozhu/p/11190195.html
#            You must make sure the version of the libreoffice in the code is correct.

import os
from typing import List, Tuple


def split_file_name(file_name: str) -> (str, str):
    """ Split a file name into file name and the extension. """
    r = file_name.rfind('.')
    if r != -1:
        return file_name[:r], file_name[r + 1:]
    else:
        return file_name, ''


class DocExtractor:
    """
    Base class as a document extractor.
    """

    def __init__(self, path: str = ''):
        self._path = path


class PdfExtractor(DocExtractor):
    """
    A text extractor for pdf files.
    """

    def __init__(self, path: str = ''):
        super().__init__(path)

    def page2png(self, output_directory: str = None) -> List[str]:
        """ Convert pdf pages into png files. Return the png file list. """

        if not output_directory:
            name, _ = split_file_name(self._path)
            output_directory = f'{name}'
            if not os.path.exists(output_directory):
                os.mkdir(output_directory)

        from wand.image import Image
        pdf2img_obj = Image(filename=self._path, resolution=300)
        png_objs = pdf2img_obj.convert('png')  # Convert Pdf file into png sequence.

        output_files = []
        # Write the sequence to file.
        for index, img in enumerate(png_objs.sequence):
            current_page = Image(image=img)
            file_name = f'{output_directory}/{index}.png'

            with open(file_name, 'wb') as out_image:
                out_image.write(current_page.make_blob('png'))
            output_files.append(file_name)

        return output_files
        # End of function page2png.

    def text(self) -> List[Tuple[int, str]]:
        """ Convert pdf pages into a list of text strings. """

        from pdfminer.converter import PDFPageAggregator
        from pdfminer.layout import LTTextBoxHorizontal, LAParams
        from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
        from pdfminer.pdfparser import PDFParser, PDFDocument

        with open(self._path, 'rb') as pdf_file:
            doc = PDFDocument()

            parser = PDFParser(pdf_file)
            parser.set_document(doc)
            doc.set_parser(parser)
            doc.initialize()
            if not doc.is_extractable:
                raise Exception('The Pdf text extraction is not allowed when procesing ' + self._path)

            rsrcmgr = PDFResourceManager()
            laparams = LAParams()
            device = PDFPageAggregator(rsrcmgr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)

            result = []
            for index, page in enumerate(doc.get_pages()):
                interpreter.process_page(page)
                layout = device.get_result()

                current_page_text = ''.join([x.get_text().strip() for x in layout
                                             if isinstance(x, LTTextBoxHorizontal)])
                result.append((index, current_page_text))

        return result


class WordExtractor(DocExtractor):
    """ A text extractor for doc, docx and other document files. """

    def __init__(self, word_path=''):
        super().__init__(word_path)

    def show_path(self):
        return self._path

    @staticmethod
    def word2pdf(word_file: str, out_pdf_file: str):
        """ Convert word document to pdf file by libreoffice. """

        import subprocess
        command = f'libreoffice7.1 --headless --convert-to pdf {word_file} --outdir {out_pdf_file}'
        subprocess.run(command, shell=True)

    def convert_to_pdf(self, out_pdf_file: str):
        self.word2pdf(self._path, out_pdf_file)

    def convert2png(self, output_directory: str = None):
        """ Convert word document to png files. """

        # Firstly, convert doc file into pdf.
        _pdf_extractor = PdfExtractor(self._path)
        # Then, convert pdf to png files.
        # The file name rule is set by PdfExtractor
        _pdf_extractor.page2png(output_directory)

    def text(self) -> List[Tuple[int, str]]:
        """ Convert word document pages into a list of text strings. """

        # The method convert word document to pdf, and then use pdf extractor to read text.
        # It's not appropriate to read from word document directly, because it's hard to read the text with page number 
        # from the docx libraries in Python. 
        file_title, _ = split_file_name(self._path)
        file_name = file_title + '.pdf'

        self.convert_to_pdf(file_name)
        _pdf_extractor = PdfExtractor(file_name)
        return _pdf_extractor.text()


if __name__ == '__main__':
    test_word_file = WordExtractor('./上海应用技术大学关于开展2019年学习标兵、学习型寝室的评选通知.doc')
    test_word_file.convert2png()
    print(test_word_file.text())

    test_pdf_file = PdfExtractor('./上海应用技术大学疫情防控指南.pdf')
    test_pdf_file.page2png()
    print(test_pdf_file.text())
