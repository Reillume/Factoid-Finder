'''
This script performs all of the search and information retrieval tasks done in
this program. It uses a bi-directional encoder to rank the top k 
results (default is 10). The top results are then passed to a cross-encoder 
for re-ranking. Results are cleaned and presented to the user with a link to
the full PDF. Basic Retrieval Augmented Generation functionality is also included.
'''
#####----- Import Packages -----#####
import pandas as pd # Critical - Necessary for working with extracted PDF content and metadata.
import torch # Critical - Provides tools for working with Small Language Models.
from sentence_transformers import SentenceTransformer, SimilarityFunction, CrossEncoder, util # Critical - Runs Small Language Models used for semantic search.
import pickle # Critical - Saves and reads the Encoded Libraries.
import os # Critical - Base Python package needed for many functions.
import re # Critical - Base Python package used to modify strings.
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline # Optional - Allows for Microsoft Phi 3.5 to be run for RAG.
import torch.nn as nn # Optional - Allows for the use Sigmoid activation function for the cross-encoder.

#####----- Load Models and Data -----#####
# This function is used to load the AI models used for semantic search.
# It is called before the GUI is loaded, so that the GUI is more responsive initially.
def initializeEmbedders():
    global embedder
    global model

    # Load the bi-directional encoder and cross-encoder that are used for semantic search.
    # Note: If desired, changing these models to new versions is relatively straight-forward.
    embedder = SentenceTransformer('sentence-transformers/msmarco-distilbert-dot-v5') # Chosen for it's combination of accuracy, speed, and integration with Sentence-Transformers.
    model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512) # Chosen based on qualitative testing and experimentation.

# This function loads an Encoded Library that was saved previously.
def loadPickle(UPickle):

    global pdfTable
    global libraryEmbeddings
    global SearchReady

    # Get the path to the Encoded Library, as specified by the user through the GUI.
    Pickle = UPickle

    # Load the Encoded Library.
    with open(Pickle, 'rb') as f:  # Python 3: open(..., 'rb')
        pdfTable, libraryEmbeddings = pickle.load(f)

    return Pickle # Return the path to the currently loaded Encoded Library.

#####----- Semantic Search -----#####
# This function takes the user's query, retrieves the most relevant text passages from the
# Encoded Library, then formats the results using markdown to present to the user.
# Semantic search functionality is based on code provided in the Sentence-Transformers documentation.
# See here for further details: https://www.sbert.net/examples/applications/semantic-search/README.html.
def Search(UInput, Results_slider, genAI): # Arguments are the user's query, the max number of results to return, and whether to include a RAG summary.
    query = UInput
    topK = min(Results_slider, len(pdfTable['Content'])) # Ensure that max number of results is not longer than the total number of records.

    # Find the closest n sentences of the corpus for each query sentence based on dot product similarity.
    queryEmbedding = embedder.encode(query, convert_to_tensor=True)
    
    # Use dot product and torch.topk to find the highest k scores
    similarity_scores = util.dot_score(queryEmbedding, libraryEmbeddings)[0].cpu().tolist()
    similarity_scores = torch.tensor(similarity_scores)
    scores, indices = torch.topk(similarity_scores, k=topK)

    # Print the query in the Command Prompt window for debugging.
    print("\nQuery:", query, "\n------------------------------------------------------")
    print(f"Top {topK} most similar paragraphs in document library:\n------------------------------------------------------ \n")

    # Initialize variables
    pairs = []
    original_indices = []

    # Create pairs of the query and each paragraph determined to be relevant (based on top k), while keeping track of original indices.
    for score, idx in zip(scores, indices):
        paragraph = pdfTable['Content'][idx.item()]
        pairs.append([query, paragraph])
        original_indices.append(idx.item())

    # Predict the similarity of each query/paragraph pair using a cross-encoder.
    cross_encoder_scores = model.predict(pairs, activation_fct=nn.Sigmoid())

    # Combine query/paragraph pairs, their similarity scores, and original indices into a list of tuples. Then sort by score in descending order
    combined = list(zip(pairs, cross_encoder_scores, original_indices))
    combined.sort(key=lambda x: x[1], reverse=True)

    sResults = "------------------------------------------------------<br>" # Initialize the variable that will present search results to the user.
    warningGiven = False # Initialize a variable to track whether a warning has already been given about the low relevancy of results (if applicable).
    relevanceWarn = '' # Initialize the warning message itself.
    
    # For each query/paragraph pair (in order of decreasing similarity scores), get relevant information to present as a search result to the user.
    for idx, (pair, ce_score, original_idx) in enumerate(combined):
        pdfPath = pdfTable['File_Path'][original_idx] # Retrieve the file path of the PDF where the paragraph in this pair was sourced.
        pageNum = pdfTable['Page'][original_idx] # Retrieve the page number.

        if os.path.exists(pdfPath) == True: # If the file exists at the specified path...
            URL = f"file:{os.path.abspath(pdfPath)}#page={pageNum}" # Create a link to the page where the paragraph originates.
            
        else: URL = "File missing or moved." # Else, if the file does not exist at the specified path, output a message to that effect.
        #htmlLink = f'<a href="{URL}"></a>' # Note: This was triggering the anti-virus so was disabled.

        # Create a list of all the potential characters that might break the markdown.
        codeChars = ['`', '*', '_', '[', ']', '(', ')', '#', '>', '-', '~', ':', '=', '^', '|', '<']
        
        # For each character in the list of problematic characters, loop through the paragraph in the current pair and add an escape character ahead of it.
        for char in codeChars:
            pair[1] = re.sub(re.escape(char), r'\\' + char, pair[1])

        # If the similarity score of a result is below 0.8, provide a warning to the user in the search results. Since results are sorted in order of decreasing similarity, this only needs to be done once.
        if (ce_score < 0.8) and (warningGiven == False):
            relevanceWarn = r'<mark>Warning: The following results do not appear to be very relevant to your query.</mark><br>'
            warningGiven = True

        else: relevanceWarn = '' # This ensures that the warning message does not persist into additional search results (only needs to be given once).

        # Concatenate the search results into one convenient package, to be presented to the user with markdown.
        sResults += f'{relevanceWarn}***Preview {idx + 1}***<br>**Similarity Score:** {ce_score:.4f}<br>**File:** {pdfTable['File_Name'][original_idx]}<br>**Page:** {pdfTable['Page'][original_idx]}<br>**Link:** {URL}<br>**Paragraph:** {pair[1]}<br>------------------------------------------------------<br>'

    # This code will use Retrieval Augmented Generation to create a summary of the top 5 search results.
    # It is heavily based on the code provided in the Microsoft Phi 3.5 documentation: https://huggingface.co/microsoft/Phi-3.5-mini-instruct.
    if genAI == True:

        # Initialize the AI language model.
        torch.random.manual_seed(0) 
        SumModel = AutoModelForCausalLM.from_pretrained( 
            "microsoft/Phi-3.5-mini-instruct",   
            torch_dtype="auto",  
            trust_remote_code=True)

        # Loads Microsoft Phi 3.5 Mini (very good at summarizing technical documents).
        tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3.5-mini-instruct") 

        toSum = "" # Initialize a string that will later be passed to the AI to summarize the contents of.

        # Create a summary of the top 5 search results for the AI.
        for idx, (pair, ce_score, original_idx) in enumerate(combined):
            if idx >= 5:
                break
            pdfPath = pdfTable['File_Path'][original_idx]
            pageNum = pdfTable['Page'][original_idx]

            toSum += f"***Search Result {idx + 1}***<br>**Similarity Score:** {ce_score:.4f}<br>**File:** {pdfTable['File_Name'][original_idx]}<br>**Page:** {pdfTable['Page'][original_idx]}<br>**Paragraph:** {pair[1]}<br>------------------------------------------------------<br>"

        # Pass the system prompt and a prompt asking the AI to summarize our top 5 search results.
        messages = [ 
            {"role": "system", "content": "You are a concise and truthful AI who answers in the style of a knowledgeable expert."}, 
            {"role": "user", "content": f"Here is text you will summarize: {toSum} \n Summarize the above text as it relates to: {query}"}
        ] 
        
        pipe = pipeline( 
            "text-generation", 
            model=SumModel, 
            tokenizer=tokenizer, 
        ) 
        
        generation_args = { 
            "max_new_tokens": 500, # Sets maximum new tokens to a reasonable value.
            "return_full_text": False, 
            "temperature": 0.0, # A more deterministic response should be less likely to hallucinate.
            "do_sample": False, 
        } 
        
        genAIout = pipe(messages, **generation_args) 

        genAIout = genAIout[0]['generated_text']
        re.sub(r'\n', '<br>', genAIout) #Reformat for markdown
        
        sResults = f"**AI Summary**: {genAIout} <br> {sResults}"
    
    print(sResults) # Print the search results to the Command Prompt window for reference.
    return sResults # Return the search results to be displayed in the GUI.