from dotenv import load_dotenv
from libs.argparser import ArgParser
from libs.llmagent import LLMAgent

load_dotenv()

def main():
    argParser = ArgParser()
    llmAgent = LLMAgent("Amara", argParser.args,  argParser.parser)
    llmAgent.run()
    

if __name__ == '__main__':
    main()


       

    

        

