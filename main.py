import ast
import os, re
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
CONVERSION_FILE_NAME = "tag_conversion_jan_8_2026.csv"
UPDATED_HMI_TAG_OUT = "hmi_tag_output_jan_12_2026.csv"
SCREEN_FILE_LIST: list[str|Path] = [
    current_dir / "HMI_source_files" / name for name in [
        "01_AUTO.xml",
        "02_STTS.xml",
        "03_MENU.xml",
        "04_RCP.xml",
        "05_RUN.xml",
        "06_STP.xml",
        "07_STP.xml",
        "08_MNL.xml",
        "09_MNL.xml",
        "10_SYS.xml",
        "12_MTRLW.xml",
        "14_MTRLX.xml",
        "30_PLY.xml",
        "50_VNDR.xml",
    ]
]

TIMER_DONE_DICT = {
    "T14[0].EN": "UPDATE_CUR_PLY_COUNT_TD.EN",
    "T14[1].EN": "UPDATE_CUR_PLY_TYPE_AND_LENGTH_TD.EN",
    "T14[10].EN": "MOVE_CUR_MAT_AND_SIDE_BACK_TD.EN",
    "T14[11].EN": "AUTO_CHECK_IF_DONE_TD.EN",
    "T14[12].EN": "MOVE_PRINT_AND_TABLE_TO_CUR_SIDE_TD.EN",
    "T14[15].EN": "MOVE_CUR_SIDE_AXIS_TO_CUT_TD.EN",
    "T14[18].EN": "STN_SERVO_DRIVE_RESET_TO.EN",
    "T14[19].EN": "AUTO_CYCLE_COMPLETE_TD.EN",
    "T14[2].EN": "MOVE_GRIPPER_LENGTH_TD.EN",
    "T14[20].EN": "STN_MAT_W_MOTION_TO.EN",
    "T14[21].EN": "STN_MAT_X_MOTION_TO.EN",
    "T14[22].EN": "STN_SIDE_W_AXIS_MOTION_TO.EN",
    "T14[23].EN": "STN_SIDE_X_AXIS_MOTION_TO.EN",
    "T14[24].EN": "STN_PRINT_AXIS_MOTION_TO.EN",
    "T14[25].EN": "STN_PRINT_SIDE_NOT_AT_W_TO.EN",
    "T14[26].EN": "STN_PRINT_SIDE_NOT_AT_X_TO.EN",
    "T14[27].EN": "STN_TABLE_SIDE_NOT_AT_W_TO.EN",
    "T14[28].EN": "STN_TABLE_SIDE_NOT_AT_X_TO.EN",
    "T14[29].EN": "STN_GRIPPER_W_NOT_OPENED_AT_PICK_TO.EN",
    "T14[3].EN": "MOV_CUR_SIDE_AXIS_TO_PICK_AND_MAT_CLR_TD.EN",
    "T14[30].EN": "STN_GRIPPER_W_NOT_OPENED_AT_PLACE_TO.EN",
    "T14[31].EN": "STN_GRIPPER_X_NOT_OPENED_AT_PICK_TO.EN",
    "T14[32].EN": "STN_GRIPPER_X_NOT_OPENED_AT_PLACE_TO.EN",
    "T14[4].EN": "MOVE_CUR_MAT_TO_GRIP_TD.EN",
    "T14[5].EN": "MOVE_CUR_MAT_TO_CUT_TD.EN",
    "T14[6].EN": "AUTO_TURN_ON_SHEAR_TD.EN",
    "T14[7].EN": "AUTO_TURN_OFF_SHEAR_TD.EN",
    "T14[8].EN": "MOVE_CUR_SIDE_TO_PLACE_AND_MAT_CLR_TD.EN",
    "T14[9].EN": "AUTO_CLOSE_CUR_SIDE_GRIPPER_TD.EN",
    "T206[0].EN": "A1_READ_INPUT_ASSEMBLY_DELAY.EN",
    "T206[10].EN": "A2_READ_INPUT_ASSEMBLY_DELAY.EN",
    "T206[12].EN": "A2_READ_OUTPUT_ASSEMBLY_DELAY.EN",
    "T206[2].EN": "A1_READ_OUTPUT_ASSEMBLY_DELAY.EN",
    "T4[0].EN": "SYS_ENABLE_MAT_DRIVES_HW_TD.EN",
    "T4[1].EN": "SYS_CYCLE_START_TD.EN",
    "T4[10].EN": "SYS_MAT_W_DRIVE_NOT_ENABLED_TO.EN",
    "T4[11].EN": "SYS_MAT_X_DRIVE_NOT_ENABLED_TO.EN",
    "T4[12].EN": "SYS_PRINT_AXIS_DRIVE_ALARM_TO.EN",
    "T4[13].EN": "SYS_SIDE_W_AXIS_DRIVE_ALARM_TO.EN",
    "T4[14].EN": "SYS_SIDE_X_AXIS_DRIVE_ALARM_TO.EN",
    "T4[2].EN": "SYS_UNLATCH_HMI_NO_BTTN.EN",
    "T4[20].EN": "INIT_BEGIN_CYCLE_TIME_DELAY.EN",
    "T4[21].EN": "INIT_MOVE_PRINT_AND_TABLE_TO_W_TD.EN",
    "T4[22].EN": "INIT_HOME_PRINT_AXIS_TD.EN",
    "T4[23].EN": "INIT_JOG_SIDE_W_AXIS_OFF_HOME_TD.EN",
    "T4[24].EN": "INIT_JOG_SIDE_X_AXIS_OFF_HOME_TD.EN",
    "T4[25].EN": "SYS_UNLATCH_HMI_YES_BUTTON.EN",
    "T4[26].EN": "SYS_UNLATCH_HMI_RESTART_BTTN_T4_26.EN",
    "T4[26].EN.EN": "SYS_UNLATCH_HMI_RESTART_BTTN_T4_26_EN.EN",
    "T4[29].EN": "INIT_CYCLE_COMPLETE_TD.EN",
    "T4[3].EN": "SYS_UNLATCH_HMI_ABORT_BTTN.EN",
    "T4[30].EN": "INIT_TURN_ON_SHEAR_TD.EN",
    "T4[31].EN": "INIT_TURN_OFF_SHEAR_TD.EN",
    "T4[32].EN": "INIT_JOG_CUR_SIDE_TO_PLACE_TD.EN",
    "T4[33].EN": "INIT_JOG_CUR_SIDE_OFF_PLACE_TD.EN",
    "T4[34].EN": "INIT_MOVE_CUR_SIDE_TO_GRIPPER_TD.EN",
    "T4[35].EN": "INIT_CLOSE_CUR_SIDE_GRIPPER_TD.EN",
    "T4[36].EN": "INIT_MOVE_MAT_CLR_TD.EN",
    "T4[37].EN": "INIT_MOVE_MAT_BACK_TD.EN",
    "T4[4].EN": "SYS_1_SEC_TIMER.EN",
    "T4[40].EN": "SYS_TURN_OFF_SHEAR_TD.EN",
    "T4[41].EN": "SYS_MOVE_MAT_CLR_TD.EN",
    "T4[42].EN": "SYS_MOVE_MAT_BACK_TD.EN",
    "T4[47].EN": "MAN_TURN_OFF_SHEAR_TD.EN",
    "T4[48].EN": "MAN_MOVE_MAT_CLR_TD.EN",
    "T4[49].EN": "MAN_MOVE_MAT_BACK_TD.EN",
    "T4[50].EN": "MAN_SIDE_W_AXIS_TO_PICK_ON_TGGL_TD.EN",
    "T4[51].EN": "MAN_SIDE_W_AXIS_TO_CUT_ON_TGGL_TD.EN",
    "T4[52].EN": "MAN_SIDE_W_AXIS_TO_PLACE_ON_TGGL_TD.EN",
    "T4[53].EN": "MAN_SIDE_W_AXIS_RETRACT_ON_TGGL_TD.EN",
    "T4[54].EN": "MAN_SIDE_X_AXIS_TO_PICK_ON_TGGL_TD.EN",
    "T4[55].EN": "MAN_SIDE_X_AXIS_TO_CUT_ON_TGGL_TD.EN",
    "T4[56].EN": "MAN_SIDE_X_AXIS_TO_PLACE_ON_TGGL_TD.EN",
    "T4[57].EN": "MAN_SIDE_X_AXIS_RETRACT_ON_TGGL_TD.EN",
    "T4[58].EN": "MAN_JOG_SIDE_W_AXIS_OFF_HOME_TD.EN",
    "T4[59].EN": "MAN_JOG_SIDE_X_AXIS_OFF_HOME_TD.EN",
    "T4[6].EN": "SYS_RESET_DATA_TIME_DELAY.EN",
    "T4[7].EN": "SYS_ENABLE_MAT_W_DRIVE_SW_TD.EN",
    "T4[8].EN": "SYS_ENABLE_MAT_X_DRIVE_SW_TD.EN",
    "T4[9].EN": "SYS_HALF_SEC_TIMER.EN",
    "T14[0].DN": "UPDATE_CUR_PLY_COUNT_TD.DN",
    "T14[1].DN": "UPDATE_CUR_PLY_TYPE_AND_LENGTH_TD.DN",
    "T14[10].DN": "MOVE_CUR_MAT_AND_SIDE_BACK_TD.DN",
    "T14[11].DN": "AUTO_CHECK_IF_DONE_TD.DN",
    "T14[12].DN": "MOVE_PRINT_AND_TABLE_TO_CUR_SIDE_TD.DN",
    "T14[15].DN": "MOVE_CUR_SIDE_AXIS_TO_CUT_TD.DN",
    "T14[18].DN": "STN_SERVO_DRIVE_RESET_TO.DN",
    "T14[19].DN": "AUTO_CYCLE_COMPLETE_TD.DN",
    "T14[2].DN": "MOVE_GRIPPER_LENGTH_TD.DN",
    "T14[20].DN": "STN_MAT_W_MOTION_TO.DN",
    "T14[21].DN": "STN_MAT_X_MOTION_TO.DN",
    "T14[22].DN": "STN_SIDE_W_AXIS_MOTION_TO.DN",
    "T14[23].DN": "STN_SIDE_X_AXIS_MOTION_TO.DN",
    "T14[24].DN": "STN_PRINT_AXIS_MOTION_TO.DN",
    "T14[25].DN": "STN_PRINT_SIDE_NOT_AT_W_TO.DN",
    "T14[26].DN": "STN_PRINT_SIDE_NOT_AT_X_TO.DN",
    "T14[27].DN": "STN_TABLE_SIDE_NOT_AT_W_TO.DN",
    "T14[28].DN": "STN_TABLE_SIDE_NOT_AT_X_TO.DN",
    "T14[29].DN": "STN_GRIPPER_W_NOT_OPENED_AT_PICK_TO.DN",
    "T14[3].DN": "MOV_CUR_SIDE_AXIS_TO_PICK_AND_MAT_CLR_TD.DN",
    "T14[30].DN": "STN_GRIPPER_W_NOT_OPENED_AT_PLACE_TO.DN",
    "T14[31].DN": "STN_GRIPPER_X_NOT_OPENED_AT_PICK_TO.DN",
    "T14[32].DN": "STN_GRIPPER_X_NOT_OPENED_AT_PLACE_TO.DN",
    "T14[4].DN": "MOVE_CUR_MAT_TO_GRIP_TD.DN",
    "T14[5].DN": "MOVE_CUR_MAT_TO_CUT_TD.DN",
    "T14[6].DN": "AUTO_TURN_ON_SHEAR_TD.DN",
    "T14[7].DN": "AUTO_TURN_OFF_SHEAR_TD.DN",
    "T14[8].DN": "MOVE_CUR_SIDE_TO_PLACE_AND_MAT_CLR_TD.DN",
    "T14[9].DN": "AUTO_CLOSE_CUR_SIDE_GRIPPER_TD.DN",
    "T206[0].DN": "A1_READ_INPUT_ASSEMBLY_DELAY.DN",
    "T206[10].DN": "A2_READ_INPUT_ASSEMBLY_DELAY.DN",
    "T206[12].DN": "A2_READ_OUTPUT_ASSEMBLY_DELAY.DN",
    "T206[2].DN": "A1_READ_OUTPUT_ASSEMBLY_DELAY.DN",
    "T4[0].DN": "SYS_ENABLE_MAT_DRIVES_HW_TD.DN",
    "T4[1].DN": "SYS_CYCLE_START_TD.DN",
    "T4[10].DN": "SYS_MAT_W_DRIVE_NOT_ENABLED_TO.DN",
    "T4[11].DN": "SYS_MAT_X_DRIVE_NOT_ENABLED_TO.DN",
    "T4[12].DN": "SYS_PRINT_AXIS_DRIVE_ALARM_TO.DN",
    "T4[13].DN": "SYS_SIDE_W_AXIS_DRIVE_ALARM_TO.DN",
    "T4[14].DN": "SYS_SIDE_X_AXIS_DRIVE_ALARM_TO.DN",
    "T4[2].DN": "SYS_UNLATCH_HMI_NO_BTTN.DN",
    "T4[20].DN": "INIT_BEGIN_CYCLE_TIME_DELAY.DN",
    "T4[21].DN": "INIT_MOVE_PRINT_AND_TABLE_TO_W_TD.DN",
    "T4[22].DN": "INIT_HOME_PRINT_AXIS_TD.DN",
    "T4[23].DN": "INIT_JOG_SIDE_W_AXIS_OFF_HOME_TD.DN",
    "T4[24].DN": "INIT_JOG_SIDE_X_AXIS_OFF_HOME_TD.DN",
    "T4[25].DN": "SYS_UNLATCH_HMI_YES_BUTTON.DN",
    "T4[26].DN": "SYS_UNLATCH_HMI_RESTART_BTTN_T4_26.DN",
    "T4[26].EN.DN": "SYS_UNLATCH_HMI_RESTART_BTTN_T4_26_EN.DN",
    "T4[29].DN": "INIT_CYCLE_COMPLETE_TD.DN",
    "T4[3].DN": "SYS_UNLATCH_HMI_ABORT_BTTN.DN",
    "T4[30].DN": "INIT_TURN_ON_SHEAR_TD.DN",
    "T4[31].DN": "INIT_TURN_OFF_SHEAR_TD.DN",
    "T4[32].DN": "INIT_JOG_CUR_SIDE_TO_PLACE_TD.DN",
    "T4[33].DN": "INIT_JOG_CUR_SIDE_OFF_PLACE_TD.DN",
    "T4[34].DN": "INIT_MOVE_CUR_SIDE_TO_GRIPPER_TD.DN",
    "T4[35].DN": "INIT_CLOSE_CUR_SIDE_GRIPPER_TD.DN",
    "T4[36].DN": "INIT_MOVE_MAT_CLR_TD.DN",
    "T4[37].DN": "INIT_MOVE_MAT_BACK_TD.DN",
    "T4[4].DN": "SYS_1_SEC_TIMER.DN",
    "T4[40].DN": "SYS_TURN_OFF_SHEAR_TD.DN",
    "T4[41].DN": "SYS_MOVE_MAT_CLR_TD.DN",
    "T4[42].DN": "SYS_MOVE_MAT_BACK_TD.DN",
    "T4[47].DN": "MAN_TURN_OFF_SHEAR_TD.DN",
    "T4[48].DN": "MAN_MOVE_MAT_CLR_TD.DN",
    "T4[49].DN": "MAN_MOVE_MAT_BACK_TD.DN",
    "T4[50].DN": "MAN_SIDE_W_AXIS_TO_PICK_ON_TGGL_TD.DN",
    "T4[51].DN": "MAN_SIDE_W_AXIS_TO_CUT_ON_TGGL_TD.DN",
    "T4[52].DN": "MAN_SIDE_W_AXIS_TO_PLACE_ON_TGGL_TD.DN",
    "T4[53].DN": "MAN_SIDE_W_AXIS_RETRACT_ON_TGGL_TD.DN",
    "T4[54].DN": "MAN_SIDE_X_AXIS_TO_PICK_ON_TGGL_TD.DN",
    "T4[55].DN": "MAN_SIDE_X_AXIS_TO_CUT_ON_TGGL_TD.DN",
    "T4[56].DN": "MAN_SIDE_X_AXIS_TO_PLACE_ON_TGGL_TD.DN",
    "T4[57].DN": "MAN_SIDE_X_AXIS_RETRACT_ON_TGGL_TD.DN",
    "T4[58].DN": "MAN_JOG_SIDE_W_AXIS_OFF_HOME_TD.DN",
    "T4[59].DN": "MAN_JOG_SIDE_X_AXIS_OFF_HOME_TD.DN",
    "T4[6].DN": "SYS_RESET_DATA_TIME_DELAY.DN",
    "T4[7].DN": "SYS_ENABLE_MAT_W_DRIVE_SW_TD.DN",
    "T4[8].DN": "SYS_ENABLE_MAT_X_DRIVE_SW_TD.DN",
    "T4[9].DN": "SYS_HALF_SEC_TIMER.DN",
}

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

IO_DICT: dict[str, str] = {
    '::[SCS_PLC]I:0.0/00': 'Local:1:I.Pt00.Data',
    '::[SCS_PLC]I:0.0/01': 'Local:1:I.Pt01.Data',
    '::[SCS_PLC]I:0.0/02': 'Local:1:I.Pt02.Data',
    '::[SCS_PLC]I:0.0/03': 'Local:1:I.Pt03.Data',
    '::[SCS_PLC]I:0.0/04': 'Local:1:I.Pt04.Data',
    '::[SCS_PLC]I:0.0/05': 'Local:1:I.Pt05.Data',
    '::[SCS_PLC]I:0.0/06': 'Local:1:I.Pt06.Data',
    '::[SCS_PLC]I:0.0/07': 'Local:1:I.Pt07.Data',
    '::[SCS_PLC]I:0.0/08': 'Local:1:I.Pt08.Data',
    '::[SCS_PLC]I:0.0/09': 'Local:1:I.Pt09.Data',
    '::[SCS_PLC]I:0.0/10': 'Local:1:I.Pt10.Data',
    '::[SCS_PLC]I:0.0/11': 'Local:1:I.Pt11.Data',
    '::[SCS_PLC]I:0.0/12': 'Local:1:I.Pt12.Data',
    '::[SCS_PLC]I:0.0/13': 'Local:1:I.Pt13.Data',
    '::[SCS_PLC]I:0.0/14': 'Local:1:I.Pt14.Data',
    '::[SCS_PLC]I:0.0/15': 'Local:1:I.Pt15.Data',
    '::[SCS_PLC]I:0.1/00': 'Local:2:I.Pt00.Data',
    '::[SCS_PLC]I:0.1/01': 'Local:2:I.Pt01.Data',
    '::[SCS_PLC]I:0.1/02': 'Local:2:I.Pt02.Data',
    '::[SCS_PLC]I:0.1/03': 'Local:2:I.Pt03.Data',
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

def update_timer_tags(source_file: str|Path, destination_file: str|Path, timer_dict: dict[str,str]):
    with open(source_file, "r") as f:
        contents = f.read()
        for find_item, replace_item in timer_dict.items():
            contents = contents.replace(find_item, replace_item)
    with open(destination_file, "w") as d:
        d.write(contents)

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


def hmi_tag_name_compare(
    hmi_tag_file: str|Path, 
    tag_name_dict: dict[str, dict[str,str]],
    io_tag_dict: None|dict[str, str] = None,
) -> tuple[dict[str, str], list[str]]:
    """
    Produce a map of HMI tags to converted PLC tags, and a list of excluded tags
    """
    df = pd.read_csv(filepath_or_buffer=hmi_tag_file, header=0, skiprows=range(1, 12)) # ty: ignore[no-matching-overload]
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
            if io_tag_dict is not None:
                updated_tag_name_dict = updated_tag_name_dict|io_tag_dict
    # return(updated_tag_name_dict.keys())
    # return(updated_tag_name_dict)
    return(
        # Mapping of HMI tags to converted tag names 
        {
            key: val for key, val in updated_tag_name_dict.items()
            if key in set(df[' Address'])
        },
        # Items in address list not found in tag name dict
        [item for item in df[' Address'].to_list() 
            if item not in updated_tag_name_dict.keys() and isinstance(item, str)]

    )
    
    # return(set(df[' Address']))
    # Current found addresses
    # return list(set(df[' Address']) & set(updated_tag_name_dict.keys()))
    # print('B3 items in tag name dict')
    # return [item for item in updated_tag_name_dict.keys() if 'B3' in item]
    # print('Items in address list not found in tag name dict')
    # return [item for item in df[' Address'].to_list() if item not in updated_tag_name_dict.keys()]

def generate_updated_tag_csv(
    source_file_name: str|Path,
    destination_file_name: str|Path,
    address: str, 
    hmi_tag_name: str, 
    hmi_tag_map: dict[str, str],
) -> dict[str, str]:
    """
    Processes a CSV file containing HMI tag mappings. Replaces values to update the tag mapping.
    Delivers an updated dictionary

    Parameters:
    ---------
    source_file_name : str|Path
        Path to the input CSV file
    destination_file_name : str|Path
        Path to the modified output CSV file
    address : str
        column name where the PLC path is mapped
    hmi_tag_name : str
        column name where the hmi tag is mapped
    hmi_tag_map : str
        dictionary of original plc tags mapped to updated plc tag duplicate_names
    
    Returns:
    --------
    dictionary : find-and-replace substitution for hmi tags | key - original data | value - updated tag
    """
    with open(source_file_name, 'r') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise TypeError("bad return for fieldnames")
        if address not in fieldnames:
            raise ValueError(f"Address Column '{address}' not found in field names")
        if hmi_tag_name not in fieldnames:
            raise ValueError(f"HMI tag name column '{hmi_tag_name}' not found in field names")

        rows: list[dict[str, str]] = []
        hmi_tag_dict: dict[str, str] = {}
        for row in reader:
            original_tag = row[address]
            if original_tag in hmi_tag_map:
                new_tag = f"::[SCS_PLC]{hmi_tag_map[original_tag]}"
                sub_tag = hmi_tag_map[original_tag]
                if 'Local' in sub_tag:
                    slot_num = sub_tag.split(':')[1]
                    pt_num = sub_tag.split('Pt')[1].split('.')[0]
                    sub_tag = f"Local_S{slot_num}_P{pt_num}"
                    break_hit = True
                hmi_tag_dict[row[hmi_tag_name]] = sub_tag
                row[address] = new_tag
                row[hmi_tag_name] = sub_tag
                if '.ACC' in sub_tag or '.DN' in sub_tag:
                    row[address] = new_tag.replace('.ACC', '').replace('.DN', '')
                    row[hmi_tag_name] = sub_tag.replace('.ACC', '').replace('.DN', '')
            rows.append(row)


        with open(destination_file_name, 'w') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            print(f"Output saved to: {destination_file_name}")

        return hmi_tag_dict

def update_screen_exports(
    screen_file_list: list[str|Path], 
    substitution_dict: dict[str, str],
    output_appendage: str = '_mod'
) -> list[str]:
    """
    Processes FactoryTalk View screen (.gfx) files by performing multiple
    find-and-replace operations based on a substitution dictionary.
    
    For each file:
    - Reads the content
    - Applies all substitutions from the dictionary
    - Saves a new file with the specified appendage added before the extension
    
    Parameters:
    -----------
    screen_file_list : List[str]
        List of full paths to .gfx (or other text-based) screen files
        
    substitution_dict : Dict[str, str]
        Dictionary of {old_string: new_string} to replace
        Example: {"[OldPLC]": "[NewPLC]", "Local::": "[Shortcut]"}
        
    output_appendage : str, optional
        String to append to the filename (before extension)
        Default: "_mod"
        
    Returns:
    --------
    List[str]
        List of paths to the newly created output files
        
    Raises:
    -------
    FileNotFoundError
        If any input file doesn't exist
    """
    created_files = []
    
    for input_path in screen_file_list:
        # Skip if file doesn't exist
        if not os.path.isfile(input_path):
            print(f"Warning: File not found, skipping: {input_path}")
            continue
            
        # Read the original file content
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {input_path}: {e}")
            continue
            
        # Apply all substitutions (in order of dictionary keys)
        modified_content = content
        for old, new in substitution_dict.items():
            # Using regex with word boundaries for safer replacement
            # (optional: remove \b if you want to match inside words)
            modified_content = re.sub(
                re.escape(old),
                new,
                modified_content
            )
            
        # Create output filename
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}{output_appendage}{ext}"
        
        # Write the modified content
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"Created: {output_path}")
            created_files.append(output_path)
        except Exception as e:
            print(f"Error writing {output_path}: {e}")
            
    print(f"\nProcessing complete. Created {len(created_files)} file(s).")
    return created_files


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
    hmi_tag_map, hmi_exclusion_list = hmi_tag_name_compare(HMI_FILE_PATH, tag_name_dict, IO_DICT)

    print(f'length of dict: {len(hmi_tag_map)} | Length of exclusion list: {len(hmi_exclusion_list)}')
    hmi_substitution_dict = generate_updated_tag_csv(
        HMI_FILE_PATH,
        UPDATED_HMI_TAG_OUT,
        ' Address',
        ' Tag Name',
        hmi_tag_map
    )
    update_screen_exports(
        SCREEN_FILE_LIST, 
        hmi_substitution_dict,
    )
    # generate_io_conversion_csv(CONVERSION_DICT, CONVERSION_FILE_NAME)
    
    # program_update = ProgramUpdate(tag_name_dict)
    # program_update.process(CONSUMED_FILE, tag_strings)
    # program_update.generate_doc(REPLACEMENT_DOC)


    # with open(PRODUCED_FILE, "w") as f:
    #     f.write("\n".join(tag_strings))

if __name__ == "__main__":
    update_timer_tags(
        'Sheeter_In_Prog_print_remove_1_15_2026.L5K', 
        'Sheeter_timer_sub_1_15_2026_B.L5K',
        TIMER_DONE_DICT
    )
    # main()

