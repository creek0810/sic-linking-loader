import math
import struct

class LinkingLoader:
    def __init__(self, start_addr, file_list):
        self.start_addr = int(start_addr, 16)
        self.file_list = file_list
        self.total_memory = 0
        self.symbol_table = {}
        self.memory = ""

    def _get_obj_length(self, code):
        return code[13:].strip()

    def _get_obj_name(self, code):
        return code[1:7].strip()

    def _get_symbol_name_addr(self, code, base_addr):
        code = code.strip()
        result = {}
        i = 1
        while i < len(code):
            raw_data = code[i:i+12].split()
            name = raw_data[0].strip()
            addr = raw_data[1].strip()
            result[name] = int(addr, 16) + base_addr
            i += 12
        return result

    def _pass1(self):
        for cur_file in self.file_list:
            with open(cur_file, "r+") as fp:
                lines = fp.readlines()
                # store program start addr
                name = self._get_obj_name(lines[0])
                base_addr = self.start_addr + self.total_memory
                self.symbol_table[name] = base_addr
                # calc total memory space
                self.total_memory += int(self._get_obj_length(lines[0]), 16)
                # scan external symbol
                for i in range(1, len(lines)):
                    if lines[i].startswith("D"):
                        result = self._get_symbol_name_addr(lines[i], base_addr)
                        self.symbol_table.update(result)
                    else:
                        break

    def _load_content(self, name, code):
        code = code.strip()
        addr = int(code[1:7], 16) + self.symbol_table[name] - self.start_addr
        addr *= 2

        length = int(code[7:9], 16) * 2
        for idx, v in enumerate(code[9:]):
            self.memory[addr+idx] = v

    def _hex_str_to_int(self, value):
        length = len(value) * 4
        result = int(value, 16)
        if result >= 2 ** (length - 1):
            result -= 2 ** length
        return result


    def _relocate_content(self, name, code):
        code = code.strip()
        # get addr
        addr = int(code[1:7], 16) + self.symbol_table[name] - self.start_addr
        addr *= 2
        # get length
        length = int(code[7:9], 16)
        if length == 5:
            addr += 1
        # get flag
        flag = code[9]
        # get symbol
        symbol = code[10:].strip()

        # get original value
        cur_value = "".join(self.memory[addr:addr+length])
        cur_value = self._hex_str_to_int(cur_value)

        # relocate
        if flag == "+":
            cur_value += self.symbol_table[symbol]
        else:
            cur_value -= self.symbol_table[symbol]
        cur_value = "{0:0{1}X}".format(cur_value, length)

        for i, v in enumerate(cur_value):
            self.memory[addr+i] = v



    def _pass2(self):
        # init memory structure
        result_len = self.total_memory * 2
        self.memory = ["." for x in range(result_len)]

        # start load
        for cur_file in self.file_list:
            with open(cur_file, "r+") as fp:
                lines = fp.readlines()
                # store program start addr
                name = self._get_obj_name(lines[0])
                # scan external symbol
                for i in range(1, len(lines)):
                    # load content
                    if lines[i].startswith("T"):
                        self._load_content(name, lines[i])
                    # relocate
                    if lines[i].startswith("M"):
                        self._relocate_content(name, lines[i])


    def print_memory(self):
        result_len = self.total_memory * 2
        line_num = math.ceil(result_len / 32)
        cur_addr = self.start_addr
        for i in range(line_num):
            result = f"0x{cur_addr:04X} "
            result +=  " ".join(self.memory[i*32:(i+1)*32])
            print(result)
            cur_addr += 16

    def execute(self):
        self._pass1()
        self._pass2()
