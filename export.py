import json
import functions
import functions as f
import networkx as nx
from datetime import datetime
import pandas as pd
import pathlib


# Export network data to R-friendly CSV. As in case of specifying a particular timeframe certain graphs might be empty,
# empty columns need to be created to allow for later merging in R

# Function to extract the quarter for a given datetime object
def getQuarter(dateobject):
    return (dateobject.month - 1) // 3 + 1


# Function to extract a CSV with the node- and edge lists of a network for a given project and time frame
def exportUserTrajectory(db, t1, t2, project_id, project_title, delims):
    for year in range(t1, t2):
        for q, d in delims.items():
            start = datetime(year, d['start_m'], d['start_d'])
            end = datetime(year, d['end_m'], d['end_d'])
            graph = f.extractJointNetwork(db, projectid=project_id, start=start, end=end)
            pathlib.Path('export/trajectories/' + project_id + '/nodes/').mkdir(parents=True, exist_ok=True)
            pathlib.Path('export/trajectories/' + project_id + '/edges/').mkdir(parents=True, exist_ok=True)
            if nx.is_empty(graph):
                nodes = pd.DataFrame.from_dict(dict(graph.nodes(data=True)), orient='index')
                nodes['user_id'] = ''
                nodes['userRoles'] = ''
                nodes['degree_reply'] = ''
                nodes['in_degree_reply'] = ''
                nodes['out_degree_reply'] = ''
                nodes['degree_comment'] = ''
                nodes['in_degree_comment'] = ''
                nodes['out_degree_comment'] = ''
                nodes['degree_total'] = ''
                nodes['in_degree_total'] = ''
                nodes['out_degree_total'] = ''
                nodes['user'] = ''
                nodes['project id'] = project_id
                nodes['time'] = start
                nodes['project_title'] = project_title
                nodes['reciprocity'] = ''
                nodes['centralisation'] = ''
                nodes.to_csv(
                    str("export/trajectories/" + project_id + "/nodes/nodes_" + project_id + str(year) + "_q" + str(
                        getQuarter(start)) + ".csv"), index=True)
                edges = nx.to_pandas_edgelist(graph)
                edges['source'] = ''
                edges['target'] = ''
                edges['discussion_title'] = ''
                edges['project_id'] = ''
                edges['discussion_id'] = ''
                edges['created_at'] = ''
                edges['board_title'] = ''
                edges['user_id'] = ''
                edges['userRoles'] = ''
                edges['project_title'] = project_title
                edges['relation'] = ''
                edges['body'] = ''
                edges['time'] = start
                edges['reciprocity'] = ''
                edges['centralisation'] = ''
                edges.to_csv(
                    str("export/trajectories/" + project_id + "/edges/edges_" + project_id + str(year) + "_q" + str(
                        getQuarter(start)) + ".csv"), index=True)
                print("Not done for network: " + project_id + " in " "q" + str(getQuarter(start)) + " " + str(year))
            else:
                nodes = pd.DataFrame.from_dict(dict(graph.nodes(data=True)), orient='index')
                nodes['user'] = nodes.index
                nodes['project id'] = project_id
                nodes['time'] = start
                nodes['project_title'] = project_title
                nodes['reciprocity'] = nx.reciprocity(graph)
                nodes['centralisation'] = f.getCentralization(nx.degree_centrality(graph),'degree')
                nodes.to_csv(
                    str("export/trajectories/" + project_id + "/nodes/nodes_" + project_id + str(year) + "_q" + str(
                        getQuarter(start)) + ".csv"), index=True)
                edges = nx.to_pandas_edgelist(graph)
                edges['time'] = start
                edges['reciprocity'] = nx.reciprocity(graph)
                edges['centralisation'] = f.getCentralization(nx.degree_centrality(graph), 'degree')
                edges.to_csv(
                    str("export/trajectories/" + project_id + "/edges/edges_" + project_id + str(year) + "_q" + str(
                        getQuarter(start)) + ".csv"), index=True)
                print("Done for network: " + project_id + " in " "q" + str(getQuarter(start)) + " " + str(year))


# Function to export the role changes to CSV
def exportRoleChanges(db, projectids):
    pathlib.Path('export/rolechanges/').mkdir(parents=True, exist_ok=True)
    for x, y in projectids.items():
        dic = f.createNestedRoleChanges(db, x)
        list_of_dicts = [value for value in dic.values()]
        df = pd.json_normalize(list_of_dicts,
                               record_path='roles',
                               meta=['user', 'userid', 'projectid', 'userRoleCount', 'project_title'])
        df.to_csv(str('export/rolechanges/' + x + '_rolechanges.csv'))


# Function to export all comments for descriptive analyses
def exportComments(db, ids):
    output = pd.DataFrame()

    for x in ids:
        data = functions.getData(db, "full", x)
        data = pd.DataFrame(data)
        output = pd.concat([output, data])

    pathlib.Path('export/comments/').mkdir(parents=True, exist_ok=True)
    output.to_csv('export/comments/comments.csv')


# Function to export network data into R-friendly CSV for all projects, time-independent
def exportNetworkDataTotal(db, projectids, ntype):
    pathlib.Path('export/totalnetworkdata/nodes/').mkdir(parents=True, exist_ok=True)
    pathlib.Path('export/totalnetworkdata/edges/').mkdir(parents=True, exist_ok=True)
    if ntype == 'reply':
        relation = 'reply'

        for x, y in projectids.items():
            graph = f.extractNetwork(db, networktype=relation, projectid=x, start=None, end=None)
            nodes = pd.DataFrame.from_dict(dict(graph.nodes(data=True)), orient='index')
            nodes['user'] = nodes.index
            nodes['project id'] = x
            nodes['project_title'] = y
            nodes['reciprocity'] = nx.reciprocity(graph)
            nodes['centralisation'] = f.getCentralization(nx.degree_centrality(graph), 'degree')
            nodes.to_csv(str("export/totalnetworkdata/nodes/" + x + "_reply.csv"), index=True)
            edges = nx.to_pandas_edgelist(graph)
            edges.to_csv(str("export/totalnetworkdata/edges/" + x + "_reply.csv"), index=True)
    if ntype == 'joint':
        for x, y in projectids.items():
            graph = f.extractJointNetwork(db=db, projectid=x, start=None, end=None)
            nodes = pd.DataFrame.from_dict(dict(graph.nodes(data=True)), orient='index')
            nodes['user'] = nodes.index
            nodes['project id'] = x
            nodes['project_title'] = y
            nodes['reciprocity'] = nx.reciprocity(graph)
            nodes['centralisation'] = f.getCentralization(nx.degree_centrality(graph), 'degree')
            nodes.to_csv(str("export/totalnetworkdata/nodes/" + x + "_joint.csv"), index=True)
            edges = nx.to_pandas_edgelist(graph)
            edges.to_csv(str("export/totalnetworkdata/edges/" + x + "_joint.csv"), index=True)


# Function to export CSV files for multiple projects in a row
def exportUserTrajectories(db, start, end, projects, delims):
    for x, y in projects.items():
        exportUserTrajectory(db, start, end, x, y, delims)
        print('User trajectory for project "' + y + '" created and exported.')
    print('All user trajectories exported')


# Function to export annotations
def exportAnnotations(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    for elem in data['projects']:
        for obj in elem['annotations']:
            obj['date'] = datetime.fromtimestamp(obj['date'] / 1000)

    df = pd.json_normalize(data['projects'],  record_path='annotations',meta=['name'])
    pathlib.Path('export/annotations/').mkdir(parents=True, exist_ok=True)
    df.to_csv('export/annotations/annotations.csv')