import cvxpy as cvx
import numpy as np
import matplotlib.pyplot as plt
import math
import time

N = 24 # time steps to look ahead
path = cvx.Variable((N, 5)) # initialize the y pos and y velocity
flap = cvx.Variable(N-1, boolean=True) # initialize the inputs, whether or not the bird should flap in each step
acc = cvx.Variable(N-1, boolean=True)
left_angle=cvx.Variable(N-1, boolean=True)
right_angle=cvx.Variable(N-1, boolean=True)

last_solution = [False, False, False] # seed last solution
left_angle_2 = [False, False, False] # seed last solution
right_angle_2 = [False, False, False] # seed last solution
last_path = [(0,0),(0,0)] # seed last path

PIPEGAPSIZE  = 100 # gap between upper and lower pipe
VehicleWIDTH = 34
EgoWIDTH = 34
EgoHEIGHT = 16
EgoVehicleDiameter = np.sqrt(EgoHEIGHT**2 + EgoWIDTH**2) # the bird rotates in the game, so we use it's maximum extent
LeftRoadBorder = 70
RightRoadBorder =130
secondLaneBorder=95
PLAYERX = 0 # location of Vehicle at initial
theta=0

def getVehicleConstraintsDistance(x, y, computercar_x,computercar_y):
    constraints = [] # init pipe constraint list
    pipe_dist = 0 # init dist from pipe center
    #for pipe in upperPipes:
    dist_from_front = computercar_x - x - EgoVehicleDiameter
    dist_from_back = computercar_x - x + VehicleWIDTH
    if (dist_from_front < 0) and (dist_from_back > 0):
        print('ifff')
        constraints += [y <= (computercar_y)] # y above lower pipe
        #constraints += [y >= (computercar_y + EgoHEIGHT)] # y below upper pipe
        #pipe_dist += cvx.abs(pipe['y'] - (PIPEGAPSIZE//2) - (EgoVehicleDiameter//2) - y) # add distance from center
    return constraints#, pipe_dist

def solve(playerx,playery,playervel_hiz,angle,computercar_x,computercar_y):

    #angle=math.radians(angle)
    playerAcc    = 0.1#  0.1   # players  accleration
    #playerFlapAcc =  -1   # players speed on flapping
    print('anglee',angle)
    # unpack path variables
    y = path[:,0]
    vy = path[:,1]
    x=path[:,2]
    playerVel=path[:,3]
    #angle=path[:,4]

    c = [] # init constraint list
    #print('ilk cccc',c)
    #c += [y <= RightRoadBorder, y >= LeftRoadBorder] # constraints for highway boundaries
    #c += [y <= secondLaneBorder] # constraints for highway boundaries
    #print('2. cccc',c)
    c += [y[0] == playery,  playerVel[0] == playervel_hiz] # initial conditions vx[0]==playerVel,x[0]==playerx,
    c += [x[0] == playerx,  playerVel[0] == playervel_hiz] # initial conditions vx[0]==playerVel,x[0]==playerx,
    #print('3....ccccccccccccccccccc',c)
    obj = 0
    #print('playerx',playerx)
    #y = playery
    #ys = [y] # init x list
    for t in range(N-1): # look ahead
        dt = 1#t//15 + 1 # let time get coarser further in the look ahead
        #playerVel+=playerAcc*acc[t]*dt
        #x += playerVel*math.cos(angle)*angle_list[t]*dt  # update x position
        #print('x',x)
        #time.sleep(5)
        #ys += [y] # add to list
        #c += [vx[t + 1] ==  vx[t] + playerVel]#*math.cos(angle)*angle_list[t]*dt]
        #c += [vy[t + 1] ==  vy[t] + playerVel]#*math.sin(angle)*angle_list[t]*dt ]# playerFlapAcc * flap[t]   ,+ playerAccY * dt # add y velocity constraint, f=ma
        c += [playerVel[t+1] == playerVel[t] + playerAcc*acc[t]*dt]
        c += [angle == angle + 1*left_angle[t] - 1*right_angle[t] ]
        angle=math.radians(angle)
        c += [y[t + 1] ==  y[t] + playerVel[t]*math.sin(angle)*dt ] # add y constraint, dy/dt = a
        c += [x[t + 1] ==  x[t] + playerVel[t]*math.cos(angle)*dt ] # add y constraint, dy/dt = a
        #x_predicted=playerx + playervel_hiz*math.cos(angle)*t*dt
        #vehicle_c = getVehicleConstraintsDistance(x_predicted, y[t+1], computercar_x,computercar_y) # add pipe constraints
        #c += vehicle_c
        #c += [playerVel<=100]
        #obj += dist

        #print('playervel',t,playerVel)
    #objective = cvx.Maximize(cvx.sum(cvx.abs(vx))) # minimize total flaps and y velocity
    print('last_x',x[-1])
    print('mip y',y[-1])
    result=((x[-1]-1500))
    objective = cvx.Minimize( cvx.abs(result))#cvx.Maximize(playerVel)#+cvx.Minimize(cvx.sum(angle_list))
    #print(objective)
    #objective = cvx.Minimize(cvx.sum(cvx.abs(vy)) + 100* obj)
    #print('4..ccccccccccccccccccc',c)
    prob = cvx.Problem(objective, c) # init the problem
    #try:
    prob.solve(verbose = False) # use this line for open source solvers
    #prob.solve(verbose = False, solver="GUROBI") # use this line if you have access to Gurobi, a faster solver
        #print('burdamiyim')
        #y.value is output of prob.solve check cvxpy documentation for more
        #print('xs',xs)
    print('y.value',y.value)
    print('x.value',x.value)
    last_path = list(zip(y.value, x.value)) # store the path
        #print('last_path',last_path)
    last_solution = np.round(acc.value).astype(bool) # store the solution
    left_angle_2 = np.round(left_angle.value).astype(bool)
    right_angle_2 = np.round(right_angle.value).astype(bool)
    print('last solution',last_solution)
    print('last left_angle_2',left_angle_2)
    print('last right_angle_2',right_angle_2)
    #print('last solution',np.round(acc.value))
    #print('last solution0000',last_solution)
        #print('last sol sonrasi')
    return last_solution[0], last_path,left_angle_2[0],right_angle_2[0] # return the next input and path for plotting
    # except:
    #     try:
    #         last_solution = last_solution[1:] # if we didn't get a solution this round, use the last solution
    #         last_path = [((x-4), y) for (x,y) in last_path[1:]]
    #         return last_solution[0], last_path
    #     except:
    #         return False, [(0,0), (0,0)] # if we fail to solve many times in a row, do nothing
