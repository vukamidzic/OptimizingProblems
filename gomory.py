import FreeSimpleGUI as sg
from pulp import *
import re
import pprint

printer = pprint.PrettyPrinter()

def createProblem(input: str, varSize: int, vars: list, varType):
    problem = LpProblem(name='Gomory')
    
    for i in range(varSize):
        var = LpVariable(name=f'x{i+1}', lowBound=0, cat=varType)
        vars.append(var)
    
    content = input.split('->')
    sense = content[1].strip()
    
    if sense.lower() == 'min': problem.sense = LpMinimize
    else: problem.sense = LpMaximize
    
    varReg = re.compile(r'(\+|\-)?\s*([1-9]+)?(\s*\*\s*)?x[1-9]+')
    funcExpr = LpAffineExpression()
    
    for i in re.finditer(varReg, content[0].strip()):
        term = i.group(0).split('*x')
        const = int(re.sub(' ', '', term[0].strip()))
        idx = int(term[1])
        
        printer.pprint(problem.variablesDict().get(vars[idx-1]))
        funcExpr.addInPlace(const*vars[idx-1])
        
    problem += funcExpr
    return problem
          
def createConstraint(constrStr, vars):
    signReg = re.compile(r'<=|>=|=')
    
    tmpDict = {
        "=" : LpConstraintEQ,
        "<=" : LpConstraintLE,
        ">=" : LpConstraintGE
    }
    
    content = list(map(lambda x: x.strip(), re.split(signReg, constrStr)))
    sign = re.findall(signReg, constrStr)[0]
    
    constraint = LpConstraint()
    constraint.sense = tmpDict.get(sign)
    constraint.changeRHS(int(content[1]))
    
    varReg = re.compile(r'(\+|\-)?\s*([1-9]+)?(\s*\*\s*)?x[1-9]+')
    
    for i in re.finditer(varReg, content[0].strip()):
        term = i.group(0).split('*x')
        const = int(re.sub(' ', '', term[0].strip()))
        idx = int(term[1])
        
        constraint.addInPlace(const*vars[idx-1])
    
    return constraint

layout = [
    [sg.Text("Unesite broj promenljivih i broj ogranicenja:") ],
    [sg.Input(key='VARS_SIZE',size=(10,1)), sg.Input(key='CONSTR_SIZE',size=(10,1))],
    [sg.Text("Izaberite tip programiranja:") ],
    [sg.Listbox(key='TYPE',values=['Linearno programiranje', 'Celobrojno programiranje'], size=(22,2))],
    [sg.Text("Unesite problem:") ],
    [sg.Multiline(size=(60, 30), rstrip=True, key='-INPUT-')],
    [sg.Button(button_text='Resi', key='SOLVE', size=(20,2)), sg.Multiline("F(x) = ", key='-FUNCTION-')],
    [sg.Multiline(size=(50, 5),key='-OUTPUT-')],
]

window = sg.Window('Celobrojno programiranje', layout=layout, resizable=True, size=(600, 800))

while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break
    elif event == 'SOLVE':
        varSize, constrSize, vars = int(values['VARS_SIZE']), int(values['CONSTR_SIZE']), []

        formula: str = list(map(lambda s: s.strip(), values['-INPUT-'].splitlines()))
        
        types = {
            'Linearno programiranje' : LpContinuous,
            'Celobrojno programiranje' : LpInteger,
        }
        solvers = {
            'Linearno programiranje' : CPLEX_PY(msg=0),
            'Celobrojno programiranje' : PULP_CBC_CMD(msg=0),
        }    
        solver = solvers[values['TYPE'][0]]
        
        problem = createProblem(formula[0], varSize, vars, types[values['TYPE'][0]])
        funcRepr = 'F(x) = ' + str(problem.objective)
        window['-FUNCTION-'].update(funcRepr)
        
        constraints = formula[1:]
        for constr in constraints:
            problem += createConstraint(constr, vars)
            
        printer.pprint(problem)
        status = problem.solve(solver)
        
        print(LpStatus[status])
        if LpStatus[status] == 'Optimal':
            output = ''
            if problem.sense == LpMinimize: output += 'Fmin() = '
            else: output += 'Fmax() = '
            output += str(value(problem.objective)) + '\n'
            
            for var in vars:
                if value(var) == None: 
                    output += f'{var.getName()}^ = {float(0)}\n'
                else:
                    output += f'{var.getName()}^ = {value(var)}\n'
                  
            window['-OUTPUT-'].update(output)
        elif LpStatus[status] == 'Unbounded':
            window['-OUTPUT-'].update('Neogranicen broj resenja...')
        else:
            window['-OUTPUT-'].update('Ne moze se doci do resenja...')