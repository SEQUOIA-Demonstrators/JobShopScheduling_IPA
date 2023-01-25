# -------- JSP Classes -------- 

from typing import List

class Operation:
  
  idCounter = 0

  def __init__(self, machine, duration, id, parent_job_id):
    self.machine = machine
    self.duration = duration
    self.id = id
    self.parent_job_id = parent_job_id
    
    self.global_o_id = Operation.idCounter
    Operation.idCounter = Operation.idCounter + 1
  
  def __str__ (self):
    return f"(m:{self.machine}, d:{self.duration}, oId:{self.id})"

  def __repr__ (self):
    return f"(m:{self.machine}, d:{self.duration}, oId:{self.id})"
    
class Job:
  
  idCounter = 0

  def __init__(self, operations: List[Operation]): 
    self.id = Job.idCounter
    Job.idCounter = Job.idCounter + 1
    self.operations = []
    for o in operations:
        #print(o)
        self.add_operation(Operation(o[0], o[1], len(self.operations), self.id))
    
  def add_operation(self, op: Operation):
    self.operations.append(op)

  def __str__ (self):
    return f"(jId:{self.id}, ops:({[(o) for o in self.operations]})"
    
  def __repr__ (self):
    return f"(jId:{self.id}, ops:({[(o) for o in self.operations]})"
    
class JSP:
  def __init__(self, jobs: List[Job]):
    self.jobs = []
    for j in jobs:
        self.add_job(Job(j))
        
  def get_number_of_machines(self):
    max_m = []
    for j in self.jobs:
        for o in j.operations:
                max_m.append(o.machine)
    return max(max_m)+1
        
  def add_job(self, job: Job):
    self.jobs.append(job)
##    self.machines = len(self.jobs) # n machines. n jobs with n operations each.


  def __str__ (self):
    s = "("
    for j in self.jobs:
      s += str(j) + ",\n"
    s += ")"
    return s
  
  
  def __repr__ (self):
    s = ""
    for j in self.jobs:
      s += str(j) + "\n"
    return s
        

# -------- Helper Functions -------- 

def read_instance(path: str) -> dict:
    job_dict = []
    with open(path) as f:
        f.readline()
        for i, line in enumerate(f):
            lint = list(map(int, line.split()))
            job_dict.append([x for x in
                               zip(lint[::2],  # machines
                                   lint[1::2]  # operation lengths
                                   )])
                       
    return job_dict

## Draw JSP Solution Utils...
from datetime import datetime
import plotly.express as px

import plotly.figure_factory as ff


def convert_to_datetime(x):
  return datetime.fromtimestamp(31536000+x*24*3600).strftime("%Y-%m-%d")

def draw_solution(jsp: JSP, solution, x_max, title=None):
    '''
    A solution dict looks as follows:

        [[[0], [1]],[[1], [4]]]

        job0op0 starts at 0
        job0op1 starts at 1

        job1op0 starts at 1
        job1op1 starts at 4
    '''

    df = []

    for j in range(len(jsp.jobs)):
        for o in range(len(jsp.jobs[j].operations)):
            try:
                machine = jsp.jobs[j].operations[o].machine
                length = jsp.jobs[j].operations[o].duration
                
                starts_of_operation = solution[j][o]
                
                for start in starts_of_operation:
                    df.append(dict(Machine=machine,
                                Start=convert_to_datetime(start),
                                Finish=convert_to_datetime(start+length),
                                Job=str(f'job-{j}'),
                                Operation=f'operation-{o}'))
            except IndexError:
                print(f'WARNING: No start time for an operation! Job-{j} Operation-{o}')

    num_tick_labels = list(range(x_max+1))
    date_ticks = [convert_to_datetime(x) for x in num_tick_labels]

    fig = px.timeline(df, title=title,  y="Machine", x_start="Start", x_end="Finish", color="Job", hover_data=["Operation"])
    fig.update_traces(marker=dict(line=dict(width=3, color='black')), opacity=0.5)
    fig.layout.xaxis.update({
        'tickvals' : date_ticks,
        'ticktext' : num_tick_labels,
        'range' : [convert_to_datetime(0), convert_to_datetime(x_max)]
    })
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
    fig.show()
    
def create_solution_schedule_from_binary_vars(jsp, resVars):
    '''
    A solution dict looks as follows:

        [[(0), (1)],[(1), (4)]]

        job2op1 starts at 0
        job2op2 starts at 1

        job1op1 starts at 1
        job1op2 starts at 4

        If an operation has multiple starts in the solution this looks as follows..
        This should not happen if everything goes right.
        [[(0,1,2), (1)],[(1), (4)]]

    '''
    solutionSchedule = []
    for j in range(len(jsp.jobs)):
        opStarts = []
        for o in range(len(jsp.jobs[j].operations)):
            # find all bin_vars for this operation which are set to one in the solution..
            try:
                # Read start time from var name e.g. if b_var_j1o1t3 then startOfOperation = 3
                ops = [x for x in resVars if f"b_var_j{j}o{o}" in x and resVars[x] == 1.0]
                if len(ops) > 1:
                    print(f'WARNING: Multiple start points for an operation! Job-{j} Operation-{o}')
                startsOfOperation = [int(x[-1]) for x in ops ] # last character in the var name
                startsOfOperation = list(startsOfOperation)
                opStarts.append(startsOfOperation)
                # print(f'startsOfOperation j{j}o{o} - {startsOfOperation}')

            except IndexError:
                print(f'WARNING: No start time for an operation! Job-{j} Operation-{o}')

            
            
            # print(startOfOperation)
        solutionSchedule.append(opStarts)

    maketime = calculate_maketime_from_solution(jsp, solutionSchedule)
    return solutionSchedule, maketime



def calculate_maketime_from_solution(jsp, solutionSchedule):
    latestCompletion = 0

    for j in range(len(jsp.jobs)):
        for o in range(len(jsp.jobs[j].operations)):
                
            # check when this operations finishes.. 
            try:
                opDuration = jsp.jobs[j].operations[o].duration
                

                for s in solutionSchedule[j][o]:
                    start = s
                    jobCompletion = start + opDuration

                    if jobCompletion > latestCompletion:
                        latestCompletion = jobCompletion
                        
            except IndexError:
                print(f'WARNING: No start time for job-{j} operation-{o}')
            
            
    return latestCompletion
