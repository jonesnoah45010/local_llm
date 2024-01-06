from flask import Flask, jsonify,request, render_template
from bot_tools import GPT_bot, delete_all_files_in_directory, list_files
import os
import time
from dotenv import load_dotenv

load_dotenv()

# use python3.10.0

bot = GPT_bot()
delete_all_files_in_directory("db")
bot.ingest()
bot.wake_up()

app = Flask(__name__)


UPLOAD_FOLDER = os.environ.get('SOURCE_DIRECTORY')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']) # You can modify this to suit your needs
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


INGESTED_FILES = list_files(os.environ.get('SOURCE_DIRECTORY'))
with open("tmp/INGESTED_FILES.txt", "w") as file:
    file.write(repr([]))



@app.route('/')
def index():
    return render_template('bot_page.html')

@app.route('/bot_response', methods=['POST'])
def bot_response():
    query = request.get_json()["prompt"]
    print("asking bot...")
    content = bot.respond(query)
    print("_________________________________________")
    print(content)
    print("_________________________________________")
    sources = content["sources"]
    docs = []
    for item in sources:
        docs.append(item["source"])
    print(docs)

    return jsonify({"response": content["answer"] + "\n SOURCES... " + str(docs)})





def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/upload_files', methods=['POST'])
def ingest_files():
    if 'file[]' not in request.files:
        return jsonify(status='No file part'), 400

    files = request.files.getlist('file[]')

    if not files:
        return jsonify(status='No selected file'), 400

    statuses = []
    for file in files:
        if file.filename == '':
            statuses.append({'filename': file.filename, 'status': 'No selected file'})
            continue

        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            statuses.append({'filename': file.filename, 'status': 'File uploaded successfully'})
        else:
            statuses.append({'filename': file.filename, 'status': 'File type not allowed'})

    return jsonify(status='Files uploaded successfully!')






@app.route('/ingest')
def ingest():
    # This simulates a delay. Remove this in production.
    # time.sleep(1) 
    INGESTED_FILES = list_files(os.environ.get('SOURCE_DIRECTORY'))
    with open("tmp/INGESTED_FILES.txt", "w") as file:
        file.write(repr(INGESTED_FILES))
    print("INGEST ==> " + str(INGESTED_FILES))
    delete_all_files_in_directory(os.environ.get('PERSIST_DIRECTORY'))
    bot.ingest()
    bot.wake_up()
    return jsonify(status='success')


@app.route('/get_ingested_docs_list', methods=['POST'])
def get_ingested_docs_list():
    # INGESTED_FILES will look like this ... ['file1.txt','file2.txt']
    with open("tmp/INGESTED_FILES.txt", "r") as file:
        INGESTED_FILES = file.read()

    print("GET INGESTED FILES ==> " + str(INGESTED_FILES))
    return jsonify(INGESTED_FILES)


@app.route('/get_docs_list', methods=['POST'])
def get_docs_list():
    # os.system("rm tmp/source_documents/.DS_Store")
    directory = os.environ.get('SOURCE_DIRECTORY')
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    print("GET UPLOADED FILES ==> " + str(files))
    return jsonify(files)




@app.route('/save_text', methods=['POST'])
def save_text():
    # Ensure the directory exists
    directory = os.environ.get('SOURCE_DIRECTORY')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Parse JSON data from the request
    data = request.json
    text = data.get('text')
    title = data.get('title')

    if not text or not title:
        return jsonify(status='Error', message='Missing text or title'), 400

    # Replace spaces with underscores in title and add .txt extension
    filename = f"{title.replace(' ', '_')}.txt"
    file_path = os.path.join(directory, filename)

    # Save the text to the file
    try:
        with open(file_path, 'w') as file:
            file.write(text)
        return jsonify(status='Success', message='File saved successfully')
    except IOError as e:
        return jsonify(status='Error', message=str(e)), 500





@app.route('/delete_files', methods=['POST'])
def delete_files():
    data = request.json
    files = data.get('files', [])
    print(files)
    
    directory = os.environ.get('SOURCE_DIRECTORY')
    responses = []

    for filename in files:
        file_path = os.path.join(directory, filename)
        print(file_path)

        # Check if file exists
        if not os.path.exists(file_path):
            responses.append({'filename': filename, 'status': 'File not found'})
            continue

        try:
            os.remove(file_path)
            responses.append({'filename': filename, 'status': 'Deleted successfully'})
        except Exception as e:
            responses.append({'filename': filename, 'status': f'Error deleting file: {str(e)}'})

    return jsonify(status="Success")







if __name__ == '__main__':
    app.run(debug=True)



