#!/usr/bin/python


'''
Skeleton Length Routines for fil-finder package


Contains:
        fil_length
        init_lengths
        pre_graph
        longest_path
        final_lengths



Requires:
        numpy
        networkx


'''




import numpy as np
import networkx as nx
from utilities import *
from pixel_ident import *
#from curvature import *
import operator,string




def fil_length(n,pixels,initial=True):
 #fil_length calculates the length of the branches, or filament. It does this by creating an array of the distances between each pixel. It then searches each column, beginning with the first, and identifies the minimum of that row. The column of the minimum is the next row to be searched. After a row is searched, the corresponding row and column are set to zero. In the initial case, the maximum distance between connected pixels is sqrt(2). The non-initial case accounts for the average position of intersections when finding the overall length of the filament. Due to the somewhat unpredictablility of these larger intersections, the minimum distances can be much larger. The value of 5 is an approximation for the largest gap that can be created, but it is possible to have values larger than this.
  dists = [];tempps = [];orders = [];order = []
  for i in range(len(pixels)):
    if pixels[i]==[[]]: pass
    else:
        eucarr = np.zeros((len(pixels[i]),len(pixels[i])))
        for j in range(len(pixels[i])):
          for k in range(len(pixels[i])):
            eucarr[j,k]=np.linalg.norm(map(operator.sub,pixels[i][k],pixels[i][j]))
        for _ in range(len(pixels[i])-1):
          if _== 0:
            j=0
            last=0
          else:
            j=last
            last = []
          try:
            min_dist = np.min(eucarr[:,j][np.nonzero(eucarr[:,j])])
          except ValueError:
            min_dist = 0 # Check to make sure this does not seriously affect the length
                         # This Error has ony
          if initial:
            if min_dist>np.sqrt(2.0):
              print "PROBLEM : Dist %s, Obj# %s,Branch# %s, # In List %s" % (min_dist,n,i,pixels[i][j])
          else:
            if min_dist>5.0:
              if j==1:
                min_dist = 0
            else: pass#print "PROBLEM : Dist %s, Obj# %s,Branch# %s, # In List %s" % (min_dist,n,i,pixels[i][j])
          dists.append(min_dist)
          x,y = np.where(eucarr==min_dist)
          order.append(j)
          for z in range(len(y)):
            if y[z]==j:
              last = x[z]
              eucarr[:,j]=0
              eucarr[j,:]=0
    tempps.append(sum(dists))
    orders.append(order)
    dists = [];order = []
  return tempps,orders


def curve(n,pts):
  #The average curvature of the filament is found using the Menger curvature. The formula relates the area of the triangle created by the three points and the distance between the points. The formula is given as 4*area/|x-y||y-z||z-x|=curvature. The curvature is weighted by the euclidean length of the three pixels.
  lenn = len(pts)
  kappa = [];seg_len = []
  for i in range(lenn-2):
    x1 = pts[i][0];y1 = pts[i][1]
    x2 = pts[i+1][0];y2 = pts[i+1][1]
    x3 = pts[i+2][0];y3 = pts[i+2][1]
    num = abs(2*((x2-x1)*(y2-y1)+(y3-y2)*(x3-x2)))
    den = np.sqrt( (pow((x2-x1),2) + pow((y2-y1),2)) * (pow((x3-x2),2)+pow((y3-y2),2 ))* (pow((x1-x3),2)+pow((y1-y3),2) ) )
    if ( den == 0 ):
      kappa.append(0)
    else:
      kappa.append(num/den)
    seg_len.append(fil_length(n,[[pts[i],pts[i+1],pts[i+2]]],initial=False)[0])
  numer = sum(kappa[i] * seg_len[i][0] for i in range(len(kappa)))
  denom = sum(seg_len[i][0] for i in range(len(seg_len)))
  if denom!= 0:
    return numer/denom
  else:
    print n
    print pts
    raise ValueError('Sum of length segments is zero.')

def av_curvature(n,finalpix,ra_picks=100,seed=500):
  #Calculates the average curvature using final skeleton points from final_lengths
  # Picks 3 random points on the filament and calculates the curvature. The average is taken of 100 picks.
  import numpy.random as ra
  seed = int(seed)
  ra.seed(seed=int(seed))
  ra_picks = int(ra_picks)

  #Initialize lists
  curvature = []

  for i in range(len(finalpix)):
    if len(finalpix[i])>3:
      trials = []
      for _ in range(ra_picks):
        picks = ra.choice(len(finalpix[i]),3,replace=False) ### REQUIRE NUMPY 1.7!!!
        points = [finalpix[i][j] for j in picks]
        trials.append(curve(n,points))
      curvature.append(np.mean(trials))
    else:
      curvature.append("Fail")
  return curvature

########################################################
###       Composite Functions
########################################################


def init_lengths(labelisofil,filbranches):
  num = len(labelisofil)

  #Initialize Lists
  lengths = []
  filpts = []

  for n in range(num):
    funcreturn = find_filpix(filbranches[n],labelisofil[n],final=False)
    leng = fil_length(n,funcreturn[0],initial=True)[0]
    for i in range(len(leng)):
      if leng[i]==0.0:
        leng.pop(i)
        leng.insert(i,0.5) # For use in longest path algorithm, will be set to zero for final analysis
    lengths.append(leng)
    filpts.append(funcreturn[0])

  return lengths,filpts




def pre_graph(labelisofil,lengths,interpts,ends):

  num = len(labelisofil)

  # Initialize lists
  end_nodes_temp = []
  end_nodes = []
  uniqs = []
  inter_nodes_temp = []
  inter_nodes = []
  nodes = []
  nodes_temp = []
  edge_list_temp = []
  edge_list = []


  for n in range(num):
    for i in ends[n]:
      end_nodes_temp.append((labelisofil[n][i[0],i[1]],lengths[n][labelisofil[n][i[0],i[1]]-1]))
    end_nodes.append(end_nodes_temp)
    for i in end_nodes_temp:
      nodes_temp.append(i[0])
    nodes.append(nodes_temp);nodes_temp = []
    end_nodes_temp = []

  #Intersection nodes are given by the intersections points of the filament. They are labelled alphabetically (if len(interpts[n])>26, subsequent labels are AA,AB,...). The branch labels attached to each intersection are included for future use.
    for j in range(len(interpts[n])):
        for i in interpts[n][j]:
          int_arr = np.array([[labelisofil[n][i[0]-1,i[1]+1],labelisofil[n][i[0],i[1]+1],labelisofil[n][i[0]+1,i[1]+1]],\
            [labelisofil[n][i[0]-1,i[1]],0,labelisofil[n][i[0]+1,i[1]]],[labelisofil[n][i[0]-1,i[1]-1],labelisofil[n][i[0],i[1]-1],labelisofil[n][i[0]+1,i[1]-1]]])
          for x in np.unique(int_arr[np.nonzero(int_arr)]):
            uniqs.append((x,lengths[n][x-1]))
        uniqs = list(set(uniqs))
        inter_nodes_temp.append(uniqs)
        uniqs = []

    inter_nodes.append(zip(product_gen(string.ascii_uppercase),inter_nodes_temp))
    inter_nodes_temp = []
    for k in inter_nodes[n]:
      nodes[n].append(k[0])

  #Edges are created from the information contained in the nodes.
  for n in range(num):
    for i in range(len(inter_nodes[n])):
      end_match = list(set(inter_nodes[n][i][1]) & set(end_nodes[n]))
      for k in end_match:
        edge_list_temp.append((inter_nodes[n][i][0],k[0],k))

      for j in range(len(inter_nodes[n])):
        if i != j:
          match = list(set(inter_nodes[n][i][1]) & set(inter_nodes[n][j][1]))
          match = list(set(match))
          if len(match)==1:
            edge_list_temp.append((inter_nodes[n][i][0],inter_nodes[n][j][0],match[0]))
          elif len(match)>1:
            multi = [match[l][1] for l in range(len(match))]
            keep = multi.index(min(multi))
            edge_list_temp.append((inter_nodes[n][i][0],inter_nodes[n][j][0],match[keep]))
    edge_list.append(edge_list_temp)
    edge_list_temp = []


  return end_nodes, inter_nodes, edge_list, nodes



def longest_path(edge_list,nodes,lengths,verbose=False):
  # Given nodes and edges from pre_graph(), finds the longest shortest path
  num = len(nodes)

  # Initialize lists
  max_path = []
  extremum = []

  for n in range(num):
    G = nx.Graph()
    G.add_nodes_from(nodes[n])
    for i in edge_list[n]:
      G.add_edge(i[0],i[1],weight=i[2][1])
    paths = nx.shortest_path_length(G,weight='weight')
    values = [];node_extrema = []
    for i in paths.iterkeys():
      j = max(paths[i].iteritems(),key=operator.itemgetter(1))
      node_extrema.append((j[0],i))
      values.append(j[1])
    start,finish = node_extrema[values.index(max(values))]
    extremum.append([start,finish])
    max_path.append(nx.shortest_path(G,start,finish))
    if verbose:
      import matplotlib.pyplot as p
      clean_graph = p.figure(1.,facecolor='1.0')
      graph = clean_graph.add_subplot(1,2,2)
      elist = [(u,v) for (u,v,d) in G.edges(data=True)]
      pos = nx.graphviz_layout(G)#,arg=str(lengths[n]))
      nx.draw_networkx_nodes(G,pos,node_size=200)
      nx.draw_networkx_edges(G,pos,edgelist=elist,width=2)
      nx.draw_networkx_labels(G,pos,font_size=10,font_family='sans-serif')
      p.axis('off')
      p.show()


  return max_path,extremum


def final_lengths(img,max_path,edge_list,labelisofil,filpts,interpts,filbranches,lengths,img_scale,length_thresh):
  #Finds the overall length of the filament from the longest_path and pre_graph outputs
  num = len(max_path)

  # Initialize lists
  curvature = []
  main_lengths = []

  for n in range(num):

    if len(max_path[n])==1: #and max_path[n][0]==max_path[n][1]: #Catch fil with no intersections
      main_lengths.append(lengths[n][0] * img_scale)
      curvature.append(av_curvature(n,filpts[n])[0])
    else:
      good_edge_list = []
      for i in range(len(max_path[n])-1):
        good_edge_list.append((max_path[n][i],max_path[n][i+1]))
      keep_branches = []
      for i in good_edge_list:
        for j in edge_list[n]:
          if (i[0]==j[0] and i[1]==j[1]) or (i[0]==j[1] and i[1]==j[0]):
            keep_branches.append(j[2][0])
            keep_branches = list(set(keep_branches))
      fils = [];good_inter = []
      for i in keep_branches:
        fils.append(filpts[n][i-1])
      branches = range(1,filbranches[n]+1)
      match = list(set(branches) & set(keep_branches))
      for i in match:
        branches.remove(i)
      delete_branches = branches
      for i in delete_branches:
        x,y = np.where(labelisofil[n]==i)
        for j in range(len(x)):
          labelisofil[n][x[j],y[j]]=0
      big_inters = []
      for i in interpts[n]:
        if len(i)>1: big_inters.append(i)
        for j in i:
          labelisofil[n][j[0],j[1]]=filbranches[n]+1
      relabel,numero=  nd.label(labelisofil[n],eight_con())
    # find_pilpix is used again to find the endpts of the remaining branches. The     branch labels are used to check which intersections are included in the longest   #path. For intersections containing multiple points, an average of the
    #positions, weighted by their value in the image, is used in the length
    #calculation.
      endpts = []; endpts.append(find_filpix(numero,relabel,final=False)[3])
      for i in interpts[n]:
        match = list(set(endpts[0]) & set(i))
        if len(match)>0:
          for h in match:
            endpts[0].remove(h)
      num_inter = []
      all_zip = zip(product_gen(string.ascii_uppercase),range(len(interpts[n])))
      for i in all_zip:
        num_inter.append(i[0])
      inter_exc = list(set(max_path[n]) & set(num_inter))
      inter_excl = list(set(num_inter) - set(inter_exc))
      for i in big_inters:
        weight = [];xs = [];ys = []
        for x,y in i:
          weight.append(img[x,y])
          xs.append(x);ys.append(y)
        av_x = weighted_av(xs,weight)
        av_y = weighted_av(ys,weight)
        interpts[n].insert(interpts[n].index(i),[(av_x,av_y)])
        interpts[n].remove(i)
  # The pixels of the longest path are combined with the intersection pixels. This gives overall length of the filament.
      good_pts = [];[[good_pts.append(i[j]) for j in range(len(i))]for i in fils]
      match = list(set(endpts[0]) & set(good_pts))
      if len(match)>0:
        for i in match:
          good_pts.remove(i)
      for i in endpts[0]:
        good_pts.insert(0,i)
      inter_find = list(set(max_path[n]) & set(string.ascii_uppercase))

      if len(inter_find) != 0:
        for i in inter_find:
          good_inter.append(interpts[n][string.ascii_uppercase.index(i)-1])
      interpts[n] = [];[[interpts[n].append(i[j]) for j in range(len(i))] for i in good_inter]
      finalpix = [good_pts + interpts[n]]
      lengthh,order = fil_length(n,finalpix,initial=False)
      main_lengths.append(lengthh[0] * img_scale)

      curvature.append(av_curvature(n,finalpix)[0]) ### SEE CURVE FOR EXPLANATION
      # import matplotlib.pyplot as p
      # p.imshow(labelisofil[n],origin='lower',interpolation=None)
      # p.show()
      # Re-adding long branches, "long" greater than length 3.0
      del_length = []
      for i in delete_branches:
        if lengths[n][i-1]> length_thresh:
          for x,y in filpts[n][i-1]:
            labelisofil[n][x,y]=i
            good_pts.insert(i,filpts[n][i-1])
      else: del_length.append(lengths[n][i-1])
      lengths[n] = list(set(lengths[n]) - set(del_length))
      filpts[n] = [];[filpts[n].append(i) for i in good_pts]

  return main_lengths,lengths,labelisofil,curvature # Returns the main lengths, the updated branch lengths, the final skeleton arrays, and curvature


def final_analysis(labelisofil):
  num = len(labelisofil)

  # Initialize lists
  filbranches = [];hubs = [];lengths = []

  for n in range(num):
    x,y = np.where(labelisofil[n]>0)
    for i in range(len(x)):
      labelisofil[n][x[i],y[i]]=1
    deletion = find_extran(1,labelisofil[n])
    funcreturn = find_filpix(1,deletion,final=False)
    relabel,kk = nd.label(funcreturn[2],eight_con())
    for i in range(kk):
      x,y = np.where(relabel==kk+1)
      if len(x)==1.0:
        labelisofil[x[0],y[0]]=0
    labelisofil.pop(n)
    labelisofil.insert(n,relabel)
    filbranches.insert(n,kk)
    hubs.append(len(funcreturn[1]))
    funcsreturn = find_filpix(kk,relabel,final=True)
    lenn,ordd = fil_length(n,funcsreturn[0],initial=True)
    lengths.append(lenn)

  return labelisofil,filbranches,hubs,lengths


if __name__ == "__main__":
    import sys
    fib(int(sys.argv[1]))











































