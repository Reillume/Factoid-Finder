'''
This script is used to extract text from machine-readable PDFs and
encode them using the Small Language Models that perform semantic
search. It currently does not incorporate OCR, though adding this
in should be relatively straightforward with PyMuPDF and Tesseract.
'''
#####----- Import Packages -----#####
import os # Critical - Base Python package needed for many functions.
import pandas as pd # Critical - Necessary for working with extracted PDF content and metadata.
import re # Critical - Base Python package used to modify strings.
from sentence_transformers import SentenceTransformer, SimilarityFunction # Critical - Runs Small Language Models used for semantic search.
import pickle # Critical - Saves and reads the Encoded Libraries.
import pymupdf # Optional - Reads the contents of PDFs. Note: If the AGPL licence is problematic, this package can be easily substituted for a different PDF reading package. 
import tqdm # Optional - Provides progress tracking.
import datetime # Optional - Makes a datetime string that is used to name files.

# Raise the current working directory to the main program folder, if it is currently set to 'Scripts'.
if os.getcwd()[-7:] == 'Scripts':
    os.chdir("..")

#####----- Identify PDFs -----#####

#This function creates a list of file paths to all of the PDFs in the folder the user specifies.
def makeList(uPDF):
    global fileList
    global pdfLog

    # Initialize blank variables
    pdfLog = ''
    fileList = []
    
    # Specify the path to the folder of PDFs we want to read in
    pdfFolder = uPDF  # User Input

    # Identify all the PDFs in the specified folder and its subdirectories, then add them to a list.
    for root, dirs, files in os.walk(pdfFolder):
        for file in files:
            if file.endswith('.pdf'): # If the file is a PDF...
                fileList.append(os.path.join(root, file)) # Save it to the list.

    if len(fileList) == 0: # If no PDFs are found...
        raise IndexError('PDF Table cannot be blank.') # Raise an error.
        
    # Print the list of PDF file names to the Command Prompt window to help track progress.
    print("PDF files found:")
    for file in fileList:
        print(file)

#####----- Extract Text -----#####

# This function will extract all of the readable text and metadata we need from the PDFs in fileList.
# It is called within a for loop in the createLibrary function that is defined below.
def extractText(file): # Takes the file path of a single PDF as an argument.
    pdf = pymupdf.open(file) # Open a pdf
    metadata = pdf.metadata # Extract metadata if available

    for i, page in enumerate(pdf): # Iterate through the document's pages. Count the pages as it goes.
        text = page.get_text() # Extract the text content of the current page.
        
        try:
            pageNum = str(page.get_label()) # Attempts to get the page label...
            if not pageNum:  #But if page label is blank or None...
                pageNum = str(i + 1)  # Label the page number manually.
        except IndexError: # If getting the label fails completely...
            pageNum = str(i + 1)  # Label the page manually.
        
        # Clean up the extracted text by removing new lines that are unlikely to denote the end of a paragraph.
        cText = re.sub(r'(-)\n', '', text) # Concatenate hyphenated words and remove the new line.
        cText = re.sub(r'(?<!\.)\n', ' ', cText) # Remove any new lines that aren't preceded by a period.
        cText = re.sub(r'(?<=e\.g\.)\n', ' ', cText) # Remove any new lines that are preceded by e.g.
        cText = re.sub(r'(?<=i\.e\.)\n', ' ', cText) # Remove any new lines that are preceded by i.e.
        cText = re.sub(r'(?<=et al\.)\n', ' ', cText) # Remove any new lines that are preceded by et al.
        cText = re.sub(r'(?<=p\.)\n', ' ', cText) # Remove any new lines that are preceded by p.
        pageNum = re.sub(r'<.*?>', '', pageNum) # Remove likely html labels from page numbers.

        #Append the metadata and text content to several lists (will be made into a dataframe later).
        File_Name.append(os.path.basename(file)) # Append the file name of the PDF.
        File_Path.append(file) # Append the full path of the PDF.
        Page.append(pageNum) # Append the page number of the current content.
        Content.append(cText) # Append the content of the current page.
        Title.append(metadata.get('title')) # Append the title of the PDF (if available).
        Author.append(metadata.get('author')) # Append the authors of the PDF (if available).
        Subject.append(metadata.get('subject')) # Append the subjects of the PDF (if available).
        Keywords.append(metadata.get('keywords')) # Append the keywords of the PDF (if available).
    
    pdf.close() # Close the PDF

# This function will break apart any paragraphs longer than the maximum specified length.
# Paragraphs will be split to the closest period where possible to preserve meaning as much as possible.
# It is used to make sure that paragraphs do not exceed the length that the SLMs can read. 
def fixChunks(text, max_chunk_size): # Arguments are content (a string from a PDF) and the maximum number of characters to allow.
    
    #Initialize variables
    chunks = []
    start = 0

    # The While loop is used to run through the full input string and split it into chunks. It creates chunks of text that do not
    # exceed the maximum specified length by using a moving window.
    while start < len(text):
        # Set 'end' to be the maximum number of characters allowed from the start character (chunk size) or full length of the string if the string is shorter than the max length.
        end = min(start + max_chunk_size, len(text)) 
        chunk = f"{text[start:end]}" # Create a chunk that is no bigger than the maximum number of characters.
        
        split_point = chunk.rfind('. ') # Find the last period followed by a space in the string. This is likely the end of a sentence.

        # If no period followed by a space is found, try splitting at the period itself.
        if split_point == -1:
            split_point = chunk.rfind('.')

        # If no period is found at all, split based on the maximum character limit as a last resort.
        if split_point == -1:
             split_point = max_chunk_size
        
        # Adjust the end point to the split point.
        end = start + split_point + 1
        
        # Add the newly identified chunk to a list.
        chunks.append(text[start:end].strip())
        
        # Move the start point to the end of the current chunk, moving the window forward to identify the next chunk.
        start = end
    
    return chunks # Returns a list of chunks that don't exceed the maximum character limit.

# This is the main function used to extract text from PDFs and generate the Encoded Library.
# The only argument it takes is a boolean as to whether the library that is being created will be merged with another library.
def createLibrary(mergeL):    
    global File_Name, File_Path, Title, Author, Subject, Keywords, Page, Content, libName, pdfLog
    
    #Initialize several variables, one for each of our columns in the table we are creating
    File_Name = [] # From file path
    File_Path = [] 
    Title = [] # From metadata
    Author = [] # From metadata
    Subject = [] # From metadata
    Keywords = [] # From metadata
    Page = [] # From document or generated automatically
    Content = [] # From document
    extractErrCount = 0 # A count of the number of errors that occur when extracting text from PDFs. Displayed in the log file.
    warnFlag = False # A boolean that tracks whether any non-critical errors have occurred.
    
    # Loop over all of the PDFs in the file list and extract the text from them.
    for file in fileList:
        try:
            extractText(file) # Extracts text and metadata from PDFs.
        except: # Sometimes a PDF will be corrupted or unreadable. Rather than stopping the whole process, this will track the problematic PDF so the user can be informed.
            print(f"Error: Could not extract text from {file}")
            pdfLog += f"An error occurred while extracting text from {file}. \n" # Save a simple error message for the log file.
            extractErrCount += 1 # Add to the error count for the log file.
    
    # Combine all of the lists into a dataframe
    pdfTable = pd.DataFrame(list(zip(File_Name, File_Path, Title, Author, Subject, Keywords, Page, Content)), 
                                     columns = ['File_Name', 'File_Path', 'Title', 'Author', 'Subject', 'Keywords', 'Page', 'Content'])
    
    pdfTable['Content'] = pdfTable['Content'].str.split('\n') # Split the text content of each page roughly into paragraphs (as determined by new lines)
    pdfTable = pdfTable.explode('Content').reset_index(drop=True) # Give each paragraph it's own record
    pdfTable['Content'] = pdfTable['Content'].str.strip() # Clean the chunks of text
    
    # This loop will check that each document chunk (paragraph) is not larger than the maximum size, or split it if it is.
    # The maximum size should be well less than 500 tokens for the current SLMs and take into account the minimum chunk size that might be added back on.
    for i in range(len(pdfTable)):
        
        if len(pdfTable.at[i, 'Content']) > 1500:  # If cell content is greater than 1500 characters...
            chunks = fixChunks(pdfTable.at[i, 'Content'], max_chunk_size = 1500)  # Split chunks to meet maximum length and...
            pdfTable.at[i, 'Content'] = chunks  # Replace cell content with list of appropriately sized strings.
            pdfTable.at[i, 'Split'] = 1 # Add a flag to that record so we know it was split unnaturally.
    
    pdfTable = pdfTable.explode('Content').reset_index(drop=True) #Split the lists generated by the fixChunks function so each paragraph is its own record.
    
    # Having split everything out based on new lines and other methods, there is a chance some of the chunks may be too small.
    # The following code will join very small chunks either back into the previous chunk or to the following chunk.
    for i in range(len(pdfTable)): 
    
        if len(pdfTable.at[i, 'Content']) < 280 and pdfTable.at[i, 'Content'] != '': # If cell content is less than 280 characters but not blank...

            # If the content was split from the preceding chunk because it exceeded the maximum character limit and the previous cell is not blank... 
            if pdfTable.at[i, 'Split'] == 1 and pdfTable.at[i-1, 'Content'] != '': 
                pdfTable.at[i-1, 'Content'] = f"{pdfTable.at[i-1, 'Content']} {pdfTable.at[i, 'Content']}" # Concatenate the content back into the previous cell.
                pdfTable.at[i, 'Content'] = '' # Set the content of the cell that we added to the previous cell to now be blank (to avoid duplication).
    
            else: # If the content was not split from another cell though...
                try:
                    # Concatenate the content with the following cell as long it's from the same document, or if this is not possible...
                    if pdfTable.at[i, 'File_Name'] == pdfTable.at[i+1, 'File_Name']: 
                        pdfTable.at[i+1, 'Content'] = f"{pdfTable.at[i, 'Content']} {pdfTable.at[i+1, 'Content']}" 
                        pdfTable.at[i, 'Content'] = '' # Set the content of the cell that we added to the previous cell to now be blank (to avoid duplication).
                        pdfTable.at[i+1, 'Split'] = None # Clear the split column if something is there to prevent a logic error.
                        
                except: 
                    # Merge the content back into the preceding cell if i+1 is out of bounds or part of another document.
                    pdfTable.at[i-1, 'Content'] = f"{pdfTable.at[i-1, 'Content']} {pdfTable.at[i, 'Content']}" #Concatenate the content with the previous cell
                    pdfTable.at[i, 'Content'] = '' # Set the content of the cell that we added to the previous cell to now be blank (to avoid duplication).

    # Clean the content once more in case the concatenating introduced weird strings.
    pdfTable['Content'] = pdfTable['Content'].str.strip()
    pdfTable.replace('', pd.NA, inplace=True)
    
    # Identify if there are any PDFs from which no text was extracted.
    noTextCount = pdfTable.groupby('File_Path')['Content'].count()
    noTextCount = noTextCount[noTextCount == 0]

    # If applicable, add a message to the Command Prompt window and log file informing the user that no text was extracted from this PDF.
    for File_Path in noTextCount.index:
        print(f'Warning: No text was found in {File_Path}. Is it machine-readable?')
        pdfLog += f'Warning: No text was found in {File_Path}. Is it machine-readable? \n'
    
    # Clean up the pdfTable one last time.
    pdfTable.sort_values(by='File_Name', inplace=True) # Sort by file name.
    pdfTable.dropna(subset=['Content'], inplace=True) # Drop rows with no content/chunks.
    pdfTable.drop_duplicates(subset=['Title', 'Author', 'Subject', 'Keywords', 'Page', 'Content'], inplace=True) # Remove any rows that appear to be duplicate PDFs.
    pdfTable.reset_index(drop=True, inplace=True) # Reset the index of the table.
    
    if pdfTable.shape[0] == 0: # If the pdfTable is empty...
        raise IndexError('PDF Table cannot be blank.') # Raise an error.

    # The following code checks for duplicates in another library if we are going to merge this library into it later.
    if mergeL == True: # If we are merging this table with another library...
        from QuickSearch import pdfTable as pdfTable0 # Import the other library (currently loaded).

        # Make a column to identify the source of all the records.
        pdfTable0['Source'] = 'pdfTable0'
        pdfTable['Source'] = 'pdfTable'

        # Combine the two libraries and drop from the current library any matching records that are identified in the existing library.
        pdfTable = pd.concat([pdfTable0, pdfTable]).drop_duplicates(subset=['Title', 'Author', 'Subject', 'Keywords', 'Page', 'Content'])
        
        # Remove the existing library so we are only left with records that contain new content in our current library.
        # This way there will be no duplicates when we merge our new library with the existing one, and we don't waste effort encoding duplicate content.
        pdfTable = pdfTable[pdfTable['Source'] == 'pdfTable'] 
        
        # Drop the Source column and remove the old library to get memory back.
        pdfTable.drop(columns=['Source'], inplace=True)
        pdfTable0.drop(columns=['Source'], inplace=True)
        pdfTable.reset_index(drop=True, inplace=True)
        del pdfTable0 #Remove this now that we no longer need it.

    # After removing duplicates, raise an error message if no new content was left.
    if pdfTable.shape[0] == 0:
        raise ValueError('No new PDFs found.')
    
    #####----- Encode text blocks -----#####
    # Load the model we are using for semantic search, then use it to encode the 'content' column of the pdfTable. 
    embedder = SentenceTransformer('sentence-transformers/msmarco-distilbert-dot-v5')
    libraryEmbeddings = embedder.encode(pdfTable['Content'].tolist(), convert_to_tensor=True, show_progress_bar=True, 
                                        tqdm_kwargs={'desc': 'Encoding text blocks', 
                                                     'bar_format': '{l_bar}{bar:20}{r_bar}{bar:-10b}',
                                                     'total': len(pdfTable['Content']) # Display a progress bar while encoding the text.
        })
    
    # Get the current date and time.
    currentTime = datetime.datetime.now()

    # Format the datetime object as a string with only numbers
    formattedTime = currentTime.strftime("%Y%m%d%H%M%S")

    cwd = os.getcwd() # Get the current working directory.
    
    libName = os.path.join(cwd, 'Encoded Libraries', f'Encoded_Library-{formattedTime}.pkl') # Create a path at which the Encoded Library will be saved.

    # Save the Encoded Library as a Pickle file.
    with open(libName, 'wb') as f:
        pickle.dump([pdfTable, libraryEmbeddings], f)
        
    #####----- Generate a Log -----#####
    logPath = os.path.join('Logs', f'{formattedTime} - PDF Extraction Log.txt') # Create a path at which the log will be saved.
    totalPDFs = len(fileList) # Count the total number of PDFs that were detected in the folder the user specified.
    pdfNoText = len(noTextCount) # Count the number of PDFs from which no text could be extracted.
    pdfsLib = pdfTable['File_Path'].nunique() # Count the number of PDFs that were added to the library in the end (errors and duplicates removed).

    # Generate the content of the log.
    logFull = f"""------------------ Summary of PDF Text Extraction ------------------
Total number of PDFs located: {totalPDFs}
Number of PDFs from which no text could be extracted: {pdfNoText}
Number of PDFs which caused unexpected errors: {extractErrCount}
Total number of PDFs successfully added to library (duplicates removed): {pdfsLib}

The encoded library is saved here: {libName}

Errors:

{pdfLog}"""

    # Save the log.
    with open(logPath, 'w') as file:
        file.write(logFull)

    # This boolean is used to pass a warning message to the user in the GUI if any PDFs were blank or some other error occured.
    if pdfNoText + extractErrCount != 0:
        warnFlag = True
    
    del pdfTable, libraryEmbeddings # Remove these potentially large variables to save memory.
    return libName, warnFlag, logPath # Return the path to the newly created Encoded Library (.pkl file), the warning flag, and the path to where the log is saved.