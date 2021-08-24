import pdfrw
from argparse import ArgumentParser
import json
import numpy as np

# PDFMINER
from pdfminer.layout import LAParams, LTChar, LTText, LTAnno
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator

data = {}


def parserCLI():
    """command arguments"""
    parser = ArgumentParser(description='Write or store pdf information.')
    parser.add_argument('-w', dest='loc', action='store_const', const=1,
                        help='test')
    parser.add_argument('-file', dest='file', action='store', required=True,
                        type=str,
                        help='test')
    parser.add_argument('-dV', dest='distVertical', action='store', required=False,
                        type=str, default=10,
                        help='Vertical Distance, 5 as default')
    parser.add_argument('-dH', dest='distHorizontal', action='store', required=False,
                        type=str, default=6,
                        help='Horizontal distance, 5 as default')
    parser.add_argument('-r', dest='loc', action='store_const', const=0,
                        help='test')

    return parser.parse_args()


def sentence(spacing, wordList):
    sentenceListPages = []
    x0, y0, x1, y1, text = -1, -1, -1, -1, ''

    for pages in range(len(wordList)):
        sentenceList = []
        length = len(wordList[pages]) - 1

        for words in range(length):
            if wordList[pages][words][4] == 'o':
                sentence = [x0, y0, x1, y1, text]
                sentenceList.append(sentence)
                x0, y0, x1, y1, text = -1, -1, -1, -1, ''
            else:
                # Set up text and coordinates.
                if x0 == -1:
                    x0, y0 = wordList[pages][words][0], wordList[pages][words][1]
                x1, y1 = wordList[pages][words][2], wordList[pages][words][3]
                text += ' ' + wordList[pages][words][4]
                # Check if current word and next word are in Y coordinate.
                if (wordList[pages][words][1] + 1) >= wordList[pages][words + 1][1] >= (wordList[pages][words][1] - 1):
                    # if spacing is bigger, reset.
                    if (wordList[pages][words + 1][0] - wordList[pages][words][2]) > spacing or \
                            wordList[pages][words + 1][0] < wordList[pages][words][2]:
                        sentence = [x0, y0, x1, y1, text]
                        sentenceList.append(sentence)
                        x0, y0, x1, y1, text = -1, -1, -1, -1, ''

                else:
                    sentence = [x0, y0, x1, y1, text]
                    sentenceList.append(sentence)
                    x0, y0, x1, y1, text = -1, -1, -1, -1, ''

        sentenceListPages.append(sentenceList)
    return sentenceListPages


def process(fileName):
    fp = open(fileName, 'rb')
    manager = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(manager, laparams=laparams)
    interpreter = PDFPageInterpreter(manager, device)
    pages = PDFPage.get_pages(fp)
    # Word per page.
    wordPages = []

    for page in pages:
        wordList = []
        print('--- Processing ---')
        interpreter.process_page(page)
        layout = device.get_result()
        x0, y0, x1, y1, text = -1, -1, -1, -1, ''
        for textbox in layout:
            if isinstance(textbox, LTText):
                for line in textbox:
                    for char in line:
                        # If the char is a line-break or an empty space, the word is complete
                        if isinstance(char, LTAnno) or char.get_text() == ' ' or char.get_text() == '_':
                            if x0 != -1:
                                word = [x0, y0, x1, y1, text]
                                wordList.append(word)
                            x0, y0, x1, y1, text = -1, -1, -1, -1, ''
                        elif isinstance(char, LTChar):
                            text += char.get_text()
                            if x0 == -1:
                                x0, y0 = char.bbox[0], char.bbox[1]
                            x1, y1 = char.bbox[2], char.bbox[3]

        # If the last symbol in the PDF was neither an empty space nor a LTAnno, print the word here
        if x0 != -1:
            word = [x0, y0, x1, y1, text]
            wordList.append(word)

        # Sort by Y coordinate
        wordList.sort(key=lambda choice: choice[1])
        wordPages.append(wordList)

    # Receive List of sentences per page.
    sentences = sentence(4, wordPages)
    return sentences


def meaningful(senteceList, coord, type, spacingH, spacingV):
    left, up, right, down = '', '', '', ''
    y = np.arange(int(float(coord[0])), int(float(coord[2])))

    if type == '/Tx':
        for sentence in senteceList:
            medianCoord = float(sentence[1]) - (float(sentence[1]) - float(sentence[3]))
            y1 = np.arange(int(float(sentence[0])), int(float(sentence[2])))
            y0 = set(y)
            if float(coord[3]) > medianCoord > float(coord[1]):
                # Catching left side.
                if (float(coord[0]) - float(sentence[2])) <= spacingH and float(coord[2]) > float(sentence[0]):
                    left += ' ' + sentence[4]
                # Catching right side.
                elif (float(sentence[0]) - float(coord[2])) < spacingH and float(coord[2]) < float(sentence[0]):
                    right += ' ' + sentence[4]

            # Checking if sentence is above text box by looking if their coord intersect.

            # Catching up side. If box coordinate y1 minus sentence coordinate y0 < the spacing AND box coordinate\
            # is less than sentence, we have a match.
            elif (float(sentence[1]) - float(coord[3])) <= spacingV and float(coord[3]) < float(sentence[3]) and \
                    y0.intersection(y1):
                up += ' ' + sentence[4]
            # Catching down side.
            elif (float(coord[1]) - float(sentence[3])) <= spacingV and float(coord[1]) > float(sentence[1]) and \
                    y0.intersection(y1):
                down += ' ' + sentence[4]
    else:
        # Double horizontal distance until it finds some text horizontally oriented, or run three times.
        rounds = 1
        while True:
            for sentence in senteceList:
                medianCoord = float(sentence[3]) - ((float(sentence[3]) - float(sentence[1])) / 2)
                if float(coord[3]) >= medianCoord >= float(coord[1]):
                    if (float(sentence[0]) - float(coord[2])) <= spacingH and float(coord[2]) < float(sentence[0]):
                        right = sentence[4]
                    elif (float(coord[0]) - float(sentence[2])) <= spacingH and float(sentence[2]) <= float(coord[0]):
                        left = sentence[4]
            if left != '' or right != '' or rounds == 3:
                break
            else:
                rounds += 1
                spacingH *= 2

    sentences = [left, up, right, down]
    return sentences


def reprocess(keyList):
    # Firs process the likelySentence.
    result = keyList
    left, top, right, bot = 0, 1, 2, 3
    doneList = []
    doneListCB = []
    listForBottom = ['Signature', 'Date', 'Day', 'Month', 'Year', 'Physician Name']
    # cx = [2] - [0]
    # cy = [3] - [1]
    # medCoord = [cx, cy]
    for item in result:
        counter = 0
        ind = 0

        # Check All sides.
        for side in range(4):
            if item['meaningfulSentence'][side] != '':
                ind = side
                counter += 1

        # Text box processing
        if item['type'] == '/Tx':

            # If there is only one meaningful sentence, that would be the likely one.
            if counter == 1:
                item['likelySentence'] = item['meaningfulSentence'][ind]
                doneList.append(item['meaningfulSentence'][ind])

            # If there is a : at the left side label it will be probably that sentence.
            elif ':' in item['meaningfulSentence'][left]:
                item['likelySentence'] = item['meaningfulSentence'][left]
                doneList.append(item['meaningfulSentence'][left])
                continue

            else:
                # Check the list for bottom, if it finds anything at the bottom side of the item inside the list,
                # that would be the likely Sentence
                botOk = False
                for i in range(len(listForBottom)):
                    if listForBottom[i] in item['meaningfulSentence'][bot]:
                        item['likelySentence'] = item['meaningfulSentence'][bot]
                        doneList.append(item['meaningfulSentence'][bot])
                        botOk = True
                if botOk:
                    continue
        # Checkbox or other checking marks
        else:
            item['likelySentence'] = item['meaningfulSentence'][right]
            doneListCB.append(item['meaningfulSentence'][right])

    for item in result:
        if item['type'] == '/Tx':
            for side in range(4):
                if item['meaningfulSentence'][side] in doneList and \
                        item['meaningfulSentence'][side] != item['likelySentence']:
                    item['meaningfulSentence'][side] = ''
        else:
            for side in range(4):
                if item['meaningfulSentence'][side] in doneListCB and \
                        item['meaningfulSentence'][side] != item['likelySentence']:
                    item['meaningfulSentence'][side] = ''

    # Cleaning json file.
    for item in result:
        if item['type'] == '/Tx':
            if item['value'] == '()' or item['value'] is None:
                item['value'] = ''
        else:
            if item['value'] is None:
                item['value'] = 'Off'
            else:
                item['value'] = 'Yes'

    return result


if __name__ == '__main__':
    args = parserCLI()

    # Open PDF
    template = pdfrw.PdfReader(args.file)

    keyList = []

    # Define spacing for editable fields.
    spacingFieldsH = args.distHorizontal
    spacingFieldsV = args.distVertical
    # Read pdf to generate JSON file, -r option
    if args.loc == 0:
        # Catch sentences and coordinates.
        sentencesPages = process(args.file)
        pageIndex = 0
        for page in template.pages:
            annotations = page['/Annots']
            sentences = sentencesPages[pageIndex]
            for annot in annotations:
                # creating Dictionary
                goodSentences = meaningful(sentences, annot.Rect, annot.FT, spacingFieldsH, spacingFieldsV)
                keys = {'keyWord': annot.T.to_unicode(), 'meaningfulSentence': goodSentences, 'likelySentence': '',
                        'type': annot.FT, 'value': annot.V, 'coord': annot.Rect,
                        'pageIndex': pageIndex}
                keyList.append(keys)
            pageIndex += 1
        # Reprocessing to input patient/doc and get the LikelySentence.
        updatedKeyList = reprocess(keyList)
        # Generating JSON file
        with open('jsonFileToFill.json', 'w') as f:
            json.dump(updatedKeyList, f, indent=2)
        f.close()

    # Write to and generate pdf, -w option
    elif args.loc == 1:
        index = 0

        with open('jsonFileToFill.json') as f:
            jsonData = json.load(f)

        # Go from page to page
        for page in template.pages:
            annotations = page['/Annots']
            for annot in annotations:
                if annot['/Subtype'] == '/Widget':
                    annot.update(pdfrw.PdfDict(V=pdfrw.PdfName(jsonData[index]['value'])))
                    index += 1

        # Save changes and write pdf
        template.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))
        completedFileName = 'Updated_' + args.file
        pdfrw.PdfWriter().write(completedFileName, template)

    else:
        print('Contact developer')
