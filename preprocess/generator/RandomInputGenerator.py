import random
from .InputGenerator import InputGenerator

class RandomInputGenerator(InputGenerator):
#    def __init__(self,fileName,functionName):
#        super(fileName,functionName)

    def generateRandomInputs(self,numInputs):
        inputs=[]
        for i in range(numInputs):
            inputVal=[]
            for var in self.varTypes:
                if var == "int":
                    inputVal.append(random.randint(-10000,10000))
                elif var == "float" or var == "double":
                    inputVal.append(random.randint(-10000,10000)*random.random())
                else:
                    print("Unrecognised type")
                    inputVal.append(0)
            inputs.append(inputVal)
        return inputs
