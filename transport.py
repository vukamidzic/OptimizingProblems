import FreeSimpleGUI as sg
from pulp import *
from collections import deque
import pprint

printer = pprint.PrettyPrinter()

def multListsOfPairs(a, b):
    return list(map(lambda x: x[0]*x[1], list(zip(a, b)))) 

def allOnes(ls: list):
    return all(x == 1 for x in ls)

def objFunc(content, model):
    res = LpAffineExpression()
    vars = []
    var_idx = 1
    for i in range(len(content)):
        for j in range(len(content[0])-1):
            var = LpVariable(f'x{var_idx}', lowBound=0, cat=LpContinuous)
            vars.append(var)
            res.addInPlace(var * content[i][j])
            var_idx += 1
    model += res
    return res, vars
    

def addConstrs(vars, a_s, b_s, model):
    n,m = len(a_s), len(b_s)
    
    row_ones = deque(m*[1] + (n*m - m)*[0])
    for i in range(n):
        constr = LpConstraint()
        constr.addInPlace(multListsOfPairs(vars, row_ones))
        constr.addInPlace(-a_s[i])
        model += constr
        row_ones.rotate(m)
        
    tmp = (n*m) * [0]
    tmp[0] = 1
    cnt, diff = n-1, m
    i = m
    while (cnt != 0):
        tmp[i] = 1
        i += m
        cnt -= 1
        
    col_ones = deque(tmp)
    for i in range(m):
        constr = LpConstraint()
        constr.addInPlace(multListsOfPairs(vars, col_ones))
        constr.addInPlace(-b_s[i])
        model += constr
        col_ones.rotate(1) 

    # for var in vars:
    #     model += var >= 0

INF = 1_000

layout = [
    [ sg.Text("""Unesite matricu:
              c_11  c_12  ...  c_1m  a_1
              c_n1  c_n2  ...  c_nm  a_n
              b_1  b_2  ...  b_m""") ],
    [ sg.Multiline(size=(60, 30), rstrip=True, key='-INPUT-')],
    [ sg.Button(button_text='Resi', key='SOLVE', size=(20,2)) ],
    [ sg.Multiline("F(x) = ", key='-FUNCTION-') ],
    [ sg.Multiline(size=(50, 5),key='-OUTPUT-') ]
]

window = sg.Window('Transportni problem', layout=layout, resizable=True)

while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break
    elif event == 'SOLVE':
        model = LpProblem('Transportni_problem', LpMinimize)
        solver = apis.getSolver('CPLEX_PY')
        print(f'solver -> {type(solver)}')
        
        problem = str(values['-INPUT-']).split('\n')
        content = list(map(lambda x: list(map(lambda y: int(y), x.split(' '))), problem[:-1]))
        b_s = list(map(lambda x: int(x), problem[-1].split(' ')))
        a_s = []
        for i in range(len(content)): a_s.append(content[i][-1])
        
        n,m = len(content), len(content[0])
        dummy_vars = []
        if (not allOnes(a_s)) or (not allOnes(b_s)): # if transportation problem
            diff = abs(sum(a_s) - sum(b_s))
            if (sum(a_s) < sum(b_s)):
                content.append(m * [INF])
                content[-1][-1] = 0
                a_s.append(diff)
                idx = 1 + n*(m-1)
                for j in range(m-1): 
                    printer.pprint('Dummy var = ' + str(idx))
                    dummy_vars.append(f'x{idx}')
                    idx += 1 
            elif (sum(a_s) > sum(b_s)):
                for content_row in content:
                    content_row.insert(-1, INF)
                b_s.append(diff)
                idx = m
                for i in range(n): 
                    dummy_vars.append(f'x{idx}')
                    idx += m
        else: # if assignment problem 
            diff = abs(sum(a_s) - sum(b_s))
            if (sum(a_s) < sum(b_s)):
                addedRows = 0
                idx = n*(m-1) + 1
                for i in range(diff):
                    content.append(m * [INF])
                    a_s.append(1)
                    addedRows += 1
                    content[-1][-1] = 0
                for i in range(n, n + addedRows):
                    for j in range(m-1):
                        dummy_vars.append(f'x{idx}')
                        idx += 1
            elif (sum(a_s) > sum(b_s)):
                for j in range(diff):
                    for content_row in content:
                        content_row.insert(-1, INF)
                    b_s.append(1)
                idx = 1
                for i in range(n):
                    for j in range(len(content[0])-1):
                        if j >= m-1: dummy_vars.append(f'x{idx}')
                        idx += 1
        
        obj_func, vars = objFunc(content, model)
        model += obj_func
        window['-FUNCTION-'].update('F(x) = ' + str(obj_func) + ' -> min')
        addConstrs(vars, a_s, b_s, model)
        
        result = model.solve(solver=solver)
        if LpStatus[result] == 'Optimal': 
            fn_min = 0
            coefs = []
            for i in range(n):
                for j in range(m-1):
                    coefs.append(content[i][j])
            # --------------------------
            vars = [var for var in vars if not var.getName() in dummy_vars]
            # --------------------------
            for i in range(len(vars)):
                if not vars[i].getName() in dummy_vars:
                    printer.pprint(coefs[i])
                    fn_min += value(vars[i])*coefs[i]
            res_text = 'Fmin(x) = ' + str(fn_min) + '\n'
            output_idx = 1
            for var in vars:
                if var.getName() not in dummy_vars:
                    res_text += f'x{output_idx}^ = {value(var)}\n'
                    output_idx += 1
            window['-OUTPUT-'].update(res_text)
        else:
            res_text = "Nije nadjeno optimalno resenje..."
            window['-OUTPUT-'].update(res_text)
            
        
window.close()

