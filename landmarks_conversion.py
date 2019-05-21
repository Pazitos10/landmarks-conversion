#!/usr/bin/env python
# coding: utf-8

import os
import argparse
import platform
import re
import pandas as pd
import numpy as np


def get_landmarks_per_individual(df, unique_individuals):
    landmarks_per_individual = [0 for _ in range(len(unique_individuals))]
    for i in df['individual']:
        for idx, u in enumerate(unique_individuals):
            if i == u:
                landmarks_per_individual[idx-1] += 1
    return landmarks_per_individual    

def create_columns(how_many=1):
    #Creates as many columns x, y, z (with numbers) as indicated by `how_many` argument. 
    template = ['x', 'y', 'z']
    columns = []
    for i in range(how_many):
        columns.append(template[0]+str(i+1)) #new x
        columns.append(template[1]+str(i+1)) #new y
        columns.append(template[2]+str(i+1)) #new z
    return columns

def organize_landmarks(landmarks, individual):
    coords = [individual]
    coords.extend(landmarks[['x','y','z']][landmarks['individual']==str(individual)].values.flatten().tolist())
    return [coords]

def get_incomplete_individuals(data):
    # returns the individuals name or id of those who have more or less registered landmarks
    # median ammount of complete columns - 1 (to avoid counting the column named 'individual') / 3 (because are 3D coordinates for each landmark) -> ammount of landmarks
    median = (data.count(1).median() - 1) // 3
    individuals = []
    print("The common ammount of landmarks is: {}".format(median))
    for i in range(data.shape[0]):
        individual = int(data.iloc[i]["individual"])
        cnames = []
        complete_columns = 0
        for c, cname in enumerate(data.columns):
            isnull = pd.isnull(data.iloc[i,c])
            if not isnull:
                complete_columns += 1
        complete_columns = (complete_columns - 1) // 3
        if complete_columns > median:
            print("Individual {} has more landmarks than it should -> {}".format(individual, complete_columns))
            individuals.append(individual)
        if complete_columns < median:
            print("Individual {} has less landmarks than it should -> {}".format(individual, complete_columns))
            individuals.append(str(individual))
    return individuals

### Processing fcsv files (markups from 3dSlicer)

def process_fcsv_files(base_path, fnames, out_name, sep):
    data = None
    for fname in fnames:
        if '.fcsv' in fname:
            match = re.search('P\d+\_\d+', fname)
            if match: 
                individual = match.group(0) #getting individual's name
            else:
                continue

            df = pd.read_csv(base_path+sep+fname, skiprows=2) #skipping header on the fcsv files.
            df = df[df.columns[[1, 2, 3, -3, -1]]] #cleaning and renaming columns
            df.columns = ["x", "y", "z", "label", "individual"]
            df['individual'] = [individual for i in df['individual']]
            df = df[df.columns[[-1, 0, 1, 2, 3]]] #reordering columns
            
            unique_individuals = df['individual'].unique()
            landmarks_per_individual = get_landmarks_per_individual(df, unique_individuals) #how many landmarks there are per individual.

            new_columns = ['individual']
            new_columns.extend(create_columns(max(landmarks_per_individual)))
            landmarks = []
            for u in unique_individuals:
                landmarks.extend(organize_landmarks(df, u))

            if data is None:
                data = pd.DataFrame(data=landmarks, columns=new_columns)
            else:
                data = data.append(pd.DataFrame(data=landmarks, columns=new_columns), sort=False)
    
    if data is None:
        print('There is not .fcsv files on {}. Please, use a valid directory.'.format(base_path))
    else:        
        data.to_csv(out_name, index=None)
        print('Data saved succesfully on {}'.format(out_name))
        #return data

### Processing .pts files (raw from Landmark)

def process_pts_files(base_path, fnames, out_name, sep):
    data = None
    for fname in fnames:
        if '.pts' in fname:
            #preprocessing
            individual = fname.split('.pts')[0].split(sep)[-1] #getting individual's name
            df = pd.read_csv(base_path+sep+fname, skiprows=1, delim_whitespace=True).reset_index() #reads pts file
            col_names = df.columns
            df = df.rename(index=str, columns={col_names[0]:"landmark_id", col_names[1]: "x", col_names[2]: "y", col_names[3]: "z"}) #renaming the columns
            col_ind = [individual for _ in range(df.shape[0])] # creating a column filled with the individual's name
            df = df.assign(individual=pd.Series(col_ind).values) # adding that column to the end
            new_order = [-1, 0, 1, 2, 3]
            df = df[df.columns[new_order]] # reordering columns to get the name one at first.

            #Giving data its final format
            new_columns = ['individual']
            new_columns.extend(create_columns(df.shape[0]))
            landmarks = organize_landmarks(df, individual)
            if data is None:
                data = pd.DataFrame(data=landmarks, columns=new_columns)
            else:
                data = data.append(pd.DataFrame(data=landmarks, columns=new_columns), sort=False)
    
    if data is None:
        print('There is not .pts files on \'{}\'. Please, use a valid directory.'.format(base_path))
    else:
        incomplete_data = get_incomplete_individuals(data)
        if incomplete_data:
            incomplete_rows = data.query("individual in {}".format(incomplete_data))
            incomplete_rows = incomplete_rows[data.columns] #reordering columns
            incomplete_rows.to_csv('datos_incompletos.csv', index=None) # saving incomplete data in a separated file
            data.drop(incomplete_rows.index) # removing incomplete rows from original data
            data.dropna(1) # removes empty columns
        data.to_csv(out_name, index=None)
        print('Data saved succesfully on \'{}\''.format(out_name))
        return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=str, help="Data directory.")
    parser.add_argument("--mode", help="[fcsv | pts]. Indicates if the script will process .fcsv files or .pts files.", default='fcsv')
    parser.add_argument("-o", "--output-file-name", help="Output file name (full path). By default it will be in the script folder.", default='output.csv')
    args = parser.parse_args()
    base_path = args.directory
    out_name = args.output_file_name
    fnames = []
    if os.path.exists(base_path):
        fnames = os.listdir(base_path)
        fnames.sort()
    else:
        print("Empty directory")

    sep = '\\' if platform.system == 'Windows' else '/'
    if args.mode == 'fcsv' and len(fnames) > 0:
        #print("processing fcsv files in {}".format(base_path))
        process_fcsv_files(base_path, fnames, out_name, sep)
    elif args.mode == 'pts' and len(fnames) > 0:
        #print("processing pts files in {}".format(base_path))
        process_pts_files(base_path, fnames, out_name, sep)
    elif args.mode != 'fcsv' and args.mode != 'pts':
        print("Unknown mode. Try with \'fcsv\' or \'pts\'.")
                
