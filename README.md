# project_pdf

## Introduction
This software was created using python native to read information from a medical request form in pdf format and write to existing fillable boxes. To accomplish this task, the software can do two functions, read and write. The read function is responsible for:
1)	 access all texts and fillable inputs
2)	process texts and fillable areas
3)	 Generate a json file with all information.
The write function is responsible for:
1)	Read a pre-defined json file linked to a pdf request
2)	Use the json file information to write directly on the pdf.
The next steps will show how each part is done and what is needed to run this software.

## Requirements:
To use this software, we require python v. 3.9+ (https://www.python.org/downloads/), the pdf should be in the same folder. You need to install pdfrw and pdfminer for the script to work.

## Argument:
•	-w to write to pdf.
•	 -r to read from pdf.
•	 -dV to change distance vertical.
•	 -dH to change distance horizontal.
•	 -file to input the file name to be processed.

## Libraries:
The project make use of two external packages:
•	 pdfminer (https://github.com/pdfminer/pdfminer.six) - this package is used to access the location of each letter in the pdf and the fillable boxes as well, the package display information such as x and y position and actual values, the actual letter or what is inside a fillable text box. 
•	pdfrw (https://github.com/pmaupin/pdfrw) – the second package is used to write from as specific json file to a specified pdf.
We use the json package to generate a json file which will contain the actual information we want.

## Software explanation:
The software write part is straightforward, so we are going to focus on the read part. The read part flow of action is as follow: 
1)	Create words out of the pdf letters.
2)	Generate sentences and text lines.
3)	Go through every fillable box and process meaningful information relative to it such as keywords, coordinate, and texts around the box.
4)	Process the list to try and clean duplicate lines of texts between fillable boxes, so it will be easier to point what label, or text, refer to what.

### 1- Word generation:

This first part of the software is done inside the method receives the pdf’s file name and uses pdfminer library to access every pdf letter inside it. Each letter contains its actual coordinate in a rectangle with x/y as bottom left and x1/y1 as right top. 

 ![1](https://user-images.githubusercontent.com/62361227/130631271-30121aa6-81c3-49e6-b2ac-3251e3737cc9.png)

The word and its coordinate are stored in a list, with element 0, 1, 2,3, and 4 being, respectively, x, y, x1, y1, word. The list is then returned to the main method.

### 2- Text line generation
The second part of this software is done in the “sentence ()” method which is called right before the word generating method “process ()” is returned, this is done to return a line of text instead of words to the main method. 
The method receives a spacing number and a list of words with coordinates. Since the list of words is ordered by its location the logic used in this method is straightforward, it goes word by word in a loop and check if the spacing between words is less than the specified amount “spacing”, like the following picture, if the space between words is higher than “spacing” it means the is not in the same text line.

 ![2](https://user-images.githubusercontent.com/62361227/130631401-3e8c7dac-49d1-45e8-ab61-009eae8970f0.png)
 
Going at the same logic as in the word processing method, this method stores the x/y from the first word and continuously store the x1/y1 from the following word, so it creates a rectangle as the previous image. The text line and its coordinate are stored in a list, with element 0, 1, 2,3, and 4 being, respectively, x, y, x1, y1, text line. The list is then returned to the “process ()” method.
### 3- Meaningful information.
The third part is relating to generating a document with meaningful information, those information’s are: 
•	The key word to access the fillable box – this is a text.
•	Meaningful sentences that are at the top, bottom, left and right of the fillable box – this is a list.
•	The likely sentence, or label, to be linked to a fillable box – this is a text.
•	The type of this fillable box, as “/Tx” meaning a text box, “/Btn” meaning everything relating to buttons – this is a string.
•	The value of the fillable box, for buttons “/Off” or “/Yes” for off or on respectively – this is a string.
•	Coordinates of the fillable box – this is a string.
•	Page index relating to the fillable box – this is a string.
The main method goes through every fillable box and calls the “meaningful ()” method, which is responsible to grab the sentences or text lines at the top, bottom, left, and right of a fillable box.
The meaningful method receives a list with all sentences, the fillable box coordinate, the fillable box type, and a spacing for horizontal and vertical situations. The method follows by going through every sentence inside the list of sentences and tries to compare the position of the sentence in relation to the position of the fillable box. The way it finds matches are as following for text boxes or buttons.
Text boxes
#### Horizontal:
1)	 First step is to check if they are vertically aligned, creating a position H symbolizing the median between y and y1 from the sentence, then checking if H is between y and y0 from the fillable box coordinate.
2)	Second step is to decide from left or right side:
a)	For the left side we check if the horizontal space is higher or equal than the difference between the x and x1 positions from the fillable box and text line respectively and see if the fillable box x1 is bigger than the sentence x, making sure we are on the right side of the pdf.
b)	For the right side we check if the horizontal space is higher or equal than the difference between x and x1 positions from the text line and fillable box respectively and see if the fillable sentence x0 is bigger than the box x1, making sure we are on the right side of the pdf.
#### Vertical:
1)	For the top we check if the difference between y and y1 from the sentence and fillable box respectively, seeing if that difference is less than or equal to the vertical spacing, and we make sure the fillable box y1 is lower than the sentence y, so it is in the right side of the pdf.
2)	For the top we check if the difference between y and y1 from the fillable box and sentence respectively, seeing if that difference is less than or equal to the vertical spacing, and we make sure the fillable box y is bigger than the sentence y1, so it is in the right side of the pdf.

Button:
The button logic is simpler, as it follows the same principle of going through every sentence, but buttons are straightforward as their labels are 95% horizontally aligned. The only difference is that, with buttons, the label could be a bit farther apart, if after going through the whole sentence list there is no text lines found, it will do another search doubling the horizontal distance, up to three loops.

After finishing the meaningful sentence, the “meaningful ()” method returns a list of texts, with four elements, left, top, right, and bottom, being respectively 0, 1, 2, 3.

### 4- Processing the list of elements.
After finishing going through every fillable box and storing its relevant information and making a list, we start by processing this list to try and shrink the amount of information inside it to focus on what could be the best option available, to do this we have the “reprocess ()” method which receives the list of fillable boxes with its data. There is also given a list of words that are commonly used at the bottom of a fillable box, as the following picture shows, and that is considered.
 
The logic around this processing is to create constrains and compare one element to all the others, one at a time ending up with a likely sentence to be stored. So, the reasoning used to store the likely sentence goes into this if/else order:
-	If there is only one sentence around the fillable box, choose it.
-	If there is a “:” and inside that text and the label is located at the left side, it has heavy chances to be the actual label, so choose it.
-	If one of the commonly used word list is at the bottom of the fillable box, use it.
Every time a sentence is chosen to be a “Likely sentence” that sentence will be add to a list called “doneList”. After processing and choosing likely sentences, we go through the list of fillable boxes again and make a match with the done sentences and the likely sentences to wipe out the texts around the fillable boxes that could be duplicates.

### 5- Generating a Json file and write.
After everything is done, we turn the list with every information into a json file to be used for writing to a pdf.
The write to pdf part is done in the main method, it reads the json file, run through the pdf accessing all fillable boxes and make matches using the “keyword” from the json file. After finding that match it used the update method from the pdfrw package to change the value of that fillable box, using the “value” form the json file creating a new pdf with the updated values inside it.

