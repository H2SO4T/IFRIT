from pycparser import parse_file, c_generator
import preprocess.support.compareSingle as compareSingle
import preprocess.generator.InputGenerator as gen
from preprocess.visitors.cVisitors import manipulateMain
from reindenter import reindent


def get_children(node):
    if isinstance(node, tuple):
        return node[1].children()
    return node.children()


def get_label(node):
    return node


def label_dist(node1, node2):
    if type(node1) != type(node2):
        return 1
    if isinstance(node1, tuple) and isinstance(node2, tuple):
        return label_dist(node1[1], node2[1])
    if node1.attr_names != node2.attr_names:
        return 1
    for attr in node1.attr_names:
        if getattr(node1, attr) != getattr(node2, attr):
            return 1
    return 0


def compute_difference(fixed, buggy, fun="main"):
    file_fixed = fixed
    file_bug = buggy
    function_name = fun

    if function_name == "main":
        manipulation_fix = manipulateMain.MainManipulator(file_fixed)
        manipulation_fix.eliminateParams()
        manipulation_fix.addGlobalParams()
        manipulation_fix.addScanfParams()
        gen_code = c_generator.CGenerator()
        F = open(f"{file_fixed}.pre.c", "w")
        F.write(gen_code.visit(manipulation_fix.main))
        F.close()
        # file_fixed = file_fixed + ".pre.c"
        manipulation_bug = manipulateMain.MainManipulator(file_bug)
        manipulation_bug.eliminateParams()
        manipulation_bug.addGlobalParams()
        manipulation_bug.addScanfParams()
        F = open(f"{file_bug}.pre.c", "w")
        F.write(gen_code.visit(manipulation_bug.main))
        F.close()
        # file_bug = file_bug + ".pre.c"
        function_name = "mainFake"

    reindent(f"{file_fixed}.pre.c")
    reindent(f"{file_bug}.pre.c")
    gen_fixed = gen.InputGenerator(f"{file_fixed}.pre.c", function_name)
    gen_bug = gen.InputGenerator(f"{file_bug}.pre.c", function_name)
    gen_code = c_generator.CGenerator()
    dictio = compareSingle.simple_distance(
        gen_fixed.target, gen_bug.target, get_children, get_label, label_dist
    )
    filtered = [i for i in dictio if i[0] != "KEEP"]
    max_a = None
    max_b = None
    for elem in filtered:
        if elem[1] == "A" and max_a is None:
            max_a = elem
        elif elem[1] == "A" and max_a is not None and max_a[2] < elem[2]:
            max_a = elem
        elif elem[1] == "B" and max_b is None:
            max_b = elem
        elif elem[1] == "B" and max_b is not None and max_b[2] < elem[2]:
            max_b = elem
    return max_a[2], max_b[2]
