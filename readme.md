# Readme

In this repository, you'll find all the code associated with the data extraction, creation of the network and provision of analysable data in the context of the conference paper *"Does Volunteer Engagement Pay Off? An Analysis of User Participation in Online Citizen Science Projects"* held during the CollabTech 2022 conference in Santiago, Chile. The paper can be found here: https://link.springer.com/chapter/10.1007/978-3-031-20218-6_5.

To run the script(s), several packages are needed, which can be seen in the `import`
paragraph at the top of the scripts. The scripts were designed to communicate with a
local **MongoDB** database, where the whole dataset provided by UPF resides, 
and which the scripts access in order to start the data wrangling process. The data from the database can be found here: LINK TO ZENODO DATASET 


The analysis pipeline is structured as follows. The scripts can be started within the `main.py`.
There, information on the database information first needs to be given:

```` 
localhost = Your localhost IP-adress (most likely 127.0.0.1)
port = The port where your MongoDB runs
````

You then can specify the name of your DB, like so:
```
db = client['zooniverse']
```

and then, desired functions can be triggered. The necessary functions to generate the networks reside in the `functions.py` file, the ones necessary for the export of data reside in the `export.py`.

The functions which can be used to replicate the results can be found in the code:

````
export.exportAnnotations('annotations.json')
export.exportUserTrajectories(db, 2016, 2022, project_ids, delims)
export.exportNetworkDataTotal(db, project_ids, 'joint')
export.exportComments(db,project_ids)
export.exportRoleChanges(db, project_ids)
````

These functions generate the output files, which in turn can be found in the `export/` folder.
