#filter physical machines from a large pool so that the resulting set of physical servers
#can handle the resource requirements of all the virtual machines.
def physical_servers_filtering(number_vms, vm_resources, physical_servers):
    
    minBWreq = vm_resources[0][1]
    maxBWreq = vm_resources[0][1]
    minCompreq = vm_resources[0][0]
    maxCompreq = vm_resources[0][0]
    
    for vm in vm_resources:
        if vm[1] < minBWreq:
            minBWreq = vm[1]
        if vm[1] > maxBWreq:
            maxBWreq = vm[1]
        if vm[0] < minCompreq:
            minCompreq = vm[0]
        if vm[0] > maxCompreq:
            maxCompreq = vm[0]


    for ps in physical_servers:
        if ps[1] < maxBWreq or ps[0] < minCompreq:
            physical_servers.remove(ps)	

    B = list()

    for i, ps in enumerate(physical_servers):
        if ps[0] > maxCompreq :
            B.append(tuple((i,ps[0],ps[1])))

    B_ = list()

    for i, ps in enumerate(physical_servers):
        if ps[0] > minCompreq:
            B_.append(tuple((i,ps[0],ps[1])))

    def sortFunc1(x):
        return x[1]

    def sortFunc2(x):
        return x[0]
        
    B.sort(reverse = True, key = sortFunc1)
    B = B[:min(number_vms,len(B))]
    B = set(B)

    B_ = set(B_)
    B_ = B_.difference(B)
    B_ = list(B_)
    B_.sort(reverse = True, key = sortFunc1)
    B_ = B_[:min(number_vms,len(B_))]

    B = list(B)

    physical_servers = B + B_
    physical_servers.sort(key=sortFunc2)

    physical_servers_filtered = list()


    for physical_server in physical_servers:
	    physical_servers_filtered.append([physical_server[1],physical_server[2]])

    return physical_servers_filtered
    
def ivne(number_vms, vm_resources,vm_links_list, number_ps, physical_servers):
    # get the bestFit matrix and update the values(infinity)
    bestFit = []
    embedding = []
    for i in range(number_ps):
        a = []
        for j in range(number_vms):
            a.append(0)
        embedding.append(a)
    print("\nInitial embedding before IVNE: ",embedding)
    for i in range(number_ps):
        a = []
        for j in range(number_vms):
            a.append(physical_servers[i][0] - vm_resources[j][0])
        bestFit.append(a)
    print("\nBest fit matrix: ",bestFit)
    # embedding the vm onto the physical server using bestFit algorithm to reduce resource wastage and maximize acceptance rate
    vms = 0
    while vms < number_vms:
        flag = 0
        for i in range(number_ps):
            for j in range(number_vms):
                if bestFit[i][j] >= 0:
                    least = bestFit[i][j]
                    vm = j
                    ps = i
                    flag = 1
                    break
            if flag == 1:
                break
        for i in range(number_ps):
            for j in range(number_vms):
                if bestFit[i][j] < least and bestFit[i][j] >= 0:
                    least = bestFit[i][j]
                    vm = j
                    ps = i
        embedding[ps][vm] = 1
        for i in range(number_vms):
            bestFit[ps][i] = -1
        for i in range(number_ps):
            bestFit[i][vm] = -1
        vms = vms + 1
    return embedding, bestFit
    
                
            

    # find the least value and assign the PS to the VM, eliminate the row and column, loop till all the VMs are embedded
    # check the original graph and update the prop delay between VMs based on the least value among the three delays between the 2 PSs
    # output graph will contain the VMs corresponding to the PS, return this

def calc_prop_delay(number_vms, number_ps, embedding, prop_delay_matrix, vm_graph):
    prop_delays_between_vms = []
    emb_dic = {}
    for i in range(number_vms):
        a = []
        for j in range(number_vms):
            a.append(0)
        prop_delays_between_vms.append(a)
    for i in range(number_ps):
        for j in range(number_vms):
            if embedding[i][j] == 1:
                emb_dic[j] = i
    for i in range(number_vms):
        for j in range(number_vms):
            if vm_graph[i][j] > 0:
                ps1 = emb_dic[i]
                ps2 = emb_dic[j]
                prop_delays_between_vms[i][j] = min(prop_delay_matrix[ps1][ps2][0],prop_delay_matrix[ps1][ps2][1],prop_delay_matrix[ps1][ps2][2])
    return prop_delays_between_vms, emb_dic
                    


def dyvine(emb_dic, embedding, vm_resources, physical_servers, number_vms, number_ps, bestFit):
    lfv_dic = {}
    ps_dic = {}
    net_dic = {}
    orig = embedding
    print("Initially without DYVINE:",embedding,"\n")
    for i in range(number_ps):
        for j in range(number_vms):
            if embedding[i][j] == 1:
                ps_dic[i] = j
    print("\nPhysical servers and the VMs embedded onto them: ",ps_dic)
    # calculate LFV and GFV (alpha and beta)

    for i in emb_dic.keys():
        lfv_dic[i] = (physical_servers[emb_dic[i]][0] - vm_resources[i][0])/physical_servers[emb_dic[i]][0]
    print("\nLFV values of each VM: ",lfv_dic)
    for i in emb_dic.keys():
        net_dic[i] = (physical_servers[emb_dic[i]][1] - vm_resources[i][1])/physical_servers[emb_dic[i]][1]
    sum_lfv = 0.0
    sum_net_dic = 0.0
    for i in lfv_dic.values():
        sum_lfv = sum_lfv + i
    for i in net_dic.values():
        sum_net_dic = sum_net_dic + i
    gfv = sum_lfv + sum_net_dic
    print("\nGFV value: ",gfv)
    all_ps_dic = {}
    for i in range(number_ps):
        if i in ps_dic.keys():
            all_ps_dic[i] = ps_dic[i]
        else:
             all_ps_dic[i] = -1
    print("\nPhysical servers and the Vms embedded in them (-1 indicates no VM): ",all_ps_dic)

    # for each VM, for each PS, if there is a VM embedded, migrate the VM and find LFV and GFV values
    for i in range(number_vms):
        valid = 1
        for j in range(number_ps):
            embedding_temp = embedding
            if all_ps_dic[j] != -1 and all_ps_dic[j] != i:
                lfv_dic_temp = lfv_dic
                net_dic_temp = net_dic
                if (vm_resources[i][0] + vm_resources[all_ps_dic[j]][0] <= physical_servers[j][0]) and (vm_resources[i][1] + vm_resources[all_ps_dic[j]][1] <= physical_servers[j][1]):
                    embedding_temp[j][i] = 1
                    embedding_temp[emb_dic[i]][i] = 0
                    lfv_dic_temp[i] = (physical_servers[j][0] - (vm_resources[i][0] + vm_resources[all_ps_dic[j]][0]))/physical_servers[j][0]
                    net_dic_temp[i] = (physical_servers[j][1] - (vm_resources[i][1] + vm_resources[all_ps_dic[j]][1]))/physical_servers[j][1]
                    sum_lfv = 0.0
                    sum_net_dic = 0.0
                    for i in lfv_dic_temp.values():
                        sum_lfv = sum_lfv + i
                    for i in net_dic_temp.values():
                        sum_net_dic = sum_net_dic + i
                    gfv_temp = sum_lfv + sum_net_dic
                    valid = 0

            # if the GFV is less than previous value after migration, update the config else revert
            if valid == 0:    
                if gfv_temp < gfv:
                    embedding = embedding_temp

    return embedding


        
# Below is the test case as given in the paper

# input data below
# number of VMs and the edges between them which represent the physical link(VN graph)
number_vms = 4
print("\nNumber of VMs: ", number_vms)
vm_graph = [[0,4,0,4],[4,0,3,0],[0,3,0,5],[4,0,5,0]]
vm_links_list = []
print("Matrix representation of the VMs and the virtual links between them: ",vm_graph)
# Calculate bandwidth requirement of each VM
for i in range(number_vms):
    sum = 0
    for j in range(number_vms):
        sum = sum + vm_graph[i][j]
    vm_links_list.append(sum)
for i in range(number_vms):
    vmn = i+1
    print("\nVM[",vmn, "] has network requirement: ",vm_links_list[i])
# VMs with their computing resource requirement and network requirement 
vm_resources = [[43,8],[49,7],[24,8],[35,9]]
print("Computational and resource requirement by VMs : ")
for i in range(number_vms):
    print(vm_resources[i][0],"               ",vm_resources[i][1])



# Physical servers with computing resource availability and network availability 
# remove physical servers if they dont meet max delay and min resource requirement
number_ps = 8
physical_servers = [[25,20],[27,33],[27,34],[28,34],[50,23],[60,27],[75,36],[77,36]]

print("Computational and resource availability by physical servers : ")
for i in range(number_ps):
    print(physical_servers[i][0],"               ",physical_servers[i][1])

physical_servers = physical_servers_filtering(number_vms,vm_resources,physical_servers)

print("Computational and resource availability by physical servers (after filtering) : ")
for i in range(number_ps):
    print(physical_servers[i][0],"               ",physical_servers[i][1])

# propagation delay matrix
prop_delay_matrix = [[[0,0,0],[0.2,0.1,0.3],[0.1,0.2,0.3],[0.3,0.1,0.2],[0.2,0.1,0.3],[0.1,0.2,0.3],[0.3,0.1,0.2],[0.1,0.2,0.3]],[[0.2,0.1,0.3],[0,0,0],[0.1,0.2,0.3],[0.3,0.1,0.2],[0.2,0.1,0.3],[0.1,0.2,0.3],[0.3,0.1,0.2],[0.1,0.2,0.3]],
[[0.2,0.1,0.3],[0.1,0.2,0.3],[0,0,0],[0.3,0.1,0.2],[0.2,0.1,0.3],[0.1,0.2,0.3],[0.3,0.1,0.2],[0.1,0.2,0.3]],[[0.2,0.1,0.3],[0.1,0.2,0.3],[0.3,0.1,0.2],[0,0,0],[0.2,0.1,0.3],[0.1,0.2,0.3],[0.3,0.1,0.2],[0.1,0.2,0.3]],
[[0.2,0.1,0.3],[0.1,0.2,0.3],[0.3,0.1,0.2],[0.2,0.1,0.3],[0,0,0],[0.1,0.2,0.3],[0.3,0.1,0.2],[0.1,0.2,0.3]],[[0.2,0.1,0.3],[0.1,0.2,0.3],[0.3,0.1,0.2],[0.2,0.1,0.3],[0.1,0.2,0.3],[0,0,0],[0.3,0.1,0.2],[0.1,0.2,0.3]],
[[0.2,0.1,0.3],[0.1,0.2,0.3],[0.3,0.1,0.2],[0.2,0.1,0.3],[0.1,0.2,0.3],[0.3,0.1,0.2],[0,0,0],[0.1,0.2,0.3]],[[0.2,0.1,0.3],[0.1,0.2,0.3],[0.3,0.1,0.2],[0.2,0.1,0.3],[0.1,0.2,0.3],[0.3,0.1,0.2],[0.1,0.2,0.3],[0,0,0]]
]
print("\nThe propogation delay matrix: \n\n", prop_delay_matrix)
print("\n")
# Run ivne algorithm
print("\nRunning the IVNE algorithm.....")
embedding, bestFit = ivne(number_vms, vm_resources,vm_links_list, number_ps, physical_servers)
print("\nEmbedding matrix after IVNE ",embedding)
for i in range(number_ps):
    for j in range(number_vms):
        if embedding[i][j] == 1:
            print("\nPhysical server ",i,"hosts VM: ",j)
prop_delays_between_vms, emb_dic = calc_prop_delay(number_vms, number_ps, embedding, prop_delay_matrix, vm_graph)
print("\nPropagation delays between each VM: ", prop_delays_between_vms)
print("\nRunning the DYVINE algorithm.....\n")
final_embedding = dyvine(emb_dic, embedding, vm_resources, physical_servers, number_vms, number_ps, bestFit)
print("\nEmbedding after running DYVINE algorithm: ", embedding)
for i in range(number_ps):
    for j in range(number_vms):
        if embedding[i][j] == 1:
            print("\nPhysical server ",i,"hosts VM: ",j)

print("\n")
# output of IVNE algorithm
# Input to the DYVINE algorithm

