#!/usr/bin/env python3
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.vectorstores import Chroma
from langchain.llms import GPT4All, LlamaCpp
import os
import argparse
import time
from constants import CHROMA_SETTINGS


import shutil




def list_files(directory):
    try:
        # List all files and directories in the given directory
        entries = os.listdir(directory)
        # Filter out directories, keep only files
        files = [file for file in entries if os.path.isfile(os.path.join(directory, file))]
        return files
    except FileNotFoundError:
        return []
    except Exception as e:
        return []

def delete_all_files_in_directory(directory_path):
    # Check if the directory exists
    if not os.path.exists(directory_path):
        print(f"{directory_path} does not exist!")
        return
    # Iterate over all the directories, subdirectories, and files
    for root_dir, dirs, files in os.walk(directory_path, topdown=False):
        for name in files:
            file_path = os.path.join(root_dir, name)
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
        for name in dirs:
            dir_path = os.path.join(root_dir, name)
            try:
                shutil.rmtree(dir_path)
                print(f"Deleted directory: {dir_path}")
            except Exception as e:
                print(f"Error deleting directory {dir_path}: {e}")

# Test
# directory_path = '/path/to/your/directory'
# delete_all_files_in_directory(directory_path)




# os.system("cp example.env .env")




class GPT_bot:
    def __init__(self):
        self.embeddings_model_name = None
        self.persist_directory = None
        self.model_type = None
        self.model_path = None
        self.model_n_ctx = None
        self.model_n_batch = None
        self.target_source_chunks = None
        self.args = None
        self.embeddings = None
        self.db = None
        self.retriever = None
        self.callbacks = None
        self.llm = None
        self.qa = None


    def wake_up(self):
        load_dotenv()
        self.embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME")
        self.persist_directory = os.environ.get('PERSIST_DIRECTORY')
        self.model_type = os.environ.get('MODEL_TYPE')
        self.model_path = os.environ.get('MODEL_PATH')
        self.model_n_ctx = os.environ.get('MODEL_N_CTX')
        self.model_n_batch = int(os.environ.get('MODEL_N_BATCH',8))
        self.target_source_chunks = int(os.environ.get('TARGET_SOURCE_CHUNKS',4))
        self.args = self.parse_arguments()
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embeddings_model_name)
        self.db = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings, client_settings=CHROMA_SETTINGS)
        self.retriever = self.db.as_retriever(search_kwargs={"k": self.target_source_chunks})
        self.callbacks = [] if self.args.mute_stream else [StreamingStdOutCallbackHandler()]
        match self.model_type:
            case "LlamaCpp":
                self.llm = LlamaCpp(model_path=self.model_path, max_tokens=self.model_n_ctx, n_batch=self.model_n_batch, callbacks=self.callbacks, verbose=False)
            case "GPT4All":
                self.llm = GPT4All(model=self.model_path, max_tokens=self.model_n_ctx, backend='gptj', n_batch=self.model_n_batch, callbacks=self.callbacks, verbose=False)
            case _default:
                # raise exception if model_type is not supported
                raise Exception(f"Model type {self.model_type} is not supported. Please choose one of the following: LlamaCpp, GPT4All")
            
        self.qa = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=self.retriever, return_source_documents= not self.args.hide_source)


    def reset(self):
        self.__init__()

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description='privateGPT: Ask questions to your documents without an internet connection, '
                                                     'using the power of LLMs.')
        parser.add_argument("--hide-source", "-S", action='store_true',
                            help='Use this flag to disable printing of source documents used for answers.')
        parser.add_argument("--mute-stream", "-M",
                            action='store_true',
                            help='Use this flag to disable the streaming StdOut callback for LLMs.')
        return parser.parse_args()


    def respond(self,query):
        # Get the answer from the chain
        start = time.time()
        res = self.qa(query)
        answer, docs = res['result'], [] if self.args.hide_source else res['source_documents']
        end = time.time()
        d = {}
        d["question"] = query
        d["answer"] = answer
        d["processing_time"] = str(round(end - start, 2))
        d["sources"] = []
        for document in docs:
            s = {}
            s["source"] = document.metadata["source"]
            s["page_content"] = document.page_content
            d["sources"].append(s)
        return d


    def ingest(self):
        os.system("python3 ingest.py")














