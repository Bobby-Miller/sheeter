import pprint

source_tag_list: list[str] = []
source_tag_dict: dict[str, str] = {}
with open('tag_add.txt','r') as f:
    for line in f:
        source_tag_list.append(line.split(' : ')[0])
        try:
            source_tag_dict[line.split(' : ')[0]] = line.split(' : ')[1]
        except IndexError:
            source_tag_dict[line.split(' : ')[0]] = ''

# pprint.pprint(source_tag_list)

working_tag_list: list[str] = []
with open('tag_only_from_l5K.txt','r') as f:
    for line in f:
        working_tag_list.append(line.split(' : ')[0])
diff_list = list(set(source_tag_list) - set(working_tag_list))
# pprint.pprint(list(set(source_tag_list) - set(working_tag_list)))
# pprint.pprint(source_tag_dict)
pprint.pprint({
    key: val
    for key, val in source_tag_dict.items()
    if key in diff_list
})
