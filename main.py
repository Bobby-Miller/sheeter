import ast
import csv
from dataclasses import dataclass
from pprint import pprint
from collections import defaultdict, namedtuple
import pandas as pd
from pathlib import Path

current_dir = Path(__file__).parent

HMI_FILE_PATH = current_dir / "HMI_source_files" / "sheeter_tags.csv"
CONSUMED_FILE = "SCS_PLC_27SEP2022.L5K"
PRODUCED_FILE = "tag_add_2.txt"
PRODUCED_FILE = "tag_add_jan_5_2026.txt"
REPLACEMENT_DOC = "tag_sub_jan_5_2026.L5K"
TAG_CSV_FILE_NAME = "Tag_CSV_Jan_5_2026.csv"
CONVERSION_FILE_NAME = "tag_conversion_jan_8_2025.csv"

NUM_DICT = {
    '00': '0',
    '01': '1',
    '02': '2',
    '03': '3',
    '04': '4',
    '05': '5',
    '06': '6',
    '07': '7',
    '08': '8',
    '09': '9',
    '10': '10',
    '11': '11',
    '12': '12',
    '13': '13',
    '14': '14',
    '15': '15',
}

CONVERSION_DICT: dict[str, str] = {
        f'ENETBRIDGE_1769:1:O.Data.{val}': f'Local:4:O.Pt{key}.Data' 
        for key, val in NUM_DICT.items()
    }|{
        f'SLOT00_Bul_1766_Placeholder.I[0].{val}': f'Local:1:I.Pt{key}.Data' 
        for key, val in NUM_DICT.items()
    }|{
        f'SLOT00_Bul_1766_Placeholder.I[1].{val}': f'Local:2:I.Pt{key}.Data' 
        for key, val in NUM_DICT.items()
    }|{
        f'SLOT00_Bul_1766_Placeholder.O[0].{val}': f'Local:3:O.Pt{key}.Data' 
        for key, val in NUM_DICT.items()
    }

class YNBool:
    def __new__(cls, bool_val):
        true_options = {True, 1, "y", "Yes", "yes",}
        false_options = {False, 0, "n", "No", "no"}
        if bool_val not in true_options and bool_val not in false_options:
            raise ValueError("value option not in true or false option arrays")
        if bool_val in true_options:
            return "Yes"
        else:
            return "No"

@dataclass
class Controller:
    processor_type: str
    major_rev: int
    redundancy_enabled: bool
    keep_test_edits_on_switch_over: bool
    security_code: int
    changes_to_detect: bytes
    sfc_execution_control: str
    sfc_restart_position: str
    sfc_last_scan: str
    serial_number: bytes
    match_project_to_controller: bool
    can_use_rpi_from_producer: bool
    inhibit_automatic_firmware_update: bool
    pass_through_configuration: str
    download_project_documentation_and_extended_properties: bool


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
            "-": "_",
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
            "MOVE_CUR_SIDE_AXIS_TO_PICK_AND_MAT_CLR_TD": "MOV_CUR_SIDE_AXIS_TO_PICK_AND_MAT_CLR_TD",
        }

    def process(self):
        with open(CONSUMED_FILE, "r") as f:
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
                                .replace('"', '')
                    )

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
        self.array_data_dict: dict = array_data_dict
        self.array_index_dict: dict = array_index_dict

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

def generate_tag_strings(tag_name_dict, tag_description_dict, mapped_data) -> list[str]:
    config_map = {
        'B': DataConfig("Decimal", "BOOL"),
        'F': DataConfig("Float", "REAL"),
        'L': DataConfig("Decimal", "DINT"),
        'T': DataConfig(None, "TIMER"),
        'C': DataConfig(None, "COUNTER"),
        'ST': DataConfig(None, "STRING"),
        'N': DataConfig("Decimal", "DINT"),
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
                # Addressing space in list item (incompatible with logix compiler)
                if isinstance(data, list):
                    data = str(data).replace(' ', '')
            except KeyError:
                continue
            if radix:
                tag_str = f'\t{tag_name} : {data_type} (Description := "{description}", RADIX := Decimal) := {data};'
            else:
                tag_str = f'\t{tag_name} : {data_type} (Description := "{description}") := {data};'
            # Handles the case where a bit of a byte array is directly referenced
            if '.' in key:
                tag_str = f'\t{tag_name} : BOOL (Description := "{description}", RADIX := Decimal) := {data};'
            string_list.append(tag_str)
    return string_list

class ProgramUpdate:
    def __init__(self, tag_name_dict: dict[str, dict[str,str]]):
        self.tag_name_dict = tag_name_dict
        self.contents = ''

    def replace_variables(self, source_line, source_text, replacement_text) -> str:
        sub_text: str = source_line.replace(f'({source_text})', f'({replacement_text})')
        sub_text = sub_text.replace(f'({source_text},', f'({replacement_text},')
        sub_text = sub_text.replace(f',{source_text})', f',{replacement_text})')
        return sub_text

    # parse the original program file to replace routine variables with associated tag names and inject tag variables
    def process(self, source: str, tag_strings: list[str]):
        with open(source, "r") as f:
            self.contents = f.read()
            for root, slices in self.tag_name_dict.items():
                for slice, tag_name in slices.items():
                    self.contents = (self.contents
                                     .replace(f"({root}{slice})", f"({tag_name})")
                                     .replace(f",{root}{slice})", f",{tag_name})")
                                     .replace(f"({root}{slice},", f"({tag_name},")
                                     .replace(f",{root}{slice},", f",{tag_name},")
                                     )
            for key, val in CONVERSION_DICT.items():
                # self.contents = self.contents.replace(f'({key})', f'({val})')
                self.contents = (self.contents
                                 .replace(f'({key})', f'({val})')
                                 .replace(f',{key})', f',{val})')
                                 .replace(f'({key},', f'({val},')
                                 .replace(f',{key},', f',{val},')
                                 )
            line_split_contents = self.contents.split('\n')
            tag_index = 0
            for idx, line in enumerate(line_split_contents):
                if line == '\tTAG':
                    tag_index = idx
            # splits the file contents at the `TAG` line and injects the tag_strings into the file
            self.contents = '\n'.join(line_split_contents[:tag_index+1] + tag_strings + line_split_contents[tag_index+1:])
        return self.contents

    def generate_doc(self, destination: str):
        with open(destination, "w") as d:
            d.write(self.contents)

def find_tag_name_duplicates(tag_name_dict: dict[str,dict[str, str]]) -> dict[str, list[str]]:
    tag_dict: dict[str,list[str]] = defaultdict(list)
    for base, extended in tag_name_dict.items():
        for array, name in extended.items():
            tag_dict[name].append(base + array)
    return {key: val for key, val in 
        tag_dict.items()
    if len(val) > 1} 

def replace_duplicates_in_tags(tag_name_dict, duplicate_dict):
    duplicate_names = duplicate_dict.keys()
    for base, extended in tag_name_dict.items():
        for array, name in extended.items():
            if name in duplicate_names:
                name: str = name + '_' + base + array.replace('[', '_').replace('.', '_').replace(']', '')
                name = name.replace('LENGTH', 'LEN')
                tag_name_dict[base][array] = name
    return tag_name_dict
            

def generate_tag_csv(tag_name_dict, tag_description_dict, mapped_data, file_name) -> None:
    csv_labels: list[str] = ['original_tag', 'Updated_tag', 'description', 'data']
    dataset: list[list[str]] = [csv_labels]
    for base, data in tag_name_dict.items():
        for array, tag_name in data.items():
            data_row: list[str] = [
                base+array,
                tag_name,
                tag_description_dict[base][array],
                mapped_data[base].get(array) if mapped_data[base].get(array) is not None else '',
            ]
            dataset.append(data_row)
    with open(file_name, 'w') as file:
        writer = csv.writer(file, delimiter='|')
        for row in dataset:
            writer.writerow(row)
    print("tag csv generated")


def generate_io_conversion_csv(conversion_dict: dict[str,str], file_name: str):
    csv_labels: list[str] = ['builtin name', 'converted I/O']
    dataset: list[list[str]] = [csv_labels]
    for key, val in conversion_dict.items():
        data_row: list[str] = [
            key,
            val,
        ]
        dataset.append(data_row)
    with open(file_name, 'w') as file:
        writer = csv.writer(file)
        for row in dataset:
            writer.writerow(row)
    print("tag conversion table generated")


def hmi_tag_name_compare(hmi_tag_file: str|Path, tag_name_dict: dict[str, dict[str,str]]):
    df = pd.read_csv(filepath_or_buffer=hmi_tag_file, header=0, skiprows=range(1, 12))
    address_dict = dict(zip(df[' Address'], df[' Tag Name']))
    updated_tag_name_dict = {}
    for base, data in tag_name_dict.items():
        for array, tag_name in data.items():
            verbose_array = ''
            if len(array.split('.')) == 1:
                verbose_array = array
            else:
                array_split = array.split('.')
                try:
                    if int(array_split[1]) < 10:
                        array_split[1] = '0' + array_split[1] 
                        verbose_array = '/'.join(array_split)
                        # print(verbose_array)
                    else:
                        verbose_array = array
                except ValueError:
                    verbose_array = array
            # print(verbose_array)

            tag_element = '::[SCS_PLC]'+base+verbose_array.replace('[', ':').replace(']', '').replace('.', '/')
            updated_tag_name_dict[tag_element] = tag_name
            if 'C5' in tag_element or 'C15' in tag_element:
                updated_tag_name_dict[tag_element + '.ACC'] = tag_name+'.ACC'
                updated_tag_name_dict[tag_element + '.DN'] = tag_name+'.DN'
    # return(updated_tag_name_dict.keys())
    
    # return(set(df[' Address']))
    # Current found addresses
    # return list(set(df[' Address']) & set(updated_tag_name_dict.keys()))
    # print('B3 items in tag name dict')
    # return [item for item in updated_tag_name_dict.keys() if 'B3' in item]
    print('Items in address list not found in tag name dict')
    return [item for item in df[' Address'].to_list() if item not in updated_tag_name_dict.keys()]
    


    return updated_tag_name_dict

    return dict(zip(df[' Address'], df[' Tag Name']))
    
    return df.head()



def main():
    (
        array_data_dict, 
        tag_name_dict, 
        tag_description_dict, 
        array_index_dict
    ) = SortTags().process()
    dup_dict = find_tag_name_duplicates(tag_name_dict)
    tag_name_dict = replace_duplicates_in_tags(tag_name_dict, dup_dict)

    mapped_data = CollectData(array_data_dict, array_index_dict).collect_data()

    tag_strings = generate_tag_strings(tag_name_dict, tag_description_dict, mapped_data)
    # generate_tag_csv(tag_name_dict, tag_description_dict, mapped_data, TAG_CSV_FILE_NAME)
    print(hmi_tag_name_compare(HMI_FILE_PATH, tag_name_dict))

    # generate_io_conversion_csv(CONVERSION_DICT, CONVERSION_FILE_NAME)
    
    # program_update = ProgramUpdate(tag_name_dict)
    # program_update.process(CONSUMED_FILE, tag_strings)
    # program_update.generate_doc(REPLACEMENT_DOC)


    # with open(PRODUCED_FILE, "w") as f:
    #     f.write("\n".join(tag_strings))

if __name__ == "__main__":
    main()

