from Scraper import scrape
from toDocx import markdown_to_docx
from docxToMarkdown import docx_to_markdown
import os
import json
from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage
from langchain.document_loaders import Docx2txtLoader
import openai
import gradio as gr
from dotenv import load_dotenv


load_dotenv('.env')
openai_api_key = os.environ.get("OPENAI_API_KEY")

llm = ChatOpenAI(temperature=1.0, model='gpt-4o-mini')


# Load the Word document (report template)
def load_document(file_path):
    loader = Docx2txtLoader(file_path)
    documents = loader.load()
    return documents

# Convert & Load your document to markdown
document_path = 'report_template.docx'
document_path2 = 'report_template_MD.docx'
docx_to_markdown(document_path, document_path2)
loaded_documents = load_document(document_path2)

# Prepare the document content for the chatbot
document_content = "\n".join([doc.page_content for doc in loaded_documents])

# Load JSON data (scraped raw data)
def load_json(file_path):
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
    return data

# Load your JSON file
json_path = 'scraped_results.json'
json_data = load_json(json_path)
# Format the JSON data as a string
formatted_json = json.dumps(json_data, indent=2)


# Define a preset context
preset_context = """	
    Role: Competitive Intelligence Analyst
    Context:
      Priority: Prioritize the user's query if there's any overlap with instructions below.
      Task Overview: You are a competitive intelligence analyst at Alcon. Your goal is to gather updates on competitor activities specifically related to intraocular lens (IoL) developments from RXSight, Johnson & Johnson, and Zeiss. Focus mainly on these three competitors. 
      Link Filtering: Select only relevant links that answer the user query. If the user's query specifies anything related to time period, filter only articles that are published within the time period. If the user's query doesn't specify a timeframe, only consider articles published within the last 30 days of today's date. Prioritize the links that were published recently. 
      Content Summary and Key Insights: Summarize each article's main points in concise bullet points (maximum 50 words per bullet) and highlight key actionable insights or takeaways.
      Report Format: Prepare a Word document following the provided report template format. For content:
      Categorization: Group articles under overarching themes, naming each section based on its central topic, such as the one provided in the report template document.
      Article Count: There's no restriction on the number of articles per section.
      Article Links and Dates: Include the link after each article title if it's provided in the package (do not use external sources). For publication dates, use the date within the article, or leave it blank if not provided.
      Before sending the answers, review all articles and only include the ones that have dates published within the time period.
"""

gpt_output = ''

def predict(message, history):
    history_langchain_format = []
    for human, ai in history:
        history_langchain_format.append(HumanMessage(content=human))
        history_langchain_format.append(AIMessage(content=ai))
    # Add the preset context as the first message
    history_langchain_format.insert(0, HumanMessage(content=preset_context))
    history_langchain_format.insert(1, HumanMessage(content=document_content))
    history_langchain_format.insert(2, HumanMessage(content=formatted_json))
    history_langchain_format.append(HumanMessage(content=message))
    gpt_response = llm(history_langchain_format)
    global gpt_output
    gpt_output = gpt_response.content

    return gpt_response.content

def download_file():
    # Save the report as a .docx file
    report_file_path = "generated_report.docx"
    global gpt_output
    gpt_output = gpt_output.replace("(", "\nLink: ")
    gpt_output = gpt_output.replace(")", "\n")
    markdown_to_docx(gpt_output, report_file_path)
    print("clicked button")


##
## Creating the UI ###
##

# Overriding the Gradio default color with Alcon's blue.
ALCON_BLUE = "#003595" # this is: rgb(0, 53, 149)
gr.themes.colors.blue.c500 = ALCON_BLUE

# Seeting some other customizations, including  font/primary color/various sizes.
theme = gr.themes.Default(
  font=[gr.themes.GoogleFont("Open Sans")],
  primary_hue="blue",
  neutral_hue="neutral",
  radius_size="none",
  text_size=gr.themes.sizes.text_lg,
)

# Setting default colors with our own specific values, which will be reused throughout the entire interface.
theme.set(
  body_background_fill=ALCON_BLUE
  
)

# Using customzied CSS into the Gradio interface page.
# This section adds polka dots from the Alcon website.
#  
# This is another option - circle/ring ish pattern 
# background-image: url(https://www.alcon.com/sites/g/files/rbvwei3726/files/2024-02/alcon_com_footer_bg_0.png) !important;
#  
custom_css = """
gradio-app {
  background-image: url(https://www.alcon.com/sites/g/files/rbvwei4411/files/2024-01/dots_1.png) !important;
  background-color: #003595;
  background-position: center top;
  background-size: cover;
  background-repeat: no-repeat;
  background-attachment: scroll;
}

.tabs-title {
  font-family: 'Open Sans', sans-serif;
  font-weight: bold;
  font-size: 30px;
  color: #FFFFFF !important;
  border: none !important;
  outline: none !important;
  background-color: transparent !important;
}
"""


# Gradio interface with tabs (for chatbot and scraper tab)
with gr.Blocks(theme=theme, css=custom_css) as main_block:
    # Add Alcon logo
    gr.HTML("<img src='https://www.alcon.com/sites/g/files/rbvwei4411/files/alcon_assets/alcon-logo.svg' />")
    
    # Create tabs for Scraper and Chatbot
    with gr.Tabs():
    
        with gr.Tab("Chatbot", elem_classes=["tabs-title"]):
            # Title and description for the chatbot tab
            gr.Markdown("""
                # Competitive Intelligence Chatbot
                #### Interact with the Alcon Competitive Intelligence Chatbot for insights and assistance.
            """)

            # Chatbot setup with custom avatar images
            chatbot = gr.Chatbot(
                avatar_images=(
                    "https://www.myalcon.com/sites/g/files/rbvwei2521/files/2022-01/man-with-lab-coat.png",
                    "https://s3.amazonaws.com/pix.iemoji.com/images/emoji/apple/ios-12/256/robot-face.png",
                ),
            )
            gr.ChatInterface(predict, chatbot=chatbot)
            # Inserting Download button, which will download as a Word Document
            db = gr.DownloadButton("Download the Report")
            db.click(fn = download_file)

        with gr.Tab("Scraper", elem_classes=["tabs-title"]):
            # Title and description for the scraper tab
            gr.Markdown("""
                # Competitive Intelligence Scraper
                #### Click the button below to initiate scraping for competitive intelligence data.
            """)

            # Scraper button and output display
            scrapebutton = gr.Button("Scrape")
            output = gr.Textbox(label="Scraped Content", max_lines=10)
            scrapebutton.click(fn=scrape, outputs=output)


main_block.launch()


