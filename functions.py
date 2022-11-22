import networkx as nx
import json
from datetime import datetime
import re
import copy

# Functions needed to extract the networks


# Function to get data from the MongoDB
def getData(db, flt, projectID):
    if flt == "reply":
        docs = db.Comments.find({'$and': [{'reply_user_id': {'$ne': None}}, {'project_id': projectID}]})
        docs = list(docs)
        for x in docs:
            x['created_at'] = extractDate(x['created_at'])
            if x['board_title'] == 'FAQ and Help':
                x['board_title'] = 'Help'
    elif flt == "full":
        docs = db.Comments.find({'project_id': projectID})
        docs = list(docs)
        for x in docs:
            x['created_at'] = extractDate(x['created_at'])
            if x['board_title'] == 'FAQ and Help':
                x['board_title'] = 'Help'
    elif flt == "comment":
        docs = db.Comments.find({'$and': [{'reply_user_id': None}, {'project_id': projectID}]})
        docs = list(docs)
        for x in docs:
            x['created_at'] = extractDate(x['created_at'])
            if x['board_title'] == 'FAQ and Help':
                x['board_title'] = 'Help'
    else:
        docs = None
    return createUserRolesHistory(docs)


# Function to convert the date string to a time object
def extractDate(string):
    data = re.sub(r'\....', '', string)
    output = datetime.strptime(data, '%Y-%m-%dT%H:%M:%SZ')
    return output


# Function to extract edges from the data for given project
def getEdges(relationdata, fulldata, start, end):
    output = []
    if start is None and end is None:
        for x in copy.deepcopy(relationdata):
            t = (x['user_login'], x['reply_user_login'],
                 {key: x[key] for key in x.keys() &
                  {
                      'user_id',
                      'body',
                      'board_title',
                      'discussion_id',
                      'discussion_title',
                      'created_at',
                      'project_id',
                      'userRoles',
                      'project_title'

                  }})
            t[2]['relation'] = 'reply'
            t[2]['targetRole'] = getTargetUserRole(fulldata, x['reply_user_login'], x['created_at'])
            output.append(t)
        return output
    elif start is not None and end is not None:
        for x in copy.deepcopy(relationdata):
            if start < x['created_at'] < end:
                t = (x['user_login'], x['reply_user_login'],
                     {key: x[key] for key in x.keys() &
                      {
                          'user_id',
                          'body',
                          'board_title',
                          'discussion_id',
                          'discussion_title',
                          'created_at',
                          'project_id',
                          'userRoles',
                          'project_title'

                      }})
                t[2]['relation'] = 'reply'
                t[2]['targetRole'] = getTargetUserRole(fulldata, x['reply_user_login'], start)
                output.append(t)
        return output
    else:
        return None


# Function to return comment-relation in networkx-suitable format
def getComments(relationdata, fulldata, discussiondata, start, end):
    output = []
    if start is None and end is None:
        for x in copy.deepcopy(relationdata):
            t = (x['user_login'], x['discussion_id'],
                 {key: x[key] for key in x.keys() &
                  {
                      'user_id',
                      'body',
                      'board_title',
                      'discussion_id',
                      'discussion_title',
                      'created_at',
                      'project_id',
                      'userRoles',
                      'project_title'

                  }})
            t[2]['relation'] = 'comment'
            t[2]['targetRole'] = getTargetUserRole(fulldata, getUserNameForID(discussiondata, x['discussion_id']),
                                                   x['created_at'])
            output.append(t)
        return output
    elif start is not None and end is not None:
        for x in copy.deepcopy(relationdata):
            if start < x['created_at'] < end:
                t = (x['user_login'], x['discussion_id'],
                     {key: x[key] for key in x.keys() &
                      {
                          'user_id',
                          'body',
                          'board_title',
                          'discussion_id',
                          'discussion_title',
                          'created_at',
                          'project_id',
                          'userRoles',
                          'project_title'

                      }})
                output.append(t)
                t[2]['relation'] = 'comment'
                t[2]['targetRole'] = getTargetUserRole(fulldata, getUserNameForID(discussiondata, x['discussion_id']), start)
        return output
    else:
        return None


# Function to generate graph based on edge set (e) and vertices set (v). Does also work with empty vertices sets,
# in order to construct the graph later used to filter out nodes not present in the network
def generateGraph(v, e):
    graph = nx.MultiDiGraph()
    if v is None:
        graph.add_edges_from(e)
    else:
        graph.add_edges_from(e)
        nx.set_node_attributes(graph, v)
    graph.remove_edges_from(nx.selfloop_edges(graph))
    return graph


# Function to absorb user roles to the most relevant one
def decideUserRole_history(rolelist):
    output = ''
    if 'scientist' in rolelist or 'admin' in rolelist:
        output = 'scientist'
        if 'moderator' in rolelist:
            output = 'scientist-moderator'
    elif 'moderator' in rolelist:
        output = 'moderator'
    elif 'team' in rolelist or 'translator' in rolelist:
        output = 'team'
    return output


# Function to create correct user roles and assign 'volunteer' if no user role
# is defined, also considering the history of user roles.
def createUserRolesHistory(data):
    users = {}
    for x in data:
        if 'userRoles' in x:
            x['userRoles'] = decideUserRole_history(x['userRoles'])
        else:
            x['userRoles'] = 'volunteer'

    for x in sorted(data, key=lambda x: x['created_at']):
        username = x['user_login']
        userrole = x['userRoles']

        if username not in users:
            users[username] = userrole
        elif username in users:
            if users[username] in userrole:
                pass
            else:
                x['userRoles'] = users[username]+"-"+userrole

    return data


# Function to get username for given user id
def getUserNameForID(discussiondata, userid):
    username = ""
    for x in discussiondata:
        if x['id'] == userid:
            username = x['user_login']
    print("the username was found and is: "+username)
    return username


# Function to get user role of the target (i.e., comment receiver) in the network
def getTargetUserRole(data, username, start):
    roles = []
    for x in sorted(data, key=lambda x: x['created_at']):
        if x['user_login'] == username:
            if x['created_at'] < start:
                roles.append(x['userRoles'])
                # print("User role "+x['userRoles']+" added.")

                # print("No user role before "+str(start)+" found.")
    if len(roles) > 0:
        lastRole = roles[-1]
    else:
        lastRole = None

    return lastRole


# Function to remove irrelevant nodes (according to the graph that is fed in)
def getRelevantNodes(data, edges):
    graph = generateGraph(None, edges)
    output = dict(
        (val, data[val]) for val in graph.nodes() if val in data
    )
    return output


# Another function to get user id for given name
def getUserId(data, username):
    output = ''
    for x in data:
        if x['user_login'] == username:
            output = x['user_id']
    return output


# Function to get former user roles
def getFormerUserRole(username, data, start):
    roles = []
    for x in sorted(data, key=lambda x: x['created_at']):
        if x['user_login'] == username:
            if x['created_at'] < start:
                roles.append(x['userRoles'])

    if len(roles) > 0:
        lastRole = roles[-1]
    else:
        lastRole = None

    return lastRole


# Function to get attributes of nodes which are not actively in time slice
def getPassiveNodeAttributes(data, edges, start, end):
    dic = {}

    for x in filterData(copy.deepcopy(data), start, end):
        dic[x['user_login']] = {}
        dic[x['user_login']]['user_id'] = x['user_id']
        dic[x['user_login']]['userRoles'] = x['userRoles']

    graph = generateGraph(None, edges)
    passives = dict(
        (key, dic.get(key)) for key in graph.nodes() if key not in dic
    )

    for key, value in passives.items():
        passives[key] = {}
        passives[key]['user_id'] = getUserId(data, key)
        passives[key]['userRoles'] = getFormerUserRole(key, data, start)

    return passives


# Function to get attributes
def getAttributes(data, start, end):
    dic = {}
    for x in filterData(copy.deepcopy(data), start, end):
        dic[x['user_login']] = {}
        dic[x['user_login']]['user_id'] = x['user_id']
        dic[x['user_login']]['userRoles'] = x['userRoles']
    return dic


# Function to filter data for given time slice
def filterData(data, start, end):
    output = []
    if start is not None and end is not None:
        for x in data:
            if start < x['created_at'] < end:
                output.append(x)
    else:
        for x in data:
            output.append(x)
    return output


# Function to export graph to JSON for given filename. The keys are currently hard-coded in order to provide the
# possibility for easy access with D3.js
def writeJSON(name, graph):
    output = nx.node_link_data(graph, {"link": "links", "source": "source", "target": "target"})

    with open(name, 'w') as f:
        json.dump(output, f, default=str)


# Function to extract the network for a given project and timeframe
def extractNetwork(db, relation, projectid, start, end):
    fulldata = getData(db, 'full', projectid)

    if relation == 'comment':

        relationdata = getData(db, 'comment', projectid)

        docs_disc = list(db.Discussions.find({'project_id': projectid}))

        edges = getComments(relationdata, fulldata, docs_disc, start, end)

        mapping = {}
        for x in docs_disc:
            mapping[x['id']] = x['user_login']

        prelim = generateGraph(None, edges)
        prelim = nx.relabel_nodes(prelim, mapping)
        nodes = getAttributes(fulldata, start, end)
        graph = generateGraph(nodes, prelim.edges(data=True))
        nx.set_node_attributes(graph, getPassiveNodeAttributes(fulldata, prelim.edges(), start, end))

    elif relation == 'reply':
        relationdata = getData(db, 'reply', projectid)
        edges = getEdges(relationdata, fulldata, start, end)
        nodes = getAttributes(fulldata, start, end)
        graph = generateGraph(nodes, edges)
        nx.set_node_attributes(graph, getPassiveNodeAttributes(fulldata, edges, start, end))

    elif relation == 'mention':
        relationdata = getData(db, 'full', projectid)
        edges = getMentions(relationdata, start, end)
        nodes = getAttributes(fulldata, start, end)
        graph = generateGraph(nodes, edges)
        nx.set_node_attributes(graph, getPassiveNodeAttributes(fulldata, edges, start, end))

    else:
        print('Please define type of relation.')
        graph = None

    return graph


# Function to calculate centralities/degrees and add them as an attribute to the graph. gtype specifies which
# type of network it is (joint network with multiple relations or singular network)
def addCentralities(g):
    nx.set_node_attributes(g, dict(g.degree()), 'degree')
    nx.set_node_attributes(g, dict(g.in_degree()), 'in_degree')
    nx.set_node_attributes(g, dict(g.out_degree()), 'out_degree')


def calculateCentralities(g, relation):
    if relation == 'total':
        nx.set_node_attributes(g, dict(g.degree()), str('degree_' + relation))
        nx.set_node_attributes(g, dict(g.in_degree()), str('in_degree_' + relation))
        nx.set_node_attributes(g, dict(g.out_degree()), str('out_degree_' + relation))
    else:
        # Create temporary subgraph for type of relation
        sg = nx.MultiDiGraph([(u, v, data) for u, v, data in g.edges(data=True) if data['relation'] == relation])

        if nx.is_empty(sg):
            nx.set_node_attributes(g, None, str('degree_' + relation))
            nx.set_node_attributes(g, None, str('in_degree_' + relation))
            nx.set_node_attributes(g, None, str('out_degree_' + relation))
        else:
            # Set attributes for the temporary subgraph
            nx.set_node_attributes(g, dict(sg.degree()), str('degree_' + relation))
            nx.set_node_attributes(g, dict(sg.in_degree()), str('in_degree_' + relation))
            nx.set_node_attributes(g, dict(sg.out_degree()), str('out_degree_' + relation))


# Function to track role changes across time and save it to a dictionary
def createNestedRoleChanges(db, projectid):
    users = {}
    for x in sorted(getData(db, 'full', projectid), key=lambda x: x['created_at']):
        username = x['user_login']
        userRoleCount = 0
        if username not in users:
            users[username] = {
                'user': username,
                'userid': x['user_id'],
                'projectid': x['project_id'],
                'project_title': x['project_title'],

                'roles': [
                    {
                        'role': x['userRoles'],
                        'assigned_at': x['created_at']
                    }

                ],
                'userRoleCount': userRoleCount + 1
            }
            print('user "' + username + '" with role "' + users[username]['roles'][userRoleCount]['role'] +
                  '", obtained at: ' + str(
                users[username]['roles'][userRoleCount]['assigned_at']) + ' added. The user has ' +
                  str(users[username]['userRoleCount']) + ' roles in total.'
                  )
        elif username in users:
            if any(d['role'] == x['userRoles'] for d in users[username]['roles']):
                print('user already has this role. No role added.')
            else:
                userRoleCount += 1
                users[username]['roles'].append(
                    {
                        'role': x['userRoles'],
                        'assigned_at': x['created_at']
                    }
                )
                users[username]['userRoleCount'] = userRoleCount + 1
                print('user "' + username + '" with role "' + users[username]['roles'][userRoleCount]['role'] +
                      '", obtained at: ' + str(users[username]['roles'][userRoleCount - 1]['assigned_at']) +
                      ' obtained another role "' + users[username]['roles'][userRoleCount]['role'] + '" at ' + str(
                    users[username]['roles'][userRoleCount - 1]['assigned_at']) +
                      '. The user thus has ' + str(users[username]['userRoleCount']) + ' roles in total.')
    return users


# Function to combine two networks and extract union
def extractJointNetwork(db, projectid, start, end):
    reply_network = extractNetwork(db, 'reply', projectid, start, end)
    comment_network = extractNetwork(db, 'comment', projectid, start, end)
    union_network = nx.compose(reply_network, comment_network)

    calculateCentralities(union_network, 'reply')
    calculateCentralities(union_network, 'comment')
    calculateCentralities(union_network, 'total')

    print('Replies: ' + str(reply_network))
    print('Comments: ' + str(comment_network))
    print('Union: ' + str(union_network))

    return union_network


# Function to extract joint network to gephi
def exportJointNetwork(network, projectid):
    for u, v, attr in network.edges(data=True):
        attr["created_at"] = attr["created_at"].strftime("%m/%d/%Y, %H:%M:%S")
    for x in network.nodes(data=True):
        if x[1]['userRoles'] is None:
            x[1]['userRoles'] = "volunteer"
    for x in network.edges(data=True):
        if x[2]['targetRole'] is None:
            x[2]['targetRole'] = "volunteer"
    nx.write_gexf(network, str(projectid + '.gexf'))


# Function to get centralization of given set of centralities
# Adopted from a publicly available GitHub Gist: https://gist.github.com/aldous-rey/e6ee7b0e82e23a686d5440bf3987ee23
def getCentralization(centrality, c_type):
    c_denominator = float(1)
    n_val = float(len(centrality))
    print(str(len(centrality)) + "," + c_type + "\n")

    if c_type == "degree":
        c_denominator = (n_val - 1) * (n_val - 2)

    # start calculations
    c_node_max = max(centrality.values())
    c_sorted = sorted(centrality.values(), reverse=True)
    c_numerator = 0

    for value in c_sorted:
        if c_type == "degree":
            c_numerator += (c_node_max * (n_val - 1) - value * (n_val - 1))
        else:
            c_numerator += (c_node_max - value)

    if c_denominator == 0:
        network_centrality = float(0)
    else:
        network_centrality = float(c_numerator / c_denominator)

    return network_centrality


