import ast
from pprint import pprint
from collections import defaultdict, namedtuple


class ArrayCluster:
    def __init__(self, name, item_list):
        self.name = name
        self.item_list = item_list
        self.item_dict = {}
        self.value_dict = {}

class SortTags:
    def __init__(self):
        self.auto_plys_done_idx = 0
        self.auto_plys_not_done_idx = 0
        self.array_data_dict = {}
        self.bit_cluster = ArrayCluster("bit", ["B3", "B13"])
        self.float_cluster = ArrayCluster("float", ["F8", "F18", "F209", "F211"])
        self.counter_cluster = ArrayCluster("counter", ["C5", "C50", "C15", "C52"])
        self.long_cluster = ArrayCluster("long", ["L19", "L204", "L208", "L210"])
        self.n_cluster = ArrayCluster("n", ["N7",])
        self.timer_cluster = ArrayCluster("timer", ["T4", "T14", "T206"])
        self.string_cluster = ArrayCluster("string", ["ST12"])
        self.clusters = [
            self.bit_cluster,
            self.float_cluster,
            self.counter_cluster,
            self.long_cluster,
            self.n_cluster,
            self.timer_cluster,
            self.string_cluster,
        ]
        self.tag_name_dict = defaultdict(dict)
        self.tag_description_dict = defaultdict(dict)
        self.array_index_dict = defaultdict(dict)
        self.in_array_flag = False
        self.in_vals_flag = False
        self.eval_array = False
        self.first_line = False
        self.array_vals = ""
        self.current_array = ""
        self.sub_dict = {
            "SYSTEM": "SYS",
            "INITIALIZE": "INIT",
            "MANUAL": "MAN",
            "AXIS1": "A1",
            "AXIS2": "A2",
            "STATION": "STN",
            "ACCELERATION": "ACCEL",
            "MATERIAL": "MAT",
            "1/2": "HALF",
            "@": "AT",
            "&": "AND",
            "/": "_",
            "%": "PCT",
            "(REAL)": "",
            "(POS._MODE)": "",
            "(DINT)": "",
            ")": "",
            "AUTO_MOVE": "MOVE",
            "AUTO_UPDATE": "UPDATE",
            "CURRENT": "CUR",
            "STANDARD": "STD",
            "FREQUENCY": "FREQ",
            "CLEAR": "CLR",
            "W$QMINIMUM_LENGTH_FACTOR_NOT_TO_RUN_BELOW_10.05_AT_<1.0_SCALE_FACTOR": "W_MIN_LEN_FACTOR",
            "X$QMINIMUM_LENGTH_FACTOR_NOT_TO_RUN_BELOW_10.05_AT_<1.0_SCALE_FACTOR": "X_MIN_LEN_FACTOR",
            "MOVE_CUR_SIDE_AXIS_TO_PICK_AND_MAT_CLR_TD": "MOV_CUR_SIDE_AXIS_TO_PICK_AND_MAT_CLR_TD"
        }
    def process(self):

        with open("SCS_PLC_27SEP2022.L5K", "r") as f:

            for line in f:
                for cluster in self.clusters:
                    for item in cluster.item_list:
                        if item + " : " in line:
                            self.in_array_flag = True
                            self.current_array = item
                if self.in_array_flag and 'RADIX' not in line:
                    try:
                        self.tag_index = line.split(" := ")[0].split("COMMENT")[1]
                    except IndexError:
                        self.tag_index = line.split(" := ")[0].split("COMMENT")[0]
                    self.tag_description = line.split(" := ")[1].split(",")[0]

                    self.tag_name = (self.tag_description
                                .replace(" - ", "_")
                                .replace(" ","_")
                                .replace(":", "")
                                .replace('"', '')
                                )
                    for word, nick in self.sub_dict.items():
                        self.tag_name = self.tag_name.replace(word, nick)

                    self.tag_name = self.tag_name.rstrip("_")
                    if self.tag_name == "AUTO_PLYS_DONE":
                        self.tag_name += "_" + str(self.auto_plys_done_idx)
                        self.auto_plys_done_idx += 1
                    if self.tag_name == "AUTO_PLYS_NOT_DONE":
                        self.tag_name += "_" + str(self.auto_plys_not_done_idx)
                        self.auto_plys_not_done_idx += 1

                    try:
                        self.array_index_dict[self.current_array][self.tag_index] = [int(self.tag_index.split(']')[0].strip('[')), 
                                                                                    int(self.tag_index.split('.')[1])]
                    except IndexError:
                        self.array_index_dict[self.current_array][self.tag_index] = [int(self.tag_index.split(']')[0].strip('['))]
                    except ValueError:
                        self.array_index_dict[self.current_array][self.tag_index] = [int(self.tag_index.split(']')[0].strip('[')), self.tag_index.split('.')[1]]


                    self.tag_name_dict[self.current_array][self.tag_index] = self.tag_name
                    self.tag_description_dict[self.current_array][self.tag_index] = (self.tag_description
                                .replace(":", "")
                                .replace('"', ''))

                if ") := " in line:
                    self.in_array_flag = False
                    if ';' not in line:
                        self.in_vals_flag = True
                    else:
                        self.array_vals = line.split(") := ")[-1]
                        self.eval_array = True
                    self.array_vals = line.split(") := ")[-1]
                    self.first_line = True

                if self.in_vals_flag and not self.first_line:
                    self.array_vals += line
                    self.first_line = False
                    if ';' in line:
                        self.in_vals_flag = False
                        self.eval_array = True
                self.first_line = False

                if self.eval_array:
                    self.array_vals = self.array_vals.replace(" ", "").replace("\n", "").replace("\t", "").rstrip(";")
                    self.array_val_list = ast.literal_eval(self.array_vals)
                    self.array_data_dict[self.current_array] = self.array_val_list
                    self.eval_array = False
                    self.current_array = ""
        return (
            self.array_data_dict,
            self.tag_name_dict,
            self.tag_description_dict,
            self.array_index_dict,
        )


class CollectData:
    def __init__(self, array_data_dict, array_index_dict):
        self.array_data_dict = array_data_dict
        self.array_index_dict = array_index_dict

    def collect_data(self):
        mapped_data_dict = defaultdict(dict)
        for index_array, index_map in self.array_index_dict.items():
            for key, val in index_map.items():
                if not val:
                    continue
                if len(val)>1 and isinstance(val[1], str):
                    continue
                if 'B' in index_array:
                    bit_str = dint_to_binary_str(self.array_data_dict[index_array][val[0]])
                    if len(val) == 2:
                        mapped_data_dict[index_array][key] = int(bit_str[val[1]])
                elif 'L' in index_array:
                    bit_str = dint_to_binary_str(self.array_data_dict[index_array][val[0]])
                    if len(val) == 2:
                        mapped_data_dict[index_array][key] = int(bit_str[val[1]])
                    if len(val) == 1:
                        mapped_data_dict[index_array][key] = self.array_data_dict[index_array][val[0]]
                else:
                    mapped_data_dict[index_array][key] = self.array_data_dict[index_array][val[0]]
        return mapped_data_dict

def cluster_definitions(tag_description_dict):
    for index_array, index_map in tag_description_dict.items():
        for key, val in index_map.items():
            if '.' in key:
                array_val = key.split('.')[0]
                main_array = tag_description_dict[index_array].get(array_val)
                if main_array:
                    tag_description_dict[index_array][key] = tag_description_dict[index_array][array_val] + ' | ' + tag_description_dict[index_array][key]

def dint_to_binary_str(dint_val):
    reversed_byte_val = dint_val.to_bytes(4, byteorder='big', signed=True)
    byte_val = ''.join(reversed(''.join(f'{b:08b}' for b in reversed_byte_val)))
    return(byte_val)

DataConfig = namedtuple('DataConfig', ['radix', 'datatype'])

def generate_tag_strings(tag_name_dict, tag_description_dict, mapped_data):
    config_map = {
        'B': DataConfig("Decimal", "BOOL"),
        'F': DataConfig("Float", "REAL"),
        'L': DataConfig("Decimal", "DINT"),
        'T': DataConfig(None, "TIMER"),
        'C': DataConfig(None, "COUNTER"),
        'ST': DataConfig(None, "STRING"),
    }
    string_list = []

    for index_array, index_map in tag_name_dict.items():
        radix = ''
        data_type = ''
        for letter, config in config_map.items():
            if letter in index_array:
                radix = config.radix
                data_type = config.datatype
        for key, val in index_map.items():
            tag_name = val
            description = tag_description_dict[index_array][key]
            try:
                data = mapped_data[index_array][key]
            except KeyError:
                continue
            if radix:
                tag_str = f'{tag_name} : {data_type} (Description := "{description}", RADIX := Decimal) := {data};'
            else:
                tag_str = f'{tag_name} : {data_type} (Description := "{description}") := {data};'
            string_list.append(tag_str)
    return string_list

def main():
    array_data_dict, tag_name_dict, tag_description_dict, array_index_dict = SortTags().process()
    mapped_data = CollectData(array_data_dict, array_index_dict).collect_data()
    cluster_definitions(tag_description_dict)

    tag_strings = generate_tag_strings(tag_name_dict, tag_description_dict, mapped_data)

    with open("tag_add.txt", "w") as f:
        f.write("\n".join(tag_strings))

if __name__ == "__main__":
    main()

