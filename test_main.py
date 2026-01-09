from main import dint_to_binary_str, YNBool

def test_dint_to_bin_str():
    assert(dint_to_binary_str(-1) == '1'*32)
    assert(dint_to_binary_str(-2) == '0'+'1'*31)
    assert(dint_to_binary_str(-1431655766)) == '01'*16
    assert(dint_to_binary_str(-1227133514)) == '011'*10 + '01'

def test_ynbool():
    assert(YNBool("y") == "Yes")
    assert(YNBool("n") == "No")
    assert(YNBool(True) == "Yes")
    assert(YNBool(False) == "No")
