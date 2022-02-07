from pycparser import parse_file, c_ast


class InputGenerator:
    def __init__(self, fileName, functionName):
        self.fileName = fileName
        self.functionName = functionName
        self.ast = parse_file(fileName)
        self.otherFuncs = []
        for func in self.ast.ext:
            if isinstance(func, c_ast.FuncDef):
                if func.decl.name == functionName:
                    self.target = func
                else:
                    self.otherFuncs.append(func)
            else:
                self.otherFuncs.append(func)
        if self.target.decl.type.args is None:
            return
        self.varNames = list(param_decl.name for param_decl in self.target.decl.type.args.params)
        self.varTypes = list(param_decl.type.type.names[0] for param_decl in self.target.decl.type.args.params)
