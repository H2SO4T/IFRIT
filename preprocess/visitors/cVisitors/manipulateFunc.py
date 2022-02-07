from pycparser import c_ast, parse_file
from . import GlobalVisitor
from . import ScanfVisitor
from copy import copy, deepcopy


class FuncManipulator:
    def __init__(self, filename, function_name):
        self.filename = filename
        self.ast = parse_file(filename)
        self.otherFuncs = []
        for func in self.ast.ext:
            if isinstance(func, c_ast.FuncDef):
                if func.decl.name == function_name:
                    self.target = func
                    if isinstance(func.children()[0][1].children()[0][1].children()[0][1], c_ast.ParamList):
                        self.params = func.children()[0][1].children()[0][1].children()[0][1]
                    else:
                        self.params = c_ast.ParamList([])
                        self.target.decl.type.args = self.params
                elif func.decl.name != "main":
                    self.otherFuncs.append(func)
            else:
                self.otherFuncs.append(func)

    def removeFunction(self, function_name):
        for func in list(self.otherFuncs):
            if func.decl.name == function_name:
                self.otherFuncs.remove(func)

    def cleanVarInit(self, var):
        if var.init == None:
            return var
        varAux = copy(var)
        varAux.init = None
        return varAux

    def addGlobalParams(self):
        glob_vis = GlobalVisitor.GlobalVisitor()
        for var in glob_vis.getVariables(self.ast):
            varAlt = deepcopy(var)
            varAlt.name = '__global__' + varAlt.name
            if (not (isinstance(varAlt.type, c_ast.ArrayDecl))):
                varAlt.type.declname = varAlt.name
                assignmentVars = c_ast.Assignment(op='=', lvalue=c_ast.ID(var.name), rvalue=c_ast.ID(varAlt.name))
                if (varAlt.init != None):
                    varAlt.init = None
                self.params.params.append(varAlt)
                self.target.body.block_items.insert(0, assignmentVars)

    # def	addScanfParams(self):
    #     scanfVis=ScanfVisitor.ScanfVisitor()
    #     varsList=scanfVis.getVariables(self.main)
    #     for var in varsList:
    #         self.params.params.append(self.cleanVarInit(var))
    #         self.main.body.block_items.remove(var)
    #     for block in list(self.main.body.block_items):
    #         if isinstance(block,c_ast.FuncCall):
    #             if block.name.name == 'scanf':
    #                 self.main.body.block_items.remove(block)
