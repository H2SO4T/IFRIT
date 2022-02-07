from pycparser import c_ast, parse_file
from . import GlobalVisitor
from . import ScanfVisitor
from copy import copy
import os
import pycparser_fake_libc


class MainManipulator:
    def __init__(self, fileName):
        self.fileName = fileName
        self.ast = parse_file(fileName, use_cpp=True,
                              cpp_args=['-E', rf'-I{pycparser_fake_libc.directory}'])
        self.otherFuncs = []
        for func in self.ast.ext:
            if isinstance(func, c_ast.FuncDef):
                if func.decl.name == 'main' or func.decl.name == 'mainFake':
                    self.main = func
                else:
                    self.otherFuncs.append(func)
            else:
                self.otherFuncs.append(func)

    def removeFunction(self, funcName):
        for func in list(self.otherFuncs):
            if func.decl.name == funcName:
                self.otherFuncs.remove(func)

    def eliminateParams(self):
        self.params = c_ast.ParamList([])
        mainDec = c_ast.Decl(name='mainFake', quals=[], init=None, bitsize=None, storage=[], funcspec=[],
                             type=c_ast.FuncDecl(self.params,
                                                 c_ast.TypeDecl('mainFake', [], c_ast.IdentifierType(['int']))))
        self.main = c_ast.FuncDef(mainDec, None, self.main.body)
        for i, func in enumerate(self.ast.ext):
            if isinstance(func, c_ast.FuncDef):
                if func.decl.name == 'main':
                    self.ast.ext[i] = self.main

    def cleanVarInit(self, var):
        if var.init is None:
            return var
        varAux = copy(var)
        varAux.init = None
        return varAux

    def addGlobalParams(self):
        glob_vis = GlobalVisitor.GlobalVisitor()
        for var in glob_vis.getVariables(self.ast):
            if var.init == None:
                self.params.params.append(var)
            else:
                self.main.body.block_items.insert(0, var)

    def addScanfParams(self):
        scanfVis = ScanfVisitor.ScanfVisitor()
        varsList = scanfVis.getVariables(self.main)
        for var in varsList:
            self.params.params.append(self.cleanVarInit(var))
            self.main.body.block_items.remove(var)
        for block in list(self.main.body.block_items):
            if isinstance(block, c_ast.FuncCall):
                if block.name.name == 'scanf':
                    self.main.body.block_items.remove(block)
