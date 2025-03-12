
'''
This script is used to add new PDFs to an existing encoded library.
For reliability and simplicity, it works by merging two libraries together,
creating a new combined library, then deleting the old one. This allows for 
many of the other functions in this program to be re-used.
'''

#####----- Import packages -----#####
import pickle # Critical - Saves and reads the Encoded Libraries.
import pandas as pd # Critical - Necessary for working with extracted PDF content and metadata.
import torch # Critical - Concatenates tensors.
import os # Critical - Base Python package needed for many functions.
from datetime import datetime # Optional - Makes a datetime string that is used to name files.

#####----- Merge Libraries -----#####

# This function takes two Encoded Libraries and merges them. It is called by the function loadLib in the
# Interface script, after the new library has been created.
def mergeLibs(loadedLibPath, libPath): #Takes the path of the active Encoded Library (loadedLibPath) and the path to the new library (libPath) that we want to merge with.

    from QuickSearch import pdfTable, libraryEmbeddings # Retrieve the variables within the active Encoded Library

    # Save the length of the pdfTable and libraryEmbeddings from the active Encoded Library.
    # These will be used later to double-check that the library merged properly.
    table1Len = pdfTable.shape[0]
    eLib1Len = libraryEmbeddings.shape[0]

    # Load the new Encoded Library.
    with open(libPath, 'rb') as f:
        pdfTable2, libraryEmbeddings2 = pickle.load(f)

    # Save the length of the pdfTable and libraryEmbeddings from the new Encoded Library.
    table2Len = pdfTable2.shape[0]
    eLib2Len = libraryEmbeddings2.shape[0]

    pdfTable = pd.concat([pdfTable, pdfTable2]) # Combine both pdfTables into one.
    libraryEmbeddings = torch.cat((libraryEmbeddings, libraryEmbeddings2), dim=0) # Combine both libraryEmbeddings tensors into one.

    pdfTable.reset_index(drop = True, inplace = True) # Reset the index of the new pdfTable.

    # Calculate the expected length of the combined data frame and tensor.
    expectedTableLen = table1Len + table2Len
    expectedLibLen = eLib1Len + eLib2Len

    # Before we start creating and deleting files, ensure that the expected lengths of the table and tensor match the actual lengths.
    if (pdfTable.shape[0] == expectedTableLen) & (libraryEmbeddings.shape[0] == expectedLibLen):
        
        print('Encoded Library lengths match expectations. Proceeding with join.')
        
        currentTime = datetime.now() # Get the current date and time
        formattedTime = currentTime.strftime("%Y%m%d%H%M%S") # Format the datetime object as a string with only numbers
        
        cwd = os.getcwd() # Get the current working directory.
        
        libName = os.path.join(cwd, 'Encoded Libraries', f'Combined_Library-{formattedTime}.pkl') # Create a path for saving the new Encoded Library 
    
        # Save the new Encoded Library.
        with open(libName, 'wb') as f:
            pickle.dump([pdfTable, libraryEmbeddings], f)

        print(f'Currently loaded library is here: {loadedLibPath}')
        print(f'Temporary library for merge is here: {libPath}')
        
        # Delete the old libraries now that they have been combined into one.
        for path in [loadedLibPath, libPath]:
            if os.path.exists(path):
                os.remove(path)
                print(f"{path} has been deleted.")
            else:
                print(f"{path} does not exist.")
                
        del pdfTable, pdfTable2, libraryEmbeddings, libraryEmbeddings2 # Delete these variables to get lots of memory back.
        
        return libName # Returns the path of the combined library.