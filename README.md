# Factoid Finder

Local semantic search for PDF documents, designed for ease of use and compatibility. No GPU required.

Tested with Python 3.12 on Windows 11.

## Introduction

The Factoid Finder was created to help identify and retrieve relevant information from collections of PDF documents. Example uses include finding small pieces of obscure information (factoids) within PDFs based on a search query and returning their location within the document, creating a short list of sections within documents that discuss a specific topic, and so on. We hope that you find this tool useful.

## Requirements

This program was designed to work on a broad range of hardware with minimal external dependencies. Requirements are:

- Python 3.12 and required packages, see the full list in Setup/requirements.txt
- A modern web browser that is capable of running a Gradio Interface (includes Chrome, Edge, Firefox, etc.)

## Quick Start

1. Install program requirements.
2. Clone this directory or download and extract the Factoid-Finder.zip folder to your computer.
3. Run the script Interface.py in an environment that has the required dependencies installed.
4. Create a new encoded PDF library or load an existing one.
5. Begin searching PDFs for relevant information by entering a query.

## Installation

1. **Install Python 3.12.**
2. **Save and unzip Factoid-Finder.zip to its own folder on your computer.** The name of this folder can be anything, but all of the files from the Factoid-Finder.zip archive must be contained within this one folder.
3. **Create and activate a virtual environment, install packages in Setup/requirements.txt, then run the script Interface.py.** Optionally, the batch file Run_Factoid_Finder.bat can be used to automate installing and opening of the program. Simply modify line 7 to point to your Python 3.12 executable if it is not saved at the default location: 'C:\\Program Files\\Python312\\python.exe'.
4. **The program will open in your default web browser.** See the next section ‘Using the Factoid Finder’ for details.

## Using the Factoid Finder
**Important information:**

- **Search Tips: The quality of search results is much higher for precise and specific questions than it is for keywords alone.**
- **After extracting text from a collection of PDFs, the Encoded Library is saved within the program’s main folder in a folder titled ‘Encoded Libraries’.** Loading this file is much faster than extracting text and creating the library anew. The ‘Current Library’ box will show where the library is saved (after it has been created).

The Factoid-Finder allows for text to be extracted from machine-readable PDFs, after which it can be searched.

To open this program, run the script Interface.py in an environment with the requirements installed or double-click ‘_Run_Factoid_Finder.bat_’ in the Factoid Finder folder. If the batch file is used, the black and white Command Prompt window must be left open for the program to run. After loading, the program will open to this view in your default web browser:  
![Image](https://github.com/Reillume/Factoid-Finder/blob/main/Setup/Picture1.png)
You will need to either create a new Encoded Library from a folder of PDFs or load an Encoded Library you have already created. Encoded libraries can be created by selecting the ‘Create New’ option and then entering a path to a folder with PDFs. This will generate a .pkl file in the ‘Encoded Libraries’ folder within the Factoid Finder’s main folder. Once an Encoded Library has been created (the .pkl file), you can load it directly in future by selecting ‘Load Existing’ and pasting the path to the .pkl file (including the file name itself).

_Note:_ Loading an Encoded Library file (.pkl) that you created previously is much faster than extracting text and creating the library anew.
![Image](https://github.com/Reillume/Factoid-Finder/blob/main/Setup/Picture2.png)
It is recommended that PDFs be saved in their own folder, somewhere they won’t be moved. If PDFs are moved after the Encoded Library has been created, the links to them that are provided in the search results will no longer work.

After entering a valid path, click ‘Start’ to create or load the library. Creating an Encoded Library may take a few minutes to a few hours, depending on the size of the PDF collection and computer hardware. Once the process finishes, a search bar will appear and queries can now be entered.

To conduct a search query, enter a question or phrase for which you are seeking information within the suite of PDFs and press “Search”. The number of search results that are returned can be modified in the “Advanced Settings” box (more settings may be added in future). Search results are displayed in order of decreasing relevance.

Search Tip: The quality of search results is much higher for precise and specific _questions_. Searches based only on keywords will generally not produce satisfactory results. For example, the search ‘wildfire salmon’ produces almost nothing of relevance, while the more specific question ‘how wildfire affects salmon’ returns useful results (provided this information is in the current library).

## Advisories

1. **User Responsibility:** Users are responsible for verifying the accuracy and relevance of the search results. While we hope the software is a useful tool to support efficient information retrieval, it is not a comprehensive or definitive source of truth.
2. **AI Limitations:** This software uses AI language models. Any biases in the training data and models remain present in this software.
3. **Compatibility:** The software has been tested on specific versions of Python and operating systems. Compatibility with other versions or systems is not guaranteed.
4. **Transferability:** Encoded libraries will only work properly on the computer on which they were created as they include file paths which are specific to that computer. If PDF files are moved after the Encoded Library was created, links to the PDF files in the Encoded Library will not work.

## Licenses

This project is licensed under the terms of the GNU Affero General Public License (AGPL) v3.0. See the LICENSE folder for details.

## Citations

This project uses several third-party libraries:

- PyMuPDF - Licensed under the AGPL v3.0
- PyTorch - Licensed under the BSD 3-Clause License
- Sentence Transformers - Licensed under the Apache License 2.0
- Transformers - Licensed under the Apache License 2.0
- Gradio - Licensed under the Apache License 2.0
- tqdm - Licensed under the MIT License
- Phi-3.5-Mini-Instruct – Licensed under the MIT License
- MS Marco Distilbert Dot-v5 – Licensed under the Apache License 2.0

For more information on these libraries, please visit their respective GitHub pages.
