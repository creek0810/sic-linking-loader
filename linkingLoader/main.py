import sys
from linkingLoader import LinkingLoader


if __name__ == "__main__":
    arg = sys.argv
    if len(arg) < 3:
        print("Please enter starting address and file path")
    else:
        loader = LinkingLoader(arg[1], arg[2:])
        loader.execute()
        loader.print_memory()