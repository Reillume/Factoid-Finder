'''
This script is the master script from which all other scripts are called. It also controls the graphical user interface
from which user's can create and search PDF libraries. The script is built around the Python package Gradio (v5.6).
Functions to be used by Gradio are defined in the first half of the script, while the GUI itself is defined in the
second half. If using the program without the included .bat file, this is the script that should be run.
'''

#####----- Prepare Environment -----#####
print('Loading program...') # Progress message for the Command Prompt window.
import QuickSearch # Critical - Python script that handles queries and information retrieval. 
import ExtractPDF # Critical - Python script that handles PDF text extraction and encoding.
import os # Critical - Base Python package needed for many functions.
from tkinter import filedialog # Optional - See above.
import MergeLibraries # Optional - Python script that can add additional PDFs to an existing library. Only used by the addPDFs button.
import gradio as gr # Optional - Package that provides the GUI from which all the functions below are run.
import tkinter as tk # Optional - Base Python package that is used to open a Select Folder window. Only used by the addPDFs button.

# If the working directory is currently the scripts folder, change it to be one level higher (to the main Factoid Finder folder).
if os.getcwd()[-7:] == 'Scripts':
    os.chdir("..")

# Loads the AI models used for semantic search and cross-encoding when the program is started.
print('Initializing AI models...') # Progress message for the Command Prompt window.
try: QuickSearch.initializeEmbedders() # Attempts to load the SLMs used for encoding and search.
except: print('An error occurred while initializing the search AIs.') # If an error occurs, displays a message in the Command Prompt window.


#####----- Define Functions -----#####

# This block updates the GUI based on whether the user select's 'Create New' or 'Load Existing' in the library selection radio buttons.
# It will then make a textbox visible next to the radio buttons with informative placeholders based on the user's selection.
def updateLibPath(choice): # Input comes from the variable 'radio'.

    #Updates the Start button to be visible when a selection is made in the radio buttons.
    updateStartBtn = gr.update(visible = True)
    
    if choice == 'Create New': # If the user chose 'Create New' on the radio buttons...

        # Updates the library path textbox to display information that is relevant to the choice made.
        updateLibPathBox = gr.update(label= "Paste the path to the folder containing your PDFs.", # Update label of the library path textbox to the specified value...
                                     placeholder = r"Path\to\PDF\folder", # Update placeholder of the textbox...
                                     value = "", # Clear the textbox...
                                     visible = True) # Make the textbox visible...

    # See above for details of how this if statement works.
    if choice == 'Load Existing': 

        updateLibPathBox = gr.update(label="Paste the path to your .pkl file (found in the same folder as this application).",
                                     placeholder = r"Path\to\.pkl\file", 
                                     value = "", 
                                     visible = True)
        
    # Return the variables that specify the updates to make to the GUI.
    return updateLibPathBox, updateStartBtn 
    
'''
The following function will perform all of the steps necessary to either create a new encoded library or load an existing one.
The arguments it receives are libPath, which specifies the path to either the folder with PDFs to encode or
the path to the Pickle file that contains an existing encoded library. This path is received from the libPath textbox.
The argument radio is received from the radio buttons where the user chooses to either make a new library or use an existing
one. The argument mergeL is received from expandLib function that is defined below, if the user has chosen to add PDFs to an
existing library. A basic progress bar that displays the results of the encoding process is included as well.
'''
def loadLib(libPath, radio, mergeL=False, progress=gr.Progress(track_tqdm=True)):
    
    global loadedLibPath # This variable is used later to save the path to the active encoded library.

    # If the user enters a blank path, it will halt the function and make no changes to the GUI.
    if libPath == "":

        gr.Info('No path was specified.', duration = 0.6) # Display a message informing the user as to why nothing is happening.
        
        # Since Gradio demands outputs, the following line specifies outputs that make no changes to the GUI.
        return gr.update(equal_height=True), gr.update(open=False), gr.update(show_label=False), gr.update(visible=True), gr.update(scale=0), gr.update(interactive=False)

    # The else statement will run as long as a string is provided.
    else:
        
        # Removes quote marks from the start and end of the string if they are present. This allows for Windows 11's Copy as Path functionality to be used efficiently.
        if libPath[0] == "\"" and libPath[-1] == "\"":
            libPath = libPath[1:-1]

        # If the user selected 'Create New' with the radio buttons...
        if radio == 'Create New':
            if os.path.isdir(libPath) == False: # Check to make sure that the path points to a folder and exists
                raise gr.Error("The specified folder could not be located.") # If it doesn't, raise an error.
                
            gr.Info("Creating library. This can take several hours.") # Display a progress message to the user in the GUI.
            print("Creating library. This can take several hours.") # Displays a progress message in the Command Prompt window.
            
            
            try:
                ExtractPDF.makeList(libPath) # Calls a function from the ExtractPDF script that makes a list of all the PDFs found at the specified path. See script for details.
                
                # The following line of code calls a very large function that creates an encoded library from PDFs. See script for details.
                # Outputs are the file path of the newly created encoded library, a flag if any errors occurred while extracting the text from PDFs, and a path to
                # a log with details of the PDF text extraction and library creation.
                libPath, warnFlag, logPath = ExtractPDF.createLibrary(mergeL)
                
                # If a non-critical error occurred while creating the encoded library (usually from unreadable PDFs), display a message to the user in the GUI and Command Prompt.
                if warnFlag == True:
                    gr.Warning(f'One or more PDFs could not be properly encoded and not included in the library. See {logPath} for details.', duration = 15)
                    print(f'One or more PDFs could not be properly encoded and so was not included in the library. See {logPath} for details.')

            # The ExtractPDF script is set to flag an index error if no content is found for the library.
            except IndexError: raise gr.Error('No PDFs with machine-readable text were found in the specified folder.', duration = 15)

            # The ExtractPDF script is set to flag a value error if content is found for the library, but none of it is new.
            except ValueError: raise gr.Error('No new machine-readable PDFs were found in the specified folder.')

            # If an unknown error occurs, display the following message in the GUI.
            except: raise gr.Error('An error occurred while creating the encoded library.')

            # Display the following progress messages in the GUI and Command Prompt window.
            gr.Info("Library created. The library and detailed logs are saved to their respective folders within the Factoid Finder folder.")
            print("Library created. The library and detailed logs are saved to their respective folders within the Factoid Finder folder.")

        # If we are adding PDFs to an existing library, run the appropriate script.
        if mergeL == True:
            libPath = MergeLibraries.mergeLibs(loadedLibPath, libPath) # Calls a function from MergeLibraries. Takes the path to the active encoded library
                                                                       # and the new folder from which to add PDFs. See script for further details.
        
        ### The rest of the code in this function is used to load an encoded library, which are saved in .pkl files.
        
        if os.path.isfile(libPath) == False: # If the specified file cannot be located...
            raise gr.Error('The specified file could not be located.') # Raise an error.

        if libPath[-4:] != '.pkl': # If the specified file is not a Pickle file...
            raise gr.Error(f"The specified path does not point to a .pkl file.") # Raise an error.

        # Display a progress message in both the GUI and Command Prompt window.
        gr.Info("Loading library...", duration = 1)
        print('Loading library...')

        # This function will try to load the specified Pickle file (contains the encoded library), or raise an error if it fails. See QuickSearch script for further details.
        try: loadedLibPath = QuickSearch.loadPickle(libPath) # Updates the variable that tracks the currently loaded library.
        except: raise gr.Error('An unexpected error occurred while loading the encoded library.')

        # Display a progress message in both the GUI and Command Prompt window.
        gr.Info("Library successfully loaded.", duration = 4)
        print('Library successfully loaded.')

        # The following variables are used to update the Gradio GUI.
        updateVis = gr.update(visible = True) # Make an element visible.
        clearSBox = gr.update(value = "") # Clear the value of the Search / Query textbox.
        updateILib = gr.update(value = loadedLibPath) # Set the textbox that displays the active encoded libary to contain the right value.
        updateLPath = gr.update(value = loadedLibPath) # Set the textbox where the user specifies the library or folder path to match the new library.

        # Update the Gradio GUI as needed. In order, this will update searchBox, advancedSettings, UInput, libPath, loadedLib, curPath.
        return updateVis, updateVis, clearSBox, updateILib, updateVis, updateLPath

# This function is used to add new PDFs to an existing library. It is triggered when the button 'addPDFs' is clicked.
def expandLib(progress=gr.Progress(track_tqdm=True)):
    
    #Display progress messages in both GUI and Command Prompt window.
    gr.Info('Folder Select opened in new window.', duration = 5)
    print('Folder Select opened in new window.')
    
    #This code will make sure that tkinter opens on the topmost window.
    root = tk.Tk()
    root.wm_attributes('-topmost', 1)
    root.withdraw()
    
    #Opens a Select Folder window through tkinter and saves the user's selection.
    folderPath = filedialog.askdirectory(parent=root)
    
    if folderPath == "": # If the user does not select a path, raise an error.
        raise gr.Error('No folder was selected.')
    
    print(f"Selected file path: {folderPath}") # Display a debugging message in the Command Prompt window.

    # Call the loadLib function with mergeL set to true. Receives all of the same outputs as loadLib.
    exOut = loadLib(folderPath, 'Create New', mergeL = True)

    return exOut # Return the variables received from loadLib.

# This block activates the tool's search function with input from the Gradio GUI. 
# It receives the user's query, maximum number of results, and generative AI checkbox as inputs.
def searchGr(UInput, Results_slider, genAI):

    # If the user has opted to create a generative AI summary of the top 5 search results, display a message informing them it will be slow.
    if genAI == True:
        gr.Info("Summarizing with generative AI. This may take 15 minutes or more.", duration = 120) # Displays message in Gradio GUI.
        
    try: qResults = QuickSearch.Search(UInput, Results_slider, genAI) # Calls the Search function from the QuickSearch script. See script for details.
    except: qResults = 'An error occurred during the search.' # Displays an error message instead of search results if something goes wrong.
    
    return qResults # Returns the search results. These are displayed in the searchResults markdown box. 

### The following two functions are used to disable buttons while other functions are running, to prevent interference.
# This function will disable all of the buttons listed in 'buttons'
def disableButtons(buttons):
    return [gr.update(interactive=False) for button in buttons]

# This function will re-enable all of the specified buttons.
def enableButtons(buttons):
    return [gr.update(interactive=True) for button in buttons]


#####----- Gradio GUI -----#####
# Set the colour scheme for the Gradio GUI. Many options are available.
# See https://www.gradio.app/guides/theming-guide for details.
theme = gr.themes.Ocean().set(
    body_background_fill='*neutral_50',
    background_fill_primary='*primary_100',
    checkbox_label_background_fill_selected='*primary_300',
    checkbox_background_color='*neutral_50'
)

### The remaining code sets up the Gradio GUI.
with gr.Blocks(fill_height=True, theme = theme, title = "Factoid Finder") as FactoidFinder: # Set the program to take a full page, use the theme specified above, and 
                                                                                            #be titled correctly.
    
    # This is the topmost row, and contains the elements needed to create or load a library.
    with gr.Row():
        # Radio button from which users can specify whether to create a new encoded library or load an existing one.
        radio = gr.Radio(
            choices=['Create New', 'Load Existing'], # The options available.
            value=0, 
            label='Encoded Library', # The label of the button.
            scale = 0) #Prevent from expanding to fill the page.

        # This is a column within the topmost row, and is located next to the radio buttons.
        with gr.Column() as pathCol:
            # The following block is a textbox where the user can input the path to the folder containing their PDF files or to their .pkl file.
            libPath = gr.Textbox(label = "This text should not be visible", # Label used for debugging.
                            placeholder = "This text should not be visible", # Label used for debugging.
                            visible = False, # Set the textbox to initially be hidden (will be updated when the user interacts with the radio button).
                            interactive = True) # Ensure the textbox can be edited.

            #This row is within the column. It contains an empty string that will expand to fill the space, and a right-aligned button that will not expand.
            with gr.Row():
                gr.Markdown("") # Empty space used to align button to the right.
                loadPath = gr.Button("Start", scale = 0, visible = False) # Button to activate the loadLib function with the path specified in the libPath textbox.
    
    gr.Markdown('---') # Separator between the topmost row and what is below.

    # A column that will display the currently loaded library and an option to add more PDFs to it.
    with gr.Column(visible = False, scale = 0) as loadedLib: # Set column to initially be hidden (until loadLib runs successfully) and to not expand to fill the remaining space.
        
        # The main content of the column is in this row.
        with gr.Row(equal_height=True): # Make all elements the same height.
            # The textbox which displays the active encoded library.
            curPath = gr.Textbox(label = 'Current library:',
                                 value = "This text shouldn't be visible", # Text for debugging.
                                 interactive = False) # Prevent textbox from being edited, as it is only meant to display information.
                     
            addPDFs = gr.Button('Add more PDFs...', scale = 0) # Button to activate the expandLib function.
        
        gr.Markdown('---') # Separator between this column and the next set of elements.

    # This row provides the textbox where the user can enter their queries, as well as the Search button.
    with gr.Row(equal_height=True, visible = False) as searchBox: # Set all elements to be equal height, and to not be visible until loadLib runs successfully.
        UInput = gr.Textbox(show_label=False, placeholder = "Question") # Textbox where the user can enter their query.

        # Button which activates the searchGr function.
        searchBtn = gr.Button("Search", 
                              scale = 0, # Set button not to expand.
                              min_width=100, # Set size of button.
                              variant = 'primary') # Set style of button (used to determine colour).

    # This accordion element allows for optional settings to be adjusted. It defaults to being closed and not visible (until loadLib runs successfully).
    with gr.Accordion("Advanced Settings", open=False, visible = False) as advancedSettings:

        # The following slider is used to set how many search results should be returned to the user.
        Results_slider = gr.Slider(5, 100, # The minimum and maximum values that can be selected.
                                   value=10, # The default value.
                                   step=5, # The step by which to change the slider.
                                   interactive=True, # Allows slider to be moved.
                                   label="Max Number of Results")

        # This checkbox is used to enable a summary of the top 5 search results created with Generative AI. It is currently disabled.
        genAI = gr.Checkbox(label = 'Summarize top 5 results with generative AI (Note: Very slow, not recommended. Included only as proof of concept.)',
                                visible = False) # The option to use generative AI has been disabled in this version of the software.
                                                 # Setting visible = True will re-enable it.
        
    searchResults = gr.Markdown(elem_classes="markdown-wrap") # This is a markdown element that is used to display the search results.

    ### The following code blocks are used to run functions when buttons are clicked. ###
    
    buttons = [searchBtn, loadPath, addPDFs, radio] #Specify the buttons to disable when other functions are running.
    
    # When Start button is clicked (to load or create a library), the buttons will all be disabled (so no additional functions can be triggered), the function searchGr will then be run with the specified
    # inputs and outputs,then the buttons will be re-enabled.
    loadPath.click(lambda: disableButtons(buttons), None, buttons).then(
        fn = loadLib, inputs = [libPath, radio], outputs = [searchBox, advancedSettings, UInput, libPath, loadedLib, curPath]).then(
        lambda: enableButtons(buttons), None, buttons)

    # Same as above, but will run if the user hits 'enter' while the libPath textbox is selected.
    libPath.submit(lambda: disableButtons(buttons), None, buttons).then(
        fn = loadLib, inputs = [libPath, radio], outputs = [searchBox, advancedSettings, UInput, libPath, loadedLib, curPath]).then(
        lambda: enableButtons(buttons), None, buttons)
    
    # Same concept as above, but for the 'Add More PDFs' button.
    addPDFs.click(lambda: disableButtons(buttons), None, buttons).then(
        fn = expandLib, inputs = None, outputs = [searchBox, advancedSettings, UInput, libPath, loadedLib, curPath]).then(
        lambda: enableButtons(buttons), None, buttons)

    # Same concept as previously, but for the 'Search' button.
    searchBtn.click(lambda: disableButtons(buttons), inputs = None, outputs = buttons).then(
        fn = searchGr, inputs = [UInput, Results_slider, genAI], outputs = searchResults).then(
        lambda: enableButtons(buttons), None, buttons)

    #This code is the exact same as that for the search button, except it runs when the user hits the enter key while the search box is selected.
    UInput.submit(lambda: disableButtons(buttons), inputs = None, outputs = buttons).then(
                  fn = searchGr, inputs = [UInput, Results_slider, genAI], outputs = searchResults).then(
                  lambda: enableButtons(buttons), None, buttons)

    radio.change(fn = updateLibPath, inputs = radio, outputs = [libPath, loadPath]) # Anytime the radio buttons are changed, this code will run. 
    
print('Program launching in default browser.') # Print message in the Command Prompt window.

FactoidFinder.queue().launch(quiet = True, inbrowser = True) # Launch the Gradio GUI in the browser.
